<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/projects'
import { drugs as drugsApi, investigations as investApi } from '@/services/api'
import { useUIStore } from '@/stores/ui'
import PageHeader from '@/components/layout/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ProjectForm from '@/components/projects/ProjectForm.vue'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const ui = useUIStore()

const isEdit  = !!route.params.id
const existingProject = ref(null)
const saving  = ref(false)
const projectFormRef  = ref(null)
const selectedPathway = ref('analog_based')

const investigations = computed(() => existingProject.value?.investigations || [])

// ─── Reference drug search ─────────────────────────────────────────────────

const drugQuery          = ref('')
const drugResults        = ref([])
const drugSearchLoading  = ref(false)
const linkingDrug        = ref(false)
const pendingReferenceDrug = ref(null)

async function searchDrugs() {
  if (!drugQuery.value.trim()) return
  drugSearchLoading.value = true
  try {
    drugResults.value = await drugsApi.search(drugQuery.value)
  } catch { drugResults.value = [] } finally { drugSearchLoading.value = false }
}

function selectReferenceDrugCreate(drug) {
  pendingReferenceDrug.value = {
    chembl_id: drug.molecule_chembl_id,
    name:      drug.pref_name || drug.molecule_chembl_id,
    smiles:    drug.molecule_structures?.canonical_smiles || '',
  }
  drugResults.value = []
  drugQuery.value   = ''
}

async function selectReferenceDrug(drug) {
  linkingDrug.value = true
  drugResults.value = []
  drugQuery.value   = ''
  try {
    await investApi.create({
      chembl_id: drug.molecule_chembl_id,
      name:      drug.pref_name || drug.molecule_chembl_id,
      smiles:    drug.molecule_structures?.canonical_smiles || '',
      project:   route.params.id,
    })
    await projectStore.fetchProject(route.params.id)
    existingProject.value = projectStore.currentProject
    ui.addToast(`${drug.pref_name || drug.molecule_chembl_id} set as reference drug`, 'success')
  } catch {
    ui.addToast('Failed to set reference drug', 'error')
  } finally {
    linkingDrug.value = false
  }
}

// ─── TPP (Target Product Profile) — persisted in localStorage ──────────────

const TPP_STORAGE_KEY = computed(() => `biointel_tpp_${route.params.id}`)
const TPP_ROUTE_OPTIONS   = ['Oral', 'IV', 'SC', 'IM', 'Inhaled', 'Topical', 'Transdermal', 'Sublingual', 'Other']
const TPP_FORMULATION_OPTIONS = ['Tablet', 'Capsule', 'Solution', 'Suspension', 'Lyophilizate', 'Patch', 'Cream/Ointment', 'Inhaler', 'Other']
const TPP_FREQ_OPTIONS    = ['Once daily (QD)', 'Twice daily (BID)', 'Three times daily (TID)', 'Weekly', 'Biweekly', 'Monthly', 'As needed (PRN)', 'Other']

const tpp = ref({
  indication: '', route_of_admin: '', dosage_form: '', dose: '', frequency: '',
  patient_population: '', comparator: '', primary_efficacy: '', primary_safety: '',
  target_claims: '', special_populations: '', contraindications: '',
})

const showTpp = ref(false)

function loadTpp() {
  if (!route.params.id) return
  const stored = localStorage.getItem(TPP_STORAGE_KEY.value)
  if (stored) {
    try { Object.assign(tpp.value, JSON.parse(stored)) } catch { /* ignore */ }
  }
}

function saveTpp() {
  if (!route.params.id) return
  localStorage.setItem(TPP_STORAGE_KEY.value, JSON.stringify(tpp.value))
  ui.addToast('TPP saved locally', 'success')
}

const tppFilled = computed(() => Object.values(tpp.value).some(v => v && v.trim()))

// ─── Navigation grid ───────────────────────────────────────────────────────

const NAV_SECTIONS = [
  {
    label: 'Discovery',
    color: '#7c3aed',
    bg:    '#f5f3ff',
    links: [
      { label: 'Analog Workspace',   icon: '🔍', to: `/analogs?project=${route.params.id}` },
      { label: 'SAR Tracker',        icon: '⚗️', to: `/projects/${route.params.id}/sar` },
      { label: 'Candidate Selection',icon: '⭐', to: `/projects/${route.params.id}/candidates` },
    ],
  },
  {
    label: 'Drug Substance',
    color: '#2563eb',
    bg:    '#eff6ff',
    links: [
      { label: 'Synthesis Hub',       icon: '🧪', to: `/projects/${route.params.id}/synthesis` },
      { label: 'Salt/Polymorph Screen',icon: '🔬',to: `/projects/${route.params.id}/salt-screening` },
      { label: 'Process Development', icon: '🏭', to: `/projects/${route.params.id}/process-development` },
    ],
  },
  {
    label: 'Drug Product',
    color: '#0891b2',
    bg:    '#ecfeff',
    links: [
      { label: 'Formulation Planning', icon: '💊', to: `/projects/${route.params.id}/formulation` },
      { label: 'Stability Planning',   icon: '📈', to: `/projects/${route.params.id}/stability` },
      { label: 'Specifications',       icon: '📋', to: `/projects/${route.params.id}/specifications` },
      { label: 'Analytical Methods',   icon: '📐', to: `/projects/${route.params.id}/analytical` },
    ],
  },
  {
    label: 'Nonclinical',
    color: '#16a34a',
    bg:    '#f0fdf4',
    links: [
      { label: 'ADMET Dashboard',       icon: '🧬', to: `/projects/${route.params.id}/admet` },
      { label: 'Preclinical Studies',   icon: '🐭', to: `/projects/${route.params.id}/preclinical` },
    ],
  },
  {
    label: 'Regulatory & CMC',
    color: '#ea580c',
    bg:    '#fff7ed',
    links: [
      { label: 'Risk Analysis',  icon: '⚠️', to: `/projects/${route.params.id}/risk` },
      { label: 'Documents',      icon: '📄', to: `/projects/${route.params.id}/documents` },
    ],
  },
]

// ─── Lifecycle ────────────────────────────────────────────────────────────

onMounted(async () => {
  if (isEdit) {
    await projectStore.fetchProject(route.params.id)
    existingProject.value = projectStore.currentProject
    loadTpp()
  }
})

const handleSubmit = async (formData) => {
  saving.value = true
  try {
    let project
    if (isEdit) {
      project = await projectStore.updateProject(route.params.id, formData)
    } else {
      project = await projectStore.createProject(formData)
    }
    if (!isEdit && pendingReferenceDrug.value) {
      await investApi.create({ ...pendingReferenceDrug.value, project: project.id })
    }
    ui.addToast(`Project ${isEdit ? 'updated' : 'created'} successfully`, 'success')
    router.push(isEdit ? '/' : `/projects/${project.id}/edit`)
  } catch {
    ui.addToast('Failed to save project', 'error')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div style="max-width:900px">
    <PageHeader :title="isEdit ? 'Project Overview' : 'New Project'" />

    <!-- Project stats (edit mode only) -->
    <div v-if="isEdit && existingProject" class="stats-strip">
      <div class="stat-pill">
        <span class="stat-val">{{ existingProject.experiment_count ?? 0 }}</span>
        <span class="stat-lbl">Experiments</span>
      </div>
      <div class="stat-pill">
        <span class="stat-val">{{ existingProject.compound_count ?? 0 }}</span>
        <span class="stat-lbl">Compounds</span>
      </div>
      <div class="stat-pill">
        <span class="stat-val">{{ existingProject.synthesis_plans?.length ?? 0 }}</span>
        <span class="stat-lbl">Synthesis Plans</span>
      </div>
      <div class="stat-pill">
        <span class="stat-val">{{ existingProject.analog_candidates?.length ?? 0 }}</span>
        <span class="stat-lbl">Analog Candidates</span>
      </div>
      <div class="stat-pill">
        <span class="stat-val status-chip" :class="existingProject.status || 'active'">
          {{ existingProject.status || 'active' }}
        </span>
        <span class="stat-lbl">Status</span>
      </div>
    </div>

    <!-- Project form -->
    <div v-if="!isEdit || existingProject" class="card mb-4">
      <ProjectForm
        ref="projectFormRef"
        :initial="existingProject || {}"
        @submit="handleSubmit"
        @update:pathway="selectedPathway = $event"
      />
    </div>
    <div v-else class="card mb-4" style="padding:32px;text-align:center">
      <LoadingSpinner />
    </div>

    <!-- Reference Drug (create mode, analog_based) -->
    <div v-if="!isEdit && selectedPathway === 'analog_based'" class="card mb-4">
      <div class="section-top">
        <div class="card-title" style="margin-bottom:0">Reference Drug</div>
        <span class="badge" style="background:#e0e7ff;color:#3730a3;font-size:10px">Required for Analog Search</span>
      </div>

      <div v-if="pendingReferenceDrug" class="ref-drug-selected">
        <div style="flex:1">
          <strong>{{ pendingReferenceDrug.name }}</strong>
          <span class="badge badge-completed" style="font-size:10px;margin-left:8px">{{ pendingReferenceDrug.chembl_id }}</span>
          <p class="text-muted text-sm" style="margin:2px 0 0;font-family:var(--mono);font-size:11px">
            {{ pendingReferenceDrug.smiles?.slice(0, 60) }}{{ pendingReferenceDrug.smiles?.length > 60 ? '…' : '' }}
          </p>
        </div>
        <button class="btn btn-secondary btn-sm" @click="pendingReferenceDrug = null">Change</button>
      </div>

      <div v-else>
        <p class="text-muted text-sm" style="margin-bottom:12px">
          Search for an approved drug (ChEMBL) to use as the structural template for analog design.
          You can also set this after creating the project.
        </p>
        <div style="display:flex;gap:8px;margin-bottom:8px">
          <input v-model="drugQuery" class="form-control" placeholder="e.g. sitagliptin, imatinib, CHEMBL192…" @keyup.enter="searchDrugs" style="flex:1" />
          <button class="btn btn-secondary" :disabled="drugSearchLoading" @click="searchDrugs">
            {{ drugSearchLoading ? 'Searching…' : 'Search ChEMBL' }}
          </button>
        </div>
        <div v-if="drugResults.length" class="drug-results">
          <div
            v-for="d in drugResults.slice(0, 10)" :key="d.molecule_chembl_id"
            class="drug-result-row"
            @click="selectReferenceDrugCreate(d)"
          >
            <div style="flex:1">
              <strong style="font-size:13px">{{ d.pref_name || d.molecule_chembl_id }}</strong>
              <span class="badge badge-completed" style="font-size:10px;margin-left:6px">{{ d.molecule_chembl_id }}</span>
              <p class="text-muted" style="font-size:11px;margin:2px 0 0">{{ d.molecule_type }}</p>
            </div>
            <span style="color:var(--primary);font-size:12px">Select →</span>
          </div>
        </div>
        <p v-if="drugResults.length === 0 && drugQuery && !drugSearchLoading" class="text-muted text-sm" style="margin-top:8px">
          No results. Try a generic name or ChEMBL ID.
        </p>
      </div>
    </div>

    <!-- Edit-mode sections -->
    <template v-if="isEdit && existingProject">

      <!-- Reference Drug -->
      <div v-if="existingProject.pathway === 'analog_based'" class="card mb-4">
        <div class="section-top">
          <div class="card-title" style="margin-bottom:0">Reference Drug</div>
          <span class="badge" style="background:#e0e7ff;color:#3730a3;font-size:10px">Required for Analog Search</span>
        </div>

        <div v-if="investigations.length" class="ref-drug-selected">
          <div style="flex:1">
            <strong>{{ investigations[0].name }}</strong>
            <span v-if="investigations[0].chembl_id" class="badge badge-completed" style="font-size:10px;margin-left:8px">{{ investigations[0].chembl_id }}</span>
            <p class="text-muted text-sm" style="margin:2px 0 0;font-family:var(--mono);font-size:11px">
              {{ investigations[0].smiles?.slice(0, 60) }}{{ investigations[0].smiles?.length > 60 ? '…' : '' }}
            </p>
          </div>
          <RouterLink :to="`/analogs?project=${route.params.id}`" class="btn btn-primary btn-sm">Open Analog Workspace →</RouterLink>
        </div>

        <div v-else>
          <p class="text-muted text-sm" style="margin-bottom:12px">
            Search for an approved drug to use as the structural template for analog design.
          </p>
          <div style="display:flex;gap:8px;margin-bottom:8px">
            <input v-model="drugQuery" class="form-control" placeholder="e.g. sitagliptin, imatinib, CHEMBL192…" @keyup.enter="searchDrugs" style="flex:1" />
            <button class="btn btn-secondary" :disabled="drugSearchLoading" @click="searchDrugs">
              {{ drugSearchLoading ? 'Searching…' : 'Search ChEMBL' }}
            </button>
          </div>
          <div v-if="drugResults.length" class="drug-results">
            <div
              v-for="d in drugResults.slice(0, 10)" :key="d.molecule_chembl_id"
              class="drug-result-row"
              :style="linkingDrug ? 'opacity:0.5;pointer-events:none' : ''"
              @click="selectReferenceDrug(d)"
            >
              <div style="flex:1">
                <strong style="font-size:13px">{{ d.pref_name || d.molecule_chembl_id }}</strong>
                <span class="badge badge-completed" style="font-size:10px;margin-left:6px">{{ d.molecule_chembl_id }}</span>
                <p class="text-muted" style="font-size:11px;margin:2px 0 0">{{ d.molecule_type }}</p>
              </div>
              <span style="color:var(--primary);font-size:12px">Select →</span>
            </div>
          </div>
          <p v-if="drugResults.length === 0 && drugQuery && !drugSearchLoading" class="text-muted text-sm" style="margin-top:8px">
            No results. Try a generic name or ChEMBL ID.
          </p>
        </div>
      </div>

      <!-- Target Product Profile (TPP) -->
      <div class="card mb-4">
        <div class="section-top" style="cursor:pointer" @click="showTpp = !showTpp">
          <div>
            <div class="card-title" style="margin-bottom:0">
              Target Product Profile (TPP)
              <span v-if="tppFilled" class="badge badge-completed" style="font-size:10px;margin-left:8px">Filled</span>
              <span v-else class="badge" style="font-size:10px;margin-left:8px;background:#f3f4f6;color:#6b7280">Optional</span>
            </div>
            <p class="text-muted text-sm" style="margin:2px 0 0">
              Define the desired profile for the final drug product. Guides all downstream development decisions.
            </p>
          </div>
          <span style="font-size:18px;color:var(--text-muted)">{{ showTpp ? '▲' : '▼' }}</span>
        </div>

        <div v-if="showTpp" class="tpp-form">
          <div class="tpp-grid">
            <div class="form-group">
              <label>Indication / Disease</label>
              <input v-model="tpp.indication" class="form-control" placeholder="e.g. Type 2 diabetes mellitus" />
            </div>
            <div class="form-group">
              <label>Patient Population</label>
              <input v-model="tpp.patient_population" class="form-control" placeholder="e.g. Adults ≥18, HbA1c 7.5–10%" />
            </div>
            <div class="form-group">
              <label>Route of Administration</label>
              <select v-model="tpp.route_of_admin" class="form-control">
                <option value="">— select —</option>
                <option v-for="o in TPP_ROUTE_OPTIONS" :key="o" :value="o">{{ o }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>Dosage Form</label>
              <select v-model="tpp.dosage_form" class="form-control">
                <option value="">— select —</option>
                <option v-for="o in TPP_FORMULATION_OPTIONS" :key="o" :value="o">{{ o }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>Target Dose</label>
              <input v-model="tpp.dose" class="form-control" placeholder="e.g. 100 mg" />
            </div>
            <div class="form-group">
              <label>Dosing Frequency</label>
              <select v-model="tpp.frequency" class="form-control">
                <option value="">— select —</option>
                <option v-for="o in TPP_FREQ_OPTIONS" :key="o" :value="o">{{ o }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>Comparator / Standard of Care</label>
              <input v-model="tpp.comparator" class="form-control" placeholder="e.g. Metformin 500 mg BID" />
            </div>
            <div class="form-group">
              <label>Special Populations</label>
              <input v-model="tpp.special_populations" class="form-control" placeholder="e.g. Renal impairment, pediatrics" />
            </div>
          </div>
          <div class="form-group" style="margin-top:10px">
            <label>Primary Efficacy Endpoint</label>
            <textarea v-model="tpp.primary_efficacy" class="form-control" rows="2" placeholder="e.g. Change from baseline HbA1c at 24 weeks vs. comparator (superiority or non-inferiority)" />
          </div>
          <div class="form-group" style="margin-top:10px">
            <label>Primary Safety Endpoint / Key Contraindications</label>
            <textarea v-model="tpp.primary_safety" class="form-control" rows="2" placeholder="e.g. No hypoglycemia; eGFR >30 mL/min; no QTc prolongation" />
          </div>
          <div class="form-group" style="margin-top:10px">
            <label>Target Label Claims</label>
            <textarea v-model="tpp.target_claims" class="form-control" rows="2" placeholder="e.g. Reduction in CV events, weight neutral, once-daily dosing" />
          </div>
          <div class="tpp-note">
            TPP is saved locally in your browser. Export to documents when ready for team sharing.
          </div>
          <button class="btn btn-primary" style="margin-top:10px" @click="saveTpp">Save TPP</button>
        </div>
      </div>

      <!-- Project Navigation Grid -->
      <div class="card mb-4">
        <div class="card-title" style="margin-bottom:12px">Project Sections</div>
        <div class="nav-grid">
          <div v-for="section in NAV_SECTIONS" :key="section.label" class="nav-section">
            <div class="nav-section-label" :style="`color:${section.color}`">{{ section.label }}</div>
            <div class="nav-links">
              <RouterLink
                v-for="link in section.links"
                :key="link.label"
                :to="link.to"
                class="nav-link"
                :style="`background:${section.bg};border-color:${section.color}20`"
              >
                <span class="nav-link-icon">{{ link.icon }}</span>
                <span class="nav-link-label">{{ link.label }}</span>
              </RouterLink>
            </div>
          </div>
        </div>
      </div>

    </template>

    <!-- Save button -->
    <div class="card" style="display:flex;align-items:center;justify-content:flex-end;gap:12px;padding:16px 20px">
      <RouterLink to="/" class="btn btn-secondary">Cancel</RouterLink>
      <button class="btn btn-primary" :disabled="saving" @click="projectFormRef?.triggerSubmit()">
        {{ saving ? 'Saving…' : (isEdit ? 'Save Changes' : 'Create Project') }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.stats-strip { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
.stat-pill   { background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; padding: 10px 16px; display: flex; flex-direction: column; align-items: center; min-width: 100px; }
.stat-val    { font-size: 18px; font-weight: 700; color: #111827; line-height: 1.2; }
.stat-lbl    { font-size: 11px; color: #6b7280; margin-top: 2px; }

.status-chip         { font-size: 12px; font-weight: 600; padding: 2px 8px; border-radius: 8px; }
.status-chip.active  { background: #dcfce7; color: #166534; }
.status-chip.on_hold { background: #fef9c3; color: #713f12; }
.status-chip.complete{ background: #dbeafe; color: #1d4ed8; }

.section-top { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 12px; gap: 12px; }

.ref-drug-selected { display: flex; align-items: center; gap: 12px; padding: 10px; background: var(--surface-raised, #f9fafb); border-radius: 6px; }

.drug-results     { border: 1px solid var(--border, #e5e7eb); border-radius: 6px; max-height: 220px; overflow-y: auto; }
.drug-result-row  { padding: 8px 12px; cursor: pointer; border-bottom: 1px solid var(--border, #e5e7eb); display: flex; align-items: center; gap: 10px; }
.drug-result-row:last-child { border-bottom: none; }
.drug-result-row:hover { background: #f8faff; }

/* TPP */
.tpp-form { display: flex; flex-direction: column; gap: 0; margin-top: 14px; }
.tpp-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-group label { font-size: 12px; font-weight: 600; color: #374151; display: block; margin-bottom: 4px; }
.tpp-note { font-size: 11px; color: #9ca3af; margin-top: 8px; }

/* Nav grid */
.nav-grid          { display: flex; flex-direction: column; gap: 16px; }
.nav-section       { }
.nav-section-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; }
.nav-links         { display: flex; flex-wrap: wrap; gap: 8px; }
.nav-link          { display: flex; align-items: center; gap: 6px; padding: 7px 12px; border: 1px solid; border-radius: 8px; font-size: 13px; color: #374151; text-decoration: none; transition: opacity 0.15s; }
.nav-link:hover    { opacity: 0.75; }
.nav-link-icon     { font-size: 15px; }
.nav-link-label    { font-weight: 500; }

.mb-4 { margin-bottom: 16px; }
</style>
