<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '@/components/layout/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useVirtualScreeningStore } from '@/stores/virtual_screening'
import { targets as targetsApi } from '@/services/api'

const route = useRoute()
const store = useVirtualScreeningStore()

const allProfiles = ref([])
const selectedProfileId = ref(route.query.target || null)
const selectedLibrary = ref('fda_approved')
const customSmiles = ref('')

const libraries = [
  { value: 'fda_approved', label: 'FDA Approved' },
  { value: 'clinical_candidates', label: 'Clinical Candidates' },
  { value: 'fragments', label: 'Fragment Library' },
  { value: 'custom', label: 'Custom SMILES' },
]

async function loadProfiles() {
  try {
    allProfiles.value = await targetsApi.listProfiles()
    if (selectedProfileId.value) {
      const profile = allProfiles.value.find(p => String(p.id) === String(selectedProfileId.value))
      if (profile) store.targetProfile = profile
    }
  } catch {}
}

function selectProfile(profile) {
  store.targetProfile = profile
  selectedProfileId.value = profile.id
}

async function startScreening() {
  const smiles = selectedLibrary.value === 'custom'
    ? customSmiles.value.split('\n').map(s => s.trim()).filter(Boolean)
    : null
  await store.startScreening(selectedLibrary.value, smiles)
}

const statusColors = { pending: '#6b7280', running: '#3b82f6', complete: '#10b981', failed: '#ef4444' }

onMounted(loadProfiles)
onUnmounted(() => store._stopPolling())
</script>

<template>
  <div>
    <PageHeader title="Virtual Screening">
      <template #actions>
        <button
          class="btn btn-primary"
          :disabled="!store.targetProfile || store.isRunning"
          @click="startScreening"
        >
          {{ store.isRunning ? 'Screening...' : 'Start Screening' }}
        </button>
      </template>
    </PageHeader>

    <div class="grid-2 mb-4" style="align-items:start">
      <!-- Target Selection -->
      <div class="card">
        <h3 class="card-title">Target</h3>
        <div v-if="allProfiles.length" style="max-height:250px;overflow-y:auto">
          <div
            v-for="p in allProfiles" :key="p.id"
            class="list-item"
            :class="{ selected: store.targetProfile?.id === p.id }"
            style="cursor:pointer"
            @click="selectProfile(p)"
          >
            <strong>{{ p.gene_symbol || p.uniprot_id }}</strong>
            <span v-if="p.selected_pdb_id" class="badge badge-info" style="margin-left:8px">{{ p.selected_pdb_id }}</span>
            <span v-else class="badge badge-warning" style="margin-left:8px">No PDB</span>
          </div>
        </div>
        <EmptyState v-else title="No target profiles" message="Create a target profile first." />
      </div>

      <!-- Library & Run Config -->
      <div class="card">
        <h3 class="card-title">Library</h3>
        <div class="form-group">
          <label>Compound Library</label>
          <select v-model="selectedLibrary" class="form-input">
            <option v-for="lib in libraries" :key="lib.value" :value="lib.value">{{ lib.label }}</option>
          </select>
        </div>
        <div v-if="selectedLibrary === 'custom'" class="form-group">
          <label>SMILES (one per line)</label>
          <textarea v-model="customSmiles" class="form-input" rows="6" placeholder="CC(=O)Oc1ccccc1C(=O)O" />
        </div>

        <!-- Run status -->
        <div v-if="store.currentRun" class="status-block" :style="{ borderLeft: `4px solid ${statusColors[store.currentRun.status]}` }">
          <strong>Run #{{ store.currentRun.id }}</strong>
          <span class="badge" :style="{ backgroundColor: statusColors[store.currentRun.status], color: '#fff', marginLeft: '8px' }">
            {{ store.currentRun.status }}
          </span>
          <div v-if="store.currentRun.result_count" class="text-muted">
            {{ store.currentRun.result_count }} hits found
          </div>
          <div v-if="store.currentRun.error_message" class="text-danger">{{ store.currentRun.error_message }}</div>
        </div>
      </div>
    </div>

    <!-- Hits Table -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Screening Hits</h3>
        <div style="display:flex;gap:8px">
          <button v-if="store.hits.length" class="btn btn-sm btn-secondary" @click="store.checkADMET(store.hits.map(h => h.id))">
            Check ADMET
          </button>
          <button v-if="store.hits.length" class="btn btn-sm btn-secondary" @click="store.checkPatents(store.hits.map(h => h.id))">
            Check Patents
          </button>
        </div>
      </div>

      <LoadingSpinner v-if="store.loading.hits" />

      <table v-else-if="store.hits.length" class="data-table">
        <thead>
          <tr>
            <th>SMILES</th>
            <th>Docking Score</th>
            <th>Patent</th>
            <th>Shortlist</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="hit in store.hits" :key="hit.id">
            <td style="font-family:monospace;font-size:11px;max-width:200px;overflow:hidden;text-overflow:ellipsis">{{ hit.smiles }}</td>
            <td>{{ hit.docking_score?.toFixed(2) ?? '-' }} kcal/mol</td>
            <td>
              <span :class="{ 'badge-success': hit.patent_status === 'free', 'badge-danger': hit.patent_status === 'covered', 'badge': true }">
                {{ hit.patent_status }}
              </span>
            </td>
            <td>
              <input type="checkbox" :checked="hit.shortlisted" @change="store.toggleShortlist(hit)" />
            </td>
          </tr>
        </tbody>
      </table>

      <EmptyState v-else title="No hits yet" message="Run a screening to see results here." />
    </div>
  </div>
</template>
