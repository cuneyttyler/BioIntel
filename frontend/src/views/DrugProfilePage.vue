<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { drugs as drugsApi, investigations as investApi } from '@/services/api'
import { useUIStore } from '@/stores/ui'
import PageHeader from '@/components/layout/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const route = useRoute()
const router = useRouter()
const ui = useUIStore()
const chemblId = route.params.chembl_id

const detail = ref(null)
const synthesis = ref([])
const trials = ref([])
const patents = ref([])
const loading = ref({ detail: true, synthesis: true, trials: true, patents: true })
const starting = ref(false)

onMounted(async () => {
  const [d, s, t, p] = await Promise.allSettled([
    drugsApi.get(chemblId),
    drugsApi.synthesis(chemblId),
    drugsApi.trials(chemblId),
    drugsApi.patents(chemblId),
  ])
  detail.value = d.status === 'fulfilled' ? d.value : null
  synthesis.value = s.status === 'fulfilled' ? (Array.isArray(s.value) ? s.value : []) : []
  trials.value = t.status === 'fulfilled' ? (Array.isArray(t.value) ? t.value : []) : []
  patents.value = p.status === 'fulfilled' ? (Array.isArray(p.value) ? p.value : []) : []
  Object.keys(loading.value).forEach(k => loading.value[k] = false)
})

const molecule = () => detail.value?.molecule || {}
const mechanisms = () => detail.value?.mechanisms || []
const formulation = () => detail.value?.formulation || {}

const startAnalogSearch = async () => {
  const mol = molecule()
  const smiles = mol.molecule_structures?.canonical_smiles || ''
  if (!smiles) { ui.addToast('No SMILES available for this drug', 'error'); return }
  starting.value = true
  try {
    const inv = await investApi.create({
      chembl_id: chemblId,
      name: mol.pref_name || chemblId,
      smiles,
    })
    router.push(`/investigations/${inv.id}`)
  } catch {
    ui.addToast('Failed to start investigation', 'error')
  } finally {
    starting.value = false
  }
}

const patentExpiry = (patent) => {
  const filing = patent.filing_date || patent.date || ''
  if (!filing) return '—'
  try {
    const year = /^\d{4}$/.test(filing) ? parseInt(filing) : new Date(filing).getFullYear()
    return `~${year + 20}`
  } catch { return '—' }
}
</script>

<template>
  <div>
    <PageHeader :title="molecule().pref_name || chemblId">
      <template #actions>
        <button class="btn btn-primary" :disabled="starting" @click="startAnalogSearch">
          {{ starting ? 'Starting...' : '🧪 Start Analog Search' }}
        </button>
      </template>
    </PageHeader>

    <!-- Identity -->
    <div class="card mb-4">
      <div v-if="loading.detail" style="text-align:center;padding:24px"><LoadingSpinner /></div>
      <div v-else-if="detail">
        <div class="flex items-center gap-2 mb-4" style="flex-wrap:wrap;margin-bottom:12px">
          <span class="badge badge-completed">{{ chemblId }}</span>
          <span v-if="molecule().max_phase" class="badge badge-phase1">Phase {{ molecule().max_phase }}</span>
          <span v-if="molecule().molecule_type" class="badge badge-active">{{ molecule().molecule_type }}</span>
        </div>
        <div class="grid-2">
          <div>
            <div class="text-muted text-sm" style="margin-bottom:4px">SMILES</div>
            <code style="font-size:12px;word-break:break-all">{{ molecule().molecule_structures?.canonical_smiles || '—' }}</code>
          </div>
          <div>
            <table style="width:100%;font-size:13px">
              <tr><td class="text-muted" style="padding:2px 8px 2px 0">Formula</td><td>{{ molecule().molecule_properties?.full_molformula || '—' }}</td></tr>
              <tr><td class="text-muted" style="padding:2px 8px 2px 0">MW</td><td>{{ molecule().molecule_properties?.full_mwt || '—' }} Da</td></tr>
              <tr><td class="text-muted" style="padding:2px 8px 2px 0">LogP</td><td>{{ molecule().molecule_properties?.alogp || '—' }}</td></tr>
              <tr><td class="text-muted" style="padding:2px 8px 2px 0">TPSA</td><td>{{ molecule().molecule_properties?.psa || '—' }}</td></tr>
            </table>
          </div>
        </div>
      </div>
      <div v-else class="text-muted text-sm">Drug not found.</div>
    </div>

    <!-- Mechanism of Action -->
    <div class="card mb-4">
      <div class="card-title">Mechanism of Action</div>
      <div v-if="loading.detail" style="padding:16px;text-align:center"><LoadingSpinner /></div>
      <div v-else-if="mechanisms().length" style="display:flex;flex-direction:column;gap:8px">
        <div v-for="m in mechanisms()" :key="m.mec_id" class="card" style="padding:10px">
          <div class="font-bold text-sm">{{ m.action_type || 'Unknown action' }}</div>
          <div class="text-muted text-sm">{{ m.mechanism_of_action }}</div>
          <div v-if="m.target_chembl_id" class="text-sm" style="margin-top:4px">Target: {{ m.target_chembl_id }}</div>
        </div>
      </div>
      <div v-else class="text-muted text-sm">No mechanism data available.</div>
    </div>

    <!-- Formulation -->
    <div class="card mb-4">
      <div class="card-title">Formulation & Label Data</div>
      <div v-if="loading.detail" style="padding:16px;text-align:center"><LoadingSpinner /></div>
      <div v-else-if="formulation().spls?.length">
        <div v-for="spl in formulation().spls.slice(0, 2)" :key="spl.setid" class="card" style="padding:10px;margin-bottom:8px">
          <div class="font-bold text-sm">{{ spl.title }}</div>
          <div class="text-muted text-sm">{{ spl.published_date }}</div>
          <a v-if="spl.setid" :href="`https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=${spl.setid}`" target="_blank" class="btn btn-secondary btn-sm" style="margin-top:6px;display:inline-flex">View Label ↗</a>
        </div>
      </div>
      <div v-else class="text-muted text-sm">No FDA label data available.</div>
    </div>

    <!-- Clinical Trials -->
    <div class="card mb-4">
      <div class="card-title">Clinical Trials ({{ trials.length }})</div>
      <div v-if="loading.trials" style="padding:16px;text-align:center"><LoadingSpinner /></div>
      <div v-else-if="trials.length" class="table-wrap">
        <table>
          <thead><tr><th>NCT ID</th><th>Title</th><th>Phase</th><th>Status</th></tr></thead>
          <tbody>
            <tr v-for="t in trials.slice(0, 10)" :key="t.protocolSection?.identificationModule?.nctId">
              <td><span class="badge badge-completed">{{ t.protocolSection?.identificationModule?.nctId }}</span></td>
              <td class="text-sm">{{ t.protocolSection?.identificationModule?.briefTitle }}</td>
              <td class="text-sm">{{ t.protocolSection?.designModule?.phases?.join(', ') || '—' }}</td>
              <td class="text-sm">{{ t.protocolSection?.statusModule?.overallStatus }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="text-muted text-sm">No clinical trials found.</div>
    </div>

    <!-- Synthesis Literature -->
    <div class="card mb-4">
      <div class="card-title">Synthesis Literature</div>
      <div v-if="loading.synthesis" style="padding:16px;text-align:center"><LoadingSpinner /></div>
      <div v-else-if="synthesis.length" style="display:flex;flex-direction:column;gap:8px">
        <div v-for="a in synthesis.slice(0, 5)" :key="a.uid" class="card" style="padding:10px">
          <div class="font-bold text-sm">{{ a.title }}</div>
          <div class="text-muted text-sm">{{ a.authors?.map(x => x.name).join(', ').slice(0, 60) }} · {{ a.pubdate || a.sortdate }}</div>
          <a :href="`https://pubmed.ncbi.nlm.nih.gov/${a.uid}/`" target="_blank" class="btn btn-secondary btn-sm" style="margin-top:6px;display:inline-flex">PubMed ↗</a>
        </div>
      </div>
      <div v-else class="text-muted text-sm">No synthesis literature found.</div>
    </div>

    <!-- Patents -->
    <div class="card">
      <div class="card-title">Patent Landscape ({{ patents.length }})</div>
      <div v-if="loading.patents" style="padding:16px;text-align:center"><LoadingSpinner /></div>
      <div v-else-if="patents.length" class="table-wrap">
        <table>
          <thead><tr><th>Patent</th><th>Title</th><th>Assignee</th><th>Filed</th><th>Expiry</th></tr></thead>
          <tbody>
            <tr v-for="p in patents" :key="p.patent_number || p.document_id">
              <td>
                <a :href="`https://worldwide.espacenet.com/patent/search?q=pn%3D${p.patent_number || p.document_id}`" target="_blank" class="badge badge-completed" style="text-decoration:none">{{ p.patent_number || p.document_id }}</a>
              </td>
              <td class="text-sm">{{ p.title || '—' }}</td>
              <td class="text-sm">{{ p.assignee || '—' }}</td>
              <td class="text-sm">{{ p.filing_date || p.date || '—' }}</td>
              <td class="text-sm">{{ patentExpiry(p) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="text-muted text-sm">No patent data found via SureChEMBL.</div>
    </div>
  </div>
</template>
