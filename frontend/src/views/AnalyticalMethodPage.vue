<script setup>
import { onMounted, ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '@/components/layout/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { useAnalyticalStore } from '@/stores/analytical'
import { useAIPageContext } from '@/composables/useAIPageContext'

const route = useRoute()
const projectId = route.params.id
const store = useAnalyticalStore()

const activeTab = ref('definition')
const creatingMethod = ref(false)
const savingDef = ref(false)
const saveStatus = ref('')

const newMethodForm = ref({ method_name: '', method_type: 'hplc', analyte: '', instrument: '', principle: '', validation_status: 'not_started' })

const defForm = ref({ method_name: '', method_type: 'hplc', analyte: '', instrument: '', principle: '', validation_status: 'not_started' })

const paramsForm = ref({})

const devLogForm = ref({ date: new Date().toISOString().slice(0, 10), description: '', key_results: '', verdict: 'needs_optimization', notes: '' })

// ─── Static reference data ────────────────────────────────────────────────────

const METHOD_TYPES = [
  { value: 'hplc', label: 'HPLC', color: '#2563eb' },
  { value: 'gc', label: 'GC', color: '#16a34a' },
  { value: 'nmr', label: 'NMR', color: '#7c3aed' },
  { value: 'ms', label: 'MS', color: '#d97706' },
  { value: 'uv_vis', label: 'UV-Vis', color: '#0891b2' },
  { value: 'dissolution', label: 'Dissolution', color: '#ea580c' },
  { value: 'particle_size', label: 'Particle Size', color: '#6b7280' },
  { value: 'other', label: 'Other', color: '#9ca3af' },
]

const PURPOSES = [
  { value: 'assay', label: 'Assay (Potency)' },
  { value: 'purity', label: 'Purity / Related Substances' },
  { value: 'dissolution', label: 'Dissolution' },
  { value: 'identification', label: 'Identification' },
  { value: 'water', label: 'Water Content' },
  { value: 'residual_solvents', label: 'Residual Solvents' },
  { value: 'particle_size', label: 'Particle Size' },
  { value: 'other', label: 'Other' },
]

const VALIDATION_STATUSES = [
  { value: 'not_started', label: 'Not Started', color: '#9ca3af' },
  { value: 'in_progress', label: 'In Progress', color: '#d97706' },
  { value: 'validated', label: 'Validated', color: '#16a34a' },
  { value: 'transferred', label: 'Transferred', color: '#2563eb' },
]

const VERDICT_OPTIONS = [
  { value: 'suitable', label: 'Suitable', color: '#16a34a' },
  { value: 'needs_optimization', label: 'Needs Optimization', color: '#d97706' },
  { value: 'not_suitable', label: 'Not Suitable', color: '#dc2626' },
]

const PRESET_INSTRUMENTS = {
  hplc: ['Agilent 1260 Infinity II', 'Agilent 1290 Infinity II (UHPLC)', 'Waters Alliance e2695', 'Waters Acquity UPLC', 'Shimadzu LC-2030', 'Thermo Vanquish'],
  gc: ['Agilent 7890B GC', 'Shimadzu GC-2030', 'Thermo TRACE 1310 GC', 'PerkinElmer Clarus 690'],
  nmr: ['Bruker AVANCE III 400 MHz', 'Bruker AVANCE NEO 600 MHz', 'Varian MR 400 MHz', 'Jeol ECZ 400 MHz'],
  ms: ['Sciex QTRAP 6500+', 'Agilent 6460 Triple Quad', 'Thermo TSQ Altis', 'Waters Xevo TQ-S'],
  uv_vis: ['Agilent Cary 60 UV-Vis', 'Shimadzu UV-2600', 'Thermo Evolution 60S'],
  dissolution: ['Agilent 708-DS', 'Sotax AT7 Smart', 'Hanson Research SR8-Plus', 'Vankel VK 7000'],
  particle_size: ['Malvern Mastersizer 3000', 'Malvern Spraytec', 'Sympatec HELOS', 'Horiba LA-960'],
}

const PRESET_PARAMS = {
  hplc: [
    {
      label: 'RP-HPLC Assay (C18, gradient, UV 220 nm)',
      params: { column: 'Agilent Eclipse Plus C18, 150×4.6 mm, 3.5 µm', mobile_phase_a: '10 mM ammonium formate pH 3.0 (0.1% FA)', mobile_phase_b: 'Acetonitrile', gradient: '0 min: 5%B → 15 min: 60%B → 18 min: 95%B → 20 min: 95%B → 21 min: 5%B (re-equil 4 min)', flow_rate: '1.0', column_temp: '40', injection_volume: '10', wavelength: '220', run_time: '25', sample_prep: 'Dissolve in diluent (50:50 MeOH:water), filter 0.22 µm' },
    },
    {
      label: 'RP-HPLC Impurity (shallow gradient, 210 nm)',
      params: { column: 'Waters XBridge BEH C18, 250×4.6 mm, 5 µm', mobile_phase_a: '0.1% TFA in water', mobile_phase_b: '0.1% TFA in acetonitrile', gradient: '0 min: 5%B → 30 min: 80%B → 32 min: 95%B → 35 min: 5%B', flow_rate: '1.0', column_temp: '30', injection_volume: '20', wavelength: '210', run_time: '35', sample_prep: '1 mg/mL in diluent; filter 0.22 µm' },
    },
    {
      label: 'UHPLC Assay (C18, 2 min, DAD)',
      params: { column: 'Agilent Poroshell 120 EC-C18, 50×2.1 mm, 2.7 µm', mobile_phase_a: '5 mM ammonium bicarbonate pH 9.0', mobile_phase_b: 'Acetonitrile', gradient: '0 min: 10%B → 1.5 min: 90%B → 2 min: 10%B', flow_rate: '0.5', column_temp: '40', injection_volume: '2', wavelength: '254', run_time: '3', sample_prep: 'Dissolve 0.5 mg/mL in 50% acetonitrile' },
    },
  ],
  gc: [
    {
      label: 'GC Headspace — Residual Solvents (ICH Q3C)',
      params: { column: 'CP-WAX 52 CB, 25m × 0.32mm × 1.2µm', carrier_gas: 'Nitrogen', flow_rate: '1.5', injector_temp: '140', oven_program: '40°C (15 min) → 20°C/min → 200°C (5 min)', detector: 'FID', detector_temp: '250', split_ratio: '1:2 (headspace)', hs_temp: '80°C, 20 min equilibration' },
    },
    {
      label: 'GC FID — Organic Volatiles',
      params: { column: 'DB-1, 30m × 0.32mm × 0.25µm', carrier_gas: 'Helium', flow_rate: '2.0', injector_temp: '200', oven_program: '50°C (5 min) → 10°C/min → 250°C (10 min)', detector: 'FID', detector_temp: '280', split_ratio: '20:1' },
    },
  ],
  dissolution: [
    {
      label: 'USP Apparatus II — IR Tablet (pH 6.8)',
      params: { apparatus: 'II (Paddle)', medium: 'Phosphate buffer pH 6.8', volume: '900', rpm: '50', temperature: '37.0 ± 0.5', timepoints: '5, 10, 15, 20, 30, 45, 60 min', filter: '10 µm full-flow PVDF', sample_volume: '5 mL (replace with fresh medium)', detection: 'UV at API λmax or HPLC' },
    },
    {
      label: 'USP Apparatus II — Extended Release (pH 7.2)',
      params: { apparatus: 'II (Paddle)', medium: 'Phosphate buffer pH 7.2', volume: '900', rpm: '100', temperature: '37.0 ± 0.5', timepoints: '1, 2, 4, 6, 8, 12 h', filter: '10 µm PVDF', sample_volume: '3 mL (no replacement)', detection: 'HPLC' },
    },
    {
      label: 'USP Apparatus I — Capsule (pH 1.2)',
      params: { apparatus: 'I (Basket)', medium: 'Simulated Gastric Fluid pH 1.2 (without enzyme)', volume: '900', rpm: '100', temperature: '37.0 ± 0.5', timepoints: '10, 20, 30, 45, 60 min', filter: '10 µm sintered', detection: 'UV at API λmax' },
    },
  ],
  nmr: [
    {
      label: 'qNMR Identity / Assay (DMSO-d6, 400 MHz)',
      params: { frequency: '400', solvent: 'DMSO-d₆', pulse_sequence: 'zg30 (30° flip angle)', scans: '64', relaxation_delay: '30', concentration: '5–20 mg/mL', reference: 'Maleic acid (internal std, 1 mg/mL)', acquisition: 'D1 ≥ 5×T1; NS = 64' },
    },
  ],
}

const ICH_CHECKLIST_GUIDANCE = {
  specificity: 'Demonstrate method is unaffected by matrix, placebo, degradation products. Perform forced degradation (acid/base/oxidation/heat/light) and confirm peak purity by DAD or MS.',
  linearity: 'Minimum 5 concentration levels across 80–120% of target concentration. r² ≥ 0.999. Include y-intercept significance test.',
  range: 'For assay: 80–120% of label claim. For impurities: reporting threshold to 120% of limit. For dissolution: 0–20% above Q value.',
  accuracy: 'Minimum 9 determinations: 3 concentrations × 3 replicates. Recovery 98–102% for assay; 70–110% for impurities. Report mean, %RSD, 95% CI.',
  precision: 'Repeatability: 6 injections at 100% conc; %RSD ≤ 2.0%. Intermediate precision: 2 analysts, 2 days, 2 instruments. Reproducibility if published method.',
  detection_limit: 'S/N ≥ 3:1. Confirm visually. Report LOD value and method used (visual / S/N / calibration slope).',
  quantitation_limit: 'S/N ≥ 10:1. Confirm accuracy and precision at LOQ (70–130%, %RSD ≤ 20%). Report LOQ and precision data.',
  robustness: 'Evaluate 1 parameter at a time: flow rate (±0.1 mL/min), pH (±0.2), column temp (±5°C), wavelength (±5 nm), column lot. Accept ±15% change in response.',
}

// ─── Computed ─────────────────────────────────────────────────────────────────

const currentProtocol = computed(() => store.currentMethod?.protocol || {})
const currentParams = computed(() => currentProtocol.value.params || {})
const currentDevLog = computed(() => currentProtocol.value.dev_log || [])

const methodTypeColor = computed(() => {
  return METHOD_TYPES.find(t => t.value === store.currentMethod?.method_type)?.color || '#6b7280'
})

const validationColor = computed(() => {
  return VALIDATION_STATUSES.find(s => s.value === store.currentMethod?.validation_status)?.color || '#9ca3af'
})

const completionPct = computed(() => store.validationStatus?.completion_pct || 0)

const methodsByType = computed(() => {
  const groups = {}
  store.methods.forEach(m => {
    const t = m.method_type || 'other'
    if (!groups[t]) groups[t] = []
    groups[t].push(m)
  })
  return groups
})

// ─── Actions ──────────────────────────────────────────────────────────────────

async function createMethod() {
  await store.createMethod(projectId, { ...newMethodForm.value })
  const created = store.methods[0]
  selectMethod(created)
  creatingMethod.value = false
  newMethodForm.value = { method_name: '', method_type: 'hplc', analyte: '', instrument: '', principle: '', validation_status: 'not_started' }
}

function selectMethod(m) {
  store.currentMethod = m
  loadDefForm(m)
  loadParams(m)
  activeTab.value = 'definition'
  store.fetchValidationStatus(m.id)
}

function loadDefForm(m) {
  defForm.value = {
    method_name: m.method_name || '',
    method_type: m.method_type || 'hplc',
    analyte: m.analyte || '',
    instrument: m.instrument || '',
    principle: m.principle || '',
    validation_status: m.validation_status || 'not_started',
  }
}

function loadParams(m) {
  paramsForm.value = { ...(m.protocol?.params || {}) }
}

async function saveDefinition() {
  savingDef.value = true
  try {
    await store.updateMethod(store.currentMethod.id, { ...defForm.value })
    saveStatus.value = 'saved'
    setTimeout(() => saveStatus.value = '', 2500)
  } finally {
    savingDef.value = false
  }
}

async function saveParams() {
  const updated = await store.updateMethod(store.currentMethod.id, {
    protocol: { ...currentProtocol.value, params: { ...paramsForm.value } },
  })
  loadParams(updated)
  saveStatus.value = 'params_saved'
  setTimeout(() => saveStatus.value = '', 2500)
}

function applyParamPreset(preset) {
  paramsForm.value = { ...preset.params }
}

async function addDevLogEntry() {
  const entry = { ...devLogForm.value, id: Date.now() }
  const newLog = [...currentDevLog.value, entry]
  await store.updateMethod(store.currentMethod.id, {
    protocol: { ...currentProtocol.value, dev_log: newLog },
  })
  devLogForm.value = { date: new Date().toISOString().slice(0, 10), description: '', key_results: '', verdict: 'needs_optimization', notes: '' }
}

async function removeLogEntry(id) {
  const newLog = currentDevLog.value.filter(e => e.id !== id)
  await store.updateMethod(store.currentMethod.id, {
    protocol: { ...currentProtocol.value, dev_log: newLog },
  })
}

async function toggleChecklist(item) {
  const current = !!currentProtocol.value[item]
  await store.updateMethod(store.currentMethod.id, {
    protocol: { ...currentProtocol.value, [item]: !current },
  })
  await store.fetchValidationStatus(store.currentMethod.id)
}

async function removeMethod(m) {
  if (!confirm(`Delete method "${m.method_name}"? This cannot be undone.`)) return
  await store.deleteMethod(m.id)
}

function verdictColor(v) {
  return VERDICT_OPTIONS.find(o => o.value === v)?.color || '#6b7280'
}

function methodColor(type) {
  return METHOD_TYPES.find(t => t.value === type)?.color || '#6b7280'
}

watch(() => store.currentMethod, (m) => {
  if (m) { loadDefForm(m); loadParams(m) }
})

const projectIdNum = computed(() => parseInt(projectId))
useAIPageContext({
  pageType: 'AnalyticalMethod',
  projectIdRef: projectIdNum,
  getEntity: () => (newMethodForm.value),
  applyFn: (s) => {
    Object.entries(s).forEach(([k, v]) => { if (k in newMethodForm.value) newMethodForm.value[k] = v })
  },
})

onMounted(async () => {
  await store.fetchMethods(projectId)
  if (store.methods.length) selectMethod(store.methods[0])
})
</script>

<template>
  <div>
    <PageHeader title="Analytical Methods">
      <template #actions>
        <button class="btn btn-primary" @click="creatingMethod = true">+ New Method</button>
      </template>
    </PageHeader>

    <!-- Create method modal -->
    <div v-if="creatingMethod" class="modal-overlay" @click.self="creatingMethod = false">
      <div class="modal-box">
        <h3 class="modal-title">New Analytical Method</h3>
        <div class="form-grid-2">
          <div class="form-group" style="grid-column: span 2">
            <label class="form-label">Method Name</label>
            <input v-model="newMethodForm.method_name" class="form-input" placeholder="e.g. Assay by RP-HPLC" />
          </div>
          <div class="form-group">
            <label class="form-label">Method Type</label>
            <select v-model="newMethodForm.method_type" class="form-input">
              <option v-for="t in METHOD_TYPES" :key="t.value" :value="t.value">{{ t.label }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Purpose</label>
            <select v-model="newMethodForm.principle" class="form-input">
              <option v-for="p in PURPOSES" :key="p.value" :value="p.value">{{ p.label }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Analyte(s)</label>
            <input v-model="newMethodForm.analyte" class="form-input" placeholder="e.g. Drug substance + 3 impurities" />
          </div>
          <div class="form-group">
            <label class="form-label">Instrument</label>
            <input v-model="newMethodForm.instrument" class="form-input" placeholder="e.g. Agilent 1260" list="instrument-presets" />
            <datalist id="instrument-presets">
              <option v-for="i in (PRESET_INSTRUMENTS[newMethodForm.method_type] || [])" :key="i" :value="i" />
            </datalist>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="creatingMethod = false">Cancel</button>
          <button class="btn btn-primary" :disabled="!newMethodForm.method_name" @click="createMethod">Create</button>
        </div>
      </div>
    </div>

    <LoadingSpinner v-if="store.loading.methods && !store.methods.length" />

    <div v-else class="page-layout">
      <!-- ── Left: methods list ──────────────────────────────────────── -->
      <div class="methods-panel">
        <div class="section-card">
          <h3 class="section-title">Methods ({{ store.methods.length }})</h3>
          <div v-if="!store.methods.length" class="empty-note">No methods yet.</div>
          <div v-else>
            <div v-for="(group, type) in methodsByType" :key="type">
              <div class="method-group-label" :style="{ color: methodColor(type) }">
                {{ METHOD_TYPES.find(t => t.value === type)?.label || type }}
              </div>
              <div
                v-for="m in group" :key="m.id"
                class="method-row"
                :class="{ active: store.currentMethod?.id === m.id }"
                @click="selectMethod(m)"
              >
                <div class="method-row-name">{{ m.method_name }}</div>
                <div class="method-row-meta">
                  <span class="analyte-text">{{ m.analyte || '—' }}</span>
                  <span class="validation-dot" :style="{ background: VALIDATION_STATUSES.find(s => s.value === m.validation_status)?.color }"></span>
                </div>
                <button class="btn-icon-danger" @click.stop="removeMethod(m)" title="Delete">✕</button>
              </div>
            </div>
          </div>
        </div>

        <!-- ICH Q2(R1) reference card -->
        <div class="section-card" style="margin-top:12px">
          <h3 class="section-title" style="font-size:12px;margin-bottom:8px">ICH Q2(R1) Validation Requirements</h3>
          <table class="ref-table">
            <thead><tr><th>Characteristic</th><th>Assay</th><th>Imp</th><th>Diss</th><th>ID</th></tr></thead>
            <tbody>
              <tr><td>Specificity</td><td class="chk">✓</td><td class="chk">✓</td><td class="chk">✓</td><td class="chk">✓</td></tr>
              <tr><td>Linearity</td><td class="chk">✓</td><td class="chk">✓</td><td class="chk">✓</td><td>—</td></tr>
              <tr><td>Range</td><td class="chk">✓</td><td class="chk">✓</td><td class="chk">✓</td><td>—</td></tr>
              <tr><td>Accuracy</td><td class="chk">✓</td><td class="chk">✓</td><td class="chk">✓</td><td>—</td></tr>
              <tr><td>Precision</td><td class="chk">✓</td><td class="chk">✓</td><td class="chk">✓</td><td>—</td></tr>
              <tr><td>LOD</td><td>—</td><td class="chk">✓</td><td>—</td><td>—</td></tr>
              <tr><td>LOQ</td><td>—</td><td class="chk">✓</td><td>—</td><td>—</td></tr>
              <tr><td>Robustness</td><td class="chk">✓</td><td class="chk">✓</td><td class="chk">✓</td><td>—</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ── Right: method detail ───────────────────────────────────── -->
      <div class="detail-panel" v-if="store.currentMethod">
        <!-- Method header -->
        <div class="method-header-bar">
          <div class="method-header-left">
            <span class="method-type-pill" :style="{ background: methodTypeColor + '20', color: methodTypeColor, border: '1px solid ' + methodTypeColor }">
              {{ METHOD_TYPES.find(t => t.value === store.currentMethod.method_type)?.label }}
            </span>
            <strong class="method-header-name">{{ store.currentMethod.method_name }}</strong>
          </div>
          <div class="method-header-right">
            <span class="validation-pill" :style="{ background: validationColor + '20', color: validationColor }">
              {{ VALIDATION_STATUSES.find(s => s.value === store.currentMethod.validation_status)?.label }}
            </span>
            <span v-if="completionPct > 0" class="completion-text">Validation {{ completionPct }}% complete</span>
          </div>
        </div>

        <!-- Tabs -->
        <div class="tab-nav">
          <button class="tab-btn" :class="{ active: activeTab === 'definition' }" @click="activeTab = 'definition'">Definition & Parameters</button>
          <button class="tab-btn" :class="{ active: activeTab === 'devlog' }" @click="activeTab = 'devlog'">
            Development Log
            <span v-if="currentDevLog.length" class="tab-badge">{{ currentDevLog.length }}</span>
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'validation' }" @click="activeTab = 'validation'">
            ICH Q2(R1) Validation
            <span v-if="completionPct > 0" class="tab-badge" :style="{ background: completionPct === 100 ? '#16a34a' : '#d97706' }">{{ completionPct }}%</span>
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'reference' }" @click="activeTab = 'reference'">Reference</button>
        </div>

        <!-- ── Tab: Definition & Parameters ──────────────────────────── -->
        <div v-if="activeTab === 'definition'" class="tab-content">
          <div class="section-card">
            <div class="section-header">
              <h3 class="section-title">Method Definition</h3>
              <div class="section-actions">
                <span v-if="saveStatus === 'saved'" class="save-confirm">✓ Saved</span>
                <button class="btn btn-primary btn-sm" :disabled="savingDef" @click="saveDefinition">
                  {{ savingDef ? 'Saving…' : 'Save' }}
                </button>
              </div>
            </div>
            <div class="form-grid-3">
              <div class="form-group" style="grid-column: span 2">
                <label class="form-label">Method Name</label>
                <input v-model="defForm.method_name" class="form-input" />
              </div>
              <div class="form-group">
                <label class="form-label">Method Type</label>
                <select v-model="defForm.method_type" class="form-input">
                  <option v-for="t in METHOD_TYPES" :key="t.value" :value="t.value">{{ t.label }}</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">Purpose / Scope</label>
                <select v-model="defForm.principle" class="form-input">
                  <option v-for="p in PURPOSES" :key="p.value" :value="p.value">{{ p.label }}</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">Analyte(s)</label>
                <input v-model="defForm.analyte" class="form-input" placeholder="e.g. API + 3 specified impurities" />
              </div>
              <div class="form-group">
                <label class="form-label">Validation Status</label>
                <select v-model="defForm.validation_status" class="form-input">
                  <option v-for="s in VALIDATION_STATUSES" :key="s.value" :value="s.value">{{ s.label }}</option>
                </select>
              </div>
              <div class="form-group" style="grid-column: span 3">
                <label class="form-label">Instrument</label>
                <input v-model="defForm.instrument" class="form-input" list="instrument-list-edit" placeholder="Instrument model" />
                <datalist id="instrument-list-edit">
                  <option v-for="i in (PRESET_INSTRUMENTS[defForm.method_type] || [])" :key="i" :value="i" />
                </datalist>
              </div>
            </div>
          </div>

          <!-- Method Parameters -->
          <div class="section-card" style="margin-top:16px">
            <div class="section-header">
              <h3 class="section-title">Method Parameters</h3>
              <div class="section-actions">
                <span v-if="saveStatus === 'params_saved'" class="save-confirm">✓ Saved</span>
                <button class="btn btn-primary btn-sm" @click="saveParams">Save Parameters</button>
              </div>
            </div>

            <!-- Preset templates -->
            <div v-if="PRESET_PARAMS[store.currentMethod.method_type]" style="margin-bottom:14px">
              <p class="preset-group-label">Parameter Templates — click to pre-fill</p>
              <div style="display:flex;flex-wrap:wrap;gap:6px">
                <button v-for="p in PRESET_PARAMS[store.currentMethod.method_type]" :key="p.label"
                  class="preset-chip" @click="applyParamPreset(p)">
                  {{ p.label }}
                </button>
              </div>
            </div>

            <!-- HPLC params -->
            <div v-if="store.currentMethod.method_type === 'hplc'" class="param-grid">
              <div class="form-group" style="grid-column: span 2"><label class="form-label">Column (stationary phase)</label><input v-model="paramsForm.column" class="form-input" placeholder="Agilent Eclipse Plus C18, 150×4.6 mm, 3.5 µm" /></div>
              <div class="form-group"><label class="form-label">Flow Rate (mL/min)</label><input v-model="paramsForm.flow_rate" type="number" step="0.1" class="form-input" /></div>
              <div class="form-group"><label class="form-label">Column Temp (°C)</label><input v-model="paramsForm.column_temp" type="number" class="form-input" /></div>
              <div class="form-group"><label class="form-label">Injection Volume (µL)</label><input v-model="paramsForm.injection_volume" type="number" class="form-input" /></div>
              <div class="form-group"><label class="form-label">Wavelength (nm)</label><input v-model="paramsForm.wavelength" type="number" class="form-input" /></div>
              <div class="form-group"><label class="form-label">Run Time (min)</label><input v-model="paramsForm.run_time" type="number" class="form-input" /></div>
              <div class="form-group"><label class="form-label">LOD (%)</label><input v-model="paramsForm.lod" type="number" step="0.001" class="form-input" /></div>
              <div class="form-group"><label class="form-label">LOQ (%)</label><input v-model="paramsForm.loq" type="number" step="0.001" class="form-input" /></div>
              <div class="form-group" style="grid-column: span 3"><label class="form-label">Mobile Phase A</label><input v-model="paramsForm.mobile_phase_a" class="form-input" placeholder="e.g. 10 mM ammonium formate pH 3.0 + 0.1% FA" /></div>
              <div class="form-group" style="grid-column: span 3"><label class="form-label">Mobile Phase B</label><input v-model="paramsForm.mobile_phase_b" class="form-input" placeholder="e.g. Acetonitrile" /></div>
              <div class="form-group" style="grid-column: span 3"><label class="form-label">Gradient Program</label><textarea v-model="paramsForm.gradient" class="form-input" rows="3" placeholder="0 min: 5%B → 15 min: 60%B → 20 min: 95%B → 22 min: 5%B (re-equil 3 min)" /></div>
              <div class="form-group" style="grid-column: span 3"><label class="form-label">Sample Preparation</label><input v-model="paramsForm.sample_prep" class="form-input" placeholder="e.g. Dissolve in 50:50 MeOH:water, filter 0.22 µm PTFE" /></div>
            </div>

            <!-- GC params -->
            <div v-else-if="store.currentMethod.method_type === 'gc'" class="param-grid">
              <div class="form-group" style="grid-column: span 2"><label class="form-label">Column</label><input v-model="paramsForm.column" class="form-input" placeholder="DB-WAX, 30m × 0.32mm × 1.2µm" /></div>
              <div class="form-group"><label class="form-label">Carrier Gas</label><select v-model="paramsForm.carrier_gas" class="form-input"><option>Helium</option><option>Nitrogen</option><option>Hydrogen</option></select></div>
              <div class="form-group"><label class="form-label">Flow Rate (mL/min)</label><input v-model="paramsForm.flow_rate" type="number" step="0.1" class="form-input" /></div>
              <div class="form-group"><label class="form-label">Injector Temp (°C)</label><input v-model="paramsForm.injector_temp" type="number" class="form-input" /></div>
              <div class="form-group"><label class="form-label">Detector</label><select v-model="paramsForm.detector" class="form-input"><option>FID</option><option>MS</option><option>ECD</option><option>NPD</option></select></div>
              <div class="form-group"><label class="form-label">Detector Temp (°C)</label><input v-model="paramsForm.detector_temp" type="number" class="form-input" /></div>
              <div class="form-group"><label class="form-label">Split Ratio</label><input v-model="paramsForm.split_ratio" class="form-input" placeholder="e.g. 20:1" /></div>
              <div class="form-group" style="grid-column: span 3"><label class="form-label">Oven Temperature Program</label><textarea v-model="paramsForm.oven_program" class="form-input" rows="3" placeholder="40°C (15 min) → 20°C/min → 200°C (5 min)" /></div>
            </div>

            <!-- NMR params -->
            <div v-else-if="store.currentMethod.method_type === 'nmr'" class="param-grid">
              <div class="form-group"><label class="form-label">Frequency (MHz)</label><select v-model="paramsForm.frequency" class="form-input"><option>300</option><option>400</option><option>500</option><option>600</option><option>800</option></select></div>
              <div class="form-group"><label class="form-label">Solvent</label><select v-model="paramsForm.solvent" class="form-input"><option>DMSO-d₆</option><option>D₂O</option><option>CDCl₃</option><option>CD₃OD</option><option>CD₃CN</option></select></div>
              <div class="form-group"><label class="form-label">Pulse Sequence</label><input v-model="paramsForm.pulse_sequence" class="form-input" placeholder="zg30" /></div>
              <div class="form-group"><label class="form-label">Number of Scans</label><input v-model="paramsForm.scans" type="number" class="form-input" /></div>
              <div class="form-group"><label class="form-label">Relaxation Delay (s)</label><input v-model="paramsForm.relaxation_delay" type="number" class="form-input" /></div>
              <div class="form-group"><label class="form-label">Concentration</label><input v-model="paramsForm.concentration" class="form-input" placeholder="e.g. 5–20 mg/mL" /></div>
              <div class="form-group" style="grid-column: span 3"><label class="form-label">Internal Standard / Reference</label><input v-model="paramsForm.reference" class="form-input" placeholder="e.g. Maleic acid 1 mg/mL (for qNMR)" /></div>
            </div>

            <!-- Dissolution params -->
            <div v-else-if="store.currentMethod.method_type === 'dissolution'" class="param-grid">
              <div class="form-group"><label class="form-label">Apparatus</label><select v-model="paramsForm.apparatus" class="form-input"><option value="I (Basket)">I — Basket</option><option value="II (Paddle)">II — Paddle</option><option value="III">III — Reciprocating Cylinder</option><option value="IV">IV — Flow-Through Cell</option></select></div>
              <div class="form-group"><label class="form-label">RPM</label><input v-model="paramsForm.rpm" type="number" class="form-input" /></div>
              <div class="form-group"><label class="form-label">Temperature (°C)</label><input v-model="paramsForm.temperature" class="form-input" placeholder="37.0 ± 0.5" /></div>
              <div class="form-group"><label class="form-label">Medium</label><input v-model="paramsForm.medium" class="form-input" placeholder="e.g. Phosphate buffer pH 6.8" /></div>
              <div class="form-group"><label class="form-label">Volume (mL)</label><input v-model="paramsForm.volume" type="number" class="form-input" /></div>
              <div class="form-group"><label class="form-label">Filter</label><input v-model="paramsForm.filter" class="form-input" placeholder="e.g. 10 µm PVDF full-flow" /></div>
              <div class="form-group" style="grid-column: span 3"><label class="form-label">Sampling Timepoints</label><input v-model="paramsForm.timepoints" class="form-input" placeholder="e.g. 5, 10, 15, 20, 30, 45, 60 min" /></div>
              <div class="form-group" style="grid-column: span 3"><label class="form-label">Detection</label><input v-model="paramsForm.detection" class="form-input" placeholder="e.g. UV at 254 nm or HPLC" /></div>
            </div>

            <!-- Generic params -->
            <div v-else class="form-grid-2">
              <div class="form-group" style="grid-column: span 2"><label class="form-label">Key Parameters</label><textarea v-model="paramsForm.notes" class="form-input" rows="5" placeholder="Describe method parameters, instrument settings, sample preparation…" /></div>
            </div>
          </div>
        </div>

        <!-- ── Tab: Development Log ───────────────────────────────────── -->
        <div v-if="activeTab === 'devlog'" class="tab-content">
          <div class="section-card">
            <div class="section-header">
              <h3 class="section-title">Development Experiments</h3>
            </div>
            <div class="form-grid-3" style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:6px;padding:14px;margin-bottom:16px">
              <div class="form-group">
                <label class="form-label">Date</label>
                <input v-model="devLogForm.date" type="date" class="form-input" />
              </div>
              <div class="form-group" style="grid-column: span 2">
                <label class="form-label">Conditions Tested</label>
                <input v-model="devLogForm.description" class="form-input" placeholder="e.g. C18 column, pH 3.5 buffer, 1.0 mL/min, 220 nm" />
              </div>
              <div class="form-group" style="grid-column: span 2">
                <label class="form-label">Key Results (Rt, Rs, As, N, % recovery…)</label>
                <input v-model="devLogForm.key_results" class="form-input" placeholder="e.g. Rt = 8.2 min, Rs = 2.4 (imp A), As = 1.15, N = 4200" />
              </div>
              <div class="form-group">
                <label class="form-label">Verdict</label>
                <select v-model="devLogForm.verdict" class="form-input">
                  <option v-for="v in VERDICT_OPTIONS" :key="v.value" :value="v.value">{{ v.label }}</option>
                </select>
              </div>
              <div class="form-group" style="grid-column: span 3">
                <label class="form-label">Notes / Next Steps</label>
                <textarea v-model="devLogForm.notes" class="form-input" rows="2" placeholder="Observations, optimization ideas, column changes to try…" />
              </div>
              <div style="grid-column: span 3">
                <button class="btn btn-primary btn-sm" :disabled="!devLogForm.description" @click="addDevLogEntry">Add Entry</button>
              </div>
            </div>

            <div v-if="currentDevLog.length">
              <table class="sci-table">
                <thead>
                  <tr><th>Date</th><th>Conditions</th><th>Key Results</th><th>Verdict</th><th>Notes</th><th></th></tr>
                </thead>
                <tbody>
                  <tr v-for="entry in [...currentDevLog].reverse()" :key="entry.id">
                    <td class="td-date">{{ entry.date }}</td>
                    <td>{{ entry.description }}</td>
                    <td class="td-mono">{{ entry.key_results || '—' }}</td>
                    <td>
                      <span class="verdict-badge" :style="{ color: verdictColor(entry.verdict), background: verdictColor(entry.verdict) + '15', border: '1px solid ' + verdictColor(entry.verdict) + '50' }">
                        {{ VERDICT_OPTIONS.find(v => v.value === entry.verdict)?.label || entry.verdict }}
                      </span>
                    </td>
                    <td class="td-notes text-muted">{{ entry.notes || '—' }}</td>
                    <td><button class="btn btn-sm btn-danger" @click.stop="removeLogEntry(entry.id)">Remove</button></td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else class="empty-note">No development experiments logged yet.</div>
          </div>

          <!-- System suitability requirements reference -->
          <div class="section-card" style="margin-top:16px">
            <h3 class="section-title">System Suitability Requirements (RP-HPLC)</h3>
            <table class="sci-table">
              <thead><tr><th>Parameter</th><th>Symbol</th><th>Acceptance Criterion</th><th>Notes</th></tr></thead>
              <tbody>
                <tr><td>Resolution</td><td class="td-mono">Rs</td><td>NLT 2.0 (adjacent peaks)</td><td>Measure between API and nearest impurity or IS</td></tr>
                <tr><td>Tailing factor</td><td class="td-mono">As</td><td>NMT 2.0 (USP); 0.8–1.5 preferred</td><td>Asymmetry at 5% peak height</td></tr>
                <tr><td>Theoretical plates</td><td class="td-mono">N</td><td>NLT 2000 (assay column)</td><td>Calculated from API peak, half-height method</td></tr>
                <tr><td>%RSD (6 injections)</td><td class="td-mono">%CV</td><td>NMT 2.0% (assay); NMT 5% (impurities)</td><td>Peak area or response factor for quantitative methods</td></tr>
                <tr><td>Retention factor</td><td class="td-mono">k'</td><td>k' ≥ 2.0 (API peak)</td><td>Ensures adequate peak separation from void volume</td></tr>
                <tr><td>Capacity factor</td><td class="td-mono">α</td><td>α ≥ 1.05 (critical pair)</td><td>Separation factor between adjacent peaks</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- ── Tab: ICH Q2(R1) Validation ──────────────────────────── -->
        <div v-if="activeTab === 'validation'" class="tab-content">
          <div class="section-card">
            <div class="section-header">
              <h3 class="section-title">ICH Q2(R1) Validation Checklist</h3>
              <div class="section-actions">
                <div class="validation-progress-wrap">
                  <div class="validation-progress-bar">
                    <div class="validation-progress-fill" :style="{ width: completionPct + '%', background: completionPct === 100 ? '#16a34a' : '#2563eb' }" />
                  </div>
                  <span class="completion-label">{{ completionPct }}% complete</span>
                </div>
              </div>
            </div>
            <LoadingSpinner v-if="store.loading.validation" />
            <div v-else-if="store.validationStatus">
              <div v-for="item in store.validationStatus.checklist" :key="item" class="validation-item">
                <label class="validation-check-label" :class="{ done: store.validationStatus.completed.includes(item) }">
                  <input type="checkbox"
                    :checked="store.validationStatus.completed.includes(item)"
                    @change="toggleChecklist(item)"
                    class="validation-checkbox"
                  />
                  <span class="validation-item-name">{{ item.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) }}</span>
                </label>
                <p class="validation-guidance">{{ ICH_CHECKLIST_GUIDANCE[item] || '' }}</p>
              </div>
            </div>
            <div v-else class="empty-note">Select a method to view its validation checklist.</div>
          </div>

          <!-- Forced degradation guide -->
          <div class="section-card" style="margin-top:16px">
            <h3 class="section-title">Forced Degradation Conditions (Specificity)</h3>
            <table class="sci-table">
              <thead><tr><th>Condition</th><th>Reagent / Parameters</th><th>Typical Duration</th><th>Target Degradation</th></tr></thead>
              <tbody>
                <tr><td>Acid hydrolysis</td><td>0.1–1 M HCl, 60–80°C</td><td>1–24 h</td><td>5–20% degradation</td></tr>
                <tr><td>Base hydrolysis</td><td>0.1–1 M NaOH, 60°C</td><td>1–24 h</td><td>5–20% degradation</td></tr>
                <tr><td>Oxidation</td><td>3–30% H₂O₂, RT</td><td>30 min – 24 h</td><td>5–20% degradation</td></tr>
                <tr><td>Thermal (solid)</td><td>60–80°C dry heat, open dish</td><td>1–4 weeks</td><td>≥5% degradation or appearance change</td></tr>
                <tr><td>Photolysis (ICH Q1B)</td><td>1.2 M lux·h visible + 200 W·h/m² UV</td><td>Cumulative</td><td>Color change or ≥5% degradation</td></tr>
                <tr><td>Hydrolysis (neutral)</td><td>Water, 60–80°C</td><td>1–7 days</td><td>Context-specific</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- ── Tab: Reference ────────────────────────────────────────── -->
        <div v-if="activeTab === 'reference'" class="tab-content">
          <div class="section-card">
            <h3 class="section-title">Method-Type Reference — HPLC</h3>
            <table class="sci-table">
              <thead><tr><th>Parameter</th><th>Typical Range / Value</th><th>Optimization Lever</th></tr></thead>
              <tbody>
                <tr><td>Column chemistry</td><td>C18 (most common), C8 (less retentive), phenyl (π–π selectivity), HILIC (polar compounds)</td><td>Change selectivity for co-eluting peaks</td></tr>
                <tr><td>Particle size</td><td>3.5 µm (HPLC) / 1.7 µm (UHPLC)</td><td>Smaller → faster, higher pressure; balance with system capability</td></tr>
                <tr><td>pH (reversed-phase)</td><td>2–8 (silica); 1–12 (hybrid BEH/XB)</td><td>pH ± 1.5 from pKa suppresses ionization; improves peak shape</td></tr>
                <tr><td>Gradient slope</td><td>1–4% B/min (typical)</td><td>Shallower → better resolution; steeper → faster run</td></tr>
                <tr><td>Wavelength (UV)</td><td>210–220 nm (non-selective); 250–280 nm (aromatics)</td><td>Lower λ = higher sensitivity; more noise from mobile phase</td></tr>
                <tr><td>Ion pair (IP-HPLC)</td><td>5–10 mM TBA, TBAOH (cations); 5 mM HFBA (anions)</td><td>For highly polar ionic compounds not retained by RP</td></tr>
              </tbody>
            </table>
          </div>
          <div class="section-card" style="margin-top:16px">
            <h3 class="section-title">Compendial / Regulatory References</h3>
            <table class="sci-table">
              <thead><tr><th>Guideline</th><th>Scope</th></tr></thead>
              <tbody>
                <tr><td>ICH Q2(R1)</td><td>Validation of analytical procedures — specificity, linearity, accuracy, precision, range, LOD, LOQ, robustness</td></tr>
                <tr><td>ICH Q2(R2) / Q14</td><td>Enhanced approach to analytical method development and validation; analytical target profile (ATP)</td></tr>
                <tr><td>ICH Q3A(R2)</td><td>Impurities in drug substances — thresholds (reporting 0.05%, ID 0.10%/1.0 mg, qualification 0.15%/1.0 mg)</td></tr>
                <tr><td>ICH Q3B(R2)</td><td>Impurities in drug products — same threshold structure, different context</td></tr>
                <tr><td>ICH Q3C(R8)</td><td>Residual solvents — Class 1/2/3 limits; GC headspace method</td></tr>
                <tr><td>USP &lt;621&gt;</td><td>Chromatography — system suitability, peak tailing, resolution, theoretical plates</td></tr>
                <tr><td>Ph. Eur. 2.2.46</td><td>Chromatographic separation techniques — same fundamentals as USP</td></tr>
                <tr><td>USP &lt;711&gt;</td><td>Dissolution — apparatus, medium, sampling, calculations, acceptance criteria</td></tr>
                <tr><td>USP &lt;905&gt; / Ph. Eur. 2.9.40</td><td>Uniformity of dosage units — acceptance value (AV) calculation</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div v-else-if="!store.methods.length" class="detail-panel">
        <div class="empty-state-page">
          <div class="empty-state-icon">🔬</div>
          <h3>No Methods Yet</h3>
          <p class="text-muted">Create an analytical method to track development, parameters, and ICH Q2(R1) validation status.</p>
          <button class="btn btn-primary" @click="creatingMethod = true">+ New Method</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-layout { display: grid; grid-template-columns: 300px 1fr; gap: 16px; align-items: start; }

/* ── Methods panel ───────────────────────────────────────────── */
.method-group-label { font-size: 10px; font-weight: 700; color: #9ca3af; text-transform: uppercase; letter-spacing: .08em; padding: 10px 0 4px; }
.method-row {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 10px; border-radius: 6px; cursor: pointer;
  transition: background .12s; position: relative; margin-bottom: 2px;
}
.method-row:hover { background: #f3f4f6; }
.method-row.active { background: #eff6ff; }
.method-row-name { font-size: 13px; font-weight: 500; color: #111827; flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.method-row-meta { display: flex; align-items: center; gap: 4px; flex-shrink: 0; }
.analyte-text { font-size: 11px; color: #9ca3af; max-width: 80px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.validation-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.btn-icon-danger { background: none; border: none; color: #d1d5db; font-size: 11px; cursor: pointer; padding: 2px 4px; border-radius: 3px; flex-shrink: 0; }
.btn-icon-danger:hover { color: #dc2626; background: #fee2e2; }

/* ── Reference table (left panel) ────────────────────────────── */
.ref-table { width: 100%; border-collapse: collapse; font-size: 11px; }
.ref-table th { background: #f9fafb; color: #6b7280; font-weight: 600; font-size: 10px; text-transform: uppercase; letter-spacing: .04em; padding: 5px 6px; border-bottom: 1px solid #e5e7eb; text-align: center; }
.ref-table td { padding: 5px 6px; border-bottom: 1px solid #f3f4f6; color: #374151; }
.ref-table td:first-child { font-size: 10px; }
.ref-table tr:last-child td { border-bottom: none; }
.chk { text-align: center; color: #16a34a; font-weight: 700; }

/* ── Method header ───────────────────────────────────────────── */
.method-header-bar { display: flex; align-items: center; justify-content: space-between; padding: 12px 0; margin-bottom: 12px; }
.method-header-left { display: flex; align-items: center; gap: 10px; }
.method-header-right { display: flex; align-items: center; gap: 10px; }
.method-header-name { font-size: 15px; font-weight: 700; color: #111827; }
.method-type-pill { padding: 3px 10px; border-radius: 9999px; font-size: 11px; font-weight: 700; }
.validation-pill { padding: 3px 10px; border-radius: 9999px; font-size: 11px; font-weight: 600; }
.completion-text { font-size: 12px; color: #6b7280; }

/* ── Validation checklist ────────────────────────────────────── */
.validation-progress-wrap { display: flex; align-items: center; gap: 10px; }
.validation-progress-bar { width: 120px; height: 6px; background: #e5e7eb; border-radius: 3px; overflow: hidden; }
.validation-progress-fill { height: 100%; border-radius: 3px; transition: width .3s; }
.completion-label { font-size: 12px; color: #6b7280; white-space: nowrap; }
.validation-item { margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid #f3f4f6; }
.validation-item:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
.validation-check-label { display: flex; align-items: center; gap: 10px; cursor: pointer; }
.validation-checkbox { width: 16px; height: 16px; accent-color: #2563eb; flex-shrink: 0; }
.validation-item-name { font-size: 14px; font-weight: 600; color: #111827; }
.validation-check-label.done .validation-item-name { color: #16a34a; }
.validation-guidance { margin: 6px 0 0 26px; font-size: 12px; color: #6b7280; line-height: 1.5; }

/* ── Dev log ─────────────────────────────────────────────────── */
.td-date { font-size: 12px; white-space: nowrap; color: #6b7280; }
.td-mono { font-family: ui-monospace, monospace; font-size: 11px; }
.verdict-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }

/* ── Param grid ──────────────────────────────────────────────── */
.param-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }

/* ── Shared ──────────────────────────────────────────────────── */
.section-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; }
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.section-title { font-size: 14px; font-weight: 600; color: #111827; margin: 0 0 16px; }
.section-header .section-title { margin: 0; }
.section-actions { display: flex; gap: 8px; align-items: center; }
.save-confirm { font-size: 12px; color: #16a34a; font-weight: 500; }
.tab-nav { display: flex; gap: 2px; margin-bottom: 16px; border-bottom: 2px solid #e5e7eb; }
.tab-btn { padding: 8px 16px; font-size: 13px; font-weight: 500; background: none; border: none; border-bottom: 2px solid transparent; margin-bottom: -2px; cursor: pointer; color: #6b7280; transition: color .15s, border-color .15s; display: flex; align-items: center; gap: 6px; }
.tab-btn:hover { color: #374151; }
.tab-btn.active { color: #2563eb; border-bottom-color: #2563eb; }
.tab-badge { display: inline-flex; align-items: center; justify-content: center; min-width: 18px; height: 18px; padding: 0 5px; border-radius: 9px; background: #6b7280; color: #fff; font-size: 11px; font-weight: 600; }
.tab-content { animation: fadeIn .15s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }
.sci-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.sci-table th { background: #f9fafb; color: #374151; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: .04em; padding: 8px 12px; border-bottom: 2px solid #e5e7eb; text-align: left; white-space: nowrap; }
.sci-table td { padding: 10px 12px; border-bottom: 1px solid #f3f4f6; color: #374151; vertical-align: top; }
.sci-table tbody tr:hover { background: #f9fafb; }
.sci-table tbody tr:last-child td { border-bottom: none; }
.td-notes { font-size: 12px; max-width: 200px; }
.text-muted { color: #6b7280; }
.empty-note { padding: 24px; text-align: center; color: #9ca3af; font-size: 13px; }
.empty-state-page { text-align: center; padding: 80px 24px; background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; }
.empty-state-icon { font-size: 48px; margin-bottom: 16px; }
.empty-state-page h3 { font-size: 18px; font-weight: 600; margin: 0 0 8px; }
.form-grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.form-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.form-group { display: flex; flex-direction: column; gap: 4px; }
.form-label { font-size: 12px; font-weight: 500; color: #374151; }
.form-input { padding: 7px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; color: #111827; background: #fff; width: 100%; box-sizing: border-box; transition: border-color .15s; }
.form-input:focus { outline: none; border-color: #2563eb; box-shadow: 0 0 0 2px #dbeafe; }
.preset-group-label { font-size: 11px; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 6px; }
.preset-chip { padding: 5px 10px; border: 1px solid #d1d5db; border-radius: 6px; background: #f9fafb; cursor: pointer; font-size: 12px; color: #1e40af; transition: background .12s, border-color .12s; }
.preset-chip:hover { background: #eff6ff; border-color: #93c5fd; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal-box { background: #fff; border-radius: 10px; padding: 28px; width: 560px; max-width: calc(100vw - 48px); box-shadow: 0 20px 60px rgba(0,0,0,.2); }
.modal-title { font-size: 16px; font-weight: 700; margin: 0 0 20px; color: #111827; }
.modal-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 20px; }
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
