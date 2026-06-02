<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '@/components/layout/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useAnalogsStore } from '@/stores/analogs'
import { useSARStore } from '@/stores/sar'
import { useUIStore } from '@/stores/ui'
import { projects as projectsApi, analogs as analogsApi } from '@/services/api'

const route = useRoute()
const projectId = route.params.id
const analogsStore = useAnalogsStore()
const sarStore = useSARStore()
const ui = useUIStore()

const project = ref(null)
const hasReferenceDrug = computed(() => project.value?.investigations?.length > 0)
const isAnalogBased = computed(() => !project.value || project.value.pathway === 'analog_based')

// Selection gate state
const selectingId = ref(null)
const selectRationale = ref('')
const selecting = ref(false)
const selectedCandidate = computed(() => analogsStore.shortlisted?.find(c => c.selected))

function startSelect(candidate) {
  selectingId.value = candidate.id
  selectRationale.value = ''
}

function cancelSelect() {
  selectingId.value = null
}

async function confirmSelect(candidate) {
  selecting.value = true
  try {
    await analogsApi.update(candidate.id, { selected: true })
    candidate.selected = true
    selectingId.value = null
    ui.addToast(`${candidate.smiles.slice(0, 20)}… selected as development candidate`, 'success')
  } catch {
    ui.addToast('Failed to select candidate', 'error')
  } finally {
    selecting.value = false
  }
}

onMounted(async () => {
  sarStore.fetchEntries(projectId)
  try { project.value = await projectsApi.get(projectId) } catch { /* non-critical */ }
})
</script>

<template>
  <div>
    <PageHeader title="Candidate Selection">
      <template #actions>
        <RouterLink v-if="hasReferenceDrug" :to="`/analogs?project=${projectId}`" class="btn btn-secondary">Analog Workspace</RouterLink>
        <RouterLink v-else :to="`/projects/${projectId}/edit`" class="btn btn-secondary">Set Reference Drug First</RouterLink>
        <RouterLink :to="`/projects/${projectId}/sar`" class="btn btn-primary">SAR Tracker</RouterLink>
      </template>
    </PageHeader>

    <!-- No reference drug warning -->
    <div v-if="isAnalogBased && !hasReferenceDrug && project" class="card mb-4" style="border:2px solid #f59e0b;background:#fffbeb">
      <div style="display:flex;align-items:center;gap:12px">
        <span style="font-size:28px">⚗️</span>
        <div style="flex:1">
          <strong>No reference drug selected</strong>
          <p class="text-muted" style="font-size:13px;margin:4px 0 0">
            This analog-based project needs a reference drug before you can search for analogs.
            Set one in the project settings.
          </p>
        </div>
        <RouterLink :to="`/projects/${projectId}/edit`" class="btn btn-primary">Set Reference Drug →</RouterLink>
      </div>
    </div>

    <!-- Development candidate selected banner -->
    <div v-if="selectedCandidate" class="card mb-4" style="border:2px solid #16a34a;background:#f0fdf4">
      <div style="display:flex;align-items:center;gap:12px">
        <span style="font-size:28px">✓</span>
        <div style="flex:1">
          <strong>Development candidate selected</strong>
          <p class="text-muted text-sm" style="margin:4px 0 0;font-family:monospace;font-size:11px">
            {{ selectedCandidate.smiles }}
          </p>
        </div>
        <RouterLink
          :to="`/synthesis?project=${projectId}&smiles=${encodeURIComponent(selectedCandidate.smiles)}&type=retro`"
          class="btn btn-primary"
        >Begin Synthesis Planning →</RouterLink>
      </div>
    </div>

    <div class="card mb-4">
      <h3 class="card-title">Shortlisted Analog Candidates</h3>
      <div v-if="analogsStore.shortlisted?.length">
        <table class="data-table">
          <thead>
            <tr>
              <th>SMILES</th>
              <th>Similarity Score</th>
              <th>Patent Status</th>
              <th>ADMET Risk</th>
              <th>Synthesis Plan</th>
              <th>Select</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in analogsStore.shortlisted" :key="c.id" :style="c.selected ? 'background:#f0fdf4' : ''">
              <td style="font-family:monospace;font-size:11px;max-width:180px;overflow:hidden;text-overflow:ellipsis">{{ c.smiles }}</td>
              <td>{{ c.similarity_score?.toFixed(2) }}</td>
              <td>
                <span :class="`badge badge-${c.patent_status === 'free' ? 'success' : c.patent_status === 'covered' ? 'danger' : 'warning'}`">
                  {{ c.patent_status }}
                </span>
              </td>
              <td>
                <span v-if="c.admet" class="text-muted">Checked</span>
                <span v-else class="text-muted">Not checked</span>
              </td>
              <td>
                <div class="flex gap-1">
                  <RouterLink :to="`/synthesis?project=${projectId}&smiles=${encodeURIComponent(c.smiles)}&type=retro`" class="btn btn-sm btn-primary">Retro</RouterLink>
                  <RouterLink :to="`/synthesis?project=${projectId}&smiles=${encodeURIComponent(c.smiles)}&type=tree`" class="btn btn-sm btn-secondary">Tree</RouterLink>
                </div>
              </td>
              <td>
                <span v-if="c.selected" style="color:#16a34a;font-weight:600;font-size:12px">✓ Selected</span>
                <template v-else-if="selectingId === c.id">
                  <div style="display:flex;flex-direction:column;gap:4px;min-width:180px">
                    <input v-model="selectRationale" class="form-control" placeholder="Rationale (optional)" style="font-size:11px;padding:4px 8px" />
                    <div class="flex gap-1">
                      <button class="btn btn-sm btn-primary" :disabled="selecting" @click="confirmSelect(c)">
                        {{ selecting ? '…' : 'Confirm' }}
                      </button>
                      <button class="btn btn-sm btn-secondary" @click="cancelSelect">Cancel</button>
                    </div>
                  </div>
                </template>
                <button v-else class="btn btn-sm btn-secondary" @click="startSelect(c)">Select →</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <EmptyState v-else title="No shortlisted candidates" message="Go to the Analog Workspace to search and shortlist candidates." />
    </div>

    <div class="card">
      <h3 class="card-title">SAR Context</h3>
      <LoadingSpinner v-if="sarStore.loading" />
      <div v-else-if="sarStore.entries.length">
        <p class="text-muted">{{ sarStore.entries.length }} SAR entries logged. Key activities:</p>
        <table class="data-table">
          <thead>
            <tr><th>R-Group</th><th>Activity</th><th>Type</th></tr>
          </thead>
          <tbody>
            <tr v-for="e in sarStore.entries.slice(0, 10)" :key="e.id">
              <td>{{ e.r_group || '-' }}</td>
              <td>{{ e.activity_value }} {{ e.activity_unit }}</td>
              <td>{{ e.activity_type }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <EmptyState v-else title="No SAR data" message="Add SAR entries to inform candidate selection." />
    </div>
  </div>
</template>
