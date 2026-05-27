<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useExperimentStore } from '@/stores/experiments'
import { createSSEStream } from '@/services/api'
import { useUIStore } from '@/stores/ui'
import PageHeader from '@/components/layout/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import MarkdownRenderer from '@/components/common/MarkdownRenderer.vue'
import StreamingIndicator from '@/components/common/StreamingIndicator.vue'

const route = useRoute()
const expStore = useExperimentStore()
const ui = useUIStore()

const id = route.params.id
const notes = ref('')
const resultData = ref({})
const submitting = ref(false)
const interpreting = ref(false)
const streamingText = ref('')
const interpretation = ref('')
const selectedDecision = ref('')

onMounted(() => expStore.fetchExperiment(id))

const submitResults = async () => {
  submitting.value = true
  try {
    await expStore.submitResults(id, {
      result_data: resultData.value,
      notes: notes.value,
      decision: selectedDecision.value,
      interpretation: interpretation.value,
    })
    ui.addToast('Results logged', 'success')
    notes.value = ''
    resultData.value = {}
  } catch {
    ui.addToast('Failed to save results', 'error')
  } finally {
    submitting.value = false }
}

const interpret = async () => {
  interpreting.value = true
  streamingText.value = ''
  try {
    const stream = createSSEStream(`/api/experiments/${id}/interpret/`, { method: 'POST', body: {} })
    for await (const event of stream) {
      if (event.type === 'text_delta') streamingText.value += event.text
      else if (event.type === 'message_stop') interpretation.value = streamingText.value
    }
  } catch {
    ui.addToast('Interpretation failed', 'error')
  } finally {
    interpreting.value = false }
}

const decisions = ['optimize', 'reproduce', 'scale', 'abort']
const decisionColors = { optimize: 'primary', reproduce: 'purple', scale: 'green', abort: 'red' }
</script>

<template>
  <div>
    <div v-if="expStore.loading" style="text-align:center;padding:48px"><LoadingSpinner size="lg" /></div>
    <div v-else-if="expStore.currentExperiment">
      <PageHeader :title="expStore.currentExperiment.title">
        <template #actions>
          <span :class="['badge', `badge-${expStore.currentExperiment.status}`]">
            {{ expStore.currentExperiment.status }}
          </span>
        </template>
      </PageHeader>

      <div class="grid-2 mb-4" style="align-items:start">
        <div>
          <div class="card mb-4">
            <div class="card-title">Experiment Details</div>
            <div class="text-sm" style="display:flex;flex-direction:column;gap:6px">
              <div><span class="text-muted">Type:</span> {{ expStore.currentExperiment.experiment_type }}</div>
              <div><span class="text-muted">Objective:</span> {{ expStore.currentExperiment.objective }}</div>
              <div v-if="expStore.currentExperiment.success_criteria"><span class="text-muted">Success criteria:</span> {{ expStore.currentExperiment.success_criteria }}</div>
            </div>
          </div>

          <div class="card mb-4">
            <div class="card-title">Log Results</div>
            <div class="form-group">
              <label class="form-label">Key Metrics (JSON)</label>
              <textarea
                class="form-control"
                rows="4"
                placeholder='{"yield": 85, "purity": 98.5, "pH": 6.8}'
                @change="e => { try { resultData = JSON.parse(e.target.value) } catch {} }"
              />
            </div>
            <div class="form-group">
              <label class="form-label">Notes / Observations</label>
              <textarea v-model="notes" class="form-control" rows="3" placeholder="Observations, anomalies, conditions..." />
            </div>

            <div class="mb-4">
              <label class="form-label">Decision</label>
              <div class="flex gap-2" style="flex-wrap:wrap">
                <button
                  v-for="d in decisions"
                  :key="d"
                  :class="['btn btn-sm', selectedDecision === d ? 'btn-primary' : 'btn-secondary']"
                  @click="selectedDecision = d"
                >{{ d }}</button>
              </div>
            </div>

            <div class="flex gap-2">
              <button class="btn btn-primary" :disabled="submitting" @click="submitResults">
                {{ submitting ? 'Saving...' : 'Log Results' }}
              </button>
              <button class="btn btn-secondary" :disabled="interpreting" @click="interpret">
                {{ interpreting ? 'Interpreting...' : '🤖 AI Interpret' }}
              </button>
            </div>
          </div>
        </div>

        <div>
          <div class="card mb-4">
            <div class="flex items-center justify-between mb-4">
              <div class="card-title" style="margin-bottom:0">AI Interpretation</div>
              <StreamingIndicator v-if="interpreting" />
            </div>
            <div v-if="!streamingText && !interpretation" class="text-muted text-sm">
              Submit results and click "AI Interpret" to get Claude's analysis.
            </div>
            <MarkdownRenderer :content="streamingText || interpretation" />
          </div>

          <div class="card">
            <div class="card-title">Results History</div>
            <div v-if="!expStore.results.length" class="text-muted text-sm">No results logged yet.</div>
            <div v-else style="display:flex;flex-direction:column;gap:8px">
              <div v-for="r in expStore.results" :key="r.id" class="card" style="padding:12px">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-sm text-muted">{{ new Date(r.recorded_at).toLocaleDateString() }}</span>
                  <span v-if="r.decision" :class="['badge', `badge-${r.decision === 'abort' ? 'failed' : 'active'}`]">{{ r.decision }}</span>
                </div>
                <pre style="font-size:12px;overflow:auto;max-height:100px">{{ JSON.stringify(r.result_data, null, 2) }}</pre>
                <p v-if="r.notes" class="text-sm text-muted mt-4" style="margin-top:4px">{{ r.notes }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
