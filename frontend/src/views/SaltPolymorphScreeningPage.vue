<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '@/components/layout/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { saltScreening } from '@/services/api'
import { useAIPageContext } from '@/composables/useAIPageContext'

const route = useRoute()
const projectId = route.params.id

// ── State ─────────────────────────────────────────────────────────────────────
const screens = ref([])
const currentScreen = ref(null)
const candidates = ref([])
const experiments = ref([])
const loading = ref(false)
const saving = ref(false)
const setupSaved = ref(false)

const showNewScreenForm = ref(false)
const showCandidateForm = ref(false)
const showExperimentForm = ref(false)
const activeSection = ref('setup')   // setup | candidates | experiments | results

// New screen creation form (separate from setup editing form)
const newScreenForm = ref({ screen_type: 'salt', objective: '' })

// Setup editing form (populated from currentScreen when selected)
const screenForm = ref({
  screen_type: 'salt',
  objective: '',
  baseline_pka: '',
  baseline_melting_point_c: '',
  baseline_hygroscopicity: '',
  baseline_solubility_mgml: '',
  baseline_logp: '',
  baseline_notes: '',
})

// Candidate form
const candidateForm = ref({
  name: '',
  cas_number: '',
  counterion_type: '',
  pka_delta: '',
  theoretical_solubility_impact: 'unknown',
  notes: '',
})

// Experiment form
const experimentForm = ref({
  candidate: '',
  prep_method: 'slurry',
  solvent: '',
  ratio: '',
  temperature_c: '',
  results_xrpd: '',
  results_dsc: '',
  results_tga: '',
  results_solubility: '',
  results_appearance: '',
  observed_form: '',
  notes: '',
})

// Form selection
const selectionForm = ref({ selected_form: '', selection_rationale: '' })

// ── Common counterion presets ─────────────────────────────────────────────────
const COMMON_COUNTERIONS = [
  { name: 'Hydrochloride (HCl)', cas: '7647-01-0', type: 'acid', pka: -7 },
  { name: 'Hydrobromide (HBr)', cas: '10035-10-6', type: 'acid', pka: -9 },
  { name: 'Sulfate', cas: '7664-93-9', type: 'acid', pka: -3 },
  { name: 'Phosphate', cas: '7664-38-2', type: 'acid', pka: 2.1 },
  { name: 'Maleate', cas: '110-16-7', type: 'acid', pka: 1.9 },
  { name: 'Tartrate', cas: '526-83-0', type: 'acid', pka: 2.9 },
  { name: 'Citrate', cas: '77-92-9', type: 'acid', pka: 3.1 },
  { name: 'Mesylate', cas: '75-75-2', type: 'acid', pka: -2 },
  { name: 'Tosylate', cas: '104-15-4', type: 'acid', pka: -1.3 },
  { name: 'Fumarate', cas: '110-17-8', type: 'acid', pka: 3.0 },
  { name: 'Succinate', cas: '110-15-6', type: 'acid', pka: 4.2 },
  { name: 'Acetate', cas: '64-19-7', type: 'acid', pka: 4.8 },
  { name: 'Oxalate', cas: '144-62-7', type: 'acid', pka: 1.3 },
  { name: 'Besylate', cas: '98-11-3', type: 'acid', pka: -2.5 },
  { name: 'Esylate', cas: '594-45-6', type: 'acid', pka: -1.6 },
  { name: 'Sodium (Na⁺)', cas: '7440-23-5', type: 'base', pka: null },
  { name: 'Potassium (K⁺)', cas: '7440-09-7', type: 'base', pka: null },
  { name: 'Calcium (Ca²⁺)', cas: '7440-70-2', type: 'base', pka: null },
  { name: 'Magnesium (Mg²⁺)', cas: '7439-95-4', type: 'base', pka: null },
]
const POLYMORPH_FORMS = [
  { name: 'Form I', type: 'polymorph' },
  { name: 'Form II', type: 'polymorph' },
  { name: 'Form III', type: 'polymorph' },
  { name: 'Amorphous', type: 'polymorph' },
  { name: 'Hydrate (Monohydrate)', type: 'polymorph' },
  { name: 'Hydrate (Dihydrate)', type: 'polymorph' },
  { name: 'Solvate (EtOH)', type: 'polymorph' },
]

// ── Computed ──────────────────────────────────────────────────────────────────
const candidateMap = computed(() => {
  const m = {}
  candidates.value.forEach(c => { m[c.id] = c })
  return m
})

const experimentsByCandidateId = computed(() => {
  const m = {}
  experiments.value.forEach(e => {
    const cid = e.candidate ?? 'none'
    if (!m[cid]) m[cid] = []
    m[cid].push(e)
  })
  return m
})

const selectedCandidate = computed(() => candidates.value.find(c => c.selected) || null)

const screenLabel = computed(() => {
  const counts = {}
  const labels = {}
  for (const s of [...screens.value].reverse()) {
    counts[s.screen_type] = (counts[s.screen_type] || 0) + 1
    labels[s.id] = counts[s.screen_type]
  }
  const typeLabel = { salt: 'Salt Screen', polymorph: 'Polymorph Screen', cocrystal: 'Co-Crystal Screen' }
  const result = {}
  for (const s of screens.value) {
    const hasDups = screens.value.filter(x => x.screen_type === s.screen_type).length > 1
    result[s.id] = hasDups ? `${typeLabel[s.screen_type] || s.screen_type} ${labels[s.id]}` : (typeLabel[s.screen_type] || s.screen_type)
  }
  return result
})

// ── Helpers ───────────────────────────────────────────────────────────────────
const FORM_COLORS = {
  crystalline: '#16a34a',
  amorphous: '#d97706',
  unchanged: '#6b7280',
  mixed: '#7c3aed',
  oily: '#dc2626',
}
const formBadgeStyle = (form) => ({
  background: FORM_COLORS[form] || '#6b7280',
  color: '#fff',
  fontSize: '11px',
  padding: '2px 7px',
  borderRadius: '4px',
  whiteSpace: 'nowrap',
})

// ── API actions ───────────────────────────────────────────────────────────────
async function load() {
  loading.value = true
  try {
    screens.value = await saltScreening.list(projectId)
    if (screens.value.length) await selectScreen(screens.value[0])
  } finally {
    loading.value = false
  }
}

async function selectScreen(screen) {
  currentScreen.value = screen
  loadScreenIntoForm(screen)
  selectionForm.value = {
    selected_form: screen.selected_form || '',
    selection_rationale: screen.selection_rationale || '',
  }
  const [cands, exps] = await Promise.all([
    saltScreening.candidates(screen.id),
    saltScreening.experiments(screen.id),
  ])
  candidates.value = cands
  experiments.value = exps
}

async function removeScreen(screen) {
  if (!confirm(`Delete "${screenLabel[screen.id]}"? This will also delete all its candidates and experiments.`)) return
  await saltScreening.delete(screen.id)
  screens.value = screens.value.filter(s => s.id !== screen.id)
  if (currentScreen.value?.id === screen.id) {
    if (screens.value.length) {
      await selectScreen(screens.value[0])
    } else {
      currentScreen.value = null
      candidates.value = []
      experiments.value = []
    }
  }
}

async function createScreen() {
  saving.value = true
  try {
    const screen = await saltScreening.create(projectId, { ...newScreenForm.value })
    screens.value.unshift(screen)
    await selectScreen(screen)
    showNewScreenForm.value = false
    newScreenForm.value = { screen_type: 'salt', objective: '' }
  } finally {
    saving.value = false
  }
}

async function saveSetup() {
  if (!currentScreen.value) return
  saving.value = true
  setupSaved.value = false
  try {
    const payload = { ...screenForm.value }
    ;['baseline_pka', 'baseline_melting_point_c', 'baseline_solubility_mgml', 'baseline_logp'].forEach(k => {
      payload[k] = payload[k] !== '' && payload[k] !== null ? parseFloat(payload[k]) : null
    })
    const updated = await saltScreening.update(currentScreen.value.id, payload)
    currentScreen.value = updated
    screens.value = screens.value.map(s => s.id === updated.id ? updated : s)
    setupSaved.value = true
    setTimeout(() => { setupSaved.value = false }, 3000)
  } finally {
    saving.value = false
  }
}

async function addPresetCandidate(preset) {
  if (!currentScreen.value) return
  const c = await saltScreening.addCandidate(currentScreen.value.id, {
    name: preset.name,
    cas_number: preset.cas || '',
    counterion_type: preset.type || '',
    pka_delta: preset.pka ?? null,
    theoretical_solubility_impact: 'unknown',
  })
  candidates.value.push(c)
}

async function addCandidate() {
  if (!currentScreen.value || !candidateForm.value.name.trim()) return
  saving.value = true
  try {
    const payload = { ...candidateForm.value }
    payload.pka_delta = payload.pka_delta !== '' ? parseFloat(payload.pka_delta) : null
    const c = await saltScreening.addCandidate(currentScreen.value.id, payload)
    candidates.value.push(c)
    candidateForm.value = { name: '', cas_number: '', counterion_type: '', pka_delta: '', theoretical_solubility_impact: 'unknown', notes: '' }
    showCandidateForm.value = false
  } finally {
    saving.value = false
  }
}

async function removeCandidate(id) {
  await saltScreening.deleteCandidate(id)
  candidates.value = candidates.value.filter(c => c.id !== id)
  experiments.value = experiments.value.filter(e => e.candidate !== id)
}

async function addExperiment() {
  if (!currentScreen.value || !experimentForm.value.candidate) return
  saving.value = true
  try {
    const payload = { ...experimentForm.value }
    payload.temperature_c = payload.temperature_c !== '' ? parseFloat(payload.temperature_c) : null
    payload.candidate = parseInt(payload.candidate)
    const exp = await saltScreening.addExperiment(currentScreen.value.id, payload)
    experiments.value.push(exp)
    experimentForm.value = { candidate: '', prep_method: 'slurry', solvent: '', ratio: '', temperature_c: '', results_xrpd: '', results_dsc: '', results_tga: '', results_solubility: '', results_appearance: '', observed_form: '', notes: '' }
    showExperimentForm.value = false
  } finally {
    saving.value = false
  }
}

async function removeExperiment(id) {
  await saltScreening.deleteExperiment(id)
  experiments.value = experiments.value.filter(e => e.id !== id)
}

async function selectForm() {
  if (!currentScreen.value || !selectionForm.value.selected_form.trim()) return
  saving.value = true
  try {
    const updated = await saltScreening.update(currentScreen.value.id, {
      ...selectionForm.value,
      status: 'complete',
    })
    currentScreen.value = updated
    screens.value = screens.value.map(s => s.id === updated.id ? updated : s)
  } finally {
    saving.value = false
  }
}

async function markCandidateSelected(candidate) {
  // deselect all others first, then toggle this one
  const newVal = !candidate.selected
  await Promise.all(candidates.value.filter(c => c.selected && c.id !== candidate.id).map(c => saltScreening.updateCandidate(c.id, { selected: false })))
  const updated = await saltScreening.updateCandidate(candidate.id, { selected: newVal })
  candidates.value = candidates.value.map(c => c.id === updated.id ? updated : { ...c, selected: false })
  if (newVal) {
    selectionForm.value.selected_form = candidate.name
  }
}

function loadScreenIntoForm(screen) {
  screenForm.value = {
    screen_type: screen.screen_type || 'salt',
    objective: screen.objective || '',
    baseline_pka: screen.baseline_pka ?? '',
    baseline_melting_point_c: screen.baseline_melting_point_c ?? '',
    baseline_hygroscopicity: screen.baseline_hygroscopicity || '',
    baseline_solubility_mgml: screen.baseline_solubility_mgml ?? '',
    baseline_logp: screen.baseline_logp ?? '',
    baseline_notes: screen.baseline_notes || '',
  }
}

const projectIdNum = computed(() => parseInt(projectId))
useAIPageContext({
  pageType: 'SaltPolymorphScreening',
  projectIdRef: projectIdNum,
  getEntity: () => ({ ...newScreenForm.value, ...screenForm.value }),
  applyFn: (s) => {
    Object.entries(s).forEach(([k, v]) => {
      if (k in screenForm.value) screenForm.value[k] = v
      else if (k in newScreenForm.value) newScreenForm.value[k] = v
    })
  },
})

onMounted(load)
</script>

<template>
  <div style="max-width:1000px">
    <PageHeader title="Salt & Polymorph Screening">
      <template #actions>
        <RouterLink :to="`/projects/${projectId}/synthesis`" class="btn btn-secondary">← Synthesis Hub</RouterLink>
        <button class="btn btn-primary" @click="showNewScreenForm = !showNewScreenForm">
          {{ showNewScreenForm ? 'Cancel' : '+ New Screen' }}
        </button>
      </template>
    </PageHeader>

    <p class="text-muted text-sm mb-4">
      Identifies the optimal solid form of the API — the salt, polymorph, or co-crystal that delivers the best combination of solubility, stability, and manufacturability for development.
    </p>

    <!-- New screen form -->
    <div v-if="showNewScreenForm" class="card mb-4">
      <div class="card-title">New Screening Campaign</div>
      <div class="grid-2" style="gap:12px;margin-bottom:12px">
        <div class="form-group" style="margin:0">
          <label class="form-label">Screen Type</label>
          <select v-model="newScreenForm.screen_type" class="form-control">
            <option value="salt">Salt Screen</option>
            <option value="polymorph">Polymorph Screen</option>
            <option value="cocrystal">Co-Crystal Screen</option>
          </select>
        </div>
        <div class="form-group" style="margin:0">
          <label class="form-label">Screening Objective</label>
          <input v-model="newScreenForm.objective" class="form-control" placeholder="e.g. Improve aqueous solubility for oral bioavailability" />
        </div>
      </div>
      <button class="btn btn-primary" :disabled="saving" @click="createScreen">
        {{ saving ? 'Creating…' : 'Create Screen' }}
      </button>
    </div>

    <!-- Loading -->
    <LoadingSpinner v-if="loading" />

    <template v-else>
      <!-- No screens yet -->
      <EmptyState
        v-if="!screens.length && !showNewScreenForm"
        title="No screening campaigns"
        message="Start by clicking '+ New Screen' to plan a salt, polymorph, or co-crystal screening campaign for your API."
      />

      <template v-else>
        <!-- Screen list — always visible -->
        <div class="card mb-4">
          <div class="flex items-center justify-between mb-3">
            <div class="card-title" style="margin-bottom:0">Screening Campaigns</div>
            <span class="text-muted text-sm">{{ screens.length }} campaign{{ screens.length !== 1 ? 's' : '' }}</span>
          </div>
          <div style="display:flex;flex-direction:column;gap:6px">
            <div
              v-for="s in screens" :key="s.id"
              style="display:flex;align-items:center;gap:12px;padding:10px 12px;border-radius:6px;border:1px solid var(--border);cursor:pointer;transition:border-color 0.15s"
              :style="currentScreen?.id === s.id ? 'border-color:var(--primary);background:var(--surface-raised,#f0f4ff)' : 'background:transparent'"
              @click="selectScreen(s)"
            >
              <div style="flex:1;min-width:0">
                <div style="font-size:13px;font-weight:600">{{ screenLabel[s.id] }}</div>
                <div v-if="s.objective" class="text-muted text-sm" style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ s.objective }}</div>
              </div>
              <span class="badge" :class="s.status === 'complete' ? 'badge-completed' : s.status === 'in_progress' ? 'badge-info' : ''" style="white-space:nowrap">
                {{ s.status?.replace('_', ' ') }}
              </span>
              <span class="text-muted" style="font-size:11px;white-space:nowrap">
                {{ s.candidates?.length ?? 0 }} candidates
              </span>
              <button
                class="btn btn-sm btn-secondary"
                style="color:#dc2626;flex-shrink:0"
                @click.stop="removeScreen(s)"
              >Remove</button>
            </div>
          </div>
        </div>

        <template v-if="currentScreen">
          <!-- Section tabs -->
          <div style="display:flex;gap:0;border-bottom:2px solid var(--border);margin-bottom:20px">
            <button
              v-for="tab in [{id:'setup',label:'Setup & Baseline'},{id:'candidates',label:`Candidates (${candidates.length})`},{id:'experiments',label:`Experiments (${experiments.length})`},{id:'results',label:'Results & Selection'}]"
              :key="tab.id"
              style="padding:8px 18px;border:none;background:none;cursor:pointer;font-size:13px;font-weight:500;border-bottom:2px solid transparent;margin-bottom:-2px"
              :style="activeSection === tab.id ? 'border-bottom-color:var(--primary);color:var(--primary)' : 'color:var(--text-muted)'"
              @click="activeSection = tab.id"
            >{{ tab.label }}</button>
          </div>

          <!-- ══ TAB: Setup & Baseline ══════════════════════════════════════════ -->
          <template v-if="activeSection === 'setup'">
            <div class="card mb-4">
              <div class="flex items-center justify-between mb-3">
                <div class="card-title" style="margin-bottom:0">Screen Configuration</div>
                <span class="badge" :class="currentScreen.status === 'complete' ? 'badge-completed' : currentScreen.status === 'in_progress' ? 'badge-info' : ''">
                  {{ currentScreen.status?.replace('_', ' ') }}
                </span>
              </div>
              <div class="grid-2" style="gap:12px;margin-bottom:12px">
                <div class="form-group" style="margin:0">
                  <label class="form-label">Screen Type</label>
                  <select v-model="screenForm.screen_type" class="form-control">
                    <option value="salt">Salt Screen</option>
                    <option value="polymorph">Polymorph Screen</option>
                    <option value="cocrystal">Co-Crystal Screen</option>
                  </select>
                </div>
                <div class="form-group" style="margin:0">
                  <label class="form-label">Objective</label>
                  <input v-model="screenForm.objective" class="form-control" placeholder="e.g. Improve aqueous solubility, avoid hygroscopic form" />
                </div>
              </div>
            </div>

            <div class="card mb-4">
              <div class="card-title">Baseline API Properties</div>
              <p class="text-muted text-sm mb-3">
                Record the free base/acid properties before screening. These are the reference values used to compare solid forms.
              </p>
              <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:12px">
                <div class="form-group" style="margin:0">
                  <label class="form-label">pKa (most basic/acidic site)</label>
                  <input v-model="screenForm.baseline_pka" type="number" step="0.1" class="form-control" placeholder="e.g. 8.3" />
                  <p class="text-muted" style="font-size:11px;margin:3px 0 0">Used to predict viable salt formers (ΔpKa ≥ 2 rule)</p>
                </div>
                <div class="form-group" style="margin:0">
                  <label class="form-label">Melting Point (°C)</label>
                  <input v-model="screenForm.baseline_melting_point_c" type="number" step="0.1" class="form-control" placeholder="e.g. 142" />
                </div>
                <div class="form-group" style="margin:0">
                  <label class="form-label">LogP (lipophilicity)</label>
                  <input v-model="screenForm.baseline_logp" type="number" step="0.1" class="form-control" placeholder="e.g. 2.1" />
                </div>
                <div class="form-group" style="margin:0">
                  <label class="form-label">Aqueous Solubility (mg/mL)</label>
                  <input v-model="screenForm.baseline_solubility_mgml" type="number" step="0.01" class="form-control" placeholder="e.g. 0.05" />
                </div>
                <div class="form-group" style="margin:0">
                  <label class="form-label">Hygroscopicity</label>
                  <select v-model="screenForm.baseline_hygroscopicity" class="form-control">
                    <option value="">— not assessed —</option>
                    <option value="non_hygroscopic">Non-hygroscopic</option>
                    <option value="slightly">Slightly Hygroscopic</option>
                    <option value="hygroscopic">Hygroscopic</option>
                    <option value="very">Very Hygroscopic / Deliquescent</option>
                  </select>
                </div>
              </div>
              <div class="form-group" style="margin-bottom:12px">
                <label class="form-label">Additional Baseline Notes (DSC, TGA, XRPD of free form)</label>
                <textarea v-model="screenForm.baseline_notes" class="form-control" rows="3" placeholder="e.g. XRPD confirms crystalline Form I. DSC shows single endotherm at 142°C. TGA shows 0.3% weight loss below 200°C (anhydrous)." style="font-size:13px;resize:vertical" />
              </div>
              <div style="display:flex;align-items:center;gap:10px">
                <button class="btn btn-primary btn-sm" :disabled="saving" @click="saveSetup">
                  {{ saving ? 'Saving…' : 'Save Setup' }}
                </button>
                <span v-if="setupSaved" style="font-size:12px;color:#16a34a;font-weight:500">✓ Saved</span>
              </div>
            </div>
          </template>

          <!-- ══ TAB: Candidates ════════════════════════════════════════════════ -->
          <template v-if="activeSection === 'candidates'">
            <div class="card mb-4">
              <div class="flex items-center justify-between mb-3">
                <div>
                  <div class="card-title" style="margin-bottom:0">Candidate Panel</div>
                  <p class="text-muted text-sm" style="margin:4px 0 0">
                    {{ currentScreen.screen_type === 'polymorph' ? 'Define crystallization conditions and polymorph forms to screen.' : 'Select salt formers or co-formers from the preset list or add manually. The ΔpKa rule: a viable salt requires |pKa(acid) − pKa(base)| ≥ 2.' }}
                  </p>
                </div>
                <button class="btn btn-secondary btn-sm" @click="showCandidateForm = !showCandidateForm">
                  {{ showCandidateForm ? 'Cancel' : '+ Add Manually' }}
                </button>
              </div>

              <!-- Manual form -->
              <div v-if="showCandidateForm" style="padding:14px;background:var(--surface-raised,#f8f9fa);border-radius:6px;margin-bottom:14px">
                <div class="grid-2" style="gap:10px;margin-bottom:10px">
                  <div class="form-group" style="margin:0">
                    <label class="form-label">Name</label>
                    <input v-model="candidateForm.name" class="form-control" placeholder="e.g. Maleate" />
                  </div>
                  <div class="form-group" style="margin:0">
                    <label class="form-label">CAS Number</label>
                    <input v-model="candidateForm.cas_number" class="form-control" placeholder="e.g. 110-16-7" />
                  </div>
                  <div class="form-group" style="margin:0">
                    <label class="form-label">Type</label>
                    <select v-model="candidateForm.counterion_type" class="form-control">
                      <option value="">— select —</option>
                      <option value="acid">Acid (for basic API)</option>
                      <option value="base">Base (for acidic API)</option>
                      <option value="coformer">Co-former</option>
                      <option value="polymorph">Polymorph condition</option>
                    </select>
                  </div>
                  <div class="form-group" style="margin:0">
                    <label class="form-label">pKa of Counterion</label>
                    <input v-model="candidateForm.pka_delta" type="number" step="0.1" class="form-control" placeholder="e.g. 1.9" />
                  </div>
                  <div class="form-group" style="margin:0">
                    <label class="form-label">Theoretical Solubility Impact</label>
                    <select v-model="candidateForm.theoretical_solubility_impact" class="form-control">
                      <option value="unknown">Unknown</option>
                      <option value="improved">Improved</option>
                      <option value="neutral">Neutral</option>
                      <option value="decreased">Decreased</option>
                    </select>
                  </div>
                  <div class="form-group" style="margin:0">
                    <label class="form-label">Notes</label>
                    <input v-model="candidateForm.notes" class="form-control" placeholder="Regulatory precedent, known issues…" />
                  </div>
                </div>
                <button class="btn btn-primary btn-sm" :disabled="!candidateForm.name.trim() || saving" @click="addCandidate">
                  {{ saving ? 'Adding…' : 'Add Candidate' }}
                </button>
              </div>

              <!-- Preset quick-add -->
              <div v-if="currentScreen.screen_type !== 'polymorph'" style="margin-bottom:16px">
                <p class="text-muted text-sm" style="margin-bottom:8px;font-weight:500">Common Salt Formers — click to add:</p>
                <div style="display:flex;flex-wrap:wrap;gap:6px">
                  <button
                    v-for="p in COMMON_COUNTERIONS" :key="p.name"
                    class="btn btn-sm btn-secondary"
                    style="font-size:11px;padding:3px 10px"
                    :disabled="candidates.some(c => c.name === p.name)"
                    @click="addPresetCandidate(p)"
                  >
                    {{ p.name }}
                  </button>
                </div>
              </div>
              <div v-else style="margin-bottom:16px">
                <p class="text-muted text-sm" style="margin-bottom:8px;font-weight:500">Common Polymorph Conditions — click to add:</p>
                <div style="display:flex;flex-wrap:wrap;gap:6px">
                  <button
                    v-for="p in POLYMORPH_FORMS" :key="p.name"
                    class="btn btn-sm btn-secondary"
                    style="font-size:11px;padding:3px 10px"
                    :disabled="candidates.some(c => c.name === p.name)"
                    @click="addPresetCandidate(p)"
                  >
                    {{ p.name }}
                  </button>
                </div>
              </div>

              <!-- Candidates table -->
              <EmptyState v-if="!candidates.length" title="No candidates added" message="Add salt formers from the preset list or manually above." />
              <table v-else style="width:100%;font-size:13px;border-collapse:collapse">
                <thead>
                  <tr style="border-bottom:2px solid var(--border)">
                    <th style="text-align:left;padding:7px 8px;font-weight:600">Name</th>
                    <th style="text-align:left;padding:7px 8px;font-weight:600">CAS</th>
                    <th style="text-align:left;padding:7px 8px;font-weight:600">Type</th>
                    <th style="text-align:right;padding:7px 8px;font-weight:600">pKa</th>
                    <th style="text-align:left;padding:7px 8px;font-weight:600">Solubility Δ</th>
                    <th style="text-align:right;padding:7px 8px;font-weight:600">Experiments</th>
                    <th style="padding:7px 8px"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="c in candidates" :key="c.id" style="border-bottom:1px solid var(--border)" :style="c.selected ? 'background:var(--surface-raised,#f0fdf4)' : ''">
                    <td style="padding:7px 8px;font-weight:500">
                      {{ c.name }}
                      <span v-if="c.selected" style="margin-left:6px;font-size:10px;background:#16a34a;color:#fff;padding:1px 6px;border-radius:3px">★ selected</span>
                    </td>
                    <td style="padding:7px 8px;color:var(--text-muted);font-size:11px">{{ c.cas_number || '—' }}</td>
                    <td style="padding:7px 8px"><span v-if="c.counterion_type" class="badge">{{ c.counterion_type }}</span></td>
                    <td style="padding:7px 8px;text-align:right">{{ c.pka_delta != null ? c.pka_delta : '—' }}</td>
                    <td style="padding:7px 8px">
                      <span :style="`color:${c.theoretical_solubility_impact==='improved'?'#16a34a':c.theoretical_solubility_impact==='decreased'?'#dc2626':'var(--text-muted)'};font-size:12px`">
                        {{ c.theoretical_solubility_impact }}
                      </span>
                    </td>
                    <td style="padding:7px 8px;text-align:right">{{ c.experiment_count ?? (experimentsByCandidateId[c.id] || []).length }}</td>
                    <td style="padding:7px 8px;text-align:right;white-space:nowrap">
                      <button class="btn btn-sm btn-secondary" style="margin-right:4px" @click="activeSection='experiments'; experimentForm.candidate=String(c.id)">+ Exp</button>
                      <button class="btn btn-sm btn-secondary" style="color:#dc2626" @click="removeCandidate(c.id)">✕</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>

          <!-- ══ TAB: Experiments ═══════════════════════════════════════════════ -->
          <template v-if="activeSection === 'experiments'">
            <div class="card mb-4">
              <div class="flex items-center justify-between mb-3">
                <div>
                  <div class="card-title" style="margin-bottom:0">Screening Experiments</div>
                  <p class="text-muted text-sm" style="margin:4px 0 0">
                    Each experiment tests one preparation method for one candidate. Record characterization data (XRPD, DSC, TGA) as results arrive.
                  </p>
                </div>
                <button class="btn btn-secondary btn-sm" :disabled="!candidates.length" @click="showExperimentForm = !showExperimentForm">
                  {{ showExperimentForm ? 'Cancel' : '+ Log Experiment' }}
                </button>
              </div>

              <!-- Experiment form -->
              <div v-if="showExperimentForm" style="padding:14px;background:var(--surface-raised,#f8f9fa);border-radius:6px;margin-bottom:16px">
                <p style="font-size:13px;font-weight:600;margin-bottom:10px">Preparation</p>
                <div class="grid-2" style="gap:10px;margin-bottom:12px">
                  <div class="form-group" style="margin:0">
                    <label class="form-label">Candidate</label>
                    <select v-model="experimentForm.candidate" class="form-control">
                      <option value="">— select —</option>
                      <option v-for="c in candidates" :key="c.id" :value="String(c.id)">{{ c.name }}</option>
                    </select>
                  </div>
                  <div class="form-group" style="margin:0">
                    <label class="form-label">Preparation Method</label>
                    <select v-model="experimentForm.prep_method" class="form-control">
                      <option value="slurry">Slurry</option>
                      <option value="evaporation">Slow Evaporation</option>
                      <option value="grinding">Grinding / Mechanochemistry</option>
                      <option value="spray_dry">Spray Drying</option>
                      <option value="antisolvent">Antisolvent Precipitation</option>
                      <option value="cooling">Cooling Crystallization</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                  <div class="form-group" style="margin:0">
                    <label class="form-label">Solvent System</label>
                    <input v-model="experimentForm.solvent" class="form-control" placeholder="e.g. EtOH/H₂O 9:1, acetone" />
                  </div>
                  <div class="form-group" style="margin:0">
                    <label class="form-label">Ratio (API:counterion)</label>
                    <input v-model="experimentForm.ratio" class="form-control" placeholder="e.g. 1:1.05 mol/mol" />
                  </div>
                  <div class="form-group" style="margin:0">
                    <label class="form-label">Temperature (°C)</label>
                    <input v-model="experimentForm.temperature_c" type="number" step="1" class="form-control" placeholder="e.g. 50" />
                  </div>
                  <div class="form-group" style="margin:0">
                    <label class="form-label">Visual Appearance</label>
                    <input v-model="experimentForm.results_appearance" class="form-control" placeholder="e.g. white crystalline powder" />
                  </div>
                </div>

                <p style="font-size:13px;font-weight:600;margin-bottom:10px">Characterization Results</p>
                <div class="grid-2" style="gap:10px;margin-bottom:12px">
                  <div class="form-group" style="margin:0">
                    <label class="form-label">XRPD Pattern</label>
                    <textarea v-model="experimentForm.results_xrpd" class="form-control" rows="2" placeholder="e.g. New crystalline pattern, distinct from free base. Peaks at 2θ = 7.2°, 14.4°, 18.6°." style="font-size:12px;resize:vertical" />
                  </div>
                  <div class="form-group" style="margin:0">
                    <label class="form-label">DSC</label>
                    <textarea v-model="experimentForm.results_dsc" class="form-control" rows="2" placeholder="e.g. Single sharp endotherm at 178°C (ΔH = 95 J/g). No polymorphic transitions." style="font-size:12px;resize:vertical" />
                  </div>
                  <div class="form-group" style="margin:0">
                    <label class="form-label">TGA</label>
                    <textarea v-model="experimentForm.results_tga" class="form-control" rows="2" placeholder="e.g. 0.2% weight loss below 150°C (anhydrous). Decomposition onset at 195°C." style="font-size:12px;resize:vertical" />
                  </div>
                  <div class="form-group" style="margin:0">
                    <label class="form-label">Solubility (mg/mL)</label>
                    <input v-model="experimentForm.results_solubility" class="form-control" placeholder="e.g. 12.4 mg/mL in pH 7.4 PBS" />
                  </div>
                </div>

                <div class="grid-2" style="gap:10px;margin-bottom:12px">
                  <div class="form-group" style="margin:0">
                    <label class="form-label">Observed Solid Form</label>
                    <select v-model="experimentForm.observed_form" class="form-control">
                      <option value="">— not yet determined —</option>
                      <option value="crystalline">Crystalline</option>
                      <option value="amorphous">Amorphous</option>
                      <option value="unchanged">Unchanged API (no salt formed)</option>
                      <option value="mixed">Mixed / Unclear</option>
                      <option value="oily">Oil / Gum</option>
                    </select>
                  </div>
                  <div class="form-group" style="margin:0">
                    <label class="form-label">Notes</label>
                    <input v-model="experimentForm.notes" class="form-control" placeholder="Scale, analyst, instrument, observations…" />
                  </div>
                </div>
                <button class="btn btn-primary btn-sm" :disabled="!experimentForm.candidate || saving" @click="addExperiment">
                  {{ saving ? 'Saving…' : 'Log Experiment' }}
                </button>
              </div>

              <!-- Experiments grouped by candidate -->
              <EmptyState v-if="!experiments.length" title="No experiments logged" message="Log your first experiment above. Add candidates first if the list is empty." />
              <div v-else>
                <div v-for="candidate in candidates" :key="candidate.id">
                  <template v-if="(experimentsByCandidateId[candidate.id] || []).length">
                    <div style="padding:6px 0;font-size:12px;font-weight:600;color:var(--text-muted);border-top:1px solid var(--border);margin-top:8px">
                      {{ candidate.name }}
                    </div>
                    <table style="width:100%;font-size:12px;border-collapse:collapse;margin-bottom:4px">
                      <thead>
                        <tr style="border-bottom:1px solid var(--border)">
                          <th style="text-align:left;padding:5px 8px;font-weight:600;color:var(--text-muted)">Method</th>
                          <th style="text-align:left;padding:5px 8px;font-weight:600;color:var(--text-muted)">Solvent</th>
                          <th style="text-align:left;padding:5px 8px;font-weight:600;color:var(--text-muted)">Ratio</th>
                          <th style="text-align:right;padding:5px 8px;font-weight:600;color:var(--text-muted)">Temp (°C)</th>
                          <th style="text-align:left;padding:5px 8px;font-weight:600;color:var(--text-muted)">Observed Form</th>
                          <th style="text-align:right;padding:5px 8px;font-weight:600;color:var(--text-muted)">Solubility</th>
                          <th style="padding:5px 8px"></th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr
                          v-for="exp in experimentsByCandidateId[candidate.id]" :key="exp.id"
                          style="border-bottom:1px solid var(--border)"
                        >
                          <td style="padding:5px 8px">{{ exp.prep_method?.replace('_', ' ') || '—' }}</td>
                          <td style="padding:5px 8px;color:var(--text-muted)">{{ exp.solvent || '—' }}</td>
                          <td style="padding:5px 8px;color:var(--text-muted)">{{ exp.ratio || '—' }}</td>
                          <td style="padding:5px 8px;text-align:right">{{ exp.temperature_c ?? '—' }}</td>
                          <td style="padding:5px 8px">
                            <span v-if="exp.observed_form" :style="formBadgeStyle(exp.observed_form)">{{ exp.observed_form }}</span>
                            <span v-else style="color:var(--text-muted)">—</span>
                          </td>
                          <td style="padding:5px 8px;text-align:right;color:var(--text-muted)">{{ exp.results_solubility || '—' }}</td>
                          <td style="padding:5px 8px;text-align:right">
                            <button class="btn btn-sm btn-secondary" style="color:#dc2626;font-size:11px" @click="removeExperiment(exp.id)">✕</button>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </template>
                </div>
              </div>
            </div>
          </template>

          <!-- ══ TAB: Results & Selection ═══════════════════════════════════════ -->
          <template v-if="activeSection === 'results'">
            <!-- Summary table -->
            <div class="card mb-4">
              <div class="card-title">Results Summary</div>
              <p class="text-muted text-sm mb-3">
                Compare all screened forms side by side. Select the preferred solid form to lock it to the project.
              </p>

              <EmptyState v-if="!candidates.length" title="No candidates" message="Add candidates and log experiments first." />
              <table v-else style="width:100%;font-size:13px;border-collapse:collapse">
                <thead>
                  <tr style="border-bottom:2px solid var(--border)">
                    <th style="text-align:left;padding:8px;font-weight:600">Form</th>
                    <th style="text-align:left;padding:8px;font-weight:600">Exp.</th>
                    <th style="text-align:left;padding:8px;font-weight:600">Best Observed Form</th>
                    <th style="text-align:left;padding:8px;font-weight:600">Best Solubility</th>
                    <th style="text-align:left;padding:8px;font-weight:600">Theoretical Δ Solubility</th>
                    <th style="padding:8px"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="c in candidates" :key="c.id"
                    style="border-bottom:1px solid var(--border)"
                    :style="c.selected ? 'background:var(--surface-raised,#f0fdf4)' : ''"
                  >
                    <td style="padding:8px;font-weight:500">
                      {{ c.name }}
                      <span v-if="c.selected" style="margin-left:6px;font-size:10px;background:#16a34a;color:#fff;padding:1px 6px;border-radius:3px">★ preferred</span>
                    </td>
                    <td style="padding:8px">{{ (experimentsByCandidateId[c.id] || []).length }}</td>
                    <td style="padding:8px">
                      <template v-if="(experimentsByCandidateId[c.id] || []).some(e => e.observed_form === 'crystalline')">
                        <span :style="formBadgeStyle('crystalline')">crystalline</span>
                      </template>
                      <template v-else-if="(experimentsByCandidateId[c.id] || []).length">
                        <span :style="formBadgeStyle((experimentsByCandidateId[c.id]||[]).at(-1)?.observed_form)">
                          {{ (experimentsByCandidateId[c.id]||[]).at(-1)?.observed_form || '—' }}
                        </span>
                      </template>
                      <span v-else style="color:var(--text-muted)">—</span>
                    </td>
                    <td style="padding:8px;color:var(--text-muted)">
                      {{ (experimentsByCandidateId[c.id] || []).map(e => e.results_solubility).filter(Boolean).at(-1) || '—' }}
                    </td>
                    <td style="padding:8px">
                      <span :style="`color:${c.theoretical_solubility_impact==='improved'?'#16a34a':c.theoretical_solubility_impact==='decreased'?'#dc2626':'var(--text-muted)'}`">
                        {{ c.theoretical_solubility_impact }}
                      </span>
                    </td>
                    <td style="padding:8px;text-align:right">
                      <button
                        class="btn btn-sm"
                        :class="c.selected ? 'btn-primary' : 'btn-secondary'"
                        @click="markCandidateSelected(c)"
                      >
                        {{ c.selected ? '★ Preferred' : 'Select' }}
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Form selection confirmation -->
            <div class="card mb-4">
              <div class="card-title">Form Selection Decision</div>
              <p class="text-muted text-sm mb-3">
                Record the selected solid form and the scientific rationale. This locks the form to the project and advances to Process Development.
              </p>
              <div class="grid-2" style="gap:12px;margin-bottom:12px">
                <div class="form-group" style="margin:0">
                  <label class="form-label">Selected Form</label>
                  <input v-model="selectionForm.selected_form" class="form-control" placeholder="e.g. Hydrochloride salt, Form I" />
                </div>
              </div>
              <div class="form-group" style="margin-bottom:12px">
                <label class="form-label">Selection Rationale</label>
                <textarea
                  v-model="selectionForm.selection_rationale"
                  class="form-control"
                  rows="4"
                  placeholder="e.g. HCl salt (Form I) selected based on: aqueous solubility 12.4 mg/mL vs 0.05 mg/mL free base (248× improvement), non-hygroscopic (0.2% moisture uptake at 75% RH), sharp DSC melting at 178°C indicating high crystallinity, XRPD pattern reproducible across three batches. pKa delta = 8.3 − 1.9 = 6.4 (well above the 2-unit threshold for robust salt formation)."
                  style="font-size:13px;resize:vertical"
                />
              </div>

              <div v-if="currentScreen.selected_form" style="padding:10px 14px;background:var(--surface-raised,#f0fdf4);border-radius:6px;border:1px solid #bbf7d0;margin-bottom:12px">
                <strong style="color:#15803d">Locked form:</strong> {{ currentScreen.selected_form }}
                <RouterLink :to="`/projects/${projectId}/process-development`" class="btn btn-sm btn-primary" style="margin-left:12px">→ Process Development</RouterLink>
              </div>

              <button class="btn btn-primary" :disabled="!selectionForm.selected_form.trim() || saving" @click="selectForm">
                {{ saving ? 'Saving…' : 'Lock Selected Form' }}
              </button>
            </div>
          </template>

        </template>
      </template>
    </template>
  </div>
</template>
