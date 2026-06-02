<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '@/components/layout/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { useSARStore } from '@/stores/sar'

const route = useRoute()
const projectId = route.params.id
const store = useSARStore()

// ─── Constants ────────────────────────────────────────────────────────────────

const ACTIVITY_TYPES = ['IC50', 'EC50', 'Ki', 'Kd', 'pIC50', 'pKi', '% inhibition', 'other']
const ACTIVITY_UNITS = ['nM', 'µM', 'mM', 'pM', '%']
const SORT_OPTIONS = [
  { value: 'potency', label: 'Potency (best first)' },
  { value: 'lipe',   label: 'LipE (highest first)' },
  { value: 'le',     label: 'LE (highest first)' },
  { value: 'date',   label: 'Date (newest first)' },
]

const POTENCY_BINS = [
  { label: 'Exceptional', max: 1,        color: '#7c3aed', bg: '#f5f3ff', border: '#ddd6fe' },
  { label: 'Excellent',   max: 10,       color: '#166534', bg: '#f0fdf4', border: '#bbf7d0' },
  { label: 'Good',        max: 100,      color: '#16a34a', bg: '#dcfce7', border: '#86efac' },
  { label: 'Moderate',    max: 1000,     color: '#ca8a04', bg: '#fefce8', border: '#fde68a' },
  { label: 'Weak',        max: 10000,    color: '#ea580c', bg: '#fff7ed', border: '#fed7aa' },
  { label: 'Inactive',    max: Infinity, color: '#dc2626', bg: '#fef2f2', border: '#fecaca' },
]

const DL_RULES = [
  { rule: 'Lipinski Ro5',          criteria: 'MW ≤ 500, cLogP ≤ 5, HBD ≤ 5, HBA ≤ 10',  note: 'Oral absorption predictor (>90% oral drugs comply)' },
  { rule: 'Veber (oral bioavail.)', criteria: 'RotBonds ≤ 10, TPSA ≤ 140 Å²',            note: 'Rat oral bioavailability predictor' },
  { rule: 'CNS MPO score',          criteria: '6 desirability functions → composite ≥ 4', note: 'BBB penetration composite; target ≥ 4/6' },
  { rule: 'Egan Egg',               criteria: 'TPSA ≤ 131.6 Å², cLogP ≤ 5.88',           note: 'Passive intestinal absorption model' },
  { rule: 'Pfizer 3/75 Rule',       criteria: 'cLogP < 3, TPSA > 75 Å²',                 note: 'Reduces hERG liability and promiscuity risk' },
  { rule: 'Beyond Ro5 (bRo5)',      criteria: 'MW 500–1000, still CYP-clean',             note: 'PROTAC / macrocycle chemical space' },
]

const SAR_MODIFICATIONS = [
  { modification: 'F → H (ring)',       effect: 'Metabolic blocking (CYP)',      guidance: '+0.1–0.5 cLogP; blocks CYP3A4/2D6 aromatic hydroxylation' },
  { modification: 'CF₃ addition',       effect: 'Lipophilicity ↑, stability ↑', guidance: '+0.8–1.5 cLogP; bioisostere for tert-butyl or Cl' },
  { modification: 'O → NH bioisostere', effect: 'HBD ↑, TPSA ↑',               guidance: 'Alters pKa; can improve selectivity and H-bond network' },
  { modification: 'N-methylation',      effect: 'Basicity ↓, cLogP ↑',         guidance: 'Reduces P-gp efflux; watch CYP induction risk' },
  { modification: 'Aryl → heteroaryl',  effect: 'TPSA ↑, solubility ↑',        guidance: 'Common selectivity handle; monitor reactive metabolite risk' },
  { modification: 'Ring contraction',   effect: 'Conformation change',           guidance: 'Alters binding geometry; impacts entropy penalty' },
  { modification: 'sp3 centre addition',effect: 'Fsp3 ↑, solubility ↑',        guidance: 'Target Fsp3 > 0.25; reduces crystal packing / low solubility' },
  { modification: 'Ester → amide',      effect: 'Metabolic stability ↑↑',       guidance: 'Blocks esterase hydrolysis; note pKa and HBD change' },
]

// ─── State ────────────────────────────────────────────────────────────────────

const selected     = ref(null)
const activeTab    = ref('activity')
const sortBy       = ref('potency')
const filterType   = ref('all')
const showCreate   = ref(false)
const showDeleteId = ref(null)
const saving       = ref(false)
const editingId    = ref(null)

const newForm = ref({
  smiles: '', r_group: '', activity_value: '', activity_unit: 'nM',
  activity_type: 'IC50', assay_description: '', notes: '',
  logp: '', mw: '', selectivity_value: '', selectivity_target: '',
})

const editForm = ref({})

// ─── Activity math ─────────────────────────────────────────────────────────────

function toNm(value, unit) {
  if (value == null || isNaN(value)) return null
  const v = parseFloat(value)
  if (unit === 'nM') return v
  if (unit === 'µM') return v * 1000
  if (unit === 'mM') return v * 1_000_000
  if (unit === 'pM') return v / 1000
  return null
}

function nmValue(entry) {
  if (entry.activity_type === 'pIC50' || entry.activity_type === 'pKi') {
    const pv = parseFloat(entry.activity_value)
    return isNaN(pv) ? null : Math.pow(10, 9 - pv)
  }
  return toNm(entry.activity_value, entry.activity_unit)
}

function pAct(entry) {
  if (entry.activity_type === 'pIC50' || entry.activity_type === 'pKi') {
    const v = parseFloat(entry.activity_value)
    return isNaN(v) ? null : +v.toFixed(2)
  }
  const nm = toNm(entry.activity_value, entry.activity_unit)
  if (!nm || nm <= 0) return null
  return +(9 - Math.log10(nm)).toFixed(2)
}

function lipe(entry) {
  const pa = pAct(entry)
  if (pa == null || entry.logp == null || entry.logp === '') return null
  return +(pa - parseFloat(entry.logp)).toFixed(2)
}

function le(entry) {
  const pa = pAct(entry)
  if (pa == null || !entry.mw) return null
  const hac = Math.round(parseFloat(entry.mw) / 13.0)
  if (!hac) return null
  return +(1.37 * pa / hac).toFixed(3)
}

function potencyBin(entry) {
  const nm = nmValue(entry)
  if (nm == null || nm <= 0) return null
  return POTENCY_BINS.find(b => nm < b.max) || POTENCY_BINS[POTENCY_BINS.length - 1]
}

function fmtNm(nm) {
  if (nm == null) return '—'
  if (nm < 1)       return `${(nm * 1000).toFixed(1)} pM`
  if (nm < 1000)    return `${nm.toFixed(1)} nM`
  if (nm < 1000000) return `${(nm / 1000).toFixed(2)} µM`
  return `${(nm / 1_000_000).toFixed(2)} mM`
}

function lipeColor(v) {
  if (v == null) return '#6b7280'
  if (v >= 5)    return '#16a34a'
  if (v >= 3)    return '#ca8a04'
  return '#dc2626'
}

function leColor(v) {
  if (v == null) return '#6b7280'
  if (v >= 0.3)  return '#16a34a'
  if (v >= 0.2)  return '#ca8a04'
  return '#dc2626'
}

// ─── Computed ─────────────────────────────────────────────────────────────────

const activityTypeOptions = computed(() => [
  'all',
  ...new Set(store.entries.map(e => e.activity_type).filter(Boolean)),
])

const filteredEntries = computed(() => {
  let list = filterType.value === 'all'
    ? [...store.entries]
    : store.entries.filter(e => e.activity_type === filterType.value)

  list.sort((a, b) => {
    if (sortBy.value === 'potency') {
      const na = nmValue(a), nb = nmValue(b)
      if (na == null && nb == null) return 0
      if (na == null) return 1
      if (nb == null) return -1
      return na - nb
    }
    if (sortBy.value === 'lipe') {
      const la = lipe(a), lb = lipe(b)
      if (la == null && lb == null) return 0
      if (la == null) return 1
      if (lb == null) return -1
      return lb - la
    }
    if (sortBy.value === 'le') {
      const la = le(a), lb = le(b)
      if (la == null && lb == null) return 0
      if (la == null) return 1
      if (lb == null) return -1
      return lb - la
    }
    return new Date(b.created_at) - new Date(a.created_at)
  })
  return list
})

const summaryStats = computed(() => {
  const withNm = store.entries.map(e => nmValue(e)).filter(v => v != null && v > 0).sort((a, b) => a - b)
  const best   = withNm[0] ?? null
  const median = withNm.length ? withNm[Math.floor(withNm.length / 2)] : null
  const lipes  = store.entries.map(e => lipe(e)).filter(v => v != null)
  const avgLipe = lipes.length ? +(lipes.reduce((a, b) => a + b, 0) / lipes.length).toFixed(2) : null
  return { count: store.entries.length, best, median, avgLipe }
})

// ─── Actions ─────────────────────────────────────────────────────────────────

function selectEntry(e) {
  selected.value = e
  editingId.value = null
  activeTab.value = 'activity'
}

function resetNewForm() {
  newForm.value = {
    smiles: '', r_group: '', activity_value: '', activity_unit: 'nM',
    activity_type: 'IC50', assay_description: '', notes: '',
    logp: '', mw: '', selectivity_value: '', selectivity_target: '',
  }
}

async function createEntry() {
  saving.value = true
  try {
    const payload = {
      ...newForm.value,
      project: projectId,
      activity_value:    parseFloat(newForm.value.activity_value)    || null,
      logp:              newForm.value.logp !== ''              ? parseFloat(newForm.value.logp)              : null,
      mw:                newForm.value.mw   !== ''              ? parseFloat(newForm.value.mw)                : null,
      selectivity_value: newForm.value.selectivity_value !== '' ? parseFloat(newForm.value.selectivity_value) : null,
    }
    const entry = await store.addEntry(payload)
    selected.value = entry
    showCreate.value = false
    resetNewForm()
  } finally {
    saving.value = false
  }
}

function startEdit() {
  editForm.value = { ...selected.value }
  editingId.value = selected.value.id
}

async function saveEdit() {
  saving.value = true
  try {
    const payload = {
      ...editForm.value,
      activity_value:    parseFloat(editForm.value.activity_value)    || null,
      logp:              (editForm.value.logp != null && editForm.value.logp !== '') ? parseFloat(editForm.value.logp) : null,
      mw:                (editForm.value.mw   != null && editForm.value.mw   !== '') ? parseFloat(editForm.value.mw)   : null,
      selectivity_value: (editForm.value.selectivity_value != null && editForm.value.selectivity_value !== '') ? parseFloat(editForm.value.selectivity_value) : null,
    }
    const updated = await store.updateEntry(editingId.value, payload)
    selected.value = updated
    editingId.value = null
  } finally {
    saving.value = false
  }
}

async function confirmDelete() {
  await store.deleteEntry(showDeleteId.value)
  if (selected.value?.id === showDeleteId.value) selected.value = null
  showDeleteId.value = null
}

onMounted(() => store.fetchEntries(projectId))
</script>

<template>
  <div class="sar-page">
    <PageHeader title="SAR Tracker">
      <template #actions>
        <RouterLink :to="`/projects/${projectId}/candidates`" class="btn btn-outline">
          Candidate Selection →
        </RouterLink>
        <button class="btn btn-primary" @click="showCreate = true">+ Add Entry</button>
      </template>
    </PageHeader>

    <!-- Summary strip -->
    <div v-if="store.entries.length" class="summary-strip">
      <div class="stat-pill">
        <span class="stat-val">{{ summaryStats.count }}</span>
        <span class="stat-lbl">Compounds</span>
      </div>
      <div class="stat-pill">
        <span class="stat-val">{{ fmtNm(summaryStats.best) }}</span>
        <span class="stat-lbl">Best Potency</span>
      </div>
      <div class="stat-pill">
        <span class="stat-val">{{ fmtNm(summaryStats.median) }}</span>
        <span class="stat-lbl">Median IC₅₀</span>
      </div>
      <div class="stat-pill">
        <span class="stat-val" :style="{ color: lipeColor(summaryStats.avgLipe) }">
          {{ summaryStats.avgLipe ?? '—' }}
        </span>
        <span class="stat-lbl">Avg LipE</span>
      </div>
    </div>

    <LoadingSpinner v-if="store.loading" />

    <div v-else-if="!store.entries.length" class="empty-wrap">
      <div class="empty-card">
        <div class="empty-icon">⚗️</div>
        <h3>No SAR entries yet</h3>
        <p>Add compounds with activity data to build your structure–activity relationship map.</p>
        <button class="btn btn-primary" @click="showCreate = true">Add First Entry</button>
      </div>
    </div>

    <div v-else class="two-col">
      <!-- Left panel: entry list -->
      <div class="left-panel">
        <div class="panel-toolbar">
          <select v-model="filterType" class="toolbar-select">
            <option v-for="t in activityTypeOptions" :key="t" :value="t">
              {{ t === 'all' ? 'All types' : t }}
            </option>
          </select>
          <select v-model="sortBy" class="toolbar-select">
            <option v-for="s in SORT_OPTIONS" :key="s.value" :value="s.value">{{ s.label }}</option>
          </select>
        </div>

        <div class="entry-list">
          <div
            v-for="entry in filteredEntries"
            :key="entry.id"
            class="entry-card"
            :class="{ active: selected?.id === entry.id }"
            @click="selectEntry(entry)"
          >
            <div class="entry-top">
              <span class="smiles-snip">{{ entry.smiles?.slice(0, 32) }}{{ entry.smiles?.length > 32 ? '…' : '' }}</span>
              <span
                v-if="potencyBin(entry)"
                class="potency-badge"
                :style="{ color: potencyBin(entry).color, background: potencyBin(entry).bg, borderColor: potencyBin(entry).border }"
              >{{ potencyBin(entry).label }}</span>
            </div>
            <div class="entry-meta">
              <span class="meta-tag">{{ entry.activity_type }} {{ entry.activity_value }}{{ entry.activity_unit !== '%' ? ' ' + entry.activity_unit : '%' }}</span>
              <span v-if="entry.r_group" class="meta-tag muted">{{ entry.r_group }}</span>
            </div>
            <div class="entry-eff">
              <span v-if="lipe(entry) != null" class="eff-chip" :style="{ color: lipeColor(lipe(entry)) }">LipE {{ lipe(entry) }}</span>
              <span v-if="le(entry)   != null" class="eff-chip" :style="{ color: leColor(le(entry)) }">LE {{ le(entry) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Right panel: detail -->
      <div class="right-panel">
        <div v-if="!selected" class="no-selection">
          <p>Select a compound from the list to view details.</p>
        </div>

        <div v-else class="detail-view">
          <div class="detail-header">
            <div class="detail-title">
              <span class="detail-type-badge">{{ selected.activity_type }}</span>
              <span
                v-if="potencyBin(selected)"
                class="potency-badge lg"
                :style="{ color: potencyBin(selected).color, background: potencyBin(selected).bg, borderColor: potencyBin(selected).border }"
              >{{ potencyBin(selected).label }}</span>
            </div>
            <div class="detail-actions">
              <button class="btn btn-sm btn-outline" @click="startEdit">Edit</button>
              <button class="btn btn-sm btn-danger"  @click="showDeleteId = selected.id">Delete</button>
            </div>
          </div>

          <div class="smiles-box">{{ selected.smiles }}</div>

          <!-- Tabs -->
          <div class="tab-bar">
            <button :class="['tab-btn', { active: activeTab === 'activity' }]"  @click="activeTab = 'activity'">Activity &amp; Efficiency</button>
            <button :class="['tab-btn', { active: activeTab === 'props' }]"     @click="activeTab = 'props'">Properties</button>
            <button :class="['tab-btn', { active: activeTab === 'notes' }]"     @click="activeTab = 'notes'">SAR Notes</button>
            <button :class="['tab-btn', { active: activeTab === 'reference' }]" @click="activeTab = 'reference'">Reference</button>
          </div>

          <!-- Edit overlay -->
          <div v-if="editingId" class="edit-overlay">
            <h4 class="edit-heading">Edit Entry</h4>
            <div class="form-row-2">
              <div class="form-group">
                <label>Activity Value</label>
                <input v-model="editForm.activity_value" type="number" class="form-input" />
              </div>
              <div class="form-group">
                <label>Unit</label>
                <select v-model="editForm.activity_unit" class="form-input">
                  <option v-for="u in ACTIVITY_UNITS" :key="u" :value="u">{{ u }}</option>
                </select>
              </div>
              <div class="form-group">
                <label>Activity Type</label>
                <select v-model="editForm.activity_type" class="form-input">
                  <option v-for="t in ACTIVITY_TYPES" :key="t" :value="t">{{ t }}</option>
                </select>
              </div>
              <div class="form-group">
                <label>R-Group / Scaffold</label>
                <input v-model="editForm.r_group" class="form-input" />
              </div>
              <div class="form-group">
                <label>LogP (measured / cLogP)</label>
                <input v-model="editForm.logp" type="number" step="0.1" class="form-input" />
              </div>
              <div class="form-group">
                <label>MW (g/mol)</label>
                <input v-model="editForm.mw" type="number" class="form-input" />
              </div>
              <div class="form-group">
                <label>Selectivity Value</label>
                <input v-model="editForm.selectivity_value" type="number" class="form-input" placeholder="fold or nM" />
              </div>
              <div class="form-group">
                <label>Selectivity Target</label>
                <input v-model="editForm.selectivity_target" class="form-input" placeholder="e.g. hERG, CYP3A4" />
              </div>
            </div>
            <div class="form-group">
              <label>Assay Description</label>
              <input v-model="editForm.assay_description" class="form-input" />
            </div>
            <div class="form-group">
              <label>Notes</label>
              <textarea v-model="editForm.notes" class="form-input" rows="3" />
            </div>
            <div class="edit-actions">
              <button class="btn btn-outline" @click="editingId = null">Cancel</button>
              <button class="btn btn-primary" :disabled="saving" @click="saveEdit">{{ saving ? 'Saving…' : 'Save' }}</button>
            </div>
          </div>

          <!-- Tab: Activity & Efficiency -->
          <div v-else-if="activeTab === 'activity'" class="tab-content">
            <div class="metrics-grid">
              <div class="metric-card">
                <div class="metric-label">Reported Activity</div>
                <div class="metric-val">{{ selected.activity_value }} {{ selected.activity_unit }}</div>
                <div class="metric-sub">{{ selected.activity_type }}</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">nM Equivalent</div>
                <div class="metric-val">{{ fmtNm(nmValue(selected)) }}</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">pActivity</div>
                <div class="metric-val">{{ pAct(selected) ?? '—' }}</div>
                <div class="metric-sub">−log₁₀([M]) = −log₁₀(conc)</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">LipE</div>
                <div class="metric-val" :style="{ color: lipeColor(lipe(selected)) }">{{ lipe(selected) ?? '—' }}</div>
                <div class="metric-sub">pAct − LogP · Target ≥ 5</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">LE</div>
                <div class="metric-val" :style="{ color: leColor(le(selected)) }">{{ le(selected) ?? '—' }}</div>
                <div class="metric-sub">1.37 × pAct / HAC · Target ≥ 0.3</div>
              </div>
              <div v-if="selected.selectivity_value" class="metric-card">
                <div class="metric-label">Selectivity vs {{ selected.selectivity_target || 'off-target' }}</div>
                <div class="metric-val">{{ selected.selectivity_value }}×</div>
              </div>
            </div>
            <div v-if="selected.assay_description" class="info-row">
              <span class="info-lbl">Assay</span>
              <span>{{ selected.assay_description }}</span>
            </div>
            <div v-if="selected.r_group" class="info-row">
              <span class="info-lbl">R-Group / Scaffold</span>
              <span>{{ selected.r_group }}</span>
            </div>
          </div>

          <!-- Tab: Properties -->
          <div v-else-if="activeTab === 'props'" class="tab-content">
            <div class="props-grid">
              <div class="prop-row">
                <span class="prop-lbl">LogP</span>
                <span class="prop-val">{{ selected.logp ?? '—' }}</span>
                <span class="prop-target">Target: 1–3 (oral), &lt; 5 (Ro5)</span>
              </div>
              <div class="prop-row">
                <span class="prop-lbl">MW</span>
                <span class="prop-val">{{ selected.mw ? selected.mw + ' g/mol' : '—' }}</span>
                <span class="prop-target">Target: &lt; 500 g/mol (Ro5)</span>
              </div>
              <div class="prop-row">
                <span class="prop-lbl">Est. HAC</span>
                <span class="prop-val">{{ selected.mw ? Math.round(parseFloat(selected.mw) / 13) : '—' }}</span>
                <span class="prop-target">Heavy atom count (MW / 13 estimate)</span>
              </div>
            </div>
            <div v-if="!selected.logp && !selected.mw" class="props-hint">
              Enter LogP and MW when editing this entry to unlock LipE and LE efficiency metrics.
            </div>
            <div class="dl-section">
              <h5 class="section-heading">Drug-Likeness Rules Reference</h5>
              <table class="ref-table">
                <thead>
                  <tr><th>Rule</th><th>Criteria</th><th>Note</th></tr>
                </thead>
                <tbody>
                  <tr v-for="r in DL_RULES" :key="r.rule">
                    <td><strong>{{ r.rule }}</strong></td>
                    <td>{{ r.criteria }}</td>
                    <td class="muted-cell">{{ r.note }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Tab: SAR Notes -->
          <div v-else-if="activeTab === 'notes'" class="tab-content">
            <div v-if="selected.notes" class="notes-box">{{ selected.notes }}</div>
            <div v-else class="notes-empty">No SAR notes recorded. Edit this entry to add observations.</div>
          </div>

          <!-- Tab: Reference -->
          <div v-else-if="activeTab === 'reference'" class="tab-content">
            <h5 class="section-heading">Common SAR Modifications</h5>
            <table class="ref-table">
              <thead>
                <tr><th>Modification</th><th>Primary Effect</th><th>Practical Guidance</th></tr>
              </thead>
              <tbody>
                <tr v-for="m in SAR_MODIFICATIONS" :key="m.modification">
                  <td><strong>{{ m.modification }}</strong></td>
                  <td>{{ m.effect }}</td>
                  <td class="muted-cell">{{ m.guidance }}</td>
                </tr>
              </tbody>
            </table>
            <div class="ref-note">
              <strong>Potency bins (IC₅₀/EC₅₀):</strong>
              <span v-for="b in POTENCY_BINS" :key="b.label" class="potency-badge sm" :style="{ color: b.color, background: b.bg, borderColor: b.border }">
                {{ b.label }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create modal -->
    <div v-if="showCreate" class="modal-overlay" @click.self="showCreate = false">
      <div class="modal-box">
        <div class="modal-header">
          <h3>New SAR Entry</h3>
          <button class="close-btn" @click="showCreate = false">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>SMILES *</label>
            <input v-model="newForm.smiles" class="form-input" placeholder="CC(=O)Oc1ccccc1C(=O)O" />
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label>Activity Value *</label>
              <input v-model="newForm.activity_value" type="number" class="form-input" placeholder="10" />
            </div>
            <div class="form-group">
              <label>Unit</label>
              <select v-model="newForm.activity_unit" class="form-input">
                <option v-for="u in ACTIVITY_UNITS" :key="u" :value="u">{{ u }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>Activity Type</label>
              <select v-model="newForm.activity_type" class="form-input">
                <option v-for="t in ACTIVITY_TYPES" :key="t" :value="t">{{ t }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>R-Group / Scaffold Note</label>
              <input v-model="newForm.r_group" class="form-input" placeholder="e.g. 4-fluoro benzyl" />
            </div>
            <div class="form-group">
              <label>LogP (cLogP or measured)</label>
              <input v-model="newForm.logp" type="number" step="0.1" class="form-input" placeholder="2.4" />
            </div>
            <div class="form-group">
              <label>MW (g/mol)</label>
              <input v-model="newForm.mw" type="number" class="form-input" placeholder="350" />
            </div>
            <div class="form-group">
              <label>Selectivity Value</label>
              <input v-model="newForm.selectivity_value" type="number" class="form-input" placeholder="fold or off-target IC50 nM" />
            </div>
            <div class="form-group">
              <label>Selectivity Target</label>
              <input v-model="newForm.selectivity_target" class="form-input" placeholder="e.g. hERG, CYP3A4" />
            </div>
          </div>
          <div class="form-group">
            <label>Assay Description</label>
            <input v-model="newForm.assay_description" class="form-input" placeholder="e.g. FP assay, cell-free, n=3 ± SD" />
          </div>
          <div class="form-group">
            <label>SAR Notes</label>
            <textarea v-model="newForm.notes" class="form-input" rows="3" placeholder="Observations, comparison to parent, next steps…" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" @click="showCreate = false; resetNewForm()">Cancel</button>
          <button class="btn btn-primary" :disabled="!newForm.smiles || !newForm.activity_value || saving" @click="createEntry">
            {{ saving ? 'Saving…' : 'Add Entry' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Delete confirm -->
    <div v-if="showDeleteId" class="modal-overlay" @click.self="showDeleteId = null">
      <div class="confirm-box">
        <h4>Delete this entry?</h4>
        <p>This action cannot be undone.</p>
        <div class="confirm-actions">
          <button class="btn btn-outline" @click="showDeleteId = null">Cancel</button>
          <button class="btn btn-danger"  @click="confirmDelete">Delete</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ── Layout ── */
.sar-page { display: flex; flex-direction: column; height: 100%; }
.two-col  { display: flex; gap: 0; flex: 1; overflow: hidden; }

/* ── Summary strip ── */
.summary-strip { display: flex; gap: 16px; padding: 12px 0 16px; flex-wrap: wrap; }
.stat-pill { background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; padding: 10px 18px; display: flex; flex-direction: column; align-items: center; min-width: 110px; }
.stat-val  { font-size: 20px; font-weight: 700; color: #111827; line-height: 1.2; }
.stat-lbl  { font-size: 11px; color: #6b7280; margin-top: 2px; }

/* ── Left panel ── */
.left-panel    { width: 320px; flex-shrink: 0; border-right: 1px solid #e5e7eb; display: flex; flex-direction: column; overflow: hidden; }
.panel-toolbar { display: flex; gap: 8px; padding: 10px 12px; border-bottom: 1px solid #f3f4f6; }
.toolbar-select { flex: 1; padding: 6px 8px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 12px; background: #fff; }
.entry-list    { flex: 1; overflow-y: auto; padding: 8px; display: flex; flex-direction: column; gap: 6px; }

.entry-card        { padding: 10px 12px; border: 1px solid #e5e7eb; border-radius: 8px; cursor: pointer; transition: border-color 0.15s, background 0.15s; }
.entry-card:hover  { border-color: #93c5fd; background: #f8faff; }
.entry-card.active { border-color: #2563eb; background: #eff6ff; }
.entry-top  { display: flex; align-items: flex-start; justify-content: space-between; gap: 6px; margin-bottom: 4px; }
.smiles-snip { font-family: monospace; font-size: 11px; color: #374151; flex: 1; overflow: hidden; }
.entry-meta { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 4px; }
.meta-tag   { font-size: 11px; background: #f3f4f6; color: #374151; border-radius: 4px; padding: 1px 6px; }
.meta-tag.muted { color: #9ca3af; }
.entry-eff  { display: flex; gap: 6px; }
.eff-chip   { font-size: 11px; font-weight: 600; }

/* ── Right panel ── */
.right-panel  { flex: 1; overflow-y: auto; padding: 20px 24px; }
.no-selection { display: flex; align-items: center; justify-content: center; height: 200px; color: #9ca3af; }

.detail-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.detail-title  { display: flex; align-items: center; gap: 8px; }
.detail-type-badge { background: #dbeafe; color: #1d4ed8; font-size: 12px; font-weight: 600; padding: 2px 8px; border-radius: 12px; }
.detail-actions    { display: flex; gap: 8px; }

.smiles-box { font-family: monospace; font-size: 12px; background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 10px 14px; word-break: break-all; margin-bottom: 14px; color: #374151; }

/* ── Tabs ── */
.tab-bar { display: flex; border-bottom: 1px solid #e5e7eb; margin-bottom: 16px; }
.tab-btn        { padding: 8px 14px; font-size: 13px; font-weight: 500; border: none; background: none; cursor: pointer; color: #6b7280; border-bottom: 2px solid transparent; margin-bottom: -1px; transition: color 0.15s; }
.tab-btn:hover  { color: #374151; }
.tab-btn.active { color: #2563eb; border-bottom-color: #2563eb; }
.tab-content    { display: flex; flex-direction: column; gap: 14px; }

/* ── Metrics ── */
.metrics-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.metric-card  { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px 14px; }
.metric-label { font-size: 11px; color: #6b7280; margin-bottom: 4px; }
.metric-val   { font-size: 20px; font-weight: 700; color: #111827; line-height: 1.2; }
.metric-sub   { font-size: 10px; color: #9ca3af; margin-top: 2px; }

.info-row { display: flex; gap: 12px; align-items: baseline; font-size: 13px; padding: 6px 0; border-bottom: 1px solid #f3f4f6; }
.info-lbl { font-weight: 600; color: #374151; min-width: 130px; flex-shrink: 0; }

/* ── Properties ── */
.props-grid { display: flex; flex-direction: column; gap: 0; margin-bottom: 16px; }
.prop-row   { display: grid; grid-template-columns: 90px 90px 1fr; gap: 8px; align-items: baseline; font-size: 13px; padding: 7px 0; border-bottom: 1px solid #f3f4f6; }
.prop-lbl    { font-weight: 600; color: #374151; }
.prop-val    { font-weight: 700; color: #111827; }
.prop-target { font-size: 11px; color: #9ca3af; }
.props-hint  { background: #fefce8; border: 1px solid #fde68a; border-radius: 6px; padding: 10px 14px; font-size: 13px; color: #92400e; }

/* ── Reference table ── */
.dl-section      { margin-top: 4px; }
.section-heading { font-size: 13px; font-weight: 700; color: #374151; margin: 0 0 8px; }
.ref-table       { width: 100%; border-collapse: collapse; font-size: 12px; }
.ref-table th    { text-align: left; padding: 6px 8px; background: #f3f4f6; font-weight: 600; color: #374151; border-bottom: 1px solid #e5e7eb; }
.ref-table td    { padding: 6px 8px; border-bottom: 1px solid #f3f4f6; color: #374151; vertical-align: top; }
.muted-cell      { color: #6b7280; }

.ref-note { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; margin-top: 14px; font-size: 12px; color: #374151; }

/* ── SAR Notes ── */
.notes-box   { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 14px; font-size: 13px; white-space: pre-wrap; color: #374151; }
.notes-empty { font-size: 13px; color: #9ca3af; font-style: italic; }

/* ── Potency badge ── */
.potency-badge    { font-size: 11px; font-weight: 600; border: 1px solid; border-radius: 10px; padding: 1px 8px; white-space: nowrap; }
.potency-badge.lg { font-size: 12px; padding: 3px 10px; }
.potency-badge.sm { font-size: 10px; padding: 1px 6px; }

/* ── Edit overlay ── */
.edit-overlay { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 10px; padding: 16px 18px; display: flex; flex-direction: column; gap: 12px; }
.edit-heading { font-size: 14px; font-weight: 700; color: #111827; margin: 0 0 4px; }
.edit-actions { display: flex; justify-content: flex-end; gap: 10px; }

/* ── Modal ── */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-box     { background: #fff; border-radius: 12px; width: 680px; max-width: 96vw; max-height: 90vh; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,.2); }
.modal-header  { display: flex; align-items: center; justify-content: space-between; padding: 20px 24px 16px; border-bottom: 1px solid #e5e7eb; flex-shrink: 0; }
.modal-header h3 { margin: 0; font-size: 16px; font-weight: 700; color: #111827; }
.close-btn     { background: none; border: none; font-size: 16px; cursor: pointer; color: #6b7280; padding: 4px; }
.close-btn:hover { color: #111827; }
.modal-body    { padding: 20px 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; }
.modal-footer  { display: flex; justify-content: flex-end; gap: 10px; padding: 16px 24px; border-top: 1px solid #e5e7eb; flex-shrink: 0; }

.confirm-box    { background: #fff; border-radius: 10px; width: 400px; max-width: 92vw; padding: 28px 28px 20px; box-shadow: 0 20px 60px rgba(0,0,0,.2); }
.confirm-box h4 { margin: 0 0 8px; font-size: 16px; color: #111827; }
.confirm-box p  { margin: 0 0 20px; font-size: 13px; color: #6b7280; }
.confirm-actions { display: flex; justify-content: flex-end; gap: 10px; }

/* ── Forms ── */
.form-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.form-group { display: flex; flex-direction: column; gap: 5px; }
.form-group label { font-size: 12px; font-weight: 600; color: #374151; }
.form-input { padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; outline: none; width: 100%; box-sizing: border-box; }
.form-input:focus { border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37,99,235,.08); }
textarea.form-input { resize: vertical; }

/* ── Empty state ── */
.empty-wrap { display: flex; align-items: center; justify-content: center; flex: 1; padding: 60px 20px; }
.empty-card { text-align: center; max-width: 400px; }
.empty-icon { font-size: 48px; margin-bottom: 16px; }
.empty-card h3 { margin: 0 0 8px; font-size: 18px; color: #111827; }
.empty-card p  { margin: 0 0 20px; font-size: 14px; color: #6b7280; }
</style>
