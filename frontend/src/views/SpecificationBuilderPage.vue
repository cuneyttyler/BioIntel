<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '@/components/layout/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { useAnalyticalStore } from '@/stores/analytical'
import { useAIPageContext } from '@/composables/useAIPageContext'

const route = useRoute()
const projectId = route.params.id
const store = useAnalyticalStore()

// ─── UI State ─────────────────────────────────────────────────────────────────
const activeTab = ref('release')
const materialType = ref('DS')
const showModal = ref(false)
const showIchRef = ref(false)
const saving = ref(false)
const saveStatus = ref('')
const editingId = ref(null)
const deletingId = ref(null)

const TABS = [
  { key: 'release', label: 'Release' },
  { key: 'shelf_life', label: 'Shelf Life' },
  { key: 'in_process', label: 'In-Process' },
  { key: 'raw_material', label: 'Raw Material' },
]

const MATERIAL_TYPES = ['DS', 'DP', 'Intermediate']

const CRITERIA_TYPES = ['NMT', 'NLT', 'between', 'conforms', 'report']

const criteriaColor = {
  NMT: '#dc2626',
  NLT: '#2563eb',
  between: '#7c3aed',
  conforms: '#16a34a',
  report: '#6b7280',
}

const emptyForm = () => ({
  spec_type: activeTab.value,
  attribute: '',
  criteria_type: 'NMT',
  acceptance_criteria: '',
  test_method: '',
  basis: '',
  analytical_method: null,
})

const form = ref(emptyForm())

// ─── Preset Specification Bank ────────────────────────────────────────────────
const PRESET_SPECS = {
  DS: {
    release: [
      { attribute: 'Appearance', criteria_type: 'conforms', acceptance_criteria: 'White to off-white crystalline powder', test_method: 'Visual inspection', basis: 'ICH Q6A' },
      { attribute: 'Identification A (HPLC)', criteria_type: 'conforms', acceptance_criteria: 'Retention time within ±2% of reference standard', test_method: 'HPLC-UV', basis: 'ICH Q6A §3.1 — two independent methods required' },
      { attribute: 'Identification B (IR)', criteria_type: 'conforms', acceptance_criteria: 'Principal peaks of test spectrum correspond to reference', test_method: 'FT-IR (KBr disc or ATR)', basis: 'ICH Q6A §3.1' },
      { attribute: 'Assay', criteria_type: 'between', acceptance_criteria: '97.0–103.0% (anhydrous basis)', test_method: 'HPLC-UV (external standard)', basis: 'ICH Q6A — reflects analytical variability ±2%' },
      { attribute: 'Specified impurity A', criteria_type: 'NMT', acceptance_criteria: 'NMT 0.20%', test_method: 'HPLC (gradient, UV/PDA)', basis: 'ICH Q3A — qualification threshold (daily dose >10 mg)' },
      { attribute: 'Specified impurity B', criteria_type: 'NMT', acceptance_criteria: 'NMT 0.20%', test_method: 'HPLC', basis: 'ICH Q3A — qualification threshold' },
      { attribute: 'Any unspecified impurity', criteria_type: 'NMT', acceptance_criteria: 'NMT 0.10%', test_method: 'HPLC', basis: 'ICH Q3A — reporting threshold 0.05%, ID threshold 0.10%' },
      { attribute: 'Total impurities', criteria_type: 'NMT', acceptance_criteria: 'NMT 0.50%', test_method: 'HPLC', basis: 'ICH Q3A — sum of all specified + unspecified' },
      { attribute: 'Residual solvents (Class 2)', criteria_type: 'NMT', acceptance_criteria: 'NMT 290 ppm ethanol; NMT 880 ppm THF', test_method: 'GC-HS (ICH Q3C method)', basis: 'ICH Q3C Appendix 1 PDE-based limits' },
      { attribute: 'Water content', criteria_type: 'NMT', acceptance_criteria: 'NMT 0.5% w/w', test_method: 'Karl Fischer titration (coulometric)', basis: 'ICH Q6A; form-specific requirement' },
      { attribute: 'Residue on ignition', criteria_type: 'NMT', acceptance_criteria: 'NMT 0.1%', test_method: 'Ph. Eur. 2.4.14 / USP <281>', basis: 'ICH Q6A' },
      { attribute: 'Elemental impurities', criteria_type: 'NMT', acceptance_criteria: 'Per ICH Q3D PDEs (e.g., Pb ≤ 5 μg/day)', test_method: 'ICP-MS (USP <232>/<233>)', basis: 'ICH Q3D — risk assessment + controls required' },
      { attribute: 'Particle size D90', criteria_type: 'NMT', acceptance_criteria: 'NMT 250 μm', test_method: 'Laser diffraction (ISO 13320)', basis: 'Bioavailability data — confirm if dissolution-rate limited' },
      { attribute: 'Polymorphic form', criteria_type: 'conforms', acceptance_criteria: 'Conforms to Form I reference diffractogram', test_method: 'XRPD (Cu Kα radiation)', basis: 'Stability / solubility data — form change confirmed not to occur' },
      { attribute: 'Microbial quality (TAMC)', criteria_type: 'NMT', acceptance_criteria: 'NMT 10² CFU/g', test_method: 'Ph. Eur. 5.1.4 / USP <61><62>', basis: 'ICH Q6A non-sterile DS — Category 3B' },
    ],
    shelf_life: [
      { attribute: 'Appearance', criteria_type: 'conforms', acceptance_criteria: 'No significant change from initial (no discoloration, caking)', test_method: 'Visual inspection', basis: 'ICH Q1A(R2)' },
      { attribute: 'Assay', criteria_type: 'between', acceptance_criteria: '95.0–105.0% (anhydrous basis)', test_method: 'HPLC-UV', basis: 'ICH Q1A(R2) — shelf life limit wider than release' },
      { attribute: 'Specified impurity A', criteria_type: 'NMT', acceptance_criteria: 'NMT 0.30%', test_method: 'HPLC', basis: 'ICH Q3A — shelf life limit = qualification threshold + analytical uncertainty' },
      { attribute: 'Total impurities', criteria_type: 'NMT', acceptance_criteria: 'NMT 1.00%', test_method: 'HPLC', basis: 'ICH Q3A shelf life limit' },
      { attribute: 'Water content', criteria_type: 'NMT', acceptance_criteria: 'NMT 1.0% w/w', test_method: 'Karl Fischer', basis: 'Stability data (accelerated + long-term ICH Q1A)' },
      { attribute: 'Polymorphic form', criteria_type: 'conforms', acceptance_criteria: 'Conforms to Form I reference', test_method: 'XRPD', basis: 'Required if polymorph conversion observed in stability studies' },
    ],
    in_process: [
      { attribute: 'In-process assay', criteria_type: 'between', acceptance_criteria: '95.0–105.0%', test_method: 'HPLC', basis: 'IPC — wider than release' },
      { attribute: 'Reaction completion', criteria_type: 'NMT', acceptance_criteria: 'Starting material NMT 1.0% area', test_method: 'HPLC / TLC', basis: 'Process endpoint criterion' },
      { attribute: 'Particle size post-milling D90', criteria_type: 'NMT', acceptance_criteria: 'NMT 200 μm', test_method: 'Laser diffraction', basis: 'Process control for downstream bioavailability' },
      { attribute: 'pH of crystallisation mother liquor', criteria_type: 'between', acceptance_criteria: '6.5–7.5', test_method: 'pH meter (calibrated)', basis: 'Process requirement — crystal form control' },
      { attribute: 'Step yield', criteria_type: 'NLT', acceptance_criteria: 'NLT 75%', test_method: 'Gravimetric', basis: 'Process efficiency limit' },
    ],
    raw_material: [
      { attribute: 'Identity (IR)', criteria_type: 'conforms', acceptance_criteria: 'Spectrum conforms to reference standard', test_method: 'FT-IR (ATR)', basis: 'Compendial / GMP requirement' },
      { attribute: 'API purity', criteria_type: 'NLT', acceptance_criteria: 'NLT 99.0% (anhydrous basis)', test_method: 'HPLC', basis: 'Supplier CoA; compendial grade' },
      { attribute: 'Water content (incoming)', criteria_type: 'NMT', acceptance_criteria: 'NMT 0.5% w/w', test_method: 'Karl Fischer', basis: 'Supplier specification' },
      { attribute: 'Elemental impurities (incoming)', criteria_type: 'NMT', acceptance_criteria: 'Per ICH Q3D PDEs', test_method: 'ICP-MS', basis: 'ICH Q3D vendor qualification' },
      { attribute: 'Microbial limits', criteria_type: 'NMT', acceptance_criteria: 'Per compendial category', test_method: 'Ph. Eur. 5.1.4', basis: 'GMP incoming control' },
    ],
  },
  DP: {
    release: [
      { attribute: 'Appearance', criteria_type: 'conforms', acceptance_criteria: 'White to off-white, round, biconvex tablet; free from chips, cracks, or discoloration', test_method: 'Visual inspection (100% or statistical sample)', basis: 'ICH Q6A' },
      { attribute: 'Identification (HPLC)', criteria_type: 'conforms', acceptance_criteria: 'Retention time of main peak conforms to reference standard (±2%)', test_method: 'HPLC-UV', basis: 'ICH Q6A §3.1' },
      { attribute: 'Assay', criteria_type: 'between', acceptance_criteria: '90.0–110.0% of label claim', test_method: 'HPLC-UV (external standard)', basis: 'ICH Q6A — includes manufacturing variability' },
      { attribute: 'Uniformity of dosage units', criteria_type: 'NMT', acceptance_criteria: 'AV ≤ 15.0; no individual outside ±25% of mean', test_method: 'Ph. Eur. 2.9.40 / USP <905> (mass variation or content uniformity)', basis: 'ICH Q6A; Ph. Eur. 2.9.40 mandatory for ≤ 25 mg or ≤ 25% fill weight' },
      { attribute: 'Dissolution (30 min, paddle)', criteria_type: 'NLT', acceptance_criteria: 'NLT Q+5% = 85% dissolved in 30 min (50 rpm, 900 mL 0.1N HCl, 37°C)', test_method: 'USP <711> / Ph. Eur. 2.9.3 Apparatus II', basis: 'ICH Q6A; bioequivalence anchor; BCS Class-dependent' },
      { attribute: 'Related substances', criteria_type: 'NMT', acceptance_criteria: 'NMT 0.50% total (sum of specified + unspecified)', test_method: 'HPLC (gradient, UV/PDA)', basis: 'ICH Q3B' },
      { attribute: 'Specified degradation product A', criteria_type: 'NMT', acceptance_criteria: 'NMT 0.20%', test_method: 'HPLC', basis: 'ICH Q3B — qualification threshold (daily dose >10 mg)' },
      { attribute: 'Water content', criteria_type: 'NMT', acceptance_criteria: 'NMT 3.0% w/w', test_method: 'Karl Fischer (extracted with methanol, 60°C)', basis: 'ICH Q6A; excipient hydration + API stability data' },
      { attribute: 'Microbial quality (TAMC)', criteria_type: 'NMT', acceptance_criteria: 'NMT 10³ CFU/g; TYMC NMT 10² CFU/g; no E. coli', test_method: 'Ph. Eur. 5.1.4 / USP <61><62>', basis: 'ICH Q6A non-sterile oral DP — Category 3A' },
      { attribute: 'Hardness', criteria_type: 'between', acceptance_criteria: '8–20 kP (target 12 kP)', test_method: 'DT hardness tester (n=10, average)', basis: 'Development data; ensures coating and friability compliance' },
      { attribute: 'Friability', criteria_type: 'NMT', acceptance_criteria: 'NMT 1.0% (n=20 tablets, 4 min at 25 rpm)', test_method: 'USP <1216> / Ph. Eur. 2.9.7', basis: 'ICH Q6A' },
      { attribute: 'Disintegration', criteria_type: 'NMT', acceptance_criteria: 'NMT 15 min in water at 37°C', test_method: 'USP <701> / Ph. Eur. 2.9.1', basis: 'ICH Q6A — if dissolution not used as surrogate' },
    ],
    shelf_life: [
      { attribute: 'Appearance', criteria_type: 'conforms', acceptance_criteria: 'No significant change from initial (no discoloration, speckles, or cracks)', test_method: 'Visual inspection', basis: 'ICH Q1A(R2)' },
      { attribute: 'Assay', criteria_type: 'between', acceptance_criteria: '87.0–113.0% of label claim', test_method: 'HPLC-UV', basis: 'ICH Q1A(R2) — shelf life limit accounts for degradation trajectory' },
      { attribute: 'Related substances', criteria_type: 'NMT', acceptance_criteria: 'NMT 1.00% total', test_method: 'HPLC', basis: 'ICH Q3B shelf life limit' },
      { attribute: 'Dissolution (30 min)', criteria_type: 'NLT', acceptance_criteria: 'NLT Q=80% in 30 min', test_method: 'USP <711>', basis: 'Stability requirement — widened Q value for shelf life' },
      { attribute: 'Water content', criteria_type: 'NMT', acceptance_criteria: 'NMT 5.0% w/w', test_method: 'Karl Fischer', basis: 'Stability data — excipient equilibrium moisture uptake' },
    ],
    in_process: [
      { attribute: 'Blend uniformity', criteria_type: 'between', acceptance_criteria: 'RSD NMT 3.0%; all individuals 90–110% of target', test_method: 'HPLC (stratified thief sampling, ASTM E2709 statistical design)', basis: 'Process control — predicts content uniformity; PQRI guidance' },
      { attribute: 'Granule moisture (post-granulation)', criteria_type: 'NMT', acceptance_criteria: 'NMT 2.0% LOD (loss-on-drying)', test_method: 'Halogen moisture analyser at 105°C', basis: 'Process control — target moisture for compressibility' },
      { attribute: 'Tablet weight variation (IPC)', criteria_type: 'NMT', acceptance_criteria: 'NMT ±5% of target weight (n=20, every 15 min)', test_method: 'Gravimetric (USP <1>)', basis: 'Compendial IPC requirement; alerts to punch wear' },
      { attribute: 'Hardness (IPC)', criteria_type: 'between', acceptance_criteria: '6–22 kP (target 12 kP)', test_method: 'DT hardness tester (n=6)', basis: 'Process control — wider than release; real-time adjustment' },
      { attribute: 'Friability (IPC)', criteria_type: 'NMT', acceptance_criteria: 'NMT 1.5%', test_method: 'USP <1216>', basis: 'IPC limit — relaxed vs. release for pre-coating check' },
      { attribute: 'Coating weight gain', criteria_type: 'between', acceptance_criteria: '2.5–3.5% w/w', test_method: 'Gravimetric (n=20 pre/post weight)', basis: 'Film coat development data — ensures appearance and moisture barrier' },
    ],
    raw_material: [
      { attribute: 'API identity (incoming)', criteria_type: 'conforms', acceptance_criteria: 'Conforms to reference standard (HPLC RT + IR spectrum)', test_method: 'HPLC-UV / FT-IR', basis: 'GMP — supplier qualification + incoming test' },
      { attribute: 'API assay (incoming)', criteria_type: 'NLT', acceptance_criteria: 'NLT 98.0% (anhydrous basis)', test_method: 'HPLC-UV', basis: 'Supplier CoA / compendial specification' },
      { attribute: 'Excipient identity', criteria_type: 'conforms', acceptance_criteria: 'Conforms to compendial specification (Ph. Eur. / NF monograph)', test_method: 'Per excipient monograph (IR, chemical tests)', basis: 'Ph. Eur. / NF compendial compliance' },
      { attribute: 'Excipient microbial limits', criteria_type: 'NMT', acceptance_criteria: 'Per compendial category 3 / 4 limits', test_method: 'Ph. Eur. 5.1.4 / USP <61><62>', basis: 'GMP incoming material control' },
    ],
  },
  Intermediate: {
    release: [
      { attribute: 'Identity (HPLC / TLC)', criteria_type: 'conforms', acceptance_criteria: 'Principal peak conforms to expected retention time or Rf value', test_method: 'HPLC or TLC', basis: 'Stage gate control — confirm correct compound' },
      { attribute: 'Assay / Purity (HPLC area%)', criteria_type: 'NLT', acceptance_criteria: 'NLT 90.0% area (HPLC)', basis: 'Stage-appropriate limit — not final DS quality', test_method: 'HPLC (area normalisation)' },
      { attribute: 'Key impurity (precursor)', criteria_type: 'NMT', acceptance_criteria: 'NMT 2.0% area', test_method: 'HPLC', basis: 'ICH Q3A fate & purge study — carry-through factor < 0.1' },
      { attribute: 'Residual solvent (reaction)', criteria_type: 'NMT', acceptance_criteria: 'NMT 5000 ppm (ICH Q3C Class 3)', test_method: 'GC-HS', basis: 'ICH Q3C — Class 3 limit; further purge steps downstream' },
      { attribute: 'Step yield', criteria_type: 'NLT', acceptance_criteria: 'NLT 70%', test_method: 'Gravimetric', basis: 'Process efficiency gate; investigate if below 60%' },
    ],
    shelf_life: [],
    in_process: [
      { attribute: 'Reaction endpoint (HPLC)', criteria_type: 'NMT', acceptance_criteria: 'Starting material NMT 1.0% area', test_method: 'HPLC (at-line sampling)', basis: 'Reaction completion — drives step yield' },
      { attribute: 'Reaction pH', criteria_type: 'between', acceptance_criteria: '7.0–8.5', test_method: 'pH meter (calibrated, 25°C)', basis: 'Process control — crystal form / impurity profile sensitive to pH' },
      { attribute: 'Temperature control', criteria_type: 'between', acceptance_criteria: 'Within ±2°C of target', test_method: 'Calibrated probe (continuous)', basis: 'Critical process parameter (CPP) — reaction selectivity' },
    ],
    raw_material: [
      { attribute: 'Reagent identity', criteria_type: 'conforms', acceptance_criteria: 'Conforms to CoA / reference', test_method: 'Per supplier specification (IR, MS)', basis: 'GMP — incoming reagent check' },
      { attribute: 'Reagent purity', criteria_type: 'NLT', acceptance_criteria: 'NLT 98.0%', test_method: 'Per supplier specification', basis: 'Process requirement — impurity carry-through risk' },
      { attribute: 'Solvent purity (reaction)', criteria_type: 'NMT', acceptance_criteria: 'Water NMT 50 ppm (anhydrous solvents)', test_method: 'KF coulometric', basis: 'Process requirement — moisture-sensitive reaction' },
    ],
  },
}

// ─── ICH Q6A Reference Table ──────────────────────────────────────────────────
const ICH_Q6A_TABLE = [
  { test: 'Appearance & Description', ds: 'required', dp: 'required', note: 'Physical description; always in spec' },
  { test: 'Identification (≥2 methods)', ds: 'required', dp: 'required', note: 'At least two orthogonal methods (e.g., HPLC + IR)' },
  { test: 'Assay', ds: 'required', dp: 'required', note: 'DS: ±3% range typical; DP: ±10% label claim' },
  { test: 'Organic impurities', ds: 'required', dp: 'required', note: 'Q3A (DS) / Q3B (DP); report/ID/qualify thresholds by dose' },
  { test: 'Inorganic impurities', ds: 'required', dp: 'case-by-case', note: 'ROI, heavy metals; ICH Q3D elemental impurities' },
  { test: 'Residual solvents', ds: 'required', dp: 'case-by-case', note: 'ICH Q3C Class 1/2/3; GC-HS method preferred' },
  { test: 'Water / moisture content', ds: 'required', dp: 'required', note: 'KF titration; critical for hydrolytic degradation' },
  { test: 'Particle size distribution', ds: 'case-by-case', dp: 'not typical', note: 'Required if BCS Class II/IV; impacts dissolution' },
  { test: 'Polymorphic / solid state', ds: 'case-by-case', dp: 'not typical', note: 'Required if conversion affects bioavailability/stability' },
  { test: 'Uniformity of dosage units', ds: 'N/A', dp: 'required', note: 'Ph. Eur. 2.9.40 / USP <905> — mass or content uniformity' },
  { test: 'Dissolution / Drug release', ds: 'N/A', dp: 'required', note: 'Solid oral DP; paddle or basket; BCS-based biowaiver possible' },
  { test: 'Disintegration', ds: 'N/A', dp: 'case-by-case', note: 'Only if dissolution is not specified' },
  { test: 'Hardness & Friability', ds: 'N/A', dp: 'required', note: 'Release only; informational at shelf life' },
  { test: 'Microbial enumeration', ds: 'required', dp: 'required', note: 'Ph. Eur. 5.1.4; oral DS/DP Category 3' },
  { test: 'Sterility / Bacterial endotoxins', ds: 'case-by-case', dp: 'case-by-case', note: 'Sterile products only; LAL or recombinant factor C test' },
]

const ichBadge = (val) => {
  if (val === 'required') return { label: 'Required', bg: '#dcfce7', color: '#15803d' }
  if (val === 'case-by-case') return { label: 'Case-by-case', bg: '#fef9c3', color: '#854d0e' }
  if (val === 'N/A') return { label: 'N/A', bg: '#f3f4f6', color: '#6b7280' }
  return { label: 'Not typical', bg: '#f3f4f6', color: '#6b7280' }
}

// ─── Computed ─────────────────────────────────────────────────────────────────
const specsByTab = computed(() => {
  const map = {}
  for (const t of TABS) {
    map[t.key] = store.specifications.filter(s => s.spec_type === t.key)
  }
  return map
})

const activeSpecs = computed(() => specsByTab.value[activeTab.value] || [])

const activePresets = computed(() =>
  PRESET_SPECS[materialType.value]?.[activeTab.value] || []
)

const alreadyAdded = computed(() => {
  const names = new Set(activeSpecs.value.map(s => s.attribute.toLowerCase()))
  return names
})

const methodOptions = computed(() => store.methods)

const linkedMethodName = (ref) => {
  const id = ref && typeof ref === 'object' ? ref.id : ref
  return store.methods.find(m => m.id === id)?.method_name || `Method #${id}`
}

// ─── Actions ──────────────────────────────────────────────────────────────────
function openCreate() {
  editingId.value = null
  form.value = emptyForm()
  form.value.spec_type = activeTab.value
  showModal.value = true
}

function openEdit(spec) {
  editingId.value = spec.id
  form.value = {
    spec_type: spec.spec_type,
    attribute: spec.attribute,
    criteria_type: spec.criteria_type || 'NMT',
    acceptance_criteria: spec.acceptance_criteria,
    test_method: spec.test_method || '',
    basis: spec.basis || '',
    analytical_method: spec.analytical_method || null,
  }
  showModal.value = true
}

function applyPreset(preset) {
  form.value = {
    spec_type: activeTab.value,
    attribute: preset.attribute,
    criteria_type: preset.criteria_type,
    acceptance_criteria: preset.acceptance_criteria,
    test_method: preset.test_method,
    basis: preset.basis,
    analytical_method: null,
  }
  editingId.value = null
  showModal.value = true
}

async function save() {
  if (!form.value.attribute || !form.value.acceptance_criteria) return
  saving.value = true
  try {
    const payload = { ...form.value }
    if (editingId.value) {
      await store.saveSpecification(projectId, { ...payload, id: editingId.value })
    } else {
      await store.saveSpecification(projectId, payload)
    }
    showModal.value = false
    saveStatus.value = 'saved'
    setTimeout(() => { saveStatus.value = '' }, 2500)
  } finally {
    saving.value = false
  }
}

async function deleteSpec(id) {
  if (!confirm('Delete this specification?')) return
  deletingId.value = id
  await store.deleteSpecification(id)
  deletingId.value = null
}

const projectIdNum = computed(() => parseInt(projectId))
useAIPageContext({
  pageType: 'SpecificationBuilder',
  projectIdRef: projectIdNum,
  getEntity: () => (form.value),
  applyFn: (s) => {
    Object.entries(s).forEach(([k, v]) => { if (k in form.value) form.value[k] = v })
  },
})

onMounted(async () => {
  await Promise.all([
    store.fetchMethods(projectId),
    store.fetchSpecifications(projectId),
  ])
})
</script>

<template>
  <div class="spec-page">
    <PageHeader title="Specification Builder">
      <template #subtitle>ICH Q6A-compliant specification management — Release, Shelf Life, In-Process, Raw Material</template>
      <template #actions>
        <span v-if="saveStatus" class="save-badge">&#10003; Saved</span>
        <button class="btn btn-outline" @click="showIchRef = !showIchRef">
          {{ showIchRef ? 'Hide' : 'ICH Q6A' }} Reference
        </button>
        <button class="btn btn-primary" @click="openCreate">+ Add Specification</button>
      </template>
    </PageHeader>

    <!-- ICH Q6A Reference Panel -->
    <div v-if="showIchRef" class="ich-ref-panel">
      <div class="panel-header">
        <strong>ICH Q6A — Test Applicability by Material Type</strong>
        <span class="panel-subtext">Decision trees for required vs. case-by-case tests</span>
      </div>
      <div class="table-scroll">
        <table class="sci-table ich-table">
          <thead>
            <tr>
              <th>Test / Characteristic</th>
              <th>Drug Substance (DS)</th>
              <th>Drug Product (DP)</th>
              <th>Notes / Guidance</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in ICH_Q6A_TABLE" :key="row.test">
              <td class="test-name">{{ row.test }}</td>
              <td>
                <span class="ich-badge" :style="{ background: ichBadge(row.ds).bg, color: ichBadge(row.ds).color }">
                  {{ ichBadge(row.ds).label }}
                </span>
              </td>
              <td>
                <span class="ich-badge" :style="{ background: ichBadge(row.dp).bg, color: ichBadge(row.dp).color }">
                  {{ ichBadge(row.dp).label }}
                </span>
              </td>
              <td class="note-cell">{{ row.note }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="ich-thresholds">
        <div class="threshold-group">
          <div class="threshold-title">ICH Q3A/B — Impurity Thresholds (DS / DP)</div>
          <table class="sci-table threshold-table">
            <thead><tr><th>Threshold Type</th><th>DS (Q3A)</th><th>DP (Q3B)</th></tr></thead>
            <tbody>
              <tr><td>Reporting</td><td>0.05% or 1.0 mg/day</td><td>0.05% or 1.0 mg/day</td></tr>
              <tr><td>Identification</td><td>0.10% or 1.0 mg/day</td><td>0.10% or 1.0 mg/day</td></tr>
              <tr><td>Qualification</td><td>0.15% or 1.0 mg/day (≥2 g/day: 0.05%)</td><td>0.20% or 2 mg/day</td></tr>
            </tbody>
          </table>
        </div>
        <div class="threshold-group">
          <div class="threshold-title">ICH Q3C — Residual Solvent Classes</div>
          <table class="sci-table threshold-table">
            <thead><tr><th>Class</th><th>Limit</th><th>Examples</th></tr></thead>
            <tbody>
              <tr><td>Class 1 (avoid)</td><td>Benzene: 2 ppm; CCl₄: 4 ppm</td><td>Known carcinogens</td></tr>
              <tr><td>Class 2 (limit)</td><td>DCM: 600 ppm; THF: 720 ppm; EtOH: 5000 ppm</td><td>Non-genotoxic concern</td></tr>
              <tr><td>Class 3 (ICH limit)</td><td>NMT 5000 ppm (0.5%)</td><td>EtOAc, IPA, MEK, acetone</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Controls bar -->
    <div class="controls-bar">
      <div class="material-toggle">
        <span class="toggle-label">Material type:</span>
        <button
          v-for="mt in MATERIAL_TYPES" :key="mt"
          class="mt-btn"
          :class="{ 'mt-active': materialType === mt }"
          @click="materialType = mt"
        >{{ mt }}</button>
      </div>
      <div class="tab-counts">
        <span v-for="t in TABS" :key="t.key" class="tab-count-chip">
          {{ t.label }}: <strong>{{ specsByTab[t.key]?.length || 0 }}</strong>
        </span>
      </div>
    </div>

    <!-- Tab Navigation -->
    <div class="tab-nav">
      <button
        v-for="t in TABS" :key="t.key"
        class="tab-btn"
        :class="{ 'tab-active': activeTab === t.key }"
        @click="activeTab = t.key"
      >
        {{ t.label }}
        <span class="tab-count">{{ specsByTab[t.key]?.length || 0 }}</span>
      </button>
    </div>

    <LoadingSpinner v-if="store.loading.specs" />

    <div v-else class="tab-content">
      <!-- Preset Chips -->
      <div v-if="activePresets.length" class="preset-section">
        <div class="preset-label">Quick-add presets ({{ materialType }} {{ activeTab.replace('_', ' ') }}):</div>
        <div class="preset-chips">
          <button
            v-for="p in activePresets" :key="p.attribute"
            class="preset-chip"
            :class="{ 'preset-added': alreadyAdded.has(p.attribute.toLowerCase()) }"
            @click="applyPreset(p)"
          >
            <span class="preset-type-dot" :style="{ background: criteriaColor[p.criteria_type] || '#6b7280' }"></span>
            {{ p.attribute }}
            <span v-if="alreadyAdded.has(p.attribute.toLowerCase())" class="preset-check">&#10003;</span>
          </button>
        </div>
      </div>

      <!-- Spec Table -->
      <div v-if="activeSpecs.length" class="spec-table-wrap">
        <table class="sci-table spec-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Attribute</th>
              <th>Type</th>
              <th>Acceptance Criteria</th>
              <th>Test Method</th>
              <th>Linked Method</th>
              <th>Basis / Justification</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(s, i) in activeSpecs" :key="s.id">
              <td class="row-num">{{ i + 1 }}</td>
              <td class="attr-cell"><strong>{{ s.attribute }}</strong></td>
              <td>
                <span
                  class="criteria-badge"
                  :style="{
                    background: (criteriaColor[s.criteria_type] || '#6b7280') + '22',
                    color: criteriaColor[s.criteria_type] || '#6b7280',
                    borderColor: (criteriaColor[s.criteria_type] || '#6b7280') + '66',
                  }"
                >{{ s.criteria_type || '—' }}</span>
              </td>
              <td class="criteria-cell">{{ s.acceptance_criteria }}</td>
              <td class="method-cell">{{ s.test_method || '—' }}</td>
              <td>
                <span v-if="s.analytical_method" class="linked-method-pill">
                  {{ linkedMethodName(s.analytical_method) }}
                </span>
                <span v-else class="text-muted">—</span>
              </td>
              <td class="basis-cell">{{ s.basis || '—' }}</td>
              <td class="actions-cell">
                <button class="btn-icon" title="Edit" @click="openEdit(s)">&#9998;</button>
                <button
                  class="btn-icon btn-icon-danger"
                  title="Delete"
                  :disabled="deletingId === s.id"
                  @click="deleteSpec(s.id)"
                >&#10005;</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-else class="empty-tab">
        <div class="empty-icon">&#128203;</div>
        <div class="empty-title">No {{ activeTab.replace('_', ' ') }} specifications</div>
        <div class="empty-sub">Use presets above or click "+ Add Specification" to create one manually.</div>
      </div>
    </div>

    <!-- Add / Edit Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal-box">
        <div class="modal-header">
          <h3>{{ editingId ? 'Edit Specification' : 'Add Specification' }}</h3>
          <button class="modal-close" @click="showModal = false">&#10005;</button>
        </div>

        <div class="modal-body">
          <div class="form-row-3">
            <div class="form-group">
              <label>Spec Type</label>
              <select v-model="form.spec_type" class="form-input">
                <option v-for="t in TABS" :key="t.key" :value="t.key">{{ t.label }}</option>
              </select>
            </div>
            <div class="form-group" style="grid-column: span 2">
              <label>Attribute Name *</label>
              <input v-model="form.attribute" class="form-input" placeholder="e.g. Assay, Dissolution, Appearance" />
            </div>
          </div>

          <div class="form-row-2">
            <div class="form-group">
              <label>Criteria Type</label>
              <div class="criteria-type-row">
                <button
                  v-for="ct in CRITERIA_TYPES" :key="ct"
                  class="ct-btn"
                  :class="{ 'ct-active': form.criteria_type === ct }"
                  :style="form.criteria_type === ct ? { background: criteriaColor[ct] + '22', borderColor: criteriaColor[ct], color: criteriaColor[ct] } : {}"
                  @click="form.criteria_type = ct"
                >{{ ct }}</button>
              </div>
            </div>
            <div class="form-group">
              <label>Linked Analytical Method</label>
              <select v-model="form.analytical_method" class="form-input">
                <option :value="null">None</option>
                <option v-for="m in methodOptions" :key="m.id" :value="m.id">{{ m.method_name }} ({{ m.method_type?.toUpperCase() }})</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label>Acceptance Criteria *</label>
            <input
              v-model="form.acceptance_criteria"
              class="form-input mono-input"
              placeholder="e.g. 97.0–103.0%, NMT 0.20%, Conforms to reference"
            />
            <div class="field-hint">
              <span v-if="form.criteria_type === 'NMT'">Enter limit value: <code>NMT X%</code> or just the value</span>
              <span v-else-if="form.criteria_type === 'NLT'">Enter limit: <code>NLT X%</code></span>
              <span v-else-if="form.criteria_type === 'between'">Enter range: <code>X–Y%</code> or <code>X to Y</code></span>
              <span v-else-if="form.criteria_type === 'conforms'">Describe reference: <code>Conforms to [reference]</code></span>
              <span v-else>Describe what is reported</span>
            </div>
          </div>

          <div class="form-row-2">
            <div class="form-group">
              <label>Test Method / Compendial Reference</label>
              <input v-model="form.test_method" class="form-input" placeholder="USP <621>, HPLC-UV, KF titration..." />
            </div>
          </div>

          <div class="form-group">
            <label>Basis / Justification</label>
            <textarea v-model="form.basis" class="form-input" rows="3"
              placeholder="ICH Q6A, development data, clinical batch experience, regulatory precedent..." />
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-outline" @click="showModal = false">Cancel</button>
          <button
            class="btn btn-primary"
            :disabled="!form.attribute || !form.acceptance_criteria || saving"
            @click="save"
          >{{ saving ? 'Saving...' : (editingId ? 'Update' : 'Add Specification') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.spec-page { padding-bottom: 60px; }

/* Controls */
.controls-bar {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 12px;
  padding: 10px 16px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}
.material-toggle { display: flex; align-items: center; gap: 8px; }
.toggle-label { font-size: 12px; color: #6b7280; font-weight: 500; }
.mt-btn {
  padding: 4px 12px;
  font-size: 13px;
  border: 1px solid #d1d5db;
  border-radius: 20px;
  background: #fff;
  cursor: pointer;
  color: #374151;
  transition: all 0.15s;
}
.mt-btn:hover { border-color: #2563eb; color: #2563eb; }
.mt-active { background: #2563eb; color: #fff !important; border-color: #2563eb; }
.tab-counts { display: flex; gap: 12px; margin-left: auto; }
.tab-count-chip { font-size: 12px; color: #6b7280; }
.tab-count-chip strong { color: #374151; }

/* Tabs */
.tab-nav {
  display: flex;
  border-bottom: 2px solid #e5e7eb;
  margin-bottom: 20px;
  gap: 4px;
}
.tab-btn {
  padding: 10px 20px;
  border: none;
  background: none;
  font-size: 14px;
  color: #6b7280;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  transition: color 0.15s;
}
.tab-btn:hover { color: #2563eb; }
.tab-active { color: #2563eb; border-bottom-color: #2563eb; }
.tab-count {
  background: #e5e7eb;
  color: #374151;
  border-radius: 10px;
  font-size: 11px;
  padding: 1px 7px;
  font-weight: 600;
}
.tab-active .tab-count { background: #dbeafe; color: #1d4ed8; }

/* Presets */
.preset-section {
  margin-bottom: 16px;
  padding: 14px 16px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}
.preset-label { font-size: 12px; color: #6b7280; font-weight: 500; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.05em; }
.preset-chips { display: flex; flex-wrap: wrap; gap: 8px; }
.preset-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  font-size: 12px;
  border: 1px solid #d1d5db;
  border-radius: 20px;
  background: #fff;
  cursor: pointer;
  color: #374151;
  transition: all 0.15s;
}
.preset-chip:hover { border-color: #2563eb; background: #eff6ff; color: #2563eb; }
.preset-added { border-color: #16a34a; background: #f0fdf4; color: #15803d; }
.preset-type-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.preset-check { margin-left: 2px; font-size: 11px; }

/* Sci-table */
.spec-table-wrap { overflow-x: auto; }
.sci-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.sci-table thead tr {
  background: #f9fafb;
  border-bottom: 2px solid #e5e7eb;
}
.sci-table th {
  padding: 10px 12px;
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #6b7280;
  white-space: nowrap;
}
.sci-table td { padding: 10px 12px; border-bottom: 1px solid #f3f4f6; vertical-align: top; }
.sci-table tbody tr:hover { background: #f9fafb; }
.sci-table tbody tr:last-child td { border-bottom: none; }

.row-num { color: #9ca3af; font-size: 12px; width: 32px; }
.attr-cell { min-width: 160px; }
.criteria-cell { font-family: 'SF Mono', 'Fira Code', monospace; font-size: 12px; min-width: 220px; color: #111827; }
.method-cell { color: #6b7280; font-size: 12px; min-width: 140px; }
.basis-cell { color: #6b7280; font-size: 11px; max-width: 200px; line-height: 1.4; }
.actions-cell { white-space: nowrap; }

.criteria-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  border: 1px solid;
  letter-spacing: 0.03em;
}
.linked-method-pill {
  display: inline-block;
  padding: 2px 8px;
  background: #eff6ff;
  color: #1d4ed8;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

/* Actions */
.btn-icon {
  background: none;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  padding: 4px 8px;
  cursor: pointer;
  font-size: 13px;
  color: #6b7280;
  margin-left: 4px;
  transition: all 0.15s;
}
.btn-icon:hover { border-color: #2563eb; color: #2563eb; }
.btn-icon-danger:hover { border-color: #dc2626; color: #dc2626; }
.btn-icon:disabled { opacity: 0.5; cursor: default; }

/* Empty */
.empty-tab {
  text-align: center;
  padding: 60px 20px;
  color: #6b7280;
}
.empty-icon { font-size: 40px; margin-bottom: 12px; }
.empty-title { font-size: 16px; font-weight: 600; color: #374151; margin-bottom: 6px; }
.empty-sub { font-size: 13px; }

/* ICH Reference Panel */
.ich-ref-panel {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  margin-bottom: 20px;
  overflow: hidden;
}
.panel-header {
  background: #1e3a5f;
  color: #fff;
  padding: 12px 20px;
  display: flex;
  align-items: baseline;
  gap: 16px;
}
.panel-subtext { font-size: 12px; color: #93c5fd; }
.table-scroll { overflow-x: auto; }
.ich-table { font-size: 12px; }
.ich-table .test-name { font-weight: 500; color: #374151; min-width: 220px; }
.ich-table .note-cell { color: #6b7280; min-width: 300px; font-size: 11px; }
.ich-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}
.ich-thresholds {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  padding: 16px;
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
}
.threshold-group {}
.threshold-title { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #6b7280; margin-bottom: 8px; }
.threshold-table { font-size: 11px; }
.threshold-table th, .threshold-table td { padding: 6px 10px; }

/* Save badge */
.save-badge {
  background: #dcfce7;
  color: #16a34a;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal-box {
  background: #fff;
  border-radius: 12px;
  width: 700px;
  max-width: 96vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,.2);
}
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 1px solid #e5e7eb;
}
.modal-header h3 { margin: 0; font-size: 16px; font-weight: 700; }
.modal-close { background: none; border: none; font-size: 18px; cursor: pointer; color: #6b7280; }
.modal-body { padding: 20px 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; }
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
}

/* Form elements */
.form-group { display: flex; flex-direction: column; gap: 5px; }
.form-group label { font-size: 12px; font-weight: 600; color: #374151; }
.form-input {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  transition: border-color 0.15s;
  width: 100%;
  box-sizing: border-box;
}
.form-input:focus { border-color: #2563eb; }
.mono-input { font-family: 'SF Mono', 'Fira Code', monospace; }
.field-hint { font-size: 11px; color: #9ca3af; margin-top: 2px; }
.field-hint code { background: #f3f4f6; padding: 1px 5px; border-radius: 3px; font-family: monospace; }
.form-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.form-row-3 { display: grid; grid-template-columns: 160px 1fr 1fr; gap: 14px; }

/* Criteria type selector */
.criteria-type-row { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 2px; }
.ct-btn {
  padding: 5px 12px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.15s;
  letter-spacing: 0.03em;
}
.ct-btn:hover { border-color: #9ca3af; color: #374151; }

/* Buttons */
.btn { padding: 8px 18px; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; border: 1px solid transparent; }
.btn-primary { background: #2563eb; color: #fff; border-color: #2563eb; }
.btn-primary:hover { background: #1d4ed8; }
.btn-primary:disabled { opacity: 0.5; cursor: default; }
.btn-outline { background: #fff; color: #374151; border-color: #d1d5db; }
.btn-outline:hover { border-color: #9ca3af; }

.text-muted { color: #9ca3af; }
</style>
