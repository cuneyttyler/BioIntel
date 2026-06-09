<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '@/components/layout/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { usePreclinicalStore } from '@/stores/preclinical'
import { useAIPageContext } from '@/composables/useAIPageContext'

const route = useRoute()
const projectId = route.params.id
const store = usePreclinicalStore()

const activeSection = ref('physicochemical')
const showBenchmarkEditor = ref(false)
const benchmarkEdits = ref({})

const SECTIONS = [
  { key: 'physicochemical', label: 'Physicochemical' },
  { key: 'absorption', label: 'Absorption (A)' },
  { key: 'distribution', label: 'Distribution (D)' },
  { key: 'metabolism', label: 'Metabolism (M)' },
  { key: 'excretion_tox', label: 'Excretion & Toxicity (E/T)' },
  { key: 'experimental', label: 'Experimental Data' },
  { key: 'context', label: 'Regulatory Context' },
]

// ─── ADMET field definitions ──────────────────────────────────────────────────
// pkCSM field name → display config
const PKCSM_FIELDS = {
  // Absorption
  'Caco2+': {
    label: 'Caco-2 Permeability', unit: 'cm/s (log)', section: 'absorption',
    benchmark: '> -5.15 (high perm)', direction: 'high',
    pass: v => v > -5.15,
    guidance: 'Intestinal epithelial cell permeability. > -5.15 log cm/s = high absorption. ICH M9 BCS Class I/II guidance.',
  },
  'HIA_Hou': {
    label: 'Human Intestinal Absorption', unit: '%', section: 'absorption',
    benchmark: '> 30%', direction: 'high',
    pass: v => v > 30,
    guidance: 'Fraction absorbed from GI tract. > 80% = high, 30–80% = moderate, < 30% = poor.',
  },
  'Pgp_inhibitor': {
    label: 'P-gp Inhibitor', unit: 'yes/no', section: 'absorption',
    benchmark: 'Non-inhibitor preferred', direction: 'low',
    pass: v => !v,
    guidance: 'P-glycoprotein inhibition → DDI risk for P-gp substrates (digoxin, cyclosporine). FDA DDI guidance requires in vitro testing.',
  },
  'Pgp_substrate': {
    label: 'P-gp Substrate', unit: 'yes/no', section: 'absorption',
    benchmark: 'Non-substrate preferred', direction: 'low',
    pass: v => !v,
    guidance: 'P-gp substrate → efflux reduces oral absorption and BBB penetration. Relevant for CNS targets.',
  },
  'renal_OCT2': {
    label: 'Renal OCT2 Substrate', unit: 'yes/no', section: 'absorption',
    benchmark: 'N/A (renal context only)', direction: null,
    pass: () => null,
    guidance: 'Organic cation transporter 2 — renal secretion. FDA DDI guidance: inhibitors of OCT2 may increase serum creatinine without affecting GFR.',
  },
  // Distribution
  'BBB_Martins': {
    label: 'BBB Penetration', unit: 'yes/no', section: 'distribution',
    benchmark: 'Target-dependent', direction: null,
    pass: () => null,
    guidance: 'Blood-brain barrier penetration. Required for CNS targets; a liability for peripheral targets (potential CNS adverse effects).',
  },
  'Fu': {
    label: 'Fraction Unbound (Fu)', unit: 'fraction', section: 'distribution',
    benchmark: 'Fu > 0.01 preferred', direction: 'high',
    pass: v => v > 0.01,
    guidance: 'Fraction not bound to plasma proteins. Low Fu → high PPB → prolonged t½ but reduced free drug available for action/clearance.',
  },
  'VDss_Lombardo': {
    label: 'Volume of Distribution (Vdss)', unit: 'L/kg (log)', section: 'distribution',
    benchmark: '0.04–20 L/kg typical', direction: null,
    pass: v => v > Math.log10(0.04) && v < Math.log10(20),
    guidance: 'log(Vdss). < 0.04 L/kg = confined to plasma; > 20 L/kg = extensive tissue distribution. Impacts dosing interval and loading dose.',
  },
  // Metabolism
  'CYP1A2_inhibitor': { label: 'CYP1A2 Inhibitor', unit: 'yes/no', section: 'metabolism', benchmark: 'Non-inhibitor preferred', direction: 'low', pass: v => !v, guidance: 'CYP1A2 inhibition: relevant for narrow-TI substrates (theophylline, clozapine, warfarin). FDA DDI guidance: static + dynamic models required if in vitro Ki < [I]/25.' },
  'CYP1A2_substrate': { label: 'CYP1A2 Substrate', unit: 'yes/no', section: 'metabolism', benchmark: 'Monitor for inducers', direction: null, pass: () => null, guidance: 'CYP1A2 substrate: inducible by smoking, omeprazole. Relevant if dose is narrow-TI.' },
  'CYP2C19_inhibitor': { label: 'CYP2C19 Inhibitor', unit: 'yes/no', section: 'metabolism', benchmark: 'Non-inhibitor preferred', direction: 'low', pass: v => !v, guidance: 'CYP2C19 inhibition: risk for PPI, clopidogrel, escitalopram. ~3% of Caucasians are poor metabolizers (PM phenotype).' },
  'CYP2C19_substrate': { label: 'CYP2C19 Substrate', unit: 'yes/no', section: 'metabolism', benchmark: 'PM risk if substrate', direction: null, pass: () => null, guidance: 'CYP2C19 substrate: genetic polymorphism (PM phenotype) can cause 5–10× AUC increase. Label PMs if substrate.' },
  'CYP2C9_inhibitor': { label: 'CYP2C9 Inhibitor', unit: 'yes/no', section: 'metabolism', benchmark: 'Non-inhibitor preferred', direction: 'low', pass: v => !v, guidance: 'CYP2C9 inhibition: high clinical relevance for warfarin, phenytoin, NSAIDs. FDA requires in vitro + clinical DDI study.' },
  'CYP2C9_substrate': { label: 'CYP2C9 Substrate', unit: 'yes/no', section: 'metabolism', benchmark: 'Monitor INR if co-administered with warfarin', direction: null, pass: () => null, guidance: 'CYP2C9 substrate: *2 and *3 alleles reduce activity 5–10×. Key for anticoagulants.' },
  'CYP2D6_inhibitor': { label: 'CYP2D6 Inhibitor', unit: 'yes/no', section: 'metabolism', benchmark: 'Non-inhibitor preferred', direction: 'low', pass: v => !v, guidance: 'CYP2D6 inhibition: ~7% Caucasians are PMs. Inhibiting this enzyme converts EMs to phenotypic PMs — major DDI risk for opioids, TCAs, antipsychotics.' },
  'CYP2D6_substrate': { label: 'CYP2D6 Substrate', unit: 'yes/no', section: 'metabolism', benchmark: 'Label PM/EM variability', direction: null, pass: () => null, guidance: 'CYP2D6 substrate: ultra-rapid metabolizers (UMs) may fail therapy; PMs may experience toxicity. FDA requires labeling if sensitive substrate.' },
  'CYP3A4_inhibitor': { label: 'CYP3A4 Inhibitor', unit: 'yes/no', section: 'metabolism', benchmark: 'Non-inhibitor preferred', direction: 'low', pass: v => !v, guidance: 'CYP3A4 accounts for ~50% of drug metabolism. Inhibition is highest DDI risk. Mechanism-based inhibition (e.g. clarithromycin) is irreversible.' },
  'CYP3A4_substrate': { label: 'CYP3A4 Substrate', unit: 'yes/no', section: 'metabolism', benchmark: 'High variability expected', direction: null, pass: () => null, guidance: 'CYP3A4 substrate: high inter-individual variability due to induction (rifampicin, St. John\'s Wort) and inhibition (azoles, protease inhibitors).' },
  // Excretion
  'T12': {
    label: 'Half-life (t½)', unit: 'hours (log)', section: 'excretion_tox',
    benchmark: '2–12 h typical oral', direction: null,
    pass: v => v > Math.log10(2) && v < Math.log10(24),
    guidance: 'Biological half-life. t½ < 2h → frequent dosing; t½ > 24h → once-daily but accumulation risk. Determines dosing interval and time-to-steady-state (4–5 × t½).',
  },
  'clearance_hepatic': {
    label: 'Hepatic Clearance', unit: 'mL/min/kg (log)', section: 'excretion_tox',
    benchmark: '< 8 mL/min/kg (low–moderate)', direction: 'low',
    pass: v => v < Math.log10(8),
    guidance: 'Hepatic extraction ratio: low (< 0.3), medium (0.3–0.7), high (> 0.7). High hepatic CL → first-pass effect → low oral bioavailability.',
  },
  'clearance_microsomal': {
    label: 'Microsomal Clearance', unit: 'mL/min/mg protein (log)', section: 'excretion_tox',
    benchmark: '< 30 μL/min/mg (low–moderate)', direction: 'low',
    pass: v => v < Math.log10(30),
    guidance: 'In vitro CYP metabolic stability. Measured in human liver microsomes (HLM). Scaled to predict in vivo CL using well-stirred model.',
  },
  // Toxicity
  'AMES': {
    label: 'AMES Mutagenicity', unit: 'yes/no', section: 'excretion_tox',
    benchmark: 'Negative (non-mutagenic)', direction: 'low',
    pass: v => !v,
    guidance: 'Ames test (Salmonella reverse mutation). AMES+ → ICH S2(R1) requires follow-up in vitro mammalian assay + in vivo micronucleus or comet. Positive result is a major development risk flag.',
  },
  'Max_tolerated_dose_human': {
    label: 'Max Tolerated Dose (human)', unit: 'log(mg/kg/day)', section: 'excretion_tox',
    benchmark: '> 0 log(mg/kg/day) = > 1 mg/kg', direction: 'high',
    pass: v => v > 0,
    guidance: 'Predicted human MTD from structural features. Very low MTD (<< 1 mg/kg) suggests high potency/toxicity — requires careful dose escalation in FIH trials.',
  },
  'hERG_karim': {
    label: 'hERG Inhibition', unit: 'pIC50', section: 'excretion_tox',
    benchmark: 'pIC50 < 5 preferred (IC50 > 10 μM)', direction: 'low',
    pass: v => v < 5,
    guidance: 'hERG (Kv11.1) potassium channel inhibition → QT prolongation → TdP arrhythmia risk. ICH S7B: hERG in vitro assay mandatory. Safety margin = hERG IC50 / clinical free Cmax ≥ 30× recommended.',
  },
  'LD50_Zhu': {
    label: 'Rat LD50', unit: 'mol/kg (log)', section: 'excretion_tox',
    benchmark: 'Higher is safer (> -1 log mol/kg)', direction: 'high',
    pass: v => v > -1,
    guidance: 'Predicted acute oral lethal dose in rat. GHS toxicity categories: I (< 5 mg/kg), II (5–50 mg/kg), III (50–300 mg/kg), IV (300–2000 mg/kg), V (2000–5000 mg/kg).',
  },
  'hepatotoxicity': {
    label: 'DILI Risk (Hepatotoxicity)', unit: 'yes/no', section: 'excretion_tox',
    benchmark: 'Non-hepatotoxic preferred', direction: 'low',
    pass: v => !v,
    guidance: 'Drug-induced liver injury risk. If positive: conduct comprehensive hepatotoxicity battery — ALT/AST elevation assay, mitochondrial toxicity, bile salt export pump (BSEP) inhibition. FDA DILI guidance for clinical monitoring.',
  },
  'skin_sensitisation': {
    label: 'Skin Sensitization', unit: 'yes/no', section: 'excretion_tox',
    benchmark: 'Non-sensitizer preferred', direction: 'low',
    pass: v => !v,
    guidance: 'Skin sensitization potential. Relevant for dermal products and occupational exposure. ICH S10: if positive, justify exposure control measures.',
  },
}

// Manual physicochemical fields (from compound properties, not pkCSM)
const PHYSCHEM_FIELDS = [
  { key: 'mw', label: 'Molecular Weight', unit: 'Da', benchmark: '≤ 500 Da (Lipinski)', pass: v => v <= 500, guidance: 'Lipinski Ro5 criterion. > 500 Da → poor oral absorption expected unless active transport involved. Beyond Ro5: up to 1000 Da with solubility/permeability optimization.' },
  { key: 'logp', label: 'LogP (cLogP)', unit: '', benchmark: '≤ 5 (Lipinski)', pass: v => v <= 5, guidance: 'Lipophilicity. > 5 → poor aqueous solubility, metabolic issues. Optimal drug-like range: 0–3. LogD (pH 7.4) more relevant for ionizable compounds.' },
  { key: 'hbd', label: 'H-bond Donors (HBD)', unit: '', benchmark: '≤ 5 (Lipinski)', pass: v => v <= 5, guidance: 'NH and OH groups. High HBD → poor membrane permeability. Prodrug strategies can mask polar groups.' },
  { key: 'hba', label: 'H-bond Acceptors (HBA)', unit: '', benchmark: '≤ 10 (Lipinski)', pass: v => v <= 10, guidance: 'N and O atoms. Combined HBD + HBA > 12 → Veber Rule violation (predicts poor oral bioavailability in rats).' },
  { key: 'tpsa', label: 'TPSA', unit: 'Å²', benchmark: '≤ 140 Å² (Veber)', pass: v => v <= 140, guidance: 'Topological polar surface area. > 140 Å² → poor oral absorption (Veber Rule). > 90 Å² → poor CNS penetration. TPSA ≤ 60 Å² for good CNS drugs.' },
  { key: 'rotatable_bonds', label: 'Rotatable Bonds', unit: '', benchmark: '≤ 10 (Veber)', pass: v => v <= 10, guidance: 'Molecular flexibility. > 10 → poor oral bioavailability in rats (Veber Rule). Macrocycles excluded from count.' },
]

// BCS classification helper
const bcsClass = computed(() => {
  const d = firstCompoundData.value
  if (!d) return null
  const hia = d['HIA_Hou']
  const caco = d['Caco2+']
  // Low solubility proxy: logP > 3 (rough)
  const logp = d?.logp ?? firstPhyschemData.value?.logp
  const highPerm = (hia != null && hia > 60) || (caco != null && caco > -5.15)
  const lowSol = logp != null && logp > 3
  if (highPerm && !lowSol) return { cls: 'I', label: 'Class I', color: '#16a34a', desc: 'High solubility, high permeability. Good oral absorption. BCS biowaiver eligible.' }
  if (!highPerm && !lowSol) return { cls: 'III', label: 'Class III', color: '#2563eb', desc: 'High solubility, low permeability. Absorption limited by permeability. Formulation strategy: permeation enhancers.' }
  if (highPerm && lowSol) return { cls: 'II', label: 'Class II', color: '#d97706', desc: 'Low solubility, high permeability. Dissolution-rate limited. Formulation strategy: micronization, amorphous dispersion, nanosuspension.' }
  return { cls: 'IV', label: 'Class IV', color: '#dc2626', desc: 'Low solubility, low permeability. Poor oral absorption. Consider parenteral or prodrug approach.' }
})

// ─── Computed helpers ─────────────────────────────────────────────────────────
const firstCompoundEntry = computed(() => {
  const entries = Object.entries(store.admetData?.computed_admet || {})
  return entries.length ? entries[0] : null
})

const firstCompoundData = computed(() => firstCompoundEntry.value?.[1]?.data || null)
const firstCompoundName = computed(() => firstCompoundEntry.value?.[0] || null)
const firstPhyschemData = computed(() => firstCompoundData.value || {})

const fieldsForSection = (sectionKey) =>
  Object.entries(PKCSM_FIELDS)
    .filter(([, cfg]) => cfg.section === sectionKey)
    .map(([key, cfg]) => ({ key, ...cfg, value: firstCompoundData.value?.[key] }))

const physchemRows = computed(() =>
  PHYSCHEM_FIELDS.map(f => ({ ...f, value: firstPhyschemData.value?.[f.key] }))
)

const lipinskiPass = computed(() => {
  const d = firstPhyschemData.value
  if (!d?.mw) return null
  const checks = {
    mw: d.mw <= 500,
    logp: d.logp <= 5,
    hbd: d.hbd <= 5,
    hba: d.hba <= 10,
  }
  return { ...checks, pass: Object.values(checks).filter(Boolean).length >= 3 }
})

const experimentalData = computed(() => store.admetData?.experimental || [])

const riskFlags = computed(() => {
  const d = firstCompoundData.value || {}
  const flags = []
  if (d['hERG_karim'] != null && d['hERG_karim'] >= 5) flags.push({ label: 'hERG Risk', severity: 'high', desc: 'pIC50 ≥ 5 (IC50 ≤ 10 μM) — cardiac safety study required (ICH S7B)' })
  if (d['AMES']) flags.push({ label: 'AMES+', severity: 'high', desc: 'Mutagenic signal — full ICH S2(R1) battery required' })
  if (d['hepatotoxicity']) flags.push({ label: 'DILI Risk', severity: 'medium', desc: 'Hepatotoxicity signal — hepatic safety panel recommended' })
  if (d['Pgp_inhibitor']) flags.push({ label: 'P-gp Inhibitor', severity: 'medium', desc: 'DDI risk for P-gp substrates — clinical DDI study (FDA guidance)' })
  if (d['CYP3A4_inhibitor']) flags.push({ label: 'CYP3A4 Inhibitor', severity: 'medium', desc: 'Major DDI pathway — clinical DDI study required' })
  if (d['BBB_Martins'] && firstPhyschemData.value?.tpsa > 60) flags.push({ label: 'BBB + High TPSA', severity: 'info', desc: 'TPSA > 60 Å² but predicted BBB+ — verify CNS penetration experimentally' })
  return flags
})

const severityColor = { high: '#dc2626', medium: '#d97706', info: '#2563eb' }
const severityBg = { high: '#fef2f2', medium: '#fffbeb', info: '#eff6ff' }

// ─── Display helpers ──────────────────────────────────────────────────────────
function formatValue(value) {
  if (value == null) return '—'
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (typeof value === 'number') return value.toFixed(3)
  return String(value)
}

function cellStatus(cfg, value) {
  if (value == null) return null
  const result = cfg.pass(value)
  if (result === null || result === undefined) return 'neutral'
  return result ? 'pass' : 'flag'
}

// ICH regulatory reference table
const ICH_ADMET_CONTEXT = [
  { flag: 'hERG pIC50 ≥ 5 (IC50 ≤ 10 μM)', guideline: 'ICH S7B', action: 'In vitro hERG assay + in vivo QT/QTc study in non-rodent. Cardiac safety margin ≥ 30× free Cmax recommended.', severity: 'high' },
  { flag: 'AMES positive (mutagenic)', guideline: 'ICH S2(R1)', action: 'Two in vitro genotoxicity tests (Ames + mammalian cell) + one in vivo test (micronucleus or comet). Positive in vivo = major development risk.', severity: 'high' },
  { flag: 'DILI signal / hepatotoxicity flag', guideline: 'FDA DILI guidance', action: 'In vitro hepatotoxicity panel: ALT/AST assay, mitochondrial membrane potential (MMP), BSEP inhibition, reactive metabolite trapping. Clinical LFT monitoring.', severity: 'medium' },
  { flag: 'P-gp inhibitor or substrate', guideline: 'FDA/EMA DDI guidance', action: 'Clinical DDI study with P-gp probe substrate (digoxin). In vitro Ki determination. Label P-gp DDI potential.', severity: 'medium' },
  { flag: 'CYP3A4/2D6/2C9 inhibitor', guideline: 'ICH M12 / FDA DDI guidance', action: 'In vitro: IC50 and/or Ki for reversible inhibition; inactivation kinetics (KI, kinact) for mechanism-based. Clinical DDI study with sensitive index substrate if R1 > 1.02.', severity: 'medium' },
  { flag: 'CYP2D6 substrate (PM/EM)', guideline: 'FDA PGx guidance', action: 'Pharmacogenomics testing in clinical trials. Label EM/PM exposure ratio. Contraindication or dose adjustment for PMs if TI is narrow.', severity: 'medium' },
  { flag: 'BBB penetration (CNS target)', guideline: 'ICH S7A', action: 'CNS safety pharmacology battery: Irwin test or FOB (functional observational battery). Seizure liability at supratherapeutic exposures.', severity: 'info' },
  { flag: 'Low solubility (BCS II/IV)', guideline: 'ICH M9 (BCS biowaiver)', action: 'Solubility-enabling formulation needed (amorphous dispersion, nanoparticle, lipid system). In vitro dissolution predictive of in vivo performance.', severity: 'info' },
  { flag: 'Skin sensitization flag', guideline: 'ICH S10 / REACH', action: 'DPRA, KeratinoSens, h-CLAT in vitro assays. In vivo LLNA if required by guideline. GHS Category 1 labeling if confirmed.', severity: 'medium' },
]

const projectIdNum = computed(() => parseInt(projectId))
useAIPageContext({
  pageType: 'ADMETDashboard',
  projectIdRef: projectIdNum,
  getEntity: () => ({ molecule_type: store.admetData?.molecule_type || "" }),
  applyFn: (s) => {
    // ADMET Dashboard is display-only; no form fields to apply
  },
})

onMounted(() => store.fetchADMETDashboard(projectId))
</script>

<template>
  <div class="admet-page">
    <PageHeader title="ADMET Dashboard">
      <template #subtitle>Computational predictions + experimental measurements · ICH safety flag integration</template>
      <template #actions>
        <span v-if="firstCompoundName" class="compound-badge">{{ firstCompoundName }}</span>
      </template>
    </PageHeader>

    <LoadingSpinner v-if="store.loading.admet" />

    <div v-else-if="store.admetData">
      <!-- Risk flag strip -->
      <div v-if="riskFlags.length" class="risk-strip">
        <span class="risk-strip-label">Risk flags:</span>
        <span
          v-for="f in riskFlags" :key="f.label"
          class="risk-badge"
          :style="{ background: severityBg[f.severity], color: severityColor[f.severity], borderColor: severityColor[f.severity] + '66' }"
          :title="f.desc"
        >{{ f.label }}</span>
      </div>

      <!-- Section nav -->
      <div class="section-nav">
        <button
          v-for="s in SECTIONS" :key="s.key"
          class="snav-btn"
          :class="{ 'snav-active': activeSection === s.key }"
          @click="activeSection = s.key"
        >{{ s.label }}</button>
      </div>

      <!-- ── Section: Physicochemical ───────────────────────────────────────── -->
      <div v-if="activeSection === 'physicochemical'" class="section-content">
        <div class="split-layout">
          <div class="split-main">
            <div class="section-card">
              <div class="card-hdr">Physicochemical Properties</div>
              <table class="sci-table">
                <thead>
                  <tr><th>Property</th><th>Value</th><th>Benchmark</th><th>Status</th><th>Guidance</th></tr>
                </thead>
                <tbody>
                  <tr v-for="r in physchemRows" :key="r.key">
                    <td class="prop-name">{{ r.label }}</td>
                    <td class="mono-val">{{ r.value != null ? (typeof r.value === 'number' ? r.value.toFixed(2) + (r.unit ? ' ' + r.unit : '') : r.value) : '—' }}</td>
                    <td class="bm-cell">{{ r.benchmark }}</td>
                    <td>
                      <span v-if="r.value != null" class="status-dot" :class="r.pass(r.value) ? 'dot-pass' : 'dot-flag'">
                        {{ r.pass(r.value) ? '✓' : '!' }}
                      </span>
                      <span v-else class="text-muted">—</span>
                    </td>
                    <td class="guidance-cell">{{ r.guidance }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="split-aside">
            <!-- Lipinski Ro5 -->
            <div class="section-card">
              <div class="card-hdr">Lipinski Rule of Five</div>
              <div v-if="lipinskiPass" class="ro5-grid">
                <div class="ro5-cell" :class="lipinskiPass.mw ? 'ro5-pass' : 'ro5-fail'">
                  <div class="ro5-label">MW ≤ 500</div>
                  <div class="ro5-verdict">{{ lipinskiPass.mw ? '✓' : '✗' }}</div>
                </div>
                <div class="ro5-cell" :class="lipinskiPass.logp ? 'ro5-pass' : 'ro5-fail'">
                  <div class="ro5-label">LogP ≤ 5</div>
                  <div class="ro5-verdict">{{ lipinskiPass.logp ? '✓' : '✗' }}</div>
                </div>
                <div class="ro5-cell" :class="lipinskiPass.hbd ? 'ro5-pass' : 'ro5-fail'">
                  <div class="ro5-label">HBD ≤ 5</div>
                  <div class="ro5-verdict">{{ lipinskiPass.hbd ? '✓' : '✗' }}</div>
                </div>
                <div class="ro5-cell" :class="lipinskiPass.hba ? 'ro5-pass' : 'ro5-fail'">
                  <div class="ro5-label">HBA ≤ 10</div>
                  <div class="ro5-verdict">{{ lipinskiPass.hba ? '✓' : '✗' }}</div>
                </div>
              </div>
              <div v-if="lipinskiPass" class="ro5-summary" :class="lipinskiPass.pass ? 'ro5-ok' : 'ro5-warn'">
                {{ lipinskiPass.pass ? '✓ Passes Ro5 — oral drug-likeness predicted' : '⚠ Violates ≥2 Lipinski rules — oral absorption risk' }}
              </div>
              <div v-else class="text-muted" style="font-size:13px;padding:12px">
                Physicochemical data not yet computed. Run compound ADMET from the Compound Profile page.
              </div>
            </div>

            <!-- BCS Classification -->
            <div class="section-card" style="margin-top:16px">
              <div class="card-hdr">BCS Classification (Predicted)</div>
              <div v-if="bcsClass" class="bcs-badge" :style="{ borderLeftColor: bcsClass.color }">
                <div class="bcs-class" :style="{ color: bcsClass.color }">{{ bcsClass.label }}</div>
                <div class="bcs-desc">{{ bcsClass.desc }}</div>
              </div>
              <div class="bcs-ref-table">
                <div class="bcs-row" v-for="c in [
                  { cls: 'I', sol: 'High', perm: 'High', note: 'Best oral absorption', color: '#16a34a' },
                  { cls: 'II', sol: 'Low', perm: 'High', note: 'Formulation-critical (ASD, nanoparticle)', color: '#d97706' },
                  { cls: 'III', sol: 'High', perm: 'Low', note: 'Permeation enhancers needed', color: '#2563eb' },
                  { cls: 'IV', sol: 'Low', perm: 'Low', note: 'Difficult oral delivery', color: '#dc2626' },
                ]" :key="c.cls">
                  <span class="bcs-cls-dot" :style="{ background: c.color }">{{ c.cls }}</span>
                  <span class="bcs-sol-perm">Sol: {{ c.sol }} / Perm: {{ c.perm }}</span>
                  <span class="bcs-note">{{ c.note }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Section: Absorption ─────────────────────────────────────────────── -->
      <div v-if="activeSection === 'absorption'" class="section-content">
        <div class="section-card">
          <div class="card-hdr">Absorption (A)</div>
          <p class="section-desc">Intestinal permeability, active transport, and oral bioavailability. Key determinants of dosing route and frequency.</p>
          <table class="sci-table">
            <thead><tr><th>Parameter</th><th>Value</th><th>Benchmark</th><th>Status</th><th>Scientific Context</th></tr></thead>
            <tbody>
              <tr v-for="r in fieldsForSection('absorption')" :key="r.key">
                <td class="prop-name">{{ r.label }} <span class="unit-tag">{{ r.unit }}</span></td>
                <td class="mono-val">{{ formatValue(r.value) }}</td>
                <td class="bm-cell">{{ r.benchmark }}</td>
                <td>
                  <span v-if="r.value != null" class="status-dot" :class="cellStatus(r, r.value) === 'pass' ? 'dot-pass' : cellStatus(r, r.value) === 'flag' ? 'dot-flag' : 'dot-neutral'">
                    {{ cellStatus(r, r.value) === 'pass' ? '✓' : cellStatus(r, r.value) === 'flag' ? '!' : '○' }}
                  </span>
                  <span v-else class="text-muted">—</span>
                </td>
                <td class="guidance-cell">{{ r.guidance }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ── Section: Distribution ──────────────────────────────────────────── -->
      <div v-if="activeSection === 'distribution'" class="section-content">
        <div class="section-card">
          <div class="card-hdr">Distribution (D)</div>
          <p class="section-desc">Blood-brain barrier penetration, plasma protein binding, and volume of distribution. Determines tissue exposure and free drug fraction.</p>
          <table class="sci-table">
            <thead><tr><th>Parameter</th><th>Value</th><th>Benchmark</th><th>Status</th><th>Scientific Context</th></tr></thead>
            <tbody>
              <tr v-for="r in fieldsForSection('distribution')" :key="r.key">
                <td class="prop-name">{{ r.label }} <span class="unit-tag">{{ r.unit }}</span></td>
                <td class="mono-val">{{ formatValue(r.value) }}</td>
                <td class="bm-cell">{{ r.benchmark }}</td>
                <td>
                  <span v-if="r.value != null" class="status-dot" :class="cellStatus(r, r.value) === 'pass' ? 'dot-pass' : cellStatus(r, r.value) === 'flag' ? 'dot-flag' : 'dot-neutral'">
                    {{ cellStatus(r, r.value) === 'pass' ? '✓' : cellStatus(r, r.value) === 'flag' ? '!' : '○' }}
                  </span>
                  <span v-else class="text-muted">—</span>
                </td>
                <td class="guidance-cell">{{ r.guidance }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ── Section: Metabolism ────────────────────────────────────────────── -->
      <div v-if="activeSection === 'metabolism'" class="section-content">
        <div class="split-layout">
          <div class="split-main">
            <div class="section-card">
              <div class="card-hdr">Metabolism (M) — CYP Enzyme Panel</div>
              <p class="section-desc">Cytochrome P450 inhibition and substrate profile. Predicts drug-drug interaction (DDI) liability and metabolic clearance route.</p>
              <table class="sci-table">
                <thead><tr><th>Enzyme / Role</th><th>Prediction</th><th>Clinical Relevance</th></tr></thead>
                <tbody>
                  <tr v-for="r in fieldsForSection('metabolism')" :key="r.key">
                    <td class="prop-name">{{ r.label }}</td>
                    <td>
                      <span v-if="r.value != null"
                        class="bool-badge"
                        :class="r.pass(r.value) ? 'bool-ok' : 'bool-flag'"
                      >{{ r.value ? 'Yes' : 'No' }}</span>
                      <span v-else class="text-muted">—</span>
                    </td>
                    <td class="guidance-cell">{{ r.guidance }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <div class="split-aside">
            <div class="section-card">
              <div class="card-hdr">CYP DDI Summary</div>
              <div class="cyp-summary">
                <div v-for="cyp in ['CYP1A2', 'CYP2C9', 'CYP2C19', 'CYP2D6', 'CYP3A4']" :key="cyp" class="cyp-row">
                  <span class="cyp-name">{{ cyp }}</span>
                  <span class="cyp-cell">
                    <span class="cyp-label">Inh</span>
                    <span :class="firstCompoundData?.[(cyp + '_inhibitor')] ? 'cyp-pos' : 'cyp-neg'">
                      {{ firstCompoundData?.[(cyp + '_inhibitor')] == null ? '—' : (firstCompoundData[(cyp + '_inhibitor')] ? '⚠ Yes' : '✓ No') }}
                    </span>
                  </span>
                  <span class="cyp-cell">
                    <span class="cyp-label">Sub</span>
                    <span :class="firstCompoundData?.[(cyp + '_substrate')] ? 'cyp-sub' : 'cyp-neg'">
                      {{ firstCompoundData?.[(cyp + '_substrate')] == null ? '—' : (firstCompoundData[(cyp + '_substrate')] ? 'Yes' : 'No') }}
                    </span>
                  </span>
                </div>
              </div>
              <div class="cyp-note">Inhibitor flag → clinical DDI study required per ICH M12 / FDA DDI guidance if R1 ≥ 1.02.</div>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Section: Excretion & Toxicity ─────────────────────────────────── -->
      <div v-if="activeSection === 'excretion_tox'" class="section-content">
        <div class="section-card">
          <div class="card-hdr">Excretion & Toxicity (E/T)</div>
          <p class="section-desc">Clearance, half-life, and safety flags. Positive toxicity signals require dedicated ICH safety studies before IND filing.</p>
          <table class="sci-table">
            <thead><tr><th>Parameter</th><th>Value</th><th>Benchmark</th><th>Status</th><th>Scientific Context</th></tr></thead>
            <tbody>
              <tr v-for="r in fieldsForSection('excretion_tox')" :key="r.key">
                <td class="prop-name">{{ r.label }} <span class="unit-tag">{{ r.unit }}</span></td>
                <td class="mono-val">{{ formatValue(r.value) }}</td>
                <td class="bm-cell">{{ r.benchmark }}</td>
                <td>
                  <span v-if="r.value != null" class="status-dot" :class="cellStatus(r, r.value) === 'pass' ? 'dot-pass' : cellStatus(r, r.value) === 'flag' ? 'dot-flag' : 'dot-neutral'">
                    {{ cellStatus(r, r.value) === 'pass' ? '✓' : cellStatus(r, r.value) === 'flag' ? '!' : '○' }}
                  </span>
                  <span v-else class="text-muted">—</span>
                </td>
                <td class="guidance-cell">{{ r.guidance }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ── Section: Experimental Data ────────────────────────────────────── -->
      <div v-if="activeSection === 'experimental'" class="section-content">
        <div class="section-card">
          <div class="card-hdr">Experimental ADMET Data (from Preclinical Studies)</div>
          <p class="section-desc">Measured values from logged preclinical studies. Experimental data overrides computational predictions for clinical decision-making.</p>
          <div v-if="experimentalData.length">
            <div v-for="exp in experimentalData" :key="exp.study_id" class="exp-study-card">
              <div class="exp-study-hdr">
                <span class="study-type-pill">{{ exp.study_type }}</span>
                <span class="exp-species">{{ exp.species }}</span>
                <span v-if="exp.mtd_mgkg" class="mtd-val">MTD: {{ exp.mtd_mgkg }} mg/kg</span>
              </div>
              <table class="sci-table" style="margin-top:8px">
                <tbody>
                  <tr v-for="(val, key) in exp.findings" :key="key">
                    <td class="prop-name">{{ key }}</td>
                    <td class="mono-val">{{ val }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <div v-else class="empty-section">
            <div class="empty-icon">&#128202;</div>
            <div class="empty-title">No experimental data logged</div>
            <div class="empty-sub">Add preclinical study results in the Study Planner and log key findings. Experimental values will appear here and are linked to the computational predictions above.</div>
          </div>
        </div>

        <!-- Computed ADMET raw summary -->
        <div v-if="Object.keys(store.admetData.computed_admet || {}).length === 0" class="section-card" style="margin-top:16px">
          <div class="card-hdr">Computed ADMET Status</div>
          <div class="empty-section">
            <div class="empty-title">No computed ADMET data available</div>
            <div class="empty-sub">Navigate to the Compound Profile page and click "Run ADMET" to generate pkCSM predictions. Data will appear in all sections of this dashboard.</div>
          </div>
        </div>
      </div>

      <!-- ── Section: Regulatory Context ───────────────────────────────────── -->
      <div v-if="activeSection === 'context'" class="section-content">
        <div class="section-card">
          <div class="card-hdr">ADMET Flag → Required ICH Study Mapping</div>
          <p class="section-desc">Use this reference to plan the safety/regulatory studies triggered by ADMET predictions. Flags in red indicate high-priority studies typically required before first-in-human dosing.</p>
          <table class="sci-table ich-context-table">
            <thead>
              <tr><th>ADMET Flag</th><th>ICH / Regulatory Guideline</th><th>Required Action</th></tr>
            </thead>
            <tbody>
              <tr v-for="row in ICH_ADMET_CONTEXT" :key="row.flag">
                <td>
                  <span class="ich-flag-badge" :style="{ background: severityBg[row.severity], color: severityColor[row.severity], borderColor: severityColor[row.severity] + '66' }">
                    {{ row.flag }}
                  </span>
                </td>
                <td class="guideline-cell">{{ row.guideline }}</td>
                <td class="action-cell">{{ row.action }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="section-card" style="margin-top:16px">
          <div class="card-hdr">ICH Safety Study Order — IND Enabling Package</div>
          <div class="ind-sequence">
            <div class="ind-step" v-for="step in [
              { num: 1, title: 'Safety Pharmacology Core Battery', guideline: 'ICH S7A/S7B', items: ['hERG (in vitro, before IND)', 'CNS Irwin test / FOB (rat)', 'Cardiovascular (in vivo telemetry, non-rodent)', 'Respiratory function'] },
              { num: 2, title: 'Genotoxicity Core Battery', guideline: 'ICH S2(R1)', items: ['Ames test (Salmonella + E. coli)', 'In vitro mammalian cell test (MLA or CHO CA)', 'In vivo micronucleus (rodent bone marrow)'] },
              { num: 3, title: 'Single-Dose Acute Toxicity', guideline: 'ICH M3(R2)', items: ['Dose range finding in rodent (and non-rodent if needed)', 'Identify MTD and dose-limiting signs', 'Guides repeat-dose starting dose'] },
              { num: 4, title: 'Repeat-Dose Toxicity (IND-enabling)', guideline: 'ICH S4 / M3(R2)', items: ['2-week GLP rat (covers 14-day clinical trials)', '2-week GLP non-rodent dog or monkey (for ≥2 week trials)', 'TK (toxicokinetics) at each dose level'] },
              { num: 5, title: 'Reproductive / Developmental Tox', guideline: 'ICH S5(R3)', items: ['DART assessment for Phase II/III enrollment of WOCBP', 'Male fertility assessment (ICH S5)', 'Embryo-fetal development (EFD) study'] },
            ]" :key="step.num">
              <div class="ind-num">{{ step.num }}</div>
              <div class="ind-body">
                <div class="ind-title">{{ step.title }} <span class="ind-guideline">{{ step.guideline }}</span></div>
                <ul class="ind-items">
                  <li v-for="item in step.items" :key="item">{{ item }}</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="empty-page">
      <div class="empty-icon">&#9876;</div>
      <div class="empty-title">No ADMET data available</div>
      <div class="empty-sub">Go to the Compound Profile page, select the project compound, and click "Run ADMET" to generate pkCSM predictions. Results will populate all sections of this dashboard.</div>
    </div>
  </div>
</template>

<style scoped>
.admet-page { padding-bottom: 60px; }

/* Risk strip */
.risk-strip {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 10px 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  margin-bottom: 16px;
}
.risk-strip-label { font-size: 12px; font-weight: 600; color: #dc2626; text-transform: uppercase; letter-spacing: 0.05em; }
.risk-badge {
  padding: 3px 10px;
  border-radius: 4px;
  border: 1px solid;
  font-size: 12px;
  font-weight: 600;
  cursor: default;
}

/* Section nav */
.section-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 20px;
  border-bottom: 2px solid #e5e7eb;
  padding-bottom: 0;
}
.snav-btn {
  padding: 9px 18px;
  border: none;
  background: none;
  font-size: 13px;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: color 0.15s;
}
.snav-btn:hover { color: #2563eb; }
.snav-active { color: #2563eb; border-bottom-color: #2563eb; }

.section-content { animation: fadeIn .15s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }

.section-desc { font-size: 13px; color: #6b7280; margin: 0 0 16px; line-height: 1.5; }

.split-layout { display: grid; grid-template-columns: 1fr 300px; gap: 20px; align-items: start; }
.split-main {}
.split-aside {}

/* Cards */
.section-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
}
.card-hdr {
  font-size: 14px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 14px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f3f4f6;
}

/* Sci table */
.sci-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.sci-table thead tr { background: #f9fafb; border-bottom: 2px solid #e5e7eb; }
.sci-table th { padding: 9px 12px; text-align: left; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: #6b7280; white-space: nowrap; }
.sci-table td { padding: 9px 12px; border-bottom: 1px solid #f3f4f6; vertical-align: top; }
.sci-table tbody tr:hover { background: #f9fafb; }
.sci-table tbody tr:last-child td { border-bottom: none; }

.prop-name { font-weight: 500; color: #374151; min-width: 180px; }
.unit-tag { font-size: 11px; color: #9ca3af; font-weight: 400; margin-left: 4px; }
.mono-val { font-family: 'SF Mono', 'Fira Code', monospace; font-size: 12px; color: #111827; min-width: 100px; }
.bm-cell { font-size: 12px; color: #6b7280; min-width: 160px; }
.guidance-cell { font-size: 11px; color: #6b7280; line-height: 1.4; max-width: 350px; }

/* Status dot */
.status-dot {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  font-size: 11px;
  font-weight: 700;
}
.dot-pass { background: #dcfce7; color: #16a34a; }
.dot-flag { background: #fee2e2; color: #dc2626; }
.dot-neutral { background: #f3f4f6; color: #6b7280; }

/* Bool badge */
.bool-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}
.bool-ok { background: #dcfce7; color: #16a34a; }
.bool-flag { background: #fee2e2; color: #dc2626; }

/* Lipinski Ro5 */
.ro5-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px; }
.ro5-cell { padding: 10px 12px; border-radius: 6px; }
.ro5-pass { background: #f0fdf4; border: 1px solid #bbf7d0; }
.ro5-fail { background: #fef2f2; border: 1px solid #fecaca; }
.ro5-label { font-size: 11px; color: #6b7280; }
.ro5-verdict { font-size: 20px; font-weight: 700; margin-top: 2px; }
.ro5-pass .ro5-verdict { color: #16a34a; }
.ro5-fail .ro5-verdict { color: #dc2626; }
.ro5-summary { padding: 8px 12px; border-radius: 6px; font-size: 13px; font-weight: 500; }
.ro5-ok { background: #f0fdf4; color: #15803d; }
.ro5-warn { background: #fffbeb; color: #92400e; }

/* BCS */
.bcs-badge { padding: 10px 14px; border-left: 4px solid; border-radius: 4px; background: #f9fafb; margin-bottom: 14px; }
.bcs-class { font-size: 16px; font-weight: 700; margin-bottom: 4px; }
.bcs-desc { font-size: 12px; color: #6b7280; line-height: 1.4; }
.bcs-ref-table { display: flex; flex-direction: column; gap: 6px; }
.bcs-row { display: flex; align-items: center; gap: 10px; font-size: 12px; }
.bcs-cls-dot { width: 22px; height: 22px; border-radius: 50%; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 12px; flex-shrink: 0; }
.bcs-sol-perm { color: #374151; font-weight: 500; min-width: 130px; }
.bcs-note { color: #6b7280; }

/* CYP summary */
.cyp-summary { display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px; }
.cyp-row { display: flex; align-items: center; gap: 12px; padding: 6px 10px; background: #f9fafb; border-radius: 4px; }
.cyp-name { font-size: 12px; font-weight: 700; color: #374151; width: 65px; }
.cyp-cell { display: flex; align-items: center; gap: 6px; }
.cyp-label { font-size: 10px; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.05em; }
.cyp-pos { font-size: 12px; color: #dc2626; font-weight: 600; }
.cyp-neg { font-size: 12px; color: #16a34a; font-weight: 600; }
.cyp-sub { font-size: 12px; color: #d97706; font-weight: 600; }
.cyp-note { font-size: 11px; color: #6b7280; background: #fffbeb; padding: 8px 12px; border-radius: 4px; border-left: 3px solid #fbbf24; }

/* ICH context table */
.ich-context-table .ich-flag-badge { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; border: 1px solid; }
.ich-context-table .guideline-cell { font-size: 12px; color: #2563eb; font-weight: 500; white-space: nowrap; }
.ich-context-table .action-cell { font-size: 12px; color: #374151; line-height: 1.4; }

/* IND sequence */
.ind-sequence { display: flex; flex-direction: column; gap: 0; }
.ind-step { display: flex; gap: 16px; padding: 16px 0; border-bottom: 1px solid #f3f4f6; }
.ind-step:last-child { border-bottom: none; }
.ind-num { width: 28px; height: 28px; background: #2563eb; color: #fff; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; flex-shrink: 0; margin-top: 2px; }
.ind-body { flex: 1; }
.ind-title { font-size: 13px; font-weight: 600; color: #111827; margin-bottom: 6px; }
.ind-guideline { font-size: 11px; font-weight: 500; color: #2563eb; margin-left: 8px; background: #eff6ff; padding: 1px 6px; border-radius: 3px; }
.ind-items { margin: 0; padding-left: 18px; }
.ind-items li { font-size: 12px; color: #6b7280; margin-bottom: 3px; line-height: 1.4; }

/* Experimental data */
.exp-study-card { border: 1px solid #e5e7eb; border-radius: 6px; padding: 14px; margin-bottom: 12px; }
.exp-study-hdr { display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }
.study-type-pill { background: #eff6ff; color: #1d4ed8; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }
.exp-species { font-size: 12px; color: #6b7280; }
.mtd-val { font-size: 12px; font-weight: 600; color: #d97706; margin-left: auto; }

/* Empty */
.empty-page { text-align: center; padding: 80px 20px; }
.empty-section { text-align: center; padding: 40px 20px; }
.empty-icon { font-size: 40px; margin-bottom: 12px; }
.empty-title { font-size: 16px; font-weight: 600; color: #374151; margin-bottom: 6px; }
.empty-sub { font-size: 13px; color: #6b7280; max-width: 480px; margin: 0 auto; line-height: 1.5; }

/* Header compound badge */
.compound-badge { background: #f3f4f6; color: #374151; padding: 4px 12px; border-radius: 4px; font-size: 13px; font-weight: 500; }
.text-muted { color: #9ca3af; }
</style>
