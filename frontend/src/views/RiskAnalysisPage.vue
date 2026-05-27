<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { risk as riskApi, createSSEStream } from '@/services/api'
import { useUIStore } from '@/stores/ui'
import PageHeader from '@/components/layout/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import MarkdownRenderer from '@/components/common/MarkdownRenderer.vue'
import StreamingIndicator from '@/components/common/StreamingIndicator.vue'

const route = useRoute()
const ui = useUIStore()
const projectId = route.params.id

const assessment = ref(null)
const loading = ref(true)
const generating = ref(false)
const streamingText = ref('')

const GRID_SIZE = 5
const levelColors = { low: '#d1fae5', medium: '#fef3c7', high: '#fee2e2', critical: '#fecaca' }
const levelText = { low: '#065f46', medium: '#92400e', high: '#991b1b', critical: '#7f1d1d' }

onMounted(async () => {
  try {
    assessment.value = await riskApi.get(projectId)
  } catch { assessment.value = null }
  loading.value = false
})

const generate = async () => {
  generating.value = true
  streamingText.value = ''
  try {
    const stream = createSSEStream(`/api/projects/${projectId}/risk-assessment/generate/`, { method: 'POST', body: {} })
    for await (const event of stream) {
      if (event.type === 'text_delta') streamingText.value += event.text
    }
    assessment.value = await riskApi.get(projectId)
    ui.addToast('Risk assessment generated', 'success')
  } catch {
    ui.addToast('Generation failed', 'error')
  } finally {
    generating.value = false }
}

const factors = (assessment) => assessment?.risk_factors || []
</script>

<template>
  <div>
    <PageHeader title="Risk Analysis">
      <template #actions>
        <button class="btn btn-primary" :disabled="generating" @click="generate">
          {{ generating ? 'Generating...' : '🤖 Generate AI Assessment' }}
        </button>
      </template>
    </PageHeader>

    <div v-if="loading" style="text-align:center;padding:48px"><LoadingSpinner size="lg" /></div>

    <div v-else>
      <div v-if="generating || streamingText" class="card mb-4">
        <div class="flex items-center gap-3 mb-4">
          <div class="card-title" style="margin-bottom:0">Generating Risk Assessment</div>
          <StreamingIndicator v-if="generating" />
        </div>
        <MarkdownRenderer :content="streamingText" />
      </div>

      <div v-if="assessment && factors(assessment).length">
        <div class="card mb-4">
          <div class="card-title">Risk Heat Map</div>
          <div style="position:relative;width:320px;height:320px;border:1px solid var(--border);border-radius:8px;overflow:hidden">
            <div style="position:absolute;inset:0;display:grid;grid-template-columns:repeat(5,1fr);grid-template-rows:repeat(5,1fr)">
              <div v-for="i in 25" :key="i"
                :style="`background:${i <= 5 ? '#d1fae5' : i <= 15 ? '#fef3c7' : '#fee2e2'};opacity:0.4;border:1px solid #fff`"
              />
            </div>
            <div style="position:absolute;bottom:0;left:0;right:0;height:20px;text-align:center;font-size:10px;color:var(--text-muted)">Probability →</div>
            <div style="position:absolute;top:0;bottom:0;left:0;width:20px;display:flex;align-items:center;justify-content:center;font-size:10px;color:var(--text-muted);writing-mode:vertical-rl">Impact →</div>
            <div
              v-for="f in factors(assessment)"
              :key="f.category"
              style="position:absolute;width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;cursor:pointer;transform:translate(-50%,-50%)"
              :title="`${f.category}: ${f.rationale}`"
              :style="`left:${((f.probability||2)/GRID_SIZE)*100}%;top:${100-((f.impact||2)/GRID_SIZE)*100}%;background:${levelColors[f.level]};color:${levelText[f.level]}`"
            >{{ f.category?.[0]?.toUpperCase() }}</div>
          </div>
          <p class="text-muted text-sm mt-4" style="margin-top:8px">X axis: Probability (1-5), Y axis: Impact (1-5)</p>
        </div>

        <div class="card">
          <div class="card-title">Risk Factors</div>
          <div style="display:flex;flex-direction:column;gap:8px">
            <div v-for="f in factors(assessment)" :key="f.category" class="card" style="padding:12px">
              <div class="flex items-center justify-between mb-2">
                <span class="font-bold text-sm">{{ f.category }}</span>
                <span :class="['badge', `badge-risk-${f.level}`]">{{ f.level }}</span>
              </div>
              <p class="text-sm text-muted" style="margin:0">{{ f.rationale }}</p>
              <div class="text-sm mt-4" style="margin-top:4px">
                Probability: {{ f.probability || '?' }}/5 · Impact: {{ f.impact || '?' }}/5
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="!generating">
        <div class="empty-state">
          <div style="font-size:48px">🛡️</div>
          <h3>No risk assessment yet</h3>
          <p>Click "Generate AI Assessment" to analyze this project's risks using clinical trial data, literature, and compound properties.</p>
        </div>
      </div>
    </div>
  </div>
</template>
