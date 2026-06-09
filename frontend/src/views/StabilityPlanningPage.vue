<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '@/components/layout/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { useStabilityStore } from '@/stores/stability'
import { useAIPageContext } from '@/composables/useAIPageContext'

const route = useRoute()
const projectId = route.params.id
const store = useStabilityStore()

const activeTab = ref('objectives')
const creatingPlan = ref(false)
const saveStatus = ref('')

const newPlanForm = ref({
  material_type: 'api',
  intended_storage_condition: '25°C/60% RH',
})

const planForm = ref({
  material_type: 'api',
  intended_storage_condition: '25°C/60% RH',
})

const conditionForm = ref({
  condition_label: '',
  temperature_c: '',
  humidity_rh: '',
  light_exposure: '',
  ich_category: '',
  timepoints_months: [],
  samples_per_timepoint: 3,
})

const resultForm = ref({
  condition_id: '',
  timepoint_weeks: '',
  appearance: '',
  assay_pct: '',
  degradants_pct: '',
  ph: '',
  water_content_pct: '',
  dissolution_pct: '',
  oos_flag: false,
  oot_flag: false,
  notes: '',
})

// ─── Static reference data ────────────────────────────────────────────────────

const MATERIAL_TYPES = [
  { value: 'api', label: 'API (Drug Substance)' },
  { value: 'dp', label: 'Drug Product' },
  { value: 'intermediate', label: 'Intermediate' },
]

const ICH_PRESETS = [
  {
    label: 'Long-term (ICH Zone I/II)',
    condition_label: 'Long-term 25°C/60% RH',
    temperature_c: 25,
    humidity_rh: 60,
    light_exposure: 'Protected from light',
    ich_category: 'long_term',
    guidance: 'ICH Q1A(R2) — primary stability data; 12, 24, 36, 48, 60 months',
    color: '#16a34a',
  },
  {
    label: 'Intermediate (ICH Zone I/II)',
    condition_label: 'Intermediate 30°C/65% RH',
    temperature_c: 30,
    humidity_rh: 65,
    light_exposure: 'Protected from light',
    ich_category: 'intermediate',
    guidance: 'ICH Q1A(R2) — bracketing condition; 6, 12 months',
    color: '#2563eb',
  },
  {
    label: 'Accelerated',
    condition_label: 'Accelerated 40°C/75% RH',
    temperature_c: 40,
    humidity_rh: 75,
    light_exposure: 'Protected from light',
    ich_category: 'accelerated',
    guidance: 'ICH Q1A(R2) — 3, 6 months; failure triggers intermediate study',
    color: '#d97706',
  },
  {
    label: 'Refrigerated (2–8°C)',
    condition_label: 'Refrigerated 5°C ± 3°C',
    temperature_c: 5,
    humidity_rh: null,
    light_exposure: 'Protected from light',
    ich_category: 'refrigerated',
    guidance: 'ICH Q1A(R2) — for cold-chain products; 12 months + accelerated 25°C/60%',
    color: '#7c3aed',
  },
  {
    label: 'Frozen (−20°C)',
    condition_label: 'Frozen −20°C',
    temperature_c: -20,
    humidity_rh: null,
    light_exposure: 'Protected from light',
    ich_category: 'frozen',
    guidance: 'ICH Q1A(R2) — case-by-case; 12+ months; freeze–thaw cycles required',
    color: '#0891b2',
  },
  {
    label: 'Photostability (ICH Q1B)',
    condition_label: 'Photostability Q1B',
    temperature_c: 25,
    humidity_rh: 60,
    light_exposure: '1.2M lux·h visible + 200 W·h/m² UV',
    ich_category: 'photo',
    guidance: 'ICH Q1B — forced degradation; confirm light sensitivity; compare open vs. closed sample',
    color: '#ea580c',
  },
]

const ICH_TIMEPOINTS = [
  { months: 0, weeks: 0, label: 'T0 (initial)' },
  { months: 1, weeks: 4, label: '1 month' },
  { months: 3, weeks: 13, label: '3 months' },
  { months: 6, weeks: 26, label: '6 months' },
  { months: 9, weeks: 39, label: '9 months' },
  { months: 12, weeks: 52, label: '12 months' },
  { months: 18, weeks: 78, label: '18 months' },
  { months: 24, weeks: 104, label: '24 months' },
  { months: 36, weeks: 156, label: '36 months' },
  { months: 48, weeks: 208, label: '48 months' },
  { months: 60, weeks: 260, label: '60 months' },
]

// ─── Computed ─────────────────────────────────────────────────────────────────

const oosCount = computed(() => {
  return Object.values(store.results).flat().filter(r => r.oos_flag).length
})

const ootCount = computed(() => {
  return Object.values(store.results).flat().filter(r => r.oot_flag && !r.oos_flag).length
})

const totalResults = computed(() => Object.values(store.results).flat().length)

const selectedConditionResults = computed(() => {
  if (!resultForm.value.condition_id) return []
  return (store.results[resultForm.value.condition_id] || []).slice().sort((a, b) => a.timepoint_weeks - b.timepoint_weeks)
})

// ─── Actions ──────────────────────────────────────────────────────────────────

async function createPlan() {
  await store.savePlan(projectId, { ...newPlanForm.value })
  creatingPlan.value = false
  loadPlanIntoForm()
}

function loadPlanIntoForm() {
  if (!store.plan) return
  planForm.value = {
    material_type: store.plan.material_type || 'api',
    intended_storage_condition: store.plan.intended_storage_condition || '25°C/60% RH',
  }
}

async function saveObjectives() {
  await store.savePlan(projectId, { ...planForm.value })
  saveStatus.value = 'saved'
  setTimeout(() => saveStatus.value = '', 2500)
}

function applyPreset(preset) {
  conditionForm.value.condition_label = preset.condition_label
  conditionForm.value.temperature_c = preset.temperature_c
  conditionForm.value.humidity_rh = preset.humidity_rh ?? ''
  conditionForm.value.light_exposure = preset.light_exposure
  conditionForm.value.ich_category = preset.ich_category
}

async function addCondition() {
  await store.addCondition({
    condition_label: conditionForm.value.condition_label,
    temperature_c: parseFloat(conditionForm.value.temperature_c) || null,
    humidity_rh: conditionForm.value.humidity_rh !== '' ? parseFloat(conditionForm.value.humidity_rh) : null,
    light_exposure: conditionForm.value.light_exposure,
  })
  conditionForm.value = { condition_label: '', temperature_c: '', humidity_rh: '', light_exposure: '', ich_category: '', timepoints_months: [], samples_per_timepoint: 3 }
}

async function logResult() {
  const payload = {
    timepoint_weeks: parseFloat(resultForm.value.timepoint_weeks),
    appearance: resultForm.value.appearance,
    assay_pct: parseFloat(resultForm.value.assay_pct) || null,
    degradants_pct: parseFloat(resultForm.value.degradants_pct) || null,
    ph: parseFloat(resultForm.value.ph) || null,
    water_content_pct: parseFloat(resultForm.value.water_content_pct) || null,
    dissolution_pct: parseFloat(resultForm.value.dissolution_pct) || null,
    oos_flag: resultForm.value.oos_flag,
    oot_flag: resultForm.value.oot_flag,
    notes: resultForm.value.notes,
  }
  await store.logResult(resultForm.value.condition_id, payload)
  resultForm.value = { condition_id: resultForm.value.condition_id, timepoint_weeks: '', appearance: '', assay_pct: '', degradants_pct: '', ph: '', water_content_pct: '', dissolution_pct: '', oos_flag: false, oot_flag: false, notes: '' }
}

function conditionLabel(c) {
  return c.condition_label
}

function ichPresetColor(condition) {
  const preset = ICH_PRESETS.find(p => p.condition_label === condition.condition_label)
  return preset?.color || '#6b7280'
}

function assayStatusColor(val) {
  if (val == null) return '#6b7280'
  if (val < 97) return '#dc2626'
  if (val < 98) return '#d97706'
  return '#16a34a'
}

function timepointLabel(weeks) {
  const found = ICH_TIMEPOINTS.find(t => Math.abs(t.weeks - weeks) < 1)
  return found ? found.label : `${weeks}w`
}

const projectIdNum = computed(() => parseInt(projectId))
useAIPageContext({
  pageType: 'StabilityPlanning',
  projectIdRef: projectIdNum,
  getEntity: () => ({ ...newPlanForm.value, ...conditionForm.value }),
  applyFn: (s) => {
    Object.entries(s).forEach(([k, v]) => {
      if (k in newPlanForm.value) newPlanForm.value[k] = v
      if (k in conditionForm.value) conditionForm.value[k] = v
    })
  },
})

onMounted(async () => {
  await store.fetchPlan(projectId)
  loadPlanIntoForm()
})
</script>

<template>
  <div>
    <PageHeader title="Stability Planning">
      <template #actions>
        <button v-if="!store.plan && !creatingPlan" class="btn btn-primary" @click="creatingPlan = true">
          + New Stability Plan
        </button>
        <button v-if="creatingPlan" class="btn btn-secondary" @click="creatingPlan = false">Cancel</button>
      </template>
    </PageHeader>

    <!-- Create Plan Modal -->
    <div v-if="creatingPlan" class="modal-overlay" @click.self="creatingPlan = false">
      <div class="modal-box">
        <h3 class="modal-title">New Stability Plan</h3>
        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label">Material Type</label>
            <select v-model="newPlanForm.material_type" class="form-input">
              <option v-for="m in MATERIAL_TYPES" :key="m.value" :value="m.value">{{ m.label }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Intended Storage Condition</label>
            <select v-model="newPlanForm.intended_storage_condition" class="form-input">
              <option>25°C/60% RH</option>
              <option>30°C/65% RH</option>
              <option>2–8°C (Refrigerated)</option>
              <option>−20°C (Frozen)</option>
              <option>−80°C (Ultra-frozen)</option>
              <option>Room Temperature (uncontrolled)</option>
            </select>
          </div>
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
          <span class="plan-header-label">Material</span>
          <span class="plan-header-value">{{ MATERIAL_TYPES.find(m => m.value === store.plan.material_type)?.label || store.plan.material_type }}</span>
        </div>
        <div class="plan-header-item">
          <span class="plan-header-label">Storage Target</span>
          <span class="plan-header-value">{{ store.plan.intended_storage_condition }}</span>
        </div>
        <div class="plan-header-item">
          <span class="plan-header-label">Conditions</span>
          <span class="plan-header-value">{{ store.conditions.length }}</span>
        </div>
        <div class="plan-header-item">
          <span class="plan-header-label">Results</span>
          <span class="plan-header-value">{{ totalResults }}</span>
        </div>
        <div class="plan-header-item">
          <span class="plan-header-label">OOS</span>
          <span class="plan-header-value" :style="{ color: oosCount > 0 ? '#dc2626' : '#16a34a' }">
            {{ oosCount > 0 ? oosCount + ' flagged' : 'None' }}
          </span>
        </div>
        <div class="plan-header-item">
          <span class="plan-header-label">OOT</span>
          <span class="plan-header-value" :style="{ color: ootCount > 0 ? '#d97706' : '#16a34a' }">
            {{ ootCount > 0 ? ootCount + ' flagged' : 'None' }}
          </span>
        </div>
        <div class="plan-header-item">
          <span class="plan-header-label">Status</span>
          <span class="plan-header-value">{{ store.plan.status }}</span>
        </div>
      </div>

      <!-- Tab navigation -->
      <div class="tab-nav">
        <button class="tab-btn" :class="{ active: activeTab === 'objectives' }" @click="activeTab = 'objectives'">
          Study Objectives
        </button>
        <button class="tab-btn" :class="{ active: activeTab === 'conditions' }" @click="activeTab = 'conditions'">
          Study Matrix
          <span v-if="store.conditions.length" class="tab-badge">{{ store.conditions.length }}</span>
        </button>
        <button class="tab-btn" :class="{ active: activeTab === 'results' }" @click="activeTab = 'results'">
          Results
          <span v-if="oosCount > 0" class="tab-badge" style="background: #dc2626">{{ oosCount }} OOS</span>
          <span v-else-if="totalResults > 0" class="tab-badge">{{ totalResults }}</span>
        </button>
        <button class="tab-btn" :class="{ active: activeTab === 'summary' }" @click="activeTab = 'summary'">
          ICH Summary
        </button>
      </div>

      <!-- ── TAB: Study Objectives ──────────────────────────────────────────── -->
      <div v-if="activeTab === 'objectives'" class="tab-content">
        <div class="section-card">
          <div class="section-header">
            <h3 class="section-title">Stability Study Objectives</h3>
            <div class="section-actions">
              <span v-if="saveStatus === 'saved'" class="save-confirm">✓ Saved</span>
              <button class="btn btn-primary btn-sm" @click="saveObjectives">Save</button>
            </div>
          </div>
          <div class="form-grid-2">
            <div class="form-group">
              <label class="form-label">Material Type</label>
              <select v-model="planForm.material_type" class="form-input">
                <option v-for="m in MATERIAL_TYPES" :key="m.value" :value="m.value">{{ m.label }}</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Intended Storage Condition (Shelf-life Claim)</label>
              <select v-model="planForm.intended_storage_condition" class="form-input">
                <option>25°C/60% RH</option>
                <option>30°C/65% RH</option>
                <option>2–8°C (Refrigerated)</option>
                <option>−20°C (Frozen)</option>
                <option>−80°C (Ultra-frozen)</option>
                <option>Room Temperature (uncontrolled)</option>
              </select>
            </div>
          </div>
        </div>

        <!-- ICH Q1A guidance reference -->
        <div class="section-card" style="margin-top:16px">
          <h3 class="section-title">ICH Q1A(R2) Study Design Reference</h3>
          <table class="sci-table">
            <thead>
              <tr>
                <th>Storage Condition</th>
                <th>Temperature</th>
                <th>Humidity</th>
                <th>Min. Duration</th>
                <th>Minimum Timepoints</th>
                <th>ICH Guideline</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><span class="ich-dot" style="background:#16a34a"></span>Long-term</td>
                <td>25°C ± 2°C</td>
                <td>60% ± 5% RH</td>
                <td>12 months</td>
                <td>0, 3, 6, 9, 12, 18, 24, 36 months</td>
                <td>ICH Q1A(R2)</td>
              </tr>
              <tr>
                <td><span class="ich-dot" style="background:#2563eb"></span>Intermediate</td>
                <td>30°C ± 2°C</td>
                <td>65% ± 5% RH</td>
                <td>6 months</td>
                <td>0, 6, 12 months</td>
                <td>ICH Q1A(R2)</td>
              </tr>
              <tr>
                <td><span class="ich-dot" style="background:#d97706"></span>Accelerated</td>
                <td>40°C ± 2°C</td>
                <td>75% ± 5% RH</td>
                <td>6 months</td>
                <td>0, 1, 2, 3, 6 months</td>
                <td>ICH Q1A(R2)</td>
              </tr>
              <tr>
                <td><span class="ich-dot" style="background:#7c3aed"></span>Refrigerated</td>
                <td>5°C ± 3°C</td>
                <td>Ambient</td>
                <td>12 months</td>
                <td>0, 3, 6, 12 months + accelerated 25°C</td>
                <td>ICH Q1A(R2)</td>
              </tr>
              <tr>
                <td><span class="ich-dot" style="background:#0891b2"></span>Frozen</td>
                <td>−20°C ± 5°C</td>
                <td>N/A</td>
                <td>12 months</td>
                <td>0, 3, 6, 12 months + freeze-thaw</td>
                <td>ICH Q1A(R2)</td>
              </tr>
              <tr>
                <td><span class="ich-dot" style="background:#ea580c"></span>Photostability</td>
                <td>25°C</td>
                <td>60% RH</td>
                <td>—</td>
                <td>Initial + after exposure (1.2M lux·h + 200 W·h/m²)</td>
                <td>ICH Q1B</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="section-card" style="margin-top:16px">
          <h3 class="section-title">Recommended Test Attributes</h3>
          <div class="info-grid-2">
            <div class="info-card">
              <div class="info-card-title">Drug Substance (API) Attributes</div>
              <ul class="attr-list">
                <li>Appearance / color / clarity</li>
                <li>Assay (HPLC) — NLT 98.0%</li>
                <li>Known degradation products (ICH limits: 0.10%/0.05%)</li>
                <li>Unknown impurities (NMT 0.10%)</li>
                <li>Residual solvents (ICH Q3C)</li>
                <li>Water content (Karl Fischer)</li>
                <li>Polymorphic form (XRPD if applicable)</li>
                <li>Particle size (if relevant to bioavailability)</li>
              </ul>
            </div>
            <div class="info-card">
              <div class="info-card-title">Drug Product Attributes</div>
              <ul class="attr-list">
                <li>Appearance</li>
                <li>Assay (HPLC)</li>
                <li>Dissolution (USP Apparatus I/II)</li>
                <li>Degradation products</li>
                <li>pH (solutions)</li>
                <li>Water content / LOD</li>
                <li>Microbiological quality</li>
                <li>Container closure integrity</li>
                <li>Hardness / friability (tablets)</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- ── TAB: Study Matrix ───────────────────────────────────────────────── -->
      <div v-if="activeTab === 'conditions'" class="tab-content">
        <!-- ICH preset buttons -->
        <div class="section-card">
          <h3 class="section-title">ICH Q1A(R2) Condition Presets</h3>
          <div class="ich-presets">
            <button
              v-for="preset in ICH_PRESETS"
              :key="preset.label"
              class="ich-preset-btn"
              :style="{ borderColor: preset.color, '--ich-color': preset.color }"
              @click="applyPreset(preset)"
            >
              <span class="ich-preset-label" :style="{ color: preset.color }">{{ preset.label }}</span>
              <span class="ich-preset-cond">{{ preset.temperature_c }}°C{{ preset.humidity_rh ? ' / ' + preset.humidity_rh + '% RH' : '' }}</span>
              <span class="ich-preset-guide">{{ preset.guidance }}</span>
            </button>
          </div>
        </div>

        <!-- Add condition form -->
        <div class="section-card" style="margin-top:16px">
          <h3 class="section-title">Add Stability Condition</h3>
          <div class="form-grid-3">
            <div class="form-group" style="grid-column: span 2">
              <label class="form-label">Condition Label</label>
              <input v-model="conditionForm.condition_label" class="form-input" placeholder="e.g. Accelerated 40°C/75% RH" />
            </div>
            <div class="form-group">
              <label class="form-label">Temperature (°C)</label>
              <input v-model="conditionForm.temperature_c" type="number" class="form-input" placeholder="40" />
            </div>
            <div class="form-group">
              <label class="form-label">Relative Humidity (%)</label>
              <input v-model="conditionForm.humidity_rh" type="number" class="form-input" placeholder="75" />
            </div>
            <div class="form-group" style="grid-column: span 2">
              <label class="form-label">Light Exposure</label>
              <input v-model="conditionForm.light_exposure" class="form-input" placeholder="Protected from light / ICH Q1B / Dark" />
            </div>
          </div>
          <button class="btn btn-primary btn-sm" :disabled="!conditionForm.condition_label" @click="addCondition">
            Add Condition
          </button>
        </div>

        <!-- Conditions list / matrix -->
        <div class="section-card" style="margin-top:16px">
          <h3 class="section-title">Study Matrix ({{ store.conditions.length }} conditions)</h3>
          <div v-if="store.conditions.length">
            <table class="sci-table">
              <thead>
                <tr>
                  <th>Condition</th>
                  <th>Temp (°C)</th>
                  <th>RH (%)</th>
                  <th>Light</th>
                  <th>Results Logged</th>
                  <th>OOS / OOT</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="c in store.conditions" :key="c.id">
                  <td>
                    <span class="ich-dot-inline" :style="{ background: ichPresetColor(c) }"></span>
                    <strong>{{ c.condition_label }}</strong>
                  </td>
                  <td class="td-num">{{ c.temperature_c ?? '—' }}</td>
                  <td class="td-num">{{ c.humidity_rh ?? '—' }}</td>
                  <td class="text-muted">{{ c.light_exposure || '—' }}</td>
                  <td class="td-num">{{ (store.results[c.id] || []).length }}</td>
                  <td>
                    <span v-if="(store.results[c.id] || []).some(r => r.oos_flag)" class="flag-oos">OOS</span>
                    <span v-else-if="(store.results[c.id] || []).some(r => r.oot_flag)" class="flag-oot">OOT</span>
                    <span v-else class="text-muted" style="font-size:12px">—</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="empty-note">No conditions added. Use presets above or add manually.</div>
        </div>

        <!-- ICH recommended timepoints reference -->
        <div class="section-card" style="margin-top:16px">
          <h3 class="section-title">ICH Recommended Timepoints</h3>
          <div class="timepoints-grid">
            <div v-for="tp in ICH_TIMEPOINTS" :key="tp.months" class="timepoint-chip">
              <span class="timepoint-label">{{ tp.label }}</span>
              <span class="timepoint-weeks text-muted">{{ tp.weeks }}w</span>
            </div>
          </div>
        </div>
      </div>

      <!-- ── TAB: Results ───────────────────────────────────────────────────── -->
      <div v-if="activeTab === 'results'" class="tab-content">
        <div v-if="oosCount > 0" class="alert-banner alert-danger">
          {{ oosCount }} Out-of-Specification (OOS) result(s) detected — investigation required per ICH Q10.
        </div>
        <div v-if="ootCount > 0" class="alert-banner alert-warning">
          {{ ootCount }} Out-of-Trend (OOT) result(s) flagged — evaluate trend against acceptance criteria.
        </div>

        <!-- Log result form -->
        <div class="section-card">
          <h3 class="section-title">Log Stability Result</h3>
          <div class="form-grid-3">
            <div class="form-group" style="grid-column: span 2">
              <label class="form-label">Condition</label>
              <select v-model="resultForm.condition_id" class="form-input">
                <option value="">— select condition —</option>
                <option v-for="c in store.conditions" :key="c.id" :value="c.id">{{ c.condition_label }}</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Timepoint (weeks)</label>
              <select v-model="resultForm.timepoint_weeks" class="form-input">
                <option value="">— select —</option>
                <option v-for="tp in ICH_TIMEPOINTS" :key="tp.weeks" :value="tp.weeks">{{ tp.label }} ({{ tp.weeks }}w)</option>
              </select>
            </div>
          </div>
          <div class="form-grid-4" style="margin-top:10px">
            <div class="form-group">
              <label class="form-label">Assay (%)</label>
              <input v-model="resultForm.assay_pct" type="number" step="0.01" class="form-input" placeholder="99.5" />
              <span class="form-hint">Spec: NLT 97.0%</span>
            </div>
            <div class="form-group">
              <label class="form-label">Total Degradants (%)</label>
              <input v-model="resultForm.degradants_pct" type="number" step="0.01" class="form-input" placeholder="0.25" />
              <span class="form-hint">Spec: NMT 2.0%</span>
            </div>
            <div class="form-group">
              <label class="form-label">pH</label>
              <input v-model="resultForm.ph" type="number" step="0.01" class="form-input" placeholder="4.5" />
            </div>
            <div class="form-group">
              <label class="form-label">Water Content (%)</label>
              <input v-model="resultForm.water_content_pct" type="number" step="0.01" class="form-input" placeholder="0.3" />
            </div>
            <div class="form-group">
              <label class="form-label">Dissolution (%)</label>
              <input v-model="resultForm.dissolution_pct" type="number" step="0.1" class="form-input" placeholder="98.5" />
              <span class="form-hint">Spec: NLT Q=80% at 30 min (typical)</span>
            </div>
            <div class="form-group" style="grid-column: span 3">
              <label class="form-label">Appearance</label>
              <input v-model="resultForm.appearance" class="form-input" placeholder="e.g. White to off-white powder, no change observed" />
            </div>
          </div>
          <div class="form-grid-2" style="margin-top:10px">
            <div class="form-group">
              <label class="form-label">Notes</label>
              <textarea v-model="resultForm.notes" class="form-input" rows="2" placeholder="Any observations, deviations, or comments" />
            </div>
            <div style="display:flex;flex-direction:column;gap:10px;padding-top:4px">
              <label class="flag-checkbox" :class="{ 'flag-oos-active': resultForm.oos_flag }">
                <input type="checkbox" v-model="resultForm.oos_flag" />
                <span>Flag as OOS (Out-of-Specification) — initiates investigation</span>
              </label>
              <label class="flag-checkbox" :class="{ 'flag-oot-active': resultForm.oot_flag }">
                <input type="checkbox" v-model="resultForm.oot_flag" />
                <span>Flag as OOT (Out-of-Trend) — trending towards limit</span>
              </label>
            </div>
          </div>
          <div style="margin-top:12px">
            <button
              class="btn btn-primary btn-sm"
              :disabled="!resultForm.condition_id || !resultForm.timepoint_weeks"
              @click="logResult"
            >
              Log Result
            </button>
          </div>
        </div>

        <!-- Results table for selected condition -->
        <div class="section-card" style="margin-top:16px" v-if="resultForm.condition_id">
          <h3 class="section-title">
            Results — {{ store.conditions.find(c => c.id == resultForm.condition_id)?.condition_label }}
          </h3>
          <table v-if="selectedConditionResults.length" class="sci-table">
            <thead>
              <tr>
                <th>Timepoint</th>
                <th>Assay (%)</th>
                <th>Degradants (%)</th>
                <th>pH</th>
                <th>H₂O (%)</th>
                <th>Dissolution (%)</th>
                <th>Appearance</th>
                <th>Flags</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in selectedConditionResults" :key="r.id" :class="{ 'row-oos': r.oos_flag, 'row-oot': r.oot_flag && !r.oos_flag }">
                <td class="td-name">{{ timepointLabel(r.timepoint_weeks) }}</td>
                <td class="td-num" :style="{ color: assayStatusColor(r.assay_pct) }">
                  {{ r.assay_pct != null ? r.assay_pct.toFixed(1) + '%' : '—' }}
                </td>
                <td class="td-num" :style="{ color: r.degradants_pct != null && r.degradants_pct > 1.0 ? '#dc2626' : '#374151' }">
                  {{ r.degradants_pct != null ? r.degradants_pct.toFixed(2) + '%' : '—' }}
                </td>
                <td class="td-num">{{ r.ph != null ? r.ph.toFixed(2) : '—' }}</td>
                <td class="td-num">{{ r.water_content_pct != null ? r.water_content_pct.toFixed(2) + '%' : '—' }}</td>
                <td class="td-num" :style="{ color: r.dissolution_pct != null && r.dissolution_pct < 80 ? '#dc2626' : '#374151' }">
                  {{ r.dissolution_pct != null ? r.dissolution_pct.toFixed(1) + '%' : '—' }}
                </td>
                <td class="text-muted td-notes">{{ r.appearance || '—' }}</td>
                <td>
                  <span v-if="r.oos_flag" class="flag-oos">OOS</span>
                  <span v-else-if="r.oot_flag" class="flag-oot">OOT</span>
                  <span v-else class="text-muted" style="font-size:11px">—</span>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-else class="empty-note">No results logged for this condition yet.</div>
        </div>

        <!-- All conditions summary when no condition selected -->
        <div class="section-card" style="margin-top:16px" v-if="totalResults > 0 && !resultForm.condition_id">
          <h3 class="section-title">All Results Overview</h3>
          <table class="sci-table">
            <thead>
              <tr><th>Condition</th><th>Results</th><th>Last Timepoint</th><th>Min Assay (%)</th><th>Max Degradants (%)</th><th>Flags</th></tr>
            </thead>
            <tbody>
              <tr v-for="c in store.conditions" :key="c.id">
                <td class="td-name">{{ c.condition_label }}</td>
                <td class="td-num">{{ (store.results[c.id] || []).length }}</td>
                <td>
                  <span v-if="(store.results[c.id] || []).length">
                    {{ timepointLabel(Math.max(...(store.results[c.id] || []).map(r => r.timepoint_weeks))) }}
                  </span>
                  <span v-else class="text-muted">—</span>
                </td>
                <td class="td-num">
                  <span v-if="(store.results[c.id] || []).some(r => r.assay_pct != null)"
                    :style="{ color: assayStatusColor(Math.min(...(store.results[c.id] || []).filter(r => r.assay_pct != null).map(r => r.assay_pct))) }">
                    {{ Math.min(...(store.results[c.id] || []).filter(r => r.assay_pct != null).map(r => r.assay_pct)).toFixed(1) }}%
                  </span>
                  <span v-else class="text-muted">—</span>
                </td>
                <td class="td-num">
                  <span v-if="(store.results[c.id] || []).some(r => r.degradants_pct != null)">
                    {{ Math.max(...(store.results[c.id] || []).filter(r => r.degradants_pct != null).map(r => r.degradants_pct)).toFixed(2) }}%
                  </span>
                  <span v-else class="text-muted">—</span>
                </td>
                <td>
                  <span v-if="(store.results[c.id] || []).some(r => r.oos_flag)" class="flag-oos">OOS</span>
                  <span v-else-if="(store.results[c.id] || []).some(r => r.oot_flag)" class="flag-oot">OOT</span>
                  <span v-else class="text-muted" style="font-size:11px">—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ── TAB: ICH Summary ───────────────────────────────────────────────── -->
      <div v-if="activeTab === 'summary'" class="tab-content">
        <div class="section-card">
          <h3 class="section-title">Stability Plan Summary</h3>
          <div class="summary-grid">
            <div>
              <p class="text-muted" style="font-size:12px;margin-bottom:4px">Material</p>
              <p class="summary-val">{{ MATERIAL_TYPES.find(m => m.value === store.plan.material_type)?.label }}</p>
            </div>
            <div>
              <p class="text-muted" style="font-size:12px;margin-bottom:4px">Storage Claim</p>
              <p class="summary-val">{{ store.plan.intended_storage_condition }}</p>
            </div>
            <div>
              <p class="text-muted" style="font-size:12px;margin-bottom:4px">Study Status</p>
              <p class="summary-val">{{ store.plan.status }}</p>
            </div>
            <div>
              <p class="text-muted" style="font-size:12px;margin-bottom:4px">Conditions</p>
              <p class="summary-val">{{ store.conditions.length }}</p>
            </div>
            <div>
              <p class="text-muted" style="font-size:12px;margin-bottom:4px">Total Results</p>
              <p class="summary-val">{{ totalResults }}</p>
            </div>
            <div>
              <p class="text-muted" style="font-size:12px;margin-bottom:4px">OOS / OOT</p>
              <p class="summary-val">
                <span v-if="oosCount" class="flag-oos">{{ oosCount }} OOS</span>
                <span v-if="ootCount" class="flag-oot" style="margin-left:6px">{{ ootCount }} OOT</span>
                <span v-if="!oosCount && !ootCount" style="color:#16a34a">None</span>
              </p>
            </div>
          </div>
        </div>

        <!-- Conditions status grid -->
        <div class="section-card" style="margin-top:16px" v-if="store.conditions.length">
          <h3 class="section-title">Conditions Status</h3>
          <div class="conditions-grid">
            <div v-for="c in store.conditions" :key="c.id" class="condition-card">
              <div class="condition-card-header" :style="{ borderLeftColor: ichPresetColor(c) }">
                <strong>{{ c.condition_label }}</strong>
              </div>
              <div class="condition-card-body">
                <div class="condition-stat">
                  <span class="text-muted">Temp</span>
                  <span>{{ c.temperature_c != null ? c.temperature_c + '°C' : '—' }}</span>
                </div>
                <div class="condition-stat">
                  <span class="text-muted">RH</span>
                  <span>{{ c.humidity_rh != null ? c.humidity_rh + '%' : '—' }}</span>
                </div>
                <div class="condition-stat">
                  <span class="text-muted">Results</span>
                  <span>{{ (store.results[c.id] || []).length }}</span>
                </div>
                <div class="condition-stat">
                  <span class="text-muted">Status</span>
                  <span v-if="(store.results[c.id] || []).some(r => r.oos_flag)" class="flag-oos">OOS</span>
                  <span v-else-if="(store.results[c.id] || []).some(r => r.oot_flag)" class="flag-oot">OOT</span>
                  <span v-else style="color:#16a34a;font-size:12px">OK</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ICH compliance checklist -->
        <div class="section-card" style="margin-top:16px">
          <h3 class="section-title">ICH Q1A(R2) Compliance Checklist</h3>
          <table class="sci-table">
            <thead><tr><th>Requirement</th><th>Status</th><th>Notes</th></tr></thead>
            <tbody>
              <tr>
                <td>Long-term condition (25°C/60% RH) defined</td>
                <td>
                  <span v-if="store.conditions.some(c => c.temperature_c === 25)" class="check-pass">✓ Done</span>
                  <span v-else class="check-fail">✗ Missing</span>
                </td>
                <td class="text-muted td-notes">Required for all NDA/MAA submissions</td>
              </tr>
              <tr>
                <td>Accelerated condition (40°C/75% RH) defined</td>
                <td>
                  <span v-if="store.conditions.some(c => c.temperature_c === 40)" class="check-pass">✓ Done</span>
                  <span v-else class="check-fail">✗ Missing</span>
                </td>
                <td class="text-muted td-notes">Required; failure triggers intermediate study</td>
              </tr>
              <tr>
                <td>Photostability assessment (ICH Q1B)</td>
                <td>
                  <span v-if="store.conditions.some(c => c.light_exposure && c.light_exposure.includes('lux'))" class="check-pass">✓ Done</span>
                  <span v-else class="check-pending">○ Pending</span>
                </td>
                <td class="text-muted td-notes">Required unless product is inherently light-protected</td>
              </tr>
              <tr>
                <td>OOS investigation documented</td>
                <td>
                  <span v-if="oosCount === 0" class="check-pass">✓ No OOS</span>
                  <span v-else class="check-fail">✗ {{ oosCount }} OOS — investigate</span>
                </td>
                <td class="text-muted td-notes">ICH Q10 requires formal OOS investigation</td>
              </tr>
              <tr>
                <td>Results available at ≥12 months</td>
                <td>
                  <span v-if="Object.values(store.results).flat().some(r => r.timepoint_weeks >= 52)" class="check-pass">✓ Done</span>
                  <span v-else class="check-pending">○ Pending</span>
                </td>
                <td class="text-muted td-notes">Minimum for NDA/MAA filing</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div v-else-if="!creatingPlan" class="empty-state-page">
      <div class="empty-state-icon">🧪</div>
      <h3>No Stability Plan</h3>
      <p class="text-muted">Create a stability plan to define ICH study conditions, log timepoint results, and track OOS/OOT flags per ICH Q1A(R2).</p>
      <button class="btn btn-primary" @click="creatingPlan = true">+ New Stability Plan</button>
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
.sci-table tbody tr.row-oos { background: #fff1f2; }
.sci-table tbody tr.row-oos:hover { background: #fee2e2; }
.sci-table tbody tr.row-oot { background: #fffbeb; }
.sci-table tbody tr.row-oot:hover { background: #fef3c7; }
.td-name { font-weight: 500; }
.td-num { font-variant-numeric: tabular-nums; text-align: right; }
.td-notes { font-size: 12px; max-width: 220px; }
.text-muted { color: #6b7280; }
.empty-note { padding: 24px; text-align: center; color: #9ca3af; font-size: 13px; }

/* ── ICH presets ─────────────────────────────────────────────── */
.ich-presets { display: flex; flex-wrap: wrap; gap: 10px; }
.ich-preset-btn {
  flex: 1;
  min-width: 180px;
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 12px 14px;
  border: 1.5px solid;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  transition: background .15s;
  text-align: left;
}
.ich-preset-btn:hover { background: #f9fafb; }
.ich-preset-label { font-size: 13px; font-weight: 600; }
.ich-preset-cond { font-size: 12px; color: #374151; font-weight: 500; }
.ich-preset-guide { font-size: 11px; color: #9ca3af; line-height: 1.4; }
.ich-dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; vertical-align: middle; }
.ich-dot-inline { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; vertical-align: middle; }

/* ── Timepoints ──────────────────────────────────────────────── */
.timepoints-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.timepoint-chip {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  min-width: 72px;
}
.timepoint-label { font-size: 12px; font-weight: 600; color: #1e40af; }
.timepoint-weeks { font-size: 11px; }

/* ── Flags ───────────────────────────────────────────────────── */
.flag-oos {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  background: #fee2e2;
  color: #dc2626;
  font-size: 11px;
  font-weight: 700;
  border: 1px solid #fca5a5;
}
.flag-oot {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  background: #fef3c7;
  color: #d97706;
  font-size: 11px;
  font-weight: 700;
  border: 1px solid #fcd34d;
}

/* ── Flag checkboxes ─────────────────────────────────────────── */
.flag-checkbox {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  cursor: pointer;
  color: #374151;
  padding: 8px 10px;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  transition: background .15s;
}
.flag-checkbox input { margin-top: 2px; flex-shrink: 0; }
.flag-oos-active { background: #fff1f2; border-color: #fca5a5; color: #dc2626; }
.flag-oot-active { background: #fffbeb; border-color: #fcd34d; color: #d97706; }

/* ── Compliance checks ───────────────────────────────────────── */
.check-pass { color: #16a34a; font-size: 12px; font-weight: 600; }
.check-fail { color: #dc2626; font-size: 12px; font-weight: 600; }
.check-pending { color: #9ca3af; font-size: 12px; font-weight: 600; }

/* ── Conditions summary grid ─────────────────────────────────── */
.conditions-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.condition-card { border: 1px solid #e5e7eb; border-radius: 6px; overflow: hidden; }
.condition-card-header { padding: 10px 12px; background: #f9fafb; border-left: 4px solid; font-size: 13px; }
.condition-card-body { padding: 10px 12px; display: flex; flex-direction: column; gap: 6px; }
.condition-stat { display: flex; justify-content: space-between; font-size: 12px; }
.condition-stat .text-muted { font-size: 12px; }

/* ── Alert banners ───────────────────────────────────────────── */
.alert-banner {
  padding: 10px 16px;
  border-radius: 6px;
  margin-bottom: 12px;
  font-size: 13px;
  font-weight: 500;
}
.alert-danger { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }
.alert-warning { background: #fef3c7; color: #92400e; border: 1px solid #fcd34d; }

/* ── Forms ───────────────────────────────────────────────────── */
.form-grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.form-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.form-grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.form-group { display: flex; flex-direction: column; gap: 4px; }
.form-label { font-size: 12px; font-weight: 500; color: #374151; }
.form-hint { font-size: 11px; color: #9ca3af; }
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

/* ── Info grid ───────────────────────────────────────────────── */
.info-grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.info-card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 14px; }
.info-card-title { font-size: 12px; font-weight: 600; color: #1e40af; margin-bottom: 8px; }
.attr-list { margin: 0; padding-left: 18px; font-size: 12px; color: #64748b; line-height: 1.8; }

/* ── Summary grid ────────────────────────────────────────────── */
.summary-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 8px; }
.summary-val { font-size: 15px; font-weight: 600; color: #111827; }

/* ── Modal ───────────────────────────────────────────────────── */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.45);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.modal-box {
  background: #fff; border-radius: 10px; padding: 28px;
  width: 520px; max-width: calc(100vw - 48px); box-shadow: 0 20px 60px rgba(0,0,0,.2);
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
.btn:disabled { opacity: .5; cursor: not-allowed; }
</style>
