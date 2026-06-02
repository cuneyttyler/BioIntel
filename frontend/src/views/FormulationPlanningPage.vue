<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '@/components/layout/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { useFormulationStore } from '@/stores/formulation'

const route = useRoute()
const projectId = route.params.id
const store = useFormulationStore()

const activeTab = ref('target')
const creatingPlan = ref(false)
const saveStatus = ref('')

const newPlanForm = ref({
  dosage_form: 'tablet',
  route_of_administration: 'oral',
  target_dose_mg: '',
  release_type: 'immediate',
  target_api_loading_pct: '',
  target_tablet_weight_mg: '',
  manufacturing_process: '',
  rationale: '',
  status: 'draft',
})

const planForm = ref({
  dosage_form: 'tablet',
  route_of_administration: 'oral',
  target_dose_mg: '',
  release_type: 'immediate',
  manufacturing_process: '',
  rationale: '',
})

const componentForm = ref({
  component_type: 'diluent',
  name: '',
  function: '',
  concentration: '',
  unit: '%w/w',
  grade: '',
  supplier: '',
  notes: '',
})

const compatForm = ref({ component_a: '', component_b: '', flag_type: 'chemical', severity: 'warning', evidence: '', notes: '' })
const checkingCompat = ref(false)
const showCompatForm = ref(false)

// ─── Static reference data ────────────────────────────────────────────────────

const DOSAGE_FORMS = [
  { value: 'tablet', label: 'Tablet' },
  { value: 'capsule', label: 'Capsule' },
  { value: 'solution', label: 'Solution' },
  { value: 'suspension', label: 'Suspension' },
  { value: 'injection', label: 'Injection (Parenteral)' },
  { value: 'topical', label: 'Topical' },
  { value: 'other', label: 'Other' },
]

const ROUTES = [
  { value: 'oral', label: 'Oral (PO)' },
  { value: 'intravenous', label: 'Intravenous (IV)' },
  { value: 'subcutaneous', label: 'Subcutaneous (SC)' },
  { value: 'intramuscular', label: 'Intramuscular (IM)' },
  { value: 'topical', label: 'Topical' },
  { value: 'inhalation', label: 'Inhalation' },
  { value: 'other', label: 'Other' },
]

const RELEASE_TYPES = [
  { value: 'immediate', label: 'Immediate Release (IR)' },
  { value: 'modified', label: 'Modified Release (MR)' },
  { value: 'extended', label: 'Extended Release (ER/XR)' },
  { value: 'delayed', label: 'Delayed Release (DR / Enteric)' },
]

const COMPONENT_TYPES = [
  { value: 'api', label: 'API (Active Pharmaceutical Ingredient)' },
  { value: 'diluent', label: 'Diluent / Filler' },
  { value: 'binder', label: 'Binder' },
  { value: 'disintegrant', label: 'Disintegrant' },
  { value: 'lubricant', label: 'Lubricant' },
  { value: 'glidant', label: 'Glidant' },
  { value: 'coating', label: 'Coating Agent' },
  { value: 'preservative', label: 'Preservative' },
  { value: 'solvent', label: 'Solvent / Co-solvent' },
  { value: 'surfactant', label: 'Surfactant / Solubilizer' },
  { value: 'other', label: 'Other' },
]

const FLAG_TYPES = [
  { value: 'chemical', label: 'Chemical Incompatibility' },
  { value: 'physical', label: 'Physical Incompatibility' },
  { value: 'microbiological', label: 'Microbiological Concern' },
  { value: 'regulatory', label: 'Regulatory Concern' },
]

const PRESET_EXCIPIENTS = {
  diluent: [
    { name: 'Microcrystalline Cellulose (Avicel PH102)', grade: 'Ph.Eur/USP-NF', iig_limit: null, typical_pct: '20–80%', notes: 'Most common filler-binder; compressibility depends on grade' },
    { name: 'Lactose Monohydrate 200M', grade: 'Ph.Eur/USP-NF', iig_limit: null, typical_pct: '10–80%', notes: 'Avoid with primary amines (Maillard); check reducing sugar sensitivity' },
    { name: 'Mannitol (Pearlitol 200SD)', grade: 'Ph.Eur/USP-NF', iig_limit: null, typical_pct: '10–90%', notes: 'Non-reducing; suitable for moisture-sensitive APIs; pleasant mouthfeel' },
    { name: 'Dibasic Calcium Phosphate Anhydrous', grade: 'USP-NF', iig_limit: null, typical_pct: '15–30%', notes: 'Insoluble; basic pH; may affect pH-sensitive APIs' },
    { name: 'Sorbitol (Neosorb 60)', grade: 'Ph.Eur/USP-NF', iig_limit: null, typical_pct: '20–70%', notes: 'Humectant; chewable/ODT formulations; osmotic laxative above 20 g/day' },
  ],
  binder: [
    { name: 'HPMC E5 (Hypromellose)', grade: 'Ph.Eur/USP-NF', iig_limit: null, typical_pct: '2–5%', notes: 'Wet granulation binder; also film coating; pH independent' },
    { name: 'PVP K30 (Povidone)', grade: 'Ph.Eur/USP-NF', iig_limit: null, typical_pct: '2–6%', notes: 'WG and DC; excellent binding; hygroscopic at high levels' },
    { name: 'HPC LF (Hydroxypropyl Cellulose)', grade: 'Ph.Eur/USP-NF', iig_limit: null, typical_pct: '2–6%', notes: 'Soluble; thermoplastic; suitable for hot-melt extrusion' },
    { name: 'Copovidone (PVP/VA 64)', grade: 'Ph.Eur/USP-NF', iig_limit: null, typical_pct: '3–10%', notes: 'Lower Tg than PVP; good for ASD; less hygroscopic' },
  ],
  disintegrant: [
    { name: 'Croscarmellose Sodium (Ac-Di-Sol)', grade: 'Ph.Eur/USP-NF', iig_limit: null, typical_pct: '1–5%', notes: 'Superdisintegrant; swells in water; intragranular + extragranular use' },
    { name: 'Sodium Starch Glycolate (Primojel)', grade: 'Ph.Eur/USP-NF', iig_limit: null, typical_pct: '2–8%', notes: 'Starch-based; avoid high NaCl levels; not for low-moisture formulations' },
    { name: 'Crospovidone (PVPP, Kollidon CL)', grade: 'Ph.Eur/USP-NF', iig_limit: null, typical_pct: '2–5%', notes: 'Insoluble; no ionic character; wicking mechanism' },
  ],
  lubricant: [
    { name: 'Magnesium Stearate', grade: 'Ph.Eur/USP-NF', iig_limit: 1.5, iig_unit: '%w/w', typical_pct: '0.25–1%', notes: 'Hydrophobic; over-lubrication delays dissolution; blend time critical' },
    { name: 'Sodium Stearyl Fumarate (PRUV)', grade: 'Ph.Eur/USP-NF', iig_limit: 2.0, iig_unit: '%w/w', typical_pct: '0.5–2%', notes: 'Less hydrophobic than Mg stearate; preferred for moisture-sensitive APIs' },
    { name: 'Stearic Acid', grade: 'Ph.Eur/USP-NF', iig_limit: null, typical_pct: '1–3%', notes: 'Less common; may affect API stability' },
  ],
  glidant: [
    { name: 'Colloidal Silicon Dioxide (Aerosil 200)', grade: 'Ph.Eur/USP-NF', iig_limit: 1.0, iig_unit: '%w/w', typical_pct: '0.1–0.5%', notes: 'Flow enhancer; adsorbs moisture; may reduce Mg stearate sensitivity' },
    { name: 'Talc', grade: 'Ph.Eur/USP-NF', iig_limit: null, typical_pct: '1–5%', notes: 'Also lubricant; avoid in inhalation; asbestos-free certification required' },
  ],
  coating: [
    { name: 'HPMC E5 (Opadry clear)', grade: 'Ph.Eur/USP-NF', iig_limit: null, typical_pct: '2–4% weight gain', notes: 'Moisture barrier; immediate-release functional coat' },
    { name: 'Eudragit L30D-55', grade: 'Ph.Eur/USP-NF', iig_limit: null, typical_pct: '5–10% weight gain', notes: 'Enteric coating; dissolves pH > 5.5' },
    { name: 'Eudragit RL/RS (sustained release)', grade: 'Ph.Eur/USP-NF', iig_limit: null, typical_pct: '5–15% weight gain', notes: 'Permeable/impermeable membrane; ratio controls release rate' },
  ],
  surfactant: [
    { name: 'Polysorbate 80 (Tween 80)', grade: 'Ph.Eur/USP-NF', iig_limit: 25.0, iig_unit: 'mg/dose (oral)', typical_pct: '0.01–0.5%', notes: 'Solubilizer/wetting agent; check peroxide content (API oxidation risk)' },
    { name: 'Sodium Lauryl Sulfate (SLS)', grade: 'Ph.Eur/USP-NF', iig_limit: null, typical_pct: '0.5–2%', notes: 'Wetting agent; irritant at high dose; interacts with cationic drugs' },
    { name: 'Vitamin E TPGS', grade: 'Ph.Eur/USP-NF', iig_limit: null, typical_pct: '0.1–1%', notes: 'P-gp inhibitor + solubilizer; amphoteric; antioxidant' },
  ],
  preservative: [
    { name: 'Benzalkonium Chloride', grade: 'Ph.Eur/USP-NF', iig_limit: 0.03, iig_unit: '%w/v', typical_pct: '0.01–0.02%', notes: 'Broad-spectrum; avoid with anionic polymers; ophthalmic concern (ciliotoxic)' },
    { name: 'Methylparaben (Nipagin M)', grade: 'Ph.Eur/USP-NF', iig_limit: 0.18, iig_unit: '%w/v', typical_pct: '0.05–0.25%', notes: 'Aqueous solutions; combination with propylparaben synergistic' },
    { name: 'Propylparaben', grade: 'Ph.Eur/USP-NF', iig_limit: 0.02, iig_unit: '%w/v', typical_pct: '0.01–0.02%', notes: 'Used in combination with methylparaben (4:1 ratio typical)' },
  ],
}

// ─── Computed ─────────────────────────────────────────────────────────────────

const totalConcentration = computed(() => {
  return store.components.reduce((s, c) => s + (parseFloat(c.concentration) || 0), 0).toFixed(1)
})

const concentrationStatus = computed(() => {
  const t = parseFloat(totalConcentration.value)
  if (t > 102) return { color: '#dc2626', label: 'Over 100%' }
  if (t > 99.5) return { color: '#16a34a', label: 'Balanced (100%)' }
  if (t > 90) return { color: '#d97706', label: 'Incomplete' }
  return { color: '#6b7280', label: `${t}%` }
})

const criticalFlagCount = computed(() => store.flags.filter(f => f.severity === 'critical').length)
const warningFlagCount = computed(() => store.flags.filter(f => f.severity === 'warning').length)

// ─── Actions ──────────────────────────────────────────────────────────────────

async function createPlan() {
  const payload = {
    ...newPlanForm.value,
    target_dose_mg: parseFloat(newPlanForm.value.target_dose_mg) || null,
  }
  await store.savePlan(projectId, payload)
  creatingPlan.value = false
  loadPlanIntoForm()
}

function loadPlanIntoForm() {
  if (!store.plan) return
  planForm.value = {
    dosage_form: store.plan.dosage_form || 'tablet',
    route_of_administration: store.plan.route_of_administration || 'oral',
    target_dose_mg: store.plan.target_dose_mg ?? '',
    release_type: store.plan.release_type || 'immediate',
    manufacturing_process: store.plan.manufacturing_process || '',
    rationale: store.plan.rationale || '',
  }
}

async function saveTarget() {
  await store.savePlan(projectId, {
    ...planForm.value,
    target_dose_mg: parseFloat(planForm.value.target_dose_mg) || null,
  })
  saveStatus.value = 'saved'
  setTimeout(() => saveStatus.value = '', 2500)
}

function addPreset(preset, type) {
  componentForm.value.component_type = type
  componentForm.value.name = preset.name
  componentForm.value.grade = preset.grade
  componentForm.value.function = preset.notes
  componentForm.value.unit = '%w/w'
}

async function addComponent() {
  await store.addComponent({
    ...componentForm.value,
    concentration: parseFloat(componentForm.value.concentration) || null,
  })
  componentForm.value = { component_type: 'diluent', name: '', function: '', concentration: '', unit: '%w/w', grade: '', supplier: '', notes: '' }
}

async function removeComponent(id) {
  if (!confirm('Remove this component?')) return
  await store.removeComponent(id)
}

async function runCompatibilityCheck() {
  checkingCompat.value = true
  try {
    await store.checkCompatibility()
  } finally {
    checkingCompat.value = false
  }
}

function flagColor(severity) {
  return severity === 'critical' ? '#dc2626' : severity === 'warning' ? '#d97706' : '#2563eb'
}

function componentTypeLabel(val) {
  return COMPONENT_TYPES.find(t => t.value === val)?.label || val
}

onMounted(async () => {
  await store.fetchPlan(projectId)
  loadPlanIntoForm()
})
</script>

<template>
  <div>
    <PageHeader title="Formulation Planning">
      <template #actions>
        <button v-if="!store.plan && !creatingPlan" class="btn btn-primary" @click="creatingPlan = true">
          + New Formulation Plan
        </button>
        <button v-if="creatingPlan" class="btn btn-secondary" @click="creatingPlan = false">Cancel</button>
      </template>
    </PageHeader>

    <!-- Create Plan Modal -->
    <div v-if="creatingPlan" class="modal-overlay" @click.self="creatingPlan = false">
      <div class="modal-box">
        <h3 class="modal-title">New Formulation Plan</h3>
        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label">Dosage Form</label>
            <select v-model="newPlanForm.dosage_form" class="form-input">
              <option v-for="f in DOSAGE_FORMS" :key="f.value" :value="f.value">{{ f.label }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Route of Administration</label>
            <select v-model="newPlanForm.route_of_administration" class="form-input">
              <option v-for="r in ROUTES" :key="r.value" :value="r.value">{{ r.label }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Target Dose (mg)</label>
            <input v-model="newPlanForm.target_dose_mg" type="number" class="form-input" placeholder="e.g. 200" />
          </div>
          <div class="form-group">
            <label class="form-label">Release Type</label>
            <select v-model="newPlanForm.release_type" class="form-input">
              <option v-for="r in RELEASE_TYPES" :key="r.value" :value="r.value">{{ r.label }}</option>
            </select>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Formulation Rationale</label>
          <textarea v-model="newPlanForm.rationale" class="form-input" rows="2" placeholder="Why this dosage form and route?" />
        </div>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="creatingPlan = false">Cancel</button>
          <button class="btn btn-primary" :disabled="store.loading.plan" @click="createPlan">
            {{ store.loading.plan ? 'Creating…' : 'Create Plan' }}
          </button>
        </div>
      </div>
    </div>

    <LoadingSpinner v-if="store.loading.plan && !store.plan" />

    <div v-else-if="store.plan">
      <!-- Plan header summary bar -->
      <div class="plan-header-bar">
        <div class="plan-header-item">
          <span class="plan-header-label">Dosage Form</span>
          <span class="plan-header-value">{{ DOSAGE_FORMS.find(f => f.value === store.plan.dosage_form)?.label || store.plan.dosage_form }}</span>
        </div>
        <div class="plan-header-item">
          <span class="plan-header-label">Route</span>
          <span class="plan-header-value">{{ ROUTES.find(r => r.value === store.plan.route_of_administration)?.label || store.plan.route_of_administration }}</span>
        </div>
        <div class="plan-header-item">
          <span class="plan-header-label">Target Dose</span>
          <span class="plan-header-value">{{ store.plan.target_dose_mg ? store.plan.target_dose_mg + ' mg' : '—' }}</span>
        </div>
        <div class="plan-header-item">
          <span class="plan-header-label">Release</span>
          <span class="plan-header-value">{{ RELEASE_TYPES.find(r => r.value === store.plan.release_type)?.label || store.plan.release_type }}</span>
        </div>
        <div class="plan-header-item">
          <span class="plan-header-label">Components</span>
          <span class="plan-header-value">{{ store.components.length }}</span>
        </div>
        <div class="plan-header-item" v-if="criticalFlagCount > 0">
          <span class="plan-header-label">Flags</span>
          <span class="plan-header-value flag-critical-text">{{ criticalFlagCount }} critical</span>
        </div>
        <div class="plan-header-item" v-else-if="warningFlagCount > 0">
          <span class="plan-header-label">Flags</span>
          <span class="plan-header-value flag-warning-text">{{ warningFlagCount }} warning</span>
        </div>
        <div class="plan-header-item" v-else>
          <span class="plan-header-label">Status</span>
          <span class="plan-header-value" :style="{ color: store.plan.status === 'finalized' ? '#16a34a' : '#6b7280' }">
            {{ store.plan.status }}
          </span>
        </div>
      </div>

      <!-- Tab navigation -->
      <div class="tab-nav">
        <button class="tab-btn" :class="{ active: activeTab === 'target' }" @click="activeTab = 'target'">
          Target Definition
        </button>
        <button class="tab-btn" :class="{ active: activeTab === 'excipients' }" @click="activeTab = 'excipients'">
          Excipient Selection
          <span v-if="store.components.length" class="tab-badge">{{ store.components.length }}</span>
        </button>
        <button class="tab-btn" :class="{ active: activeTab === 'compatibility' }" @click="activeTab = 'compatibility'">
          Compatibility
          <span v-if="store.flags.length" class="tab-badge" :style="{ background: criticalFlagCount > 0 ? '#dc2626' : '#d97706' }">
            {{ store.flags.length }}
          </span>
        </button>
        <button class="tab-btn" :class="{ active: activeTab === 'summary' }" @click="activeTab = 'summary'">
          Summary
        </button>
      </div>

      <!-- ── TAB: Target Definition ──────────────────────────────────────────── -->
      <div v-if="activeTab === 'target'" class="tab-content">
        <div class="section-card">
          <div class="section-header">
            <h3 class="section-title">Drug Product Target Profile</h3>
            <div class="section-actions">
              <span v-if="saveStatus === 'saved'" class="save-confirm">✓ Saved</span>
              <button class="btn btn-primary btn-sm" @click="saveTarget">Save</button>
            </div>
          </div>
          <div class="form-grid-3">
            <div class="form-group">
              <label class="form-label">Dosage Form</label>
              <select v-model="planForm.dosage_form" class="form-input">
                <option v-for="f in DOSAGE_FORMS" :key="f.value" :value="f.value">{{ f.label }}</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Route of Administration</label>
              <select v-model="planForm.route_of_administration" class="form-input">
                <option v-for="r in ROUTES" :key="r.value" :value="r.value">{{ r.label }}</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Release Type</label>
              <select v-model="planForm.release_type" class="form-input">
                <option v-for="r in RELEASE_TYPES" :key="r.value" :value="r.value">{{ r.label }}</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Target Dose (mg)</label>
              <input v-model="planForm.target_dose_mg" type="number" class="form-input" placeholder="e.g. 200" />
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Formulation Rationale</label>
            <textarea v-model="planForm.rationale" class="form-input" rows="3"
              placeholder="e.g. Oral tablet chosen for convenience; IR release appropriate for Cmax-driven efficacy; target dose 200 mg based on Phase I PK data…" />
          </div>
          <div class="form-group">
            <label class="form-label">Manufacturing Process Description</label>
            <textarea v-model="planForm.manufacturing_process" class="form-input" rows="4"
              placeholder="e.g. Wet granulation (high-shear): blend API + MCC + Lac → granulate with HPMC E5 solution → dry to LOD &lt;2% → screen → blend with Ac-Di-Sol extragranularly → lubricate → compress → coat (Opadry)…" />
          </div>
        </div>

        <div class="section-card" style="margin-top:16px">
          <h3 class="section-title">Biopharmaceutical Considerations</h3>
          <div class="info-grid">
            <div class="info-card">
              <div class="info-card-title">BCS Classification</div>
              <div class="info-card-body">Document API solubility class (I–IV) to guide formulation strategy. Class II/IV APIs require solubilization strategies (amorphous dispersion, nano, salt, cyclodextrin).</div>
            </div>
            <div class="info-card">
              <div class="info-card-title">API Properties Impact</div>
              <div class="info-card-body">Review MW, pKa, logP, hygroscopicity, melting point, and polymorphic form before selecting excipients. Flag any known incompatibilities from salt screen.</div>
            </div>
            <div class="info-card">
              <div class="info-card-title">Bioavailability Target</div>
              <div class="info-card-body">Define target F% and Tmax/Cmax. For ER formulations, set in vitro-in vivo correlation (IVIVC) target dissolution profile.</div>
            </div>
          </div>
        </div>
      </div>

      <!-- ── TAB: Excipient Selection ───────────────────────────────────────── -->
      <div v-if="activeTab === 'excipients'" class="tab-content">

        <!-- Composition tracker bar -->
        <div class="composition-bar-wrap">
          <div class="composition-bar-label">
            Total composition: <strong :style="{ color: concentrationStatus.color }">{{ totalConcentration }}%</strong>
            <span class="composition-status" :style="{ color: concentrationStatus.color }">{{ concentrationStatus.label }}</span>
          </div>
          <div class="composition-bar-track">
            <div class="composition-bar-fill" :style="{ width: Math.min(parseFloat(totalConcentration), 100) + '%', background: concentrationStatus.color }" />
          </div>
        </div>

        <!-- Current composition table -->
        <div class="section-card">
          <div class="section-header">
            <h3 class="section-title">Composition ({{ store.components.length }} components)</h3>
          </div>
          <table v-if="store.components.length" class="sci-table">
            <thead>
              <tr>
                <th>Component</th>
                <th>Functional Role</th>
                <th>Concentration</th>
                <th>Grade</th>
                <th>Supplier</th>
                <th>Notes / Function</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in store.components" :key="c.id">
                <td class="td-name">{{ c.name }}</td>
                <td><span class="role-badge">{{ componentTypeLabel(c.component_type) }}</span></td>
                <td class="td-num">{{ c.concentration != null ? c.concentration + ' ' + c.unit : '—' }}</td>
                <td>{{ c.grade || '—' }}</td>
                <td class="text-muted">{{ c.supplier || '—' }}</td>
                <td class="td-notes text-muted">{{ c.function || c.notes || '—' }}</td>
                <td>
                  <button class="btn btn-sm btn-danger" @click.stop="removeComponent(c.id)">Remove</button>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-else class="empty-note">No components added yet. Use presets below or add manually.</div>
        </div>

        <!-- Add component form -->
        <div class="section-card" style="margin-top:16px">
          <h3 class="section-title">Add Component</h3>
          <div class="form-grid-4">
            <div class="form-group">
              <label class="form-label">Functional Role</label>
              <select v-model="componentForm.component_type" class="form-input">
                <option v-for="t in COMPONENT_TYPES" :key="t.value" :value="t.value">{{ t.label }}</option>
              </select>
            </div>
            <div class="form-group" style="grid-column: span 2">
              <label class="form-label">Name</label>
              <input v-model="componentForm.name" class="form-input" placeholder="e.g. Microcrystalline Cellulose Avicel PH102" />
            </div>
            <div class="form-group">
              <label class="form-label">Grade</label>
              <input v-model="componentForm.grade" class="form-input" placeholder="Ph.Eur/USP-NF" />
            </div>
            <div class="form-group">
              <label class="form-label">Concentration</label>
              <input v-model="componentForm.concentration" type="number" class="form-input" placeholder="e.g. 40" />
            </div>
            <div class="form-group">
              <label class="form-label">Unit</label>
              <select v-model="componentForm.unit" class="form-input">
                <option>%w/w</option>
                <option>%w/v</option>
                <option>mg/unit</option>
                <option>mg/mL</option>
                <option>%v/v</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Supplier</label>
              <input v-model="componentForm.supplier" class="form-input" placeholder="e.g. FMC BioPolymer" />
            </div>
            <div class="form-group" style="grid-column: span 2">
              <label class="form-label">Function / Notes</label>
              <input v-model="componentForm.function" class="form-input" placeholder="e.g. Wet granulation binder; 5% in IPA" />
            </div>
          </div>
          <button class="btn btn-primary btn-sm" :disabled="!componentForm.name" @click="addComponent">
            Add Component
          </button>
        </div>

        <!-- Preset excipients -->
        <div class="section-card" style="margin-top:16px">
          <h3 class="section-title">Common Excipients — Click to Pre-fill</h3>
          <div v-for="(presets, role) in PRESET_EXCIPIENTS" :key="role" class="preset-group">
            <div class="preset-group-label">{{ COMPONENT_TYPES.find(t => t.value === role)?.label || role }}</div>
            <div class="preset-chips">
              <button v-for="p in presets" :key="p.name" class="preset-chip" @click="addPreset(p, role)" :title="p.notes">
                <span class="preset-chip-name">{{ p.name.split('(')[0].trim() }}</span>
                <span class="preset-chip-pct text-muted">{{ p.typical_pct }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- ── TAB: Compatibility ─────────────────────────────────────────────── -->
      <div v-if="activeTab === 'compatibility'" class="tab-content">
        <div class="section-card">
          <div class="section-header">
            <h3 class="section-title">API–Excipient Compatibility Assessment</h3>
            <div class="section-actions">
              <button class="btn btn-secondary btn-sm" @click="showCompatForm = !showCompatForm">
                {{ showCompatForm ? 'Hide Form' : '+ Add Flag' }}
              </button>
              <button class="btn btn-primary btn-sm" :disabled="checkingCompat || store.components.length < 2" @click="runCompatibilityCheck">
                {{ checkingCompat ? 'Checking…' : 'Run Auto-Check' }}
              </button>
            </div>
          </div>

          <div v-if="showCompatForm" class="compat-form">
            <div class="form-grid-3">
              <div class="form-group">
                <label class="form-label">Component A</label>
                <input v-model="compatForm.component_a" class="form-input" placeholder="API or excipient name" />
              </div>
              <div class="form-group">
                <label class="form-label">Component B</label>
                <input v-model="compatForm.component_b" class="form-input" placeholder="API or excipient name" />
              </div>
              <div class="form-group">
                <label class="form-label">Type</label>
                <select v-model="compatForm.flag_type" class="form-input">
                  <option v-for="ft in FLAG_TYPES" :key="ft.value" :value="ft.value">{{ ft.label }}</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">Severity</label>
                <select v-model="compatForm.severity" class="form-input">
                  <option value="info">Info</option>
                  <option value="warning">Warning</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
              <div class="form-group" style="grid-column: span 2">
                <label class="form-label">Evidence / Literature Reference</label>
                <input v-model="compatForm.evidence" class="form-input" placeholder="e.g. Maillard reaction lactose + primary amine API; Handbook of Pharm. Excipients 8th ed." />
              </div>
            </div>
            <button class="btn btn-primary btn-sm">Add Flag</button>
          </div>

          <div v-if="store.flags.length" style="margin-top:12px">
            <table class="sci-table">
              <thead>
                <tr>
                  <th>Component A</th>
                  <th>Component B</th>
                  <th>Type</th>
                  <th>Severity</th>
                  <th>Evidence</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="flag in store.flags" :key="flag.id">
                  <td class="td-name">{{ flag.component_a }}</td>
                  <td class="td-name">{{ flag.component_b }}</td>
                  <td>{{ FLAG_TYPES.find(t => t.value === flag.flag_type)?.label || flag.flag_type }}</td>
                  <td>
                    <span class="severity-badge" :style="{ background: flagColor(flag.severity) + '20', color: flagColor(flag.severity), border: '1px solid ' + flagColor(flag.severity) }">
                      {{ flag.severity.toUpperCase() }}
                    </span>
                  </td>
                  <td class="text-muted td-notes">{{ flag.evidence || flag.notes || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="empty-note">No compatibility flags. Run auto-check or add flags manually.</div>
        </div>

        <div class="section-card" style="margin-top:16px">
          <h3 class="section-title">Compatibility Reference Guidance</h3>
          <table class="sci-table">
            <thead><tr><th>Known Risk Pair</th><th>Mechanism</th><th>Mitigation</th></tr></thead>
            <tbody>
              <tr>
                <td>Primary amine API + Lactose</td>
                <td>Maillard reaction (discoloration, degradation)</td>
                <td>Use mannitol, MCC, or calcium phosphate instead</td>
              </tr>
              <tr>
                <td>Magnesium Stearate (over-lubrication)</td>
                <td>Hydrophobic film inhibits wetting → slow dissolution</td>
                <td>Limit to 0.25–0.5%; minimize blend time; use PRUV</td>
              </tr>
              <tr>
                <td>Carboxylic acid API + Mg Stearate</td>
                <td>Salt formation; API degradation</td>
                <td>Use sodium stearyl fumarate (PRUV) or stearic acid</td>
              </tr>
              <tr>
                <td>Cationic drug + SLS</td>
                <td>Ion-pair complex; reduced bioavailability</td>
                <td>Avoid SLS; use polysorbate 80 or Vit E TPGS</td>
              </tr>
              <tr>
                <td>Eudragit + plasticizer</td>
                <td>Incompatible plasticizer ratio affects film integrity</td>
                <td>Test TEC, triacetin, PEG at 10–25% of polymer wt</td>
              </tr>
              <tr>
                <td>Oxidation-prone API + Polysorbate 80</td>
                <td>Residual peroxides → API oxidation</td>
                <td>Use low-peroxide grade; add BHT/Vit E as antioxidant</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ── TAB: Summary ───────────────────────────────────────────────────── -->
      <div v-if="activeTab === 'summary'" class="tab-content">
        <div class="section-card">
          <h3 class="section-title">Formulation Summary</h3>
          <div class="summary-grid">
            <div>
              <p class="text-muted" style="font-size:12px;margin-bottom:4px">Dosage Form</p>
              <p class="summary-val">{{ DOSAGE_FORMS.find(f => f.value === store.plan.dosage_form)?.label }}</p>
            </div>
            <div>
              <p class="text-muted" style="font-size:12px;margin-bottom:4px">Route</p>
              <p class="summary-val">{{ ROUTES.find(r => r.value === store.plan.route_of_administration)?.label }}</p>
            </div>
            <div>
              <p class="text-muted" style="font-size:12px;margin-bottom:4px">Target Dose</p>
              <p class="summary-val">{{ store.plan.target_dose_mg ? store.plan.target_dose_mg + ' mg' : '—' }}</p>
            </div>
            <div>
              <p class="text-muted" style="font-size:12px;margin-bottom:4px">Release</p>
              <p class="summary-val">{{ RELEASE_TYPES.find(r => r.value === store.plan.release_type)?.label }}</p>
            </div>
            <div>
              <p class="text-muted" style="font-size:12px;margin-bottom:4px">Total Components</p>
              <p class="summary-val">{{ store.components.length }}</p>
            </div>
            <div>
              <p class="text-muted" style="font-size:12px;margin-bottom:4px">Total Concentration</p>
              <p class="summary-val" :style="{ color: concentrationStatus.color }">{{ totalConcentration }}%</p>
            </div>
            <div>
              <p class="text-muted" style="font-size:12px;margin-bottom:4px">Compatibility Flags</p>
              <p class="summary-val">
                <span v-if="criticalFlagCount" class="flag-critical-text">{{ criticalFlagCount }} critical</span>
                <span v-else-if="warningFlagCount" class="flag-warning-text">{{ warningFlagCount }} warning</span>
                <span v-else style="color:#16a34a">None</span>
              </p>
            </div>
            <div>
              <p class="text-muted" style="font-size:12px;margin-bottom:4px">Status</p>
              <p class="summary-val">{{ store.plan.status }}</p>
            </div>
          </div>
          <div v-if="store.plan.rationale" style="margin-top:16px">
            <p class="text-muted" style="font-size:12px;margin-bottom:4px">Rationale</p>
            <p style="font-size:14px;color:#374151;white-space:pre-wrap">{{ store.plan.rationale }}</p>
          </div>
          <div v-if="store.plan.manufacturing_process" style="margin-top:12px">
            <p class="text-muted" style="font-size:12px;margin-bottom:4px">Manufacturing Process</p>
            <p style="font-size:14px;color:#374151;white-space:pre-wrap">{{ store.plan.manufacturing_process }}</p>
          </div>
        </div>

        <div class="section-card" style="margin-top:16px" v-if="store.components.length">
          <h3 class="section-title">Full Composition Table</h3>
          <table class="sci-table">
            <thead>
              <tr><th>Component</th><th>Functional Role</th><th>Concentration</th><th>Grade</th><th>Notes</th></tr>
            </thead>
            <tbody>
              <tr v-for="c in store.components" :key="c.id">
                <td class="td-name">{{ c.name }}</td>
                <td><span class="role-badge">{{ componentTypeLabel(c.component_type) }}</span></td>
                <td class="td-num">{{ c.concentration != null ? c.concentration + ' ' + c.unit : '—' }}</td>
                <td>{{ c.grade || '—' }}</td>
                <td class="text-muted td-notes">{{ c.function || c.notes || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div v-else-if="!creatingPlan" class="empty-state-page">
      <div class="empty-state-icon">⚗️</div>
      <h3>No Formulation Plan</h3>
      <p class="text-muted">Create a formulation plan to define the drug product target profile, select excipients, and assess API–excipient compatibility.</p>
      <button class="btn btn-primary" @click="creatingPlan = true">+ New Formulation Plan</button>
    </div>
  </div>
</template>

<style scoped>
/* ── Layout ──────────────────────────────────────────────────── */
.plan-header-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 0;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  margin-bottom: 16px;
  overflow: hidden;
}
.plan-header-item {
  flex: 1;
  min-width: 110px;
  padding: 10px 16px;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.plan-header-item:last-child { border-right: none; }
.plan-header-label { font-size: 11px; color: #9ca3af; text-transform: uppercase; letter-spacing: .04em; }
.plan-header-value { font-size: 13px; font-weight: 600; color: #111827; }
.flag-critical-text { color: #dc2626; }
.flag-warning-text { color: #d97706; }

/* ── Tabs ────────────────────────────────────────────────────── */
.tab-nav {
  display: flex;
  gap: 2px;
  margin-bottom: 16px;
  border-bottom: 2px solid #e5e7eb;
}
.tab-btn {
  padding: 8px 18px;
  font-size: 13px;
  font-weight: 500;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  cursor: pointer;
  color: #6b7280;
  transition: color .15s, border-color .15s;
  display: flex;
  align-items: center;
  gap: 6px;
}
.tab-btn:hover { color: #374151; }
.tab-btn.active { color: #2563eb; border-bottom-color: #2563eb; }
.tab-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background: #6b7280;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
}
.tab-content { animation: fadeIn .15s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }

/* ── Cards ───────────────────────────────────────────────────── */
.section-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px;
}
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.section-title { font-size: 14px; font-weight: 600; color: #111827; margin: 0 0 16px; }
.section-header .section-title { margin: 0; }
.section-actions { display: flex; gap: 8px; align-items: center; }
.save-confirm { font-size: 12px; color: #16a34a; font-weight: 500; }

/* ── Tables ──────────────────────────────────────────────────── */
.sci-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.sci-table th {
  background: #f9fafb;
  color: #374151;
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: .04em;
  padding: 8px 12px;
  border-bottom: 2px solid #e5e7eb;
  text-align: left;
  white-space: nowrap;
}
.sci-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #f3f4f6;
  color: #374151;
  vertical-align: top;
}
.sci-table tbody tr:hover { background: #f9fafb; }
.sci-table tbody tr:last-child td { border-bottom: none; }
.td-name { font-weight: 500; }
.td-num { font-variant-numeric: tabular-nums; text-align: right; }
.td-notes { font-size: 12px; max-width: 220px; }
.text-muted { color: #6b7280; }
.empty-note { padding: 24px; text-align: center; color: #9ca3af; font-size: 13px; }

/* ── Badges ──────────────────────────────────────────────────── */
.role-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 9999px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;
}
.severity-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 9999px;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}

/* ── Forms ───────────────────────────────────────────────────── */
.form-grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.form-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.form-grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.form-group { display: flex; flex-direction: column; gap: 4px; }
.form-label { font-size: 12px; font-weight: 500; color: #374151; }
.form-input {
  padding: 7px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 13px;
  color: #111827;
  background: #fff;
  transition: border-color .15s;
  width: 100%;
  box-sizing: border-box;
}
.form-input:focus { outline: none; border-color: #2563eb; box-shadow: 0 0 0 2px #dbeafe; }

/* ── Composition bar ─────────────────────────────────────────── */
.composition-bar-wrap { margin-bottom: 14px; }
.composition-bar-label { font-size: 13px; margin-bottom: 4px; color: #374151; }
.composition-status { margin-left: 8px; font-size: 12px; font-weight: 500; }
.composition-bar-track { height: 6px; background: #e5e7eb; border-radius: 3px; overflow: hidden; }
.composition-bar-fill { height: 100%; border-radius: 3px; transition: width .3s, background .3s; }

/* ── Presets ─────────────────────────────────────────────────── */
.preset-group { margin-bottom: 14px; }
.preset-group-label { font-size: 11px; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 6px; }
.preset-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.preset-chip {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #f9fafb;
  cursor: pointer;
  transition: background .15s, border-color .15s;
  text-align: left;
}
.preset-chip:hover { background: #eff6ff; border-color: #93c5fd; }
.preset-chip-name { font-size: 12px; font-weight: 500; color: #1e40af; }
.preset-chip-pct { font-size: 11px; color: #9ca3af; }

/* ── Info cards ──────────────────────────────────────────────── */
.info-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.info-card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; }
.info-card-title { font-size: 12px; font-weight: 600; color: #1e40af; margin-bottom: 6px; }
.info-card-body { font-size: 12px; color: #64748b; line-height: 1.5; }

/* ── Compat form ─────────────────────────────────────────────── */
.compat-form { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 14px; margin-bottom: 12px; }

/* ── Summary grid ────────────────────────────────────────────── */
.summary-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 8px; }
.summary-val { font-size: 15px; font-weight: 600; color: #111827; }

/* ── Modal ───────────────────────────────────────────────────── */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.45);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.modal-box {
  background: #fff; border-radius: 10px; padding: 28px;
  width: 600px; max-width: calc(100vw - 48px); box-shadow: 0 20px 60px rgba(0,0,0,.2);
}
.modal-title { font-size: 16px; font-weight: 700; margin: 0 0 20px; color: #111827; }
.modal-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 20px; }

/* ── Empty state ─────────────────────────────────────────────── */
.empty-state-page {
  text-align: center; padding: 80px 24px;
  background: #fff; border: 1px solid #e5e7eb; border-radius: 8px;
}
.empty-state-icon { font-size: 48px; margin-bottom: 16px; }
.empty-state-page h3 { font-size: 18px; font-weight: 600; margin: 0 0 8px; }

/* ── Buttons ─────────────────────────────────────────────────── */
.btn { padding: 8px 16px; border-radius: 6px; font-size: 13px; font-weight: 500; border: none; cursor: pointer; transition: background .15s; }
.btn-sm { padding: 5px 11px; font-size: 12px; }
.btn-primary { background: #2563eb; color: #fff; }
.btn-primary:hover:not(:disabled) { background: #1d4ed8; }
.btn-secondary { background: #f3f4f6; color: #374151; border: 1px solid #d1d5db; }
.btn-secondary:hover:not(:disabled) { background: #e5e7eb; }
.btn-danger { background: #fee2e2; color: #dc2626; border: 1px solid #fca5a5; }
.btn-danger:hover:not(:disabled) { background: #fecaca; }
.btn:disabled { opacity: .5; cursor: not-allowed; }
</style>
