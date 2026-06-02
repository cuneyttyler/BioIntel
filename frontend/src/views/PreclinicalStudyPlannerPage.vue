<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '@/components/layout/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { usePreclinicalStore } from '@/stores/preclinical'

const route = useRoute()
const projectId = route.params.id
const store = usePreclinicalStore()

// ─── Constants ────────────────────────────────────────────────────────────────

const STUDY_TYPES = [
  { value: 'acute_tox',         label: 'Acute Toxicology',          group: 'Toxicology' },
  { value: 'repeat_dose_tox',   label: 'Repeat-Dose Toxicology',    group: 'Toxicology' },
  { value: 'genotoxicity',      label: 'Genotoxicity',              group: 'Toxicology' },
  { value: 'reproductive_tox',  label: 'Reproductive Toxicology',   group: 'Toxicology' },
  { value: 'safety_pharmacology', label: 'Safety Pharmacology',     group: 'Safety' },
  { value: 'pk',                label: 'Pharmacokinetics',          group: 'PK/ADME' },
  { value: 'adme',              label: 'ADME',                      group: 'PK/ADME' },
  { value: 'efficacy',          label: 'Efficacy (In Vivo)',        group: 'Efficacy' },
]

const SPECIES_OPTIONS = ['rat', 'mouse', 'dog', 'monkey', 'rabbit', 'guinea_pig', 'minipig', 'in_vitro', 'other']
const ROUTE_OPTIONS   = ['oral', 'intravenous', 'subcutaneous', 'intraperitoneal', 'intramuscular', 'inhalation', 'dermal', 'in_vitro', 'other']

const STUDY_PRESETS = {
  acute_tox: [
    {
      label: 'ICH M3(R2) Limit Test — Rat PO',
      title: 'Single-Dose Acute Oral Toxicology — Rat (Limit Test)',
      species: 'rat', dose_route: 'oral', dose_levels: [2000],
      duration_days: 14, glp: true,
      objective: 'Determine acute oral toxicity in rat at the ICH M3(R2) limit dose (2000 mg/kg). Identify clinical signs, body weight effects, and gross pathological findings to characterise the acute hazard and support IND filing.',
      primary_endpoints: [
        'Clinical observation score (0.5h, 1h, 2h, 4h, 8h, 24h, then daily to Day 14)',
        'Body weight (Day 0, 7, 14)',
        'Mortality / morbidity criteria',
        'Gross necropsy at scheduled sacrifice (Day 14) or at death',
      ],
      success_criteria: 'No mortality at 2000 mg/kg limit dose. Document all reversible clinical signs for Phase 1 briefing document.',
    },
    {
      label: 'Dose-Range Finding — Mouse IP',
      title: 'Single-Dose Acute Toxicology — Mouse (MTD Estimation)',
      species: 'mouse', dose_route: 'intraperitoneal', dose_levels: [100, 300, 1000, 2000],
      duration_days: 14, glp: false,
      objective: 'Estimate maximum tolerated dose (MTD) in mouse via dose-escalation to guide starting dose selection for 28-day repeat-dose studies.',
      primary_endpoints: [
        'Clinical signs throughout 14-day observation',
        'Body weight change (%)',
        'Mortality / moribund sacrifice',
        'Macroscopic findings at scheduled necropsy',
      ],
      success_criteria: 'Establish MTD and approximate NOAEL for repeat-dose dose selection.',
    },
  ],
  repeat_dose_tox: [
    {
      label: 'IND-Enabling 28-Day GLP — Rat PO',
      title: '28-Day Repeat-Dose Oral Toxicology — Sprague-Dawley Rat (GLP)',
      species: 'rat', dose_route: 'oral', dose_levels: [10, 30, 100],
      duration_days: 28, glp: true,
      objective: 'Characterise systemic toxicity of daily oral dosing in rat for 28 days with 14-day recovery per ICH M3(R2). Required to support Phase 1 single-ascending dose clinical study.',
      primary_endpoints: [
        'Clinical signs (daily)',
        'Body weight and food consumption (weekly)',
        'Clinical pathology — haematology, serum biochemistry, urinalysis (Weeks 1, 4, recovery)',
        'Organ weights at terminal necropsy (liver, kidney, heart, lung, brain, adrenals, spleen, thymus, gonads)',
        'Histopathology — full panel on control and high-dose; target organs all groups',
        'Toxicokinetics (Day 1 and Day 28, satellite animals)',
      ],
      success_criteria: 'NOAEL ≥10× clinical AUC (human equivalent dose). No irreversible histopathological findings at NOAEL.',
    },
    {
      label: 'IND-Enabling 28-Day GLP — Dog PO',
      title: '28-Day Repeat-Dose Oral Toxicology — Beagle Dog (GLP)',
      species: 'dog', dose_route: 'oral', dose_levels: [3, 10, 30],
      duration_days: 28, glp: true,
      objective: 'Second-species 28-day GLP toxicology study in beagle dog per ICH M3(R2). Required alongside rat study for Phase 1 IND package.',
      primary_endpoints: [
        'Clinical signs (daily)',
        'Body weight, food consumption (weekly)',
        'Ophthalmic examination (pre-study, Week 4)',
        'ECG (12-lead, pre-study and Week 4)',
        'Clinical pathology (haematology, biochemistry, urinalysis)',
        'Organ weights + histopathology at necropsy',
        'Toxicokinetics (Day 1 and Day 28)',
      ],
      success_criteria: 'NOAEL established. Safety margin ≥5× AUC at HNSTD relative to intended Phase 1 starting dose.',
    },
    {
      label: 'Phase 2-Enabling 90-Day GLP — Rat PO',
      title: '90-Day Repeat-Dose Oral Toxicology — Rat (GLP)',
      species: 'rat', dose_route: 'oral', dose_levels: [10, 30, 100],
      duration_days: 90, glp: true,
      objective: 'Support 3-month clinical dosing in Phase 2 per ICH M3(R2) Table 1. Extends NOAEL characterisation and identifies chronic-exposure target organs.',
      primary_endpoints: [
        'Clinical signs (daily), body weight / food consumption (weekly)',
        'Ophthalmology (baseline, Week 13)',
        'Neurobehavioural Irwin screen (Weeks 1, 6, 13)',
        'Clinical pathology (Weeks 4, 13, recovery)',
        'Full organ weight and histopathology at necropsy',
        'Toxicokinetics (Day 1, Day 45, Day 90)',
      ],
      success_criteria: 'NOAEL establishes ≥10× safety margin to Phase 2 exposure. No irreversible findings at doses supporting clinical progression.',
    },
  ],
  genotoxicity: [
    {
      label: 'ICH S2(R1) Ames Test — In Vitro Bacterial',
      title: 'Bacterial Reverse Mutation Assay (Ames Test)',
      species: 'in_vitro', dose_route: 'in_vitro', dose_levels: [],
      duration_days: 5, glp: true,
      objective: 'Assess mutagenic potential in five Salmonella typhimurium / E. coli strains ±S9 per ICH S2(R1). First element of standard two-assay genotoxicity battery required for IND.',
      primary_endpoints: [
        'Revertant colony counts in TA98, TA100, TA1535, TA1537, WP2uvrA',
        '±S9 metabolic activation (Aroclor 1254-induced rat liver)',
        'Cytotoxicity assessment at each concentration',
        'Positive and negative control responses within lab historical range',
      ],
      success_criteria: 'Negative: ≤2× spontaneous revertant background in all strains. If positive, in vivo follow-up per ICH S2(R1) Section 3.4 required.',
    },
    {
      label: 'ICH S2(R1) In Vitro Micronucleus — TK6 Cells',
      title: 'In Vitro Micronucleus Test — Human TK6 Lymphoblastoid Cells',
      species: 'in_vitro', dose_route: 'in_vitro', dose_levels: [],
      duration_days: 3, glp: true,
      objective: 'Detect clastogenic and aneugenic activity in TK6 cells ±S9 per ICH S2(R1). Second element of standard battery; replaces chromosome aberration assay in modern submissions.',
      primary_endpoints: [
        'Micronucleus frequency in 2000 binucleate cells (cytochalasin B block)',
        'Cytotoxicity: CBPI ≥55% or viability ≥45% at scored concentration',
        'Short (3h+S9, 3h-S9) and continuous (24h-S9) treatment conditions',
      ],
      success_criteria: 'Negative: MN frequency not statistically or biologically significantly elevated versus vehicle control.',
    },
    {
      label: 'ICH S2(R1) In Vivo Rat Bone Marrow Micronucleus',
      title: 'In Vivo Micronucleus — Rat Bone Marrow Erythrocytes',
      species: 'rat', dose_route: 'oral', dose_levels: [500, 1000, 2000],
      duration_days: 3, glp: true,
      objective: 'In vivo confirmation of clastogenicity / aneugenicity in rat bone marrow. Required when in vitro assays are positive or equivocal, or combined with 28-day tox via integration approach.',
      primary_endpoints: [
        'Micronucleated polychromatic erythrocytes (MNPCE) per 2000 PCE',
        'PCE/(PCE+NCE) ratio — indicator of bone marrow toxicity',
        'Sampling at 24h and 48h post-final dose',
      ],
      success_criteria: 'MNPCE frequency within historical negative control range. PCE ratio >20% of vehicle control confirming bone marrow exposure.',
    },
  ],
  safety_pharmacology: [
    {
      label: 'ICH S7A CNS Core Battery — Irwin/FOB Rat',
      title: 'CNS Safety Pharmacology — Irwin Modified Observational Screen (Rat)',
      species: 'rat', dose_route: 'oral', dose_levels: [30, 100, 300],
      duration_days: 1, glp: true,
      objective: 'Evaluate CNS effects at single oral doses per ICH S7A core battery. Screen for motor, sensory, autonomic, and behavioural effects; assess seizure and sedation potential.',
      primary_endpoints: [
        'Modified Irwin / FOB score (grip strength, pain reflexes, body temperature, muscle tone, autonomic signs)',
        'Spontaneous locomotor activity (actimeter, 0–30 min post-dose)',
        'Body temperature (rectal) at 1h, 4h',
        'Clinical observations at 0.5, 1, 2, 4, 8, 24h post-dose',
      ],
      success_criteria: 'No adverse CNS effects (≥50% decrease in locomotor activity, seizure, sedation) at exposures ≥10× Cmax of intended clinical dose.',
    },
    {
      label: 'ICH S7B hERG Patch Clamp — In Vitro',
      title: 'hERG Channel Inhibition — Manual Whole-Cell Patch Clamp',
      species: 'in_vitro', dose_route: 'in_vitro', dose_levels: [],
      duration_days: 1, glp: false,
      objective: 'Quantify IKr inhibitory potency (IC50) at hERG channel per ICH S7B. Informs cardiac safety risk category and guides design of in vivo cardiovascular telemetry study.',
      primary_endpoints: [
        'IC50 for IKr tail current inhibition (6–8 concentrations)',
        'Concentration-response curve with Hill coefficient',
        'Comparison vs. positive control (cisapride or dofetilide)',
      ],
      success_criteria: 'IC50 >30× free Cmax (low risk). IC50 3–30× Cmax (medium risk — in vivo CV study and risk assessment required). <3× (high risk — likely program stopper).',
    },
    {
      label: 'ICH S7A Cardiovascular Telemetry — Conscious Dog',
      title: 'Cardiovascular Safety Pharmacology — Telemetry (Conscious Beagle Dog)',
      species: 'dog', dose_route: 'oral', dose_levels: [3, 10, 30],
      duration_days: 1, glp: true,
      objective: 'Assess cardiovascular effects on blood pressure, heart rate, and QTc per ICH S7A core battery. In vivo telemetry in conscious dog is the GLP-quality CV safety study required for IND.',
      primary_endpoints: [
        'Blood pressure (systolic, diastolic, MAP) — continuous telemetry, 24h',
        'Heart rate — continuous telemetry',
        'ECG intervals: PR, QRS, QT, QTcF, QTcB — continuous',
        'Clinical observations throughout',
      ],
      success_criteria: 'No QTcF prolongation >20 ms at any dose. No adverse BP or HR effects at ≥3× clinical free Cmax.',
    },
    {
      label: 'ICH S7A Respiratory — Whole-Body Plethysmography Rat',
      title: 'Respiratory Safety Pharmacology — Whole-Body Plethysmography (Rat)',
      species: 'rat', dose_route: 'oral', dose_levels: [30, 100, 300],
      duration_days: 1, glp: true,
      objective: 'Assess respiratory function per ICH S7A core battery. Required for IND package alongside CNS and CV studies.',
      primary_endpoints: [
        'Respiratory rate (breaths/min)',
        'Tidal volume (mL/breath)',
        'Minute volume (L/min)',
        'SpO₂ (pulse oximetry if equipped)',
      ],
      success_criteria: 'No biologically significant changes (>15% shift from baseline) at doses providing ≥10× clinical Cmax.',
    },
  ],
  pk: [
    {
      label: 'Single-Dose IV/PO Crossover — Rat',
      title: 'Pharmacokinetic Profile and Oral Bioavailability — Rat (IV/PO)',
      species: 'rat', dose_route: 'oral', dose_levels: [10],
      duration_days: 1, glp: false,
      objective: 'Determine absolute oral bioavailability (F%), Cmax, Tmax, AUC, t½, Vd, and CL in rat. Cassette IV arm (1 mg/kg, iv) paired with oral arm (10 mg/kg, po).',
      primary_endpoints: [
        'Cmax (ng/mL) and Tmax (h)',
        'AUC0–t and AUC0–∞ (ng·h/mL)',
        'Terminal t½ (h)',
        'Volume of distribution Vd (L/kg) and clearance CL (mL/min/kg)',
        'F% = (AUCpo / AUCiv) × (Doseiv / Dosepo) × 100',
      ],
      success_criteria: 'F% ≥20% for an oral programme. AUC0–24h ≥3× in vitro IC50 (target-based) to support POC efficacy study design.',
    },
    {
      label: 'Dose-Proportionality — Rat',
      title: 'Dose-Proportionality and Saturation Assessment — Rat (Oral)',
      species: 'rat', dose_route: 'oral', dose_levels: [10, 30, 100, 300],
      duration_days: 1, glp: false,
      objective: 'Assess linearity of AUC and Cmax across the dose range to be used in toxicology studies. Identify absorption saturation and support dose selection for repeat-dose studies.',
      primary_endpoints: [
        'AUC0–t per dose group',
        'Cmax per dose group',
        'Power model analysis — slope β (dose-proportional = 0.85–1.15)',
        'Bioavailability estimate at each dose',
      ],
      success_criteria: 'Dose-proportional (β coefficient 0.85–1.15) or deviation characterised for PK/PD modelling.',
    },
    {
      label: 'Toxicokinetics Satellite — 28-Day Study',
      title: 'Toxicokinetics — Satellite Arms (28-Day Repeat-Dose)',
      species: 'rat', dose_route: 'oral', dose_levels: [10, 30, 100],
      duration_days: 28, glp: true,
      objective: 'Characterise systemic exposure (AUC, Cmax) on Days 1 and 28 in satellite TK groups. Determine accumulation ratio and confirm linear dose-exposure relationship for margin calculations.',
      primary_endpoints: [
        'Cmax and AUC0–24h on Day 1 and Day 28 per dose group',
        'Accumulation ratio R = AUCDay28 / AUCDay1',
        'Linearity index across dose groups',
        'Sex differences (male / female satellite arms)',
      ],
      success_criteria: 'Accumulation ratio ≤5. Confirm ≥10× AUC safety margin at NOAEL vs. intended clinical AUC.',
    },
  ],
  adme: [
    {
      label: 'In Vitro ADME Standard Panel',
      title: 'In Vitro ADME Profiling — Standard IND-Enabling Panel',
      species: 'in_vitro', dose_route: 'in_vitro', dose_levels: [],
      duration_days: 10, glp: false,
      objective: 'Comprehensive in vitro ADME characterisation to predict human PK liabilities and inform toxicology study design. Panel should be completed before GLP tox start.',
      primary_endpoints: [
        'Kinetic solubility (FaSSIF/FeSSIF, PBS pH 7.4)',
        'Caco-2 permeability: Papp A→B, B→A, efflux ratio ±GF120918',
        'Human liver microsome (HLM) t½ and CLint; rat liver microsome (RLM) for cross-species comparison',
        'Plasma protein binding fu,p — rat, dog, human (rapid equilibrium dialysis)',
        'CYP reaction phenotyping (CYP1A2, 2C9, 2C19, 2D6, 3A4) — fraction metabolised (fm)',
        'CYP inhibition IC50 (reversible) + time-dependent inhibition screen',
        'P-gp / BCRP substrate assessment (Caco-2 ± elacridar)',
        'Plasma stability and blood:plasma ratio',
      ],
      success_criteria: 'HLM CLint <20 µL/min/mg (low clearance). fu,p >1%. No TDI. P-gp efflux ratio <2 (or characterised for CNS programmes, target <1).',
    },
    {
      label: 'In Vivo Mass Balance — [¹⁴C] Rat',
      title: 'In Vivo ADME Mass Balance — [¹⁴C]-Radiolabelled Rat',
      species: 'rat', dose_route: 'oral', dose_levels: [10],
      duration_days: 7, glp: false,
      objective: 'Determine routes of excretion, complete mass balance, and identify major circulating metabolites using [¹⁴C]-labelled compound. Required for NDA/MAA filing; recommended to start pre-Phase 2.',
      primary_endpoints: [
        '% dose recovered in urine, faeces, cage rinse (cumulative 0–168h)',
        'Blood and plasma radioactivity AUC, Cmax, t½ for total [¹⁴C]',
        'Plasma metabolite profiling (HPLC-radiodetection + LC-MS/MS structural characterisation)',
        'Whole-body autoradiography (QWBA) for tissue distribution',
        'Identification and quantification of all circulating metabolites >10% of total AUC',
      ],
      success_criteria: '≥90% mass balance recovery. All metabolites >10% AUC identified; safety covered by tox species or separate bridging toxicology as required by ICH M3(R2)/M7.',
    },
  ],
  efficacy: [
    {
      label: 'Proof-of-Concept — Rodent Disease Model',
      title: 'In Vivo Efficacy — Rodent Disease Model (POC)',
      species: 'mouse', dose_route: 'oral', dose_levels: [10, 30, 100],
      duration_days: 21, glp: false,
      objective: 'Establish proof-of-concept efficacy in pharmacologically validated disease model. Determine minimal effective dose (MED) and characterise dose-response for translational dose projection to first-in-human.',
      primary_endpoints: [
        'Primary pharmacodynamic endpoint (disease model-specific, e.g. tumour volume, disease score, biomarker)',
        'Exposure-response correlation (PK/PD) — PK satellite arms',
        'Body weight, clinical health score throughout',
        'Secondary biomarker panel (mechanistic confirmation of target engagement)',
      ],
      success_criteria: 'Statistically significant primary endpoint effect (p<0.05 vs. vehicle) at ≥1 dose level. MED established for PK/PD modelling.',
    },
    {
      label: 'Dose-Response Efficacy — Chronic Model',
      title: 'Dose-Response and ED₅₀ — Chronic Disease Model',
      species: 'rat', dose_route: 'oral', dose_levels: [3, 10, 30, 100],
      duration_days: 56, glp: false,
      objective: 'Establish full dose-response relationship and ED₅₀ for PK/PD modelling and clinical dose projection. Supports Target Product Profile therapeutic window definition.',
      primary_endpoints: [
        'Primary endpoint AUC over 8 weeks',
        'Secondary mechanistic biomarker panel',
        'PK sampling per dose group (Day 1 and Day 56)',
        'Emax / sigmoid-Emax PK/PD modelling',
      ],
      success_criteria: 'ED₅₀ established with ≥3-point dose-response. Predicted human efficacious dose provides ≥5× safety margin over NOAEL-derived HED.',
    },
  ],
  reproductive_tox: [
    {
      label: 'ICH S5(R3) Fertility & Early Embryonic Dev — Rat',
      title: 'Fertility and Early Embryonic Development — Rat (ICH S5(R3) Segment I)',
      species: 'rat', dose_route: 'oral', dose_levels: [30, 100, 300],
      duration_days: 70, glp: true,
      objective: 'Assess effects on male and female fertility, mating behaviour, pre-implantation loss, and early embryo viability per ICH S5(R3). Required pre-Phase 3 for drugs used in women of childbearing potential.',
      primary_endpoints: [
        'Mating index, fertility index, conception rate',
        'Sperm parameters: count, motility, morphology (males — 10-week treatment)',
        'Estrous cycle normality (females — 2-week pre-mating)',
        'Implantation sites, corpora lutea counts',
        'Pre- and post-implantation loss rates',
      ],
      success_criteria: 'NOAEL established for reproductive parameters. No adverse effect on fertility or early embryo development at NOAEL.',
    },
    {
      label: 'ICH S5(R3) Embryo-Fetal Development — Rat',
      title: 'Embryo-Fetal Development Study — Rat (ICH S5(R3) Segment II)',
      species: 'rat', dose_route: 'oral', dose_levels: [30, 100, 300],
      duration_days: 17, glp: true,
      objective: 'Determine teratogenic potential and embryo-fetal toxicity during organogenesis (GD 6–17) per ICH S5(R3). Required in both rat and rabbit before Phase 3 in women of childbearing potential.',
      primary_endpoints: [
        'Maternal body weight, food consumption, clinical signs (GD 0, 6, 9, 12, 15, 17, 20)',
        'Litter parameters: resorptions, live fetuses, sex ratio',
        'Fetal body weight (male/female)',
        'External, visceral, and skeletal fetal examination',
      ],
      success_criteria: 'No treatment-related malformations or variations at any dose. Establish developmental NOAEL and maternal NOAEL separately.',
    },
  ],
}

const IND_PACKAGE = [
  {
    category: 'Safety Pharmacology',
    guideline: 'ICH S7A/S7B',
    note: 'Core battery (CNS, CV, respiratory) required before first-in-human.',
    studies: [
      { key: 'sp_cns',    label: 'CNS core battery (Irwin/FOB)',              required: true },
      { key: 'sp_herg',   label: 'hERG channel inhibition (in vitro)',        required: true },
      { key: 'sp_cv',     label: 'Cardiovascular telemetry (in vivo, dog)',   required: true },
      { key: 'sp_resp',   label: 'Respiratory function (plethysmography)',    required: true },
      { key: 'sp_gi',     label: 'GI motility / gastric emptying',            required: false },
      { key: 'sp_renal',  label: 'Renal function (urine parameters)',         required: false },
    ],
  },
  {
    category: 'Genotoxicity',
    guideline: 'ICH S2(R1)',
    note: 'Standard two-assay battery. In vivo study required if in vitro positive.',
    studies: [
      { key: 'geno_ames',     label: 'Ames test (bacterial reverse mutation)',                  required: true },
      { key: 'geno_mn_vitro', label: 'In vitro micronucleus or chromosome aberration',         required: true },
      { key: 'geno_mn_vivo',  label: 'In vivo micronucleus (if in vitro positive/equivocal)',  required: false },
    ],
  },
  {
    category: 'Acute / Single-Dose Toxicology',
    guideline: 'ICH M3(R2)',
    note: 'Dose-range finding in rodent to guide repeat-dose design.',
    studies: [
      { key: 'tox_acute_rodent',    label: 'Acute tox — rodent (DRF / limit test)', required: true },
      { key: 'tox_acute_nonrodent', label: 'Acute tox — non-rodent',                required: false },
    ],
  },
  {
    category: 'Repeat-Dose Toxicology',
    guideline: 'ICH M3(R2)',
    note: '28-day GLP in two species required for Phase 1. 90-day for Phase 2 (3-month dosing).',
    studies: [
      { key: 'tox_28d_rat',   label: '28-day GLP repeat-dose — rat (PO)',   required: true },
      { key: 'tox_28d_dog',   label: '28-day GLP repeat-dose — dog (PO)',   required: true },
      { key: 'tox_90d_rat',   label: '90-day GLP repeat-dose — rat',        required: false },
      { key: 'tox_90d_dog',   label: '90-day GLP repeat-dose — dog',        required: false },
    ],
  },
  {
    category: 'Pharmacokinetics & ADME',
    guideline: 'ICH M3(R2)',
    note: 'PK and TK data required to calculate safety margins and support dose selection.',
    studies: [
      { key: 'pk_rat',         label: 'Single-dose PK — rat (IV + PO)',         required: true },
      { key: 'pk_dog',         label: 'Single-dose PK — dog or non-rodent',     required: true },
      { key: 'adme_invitro',   label: 'In vitro ADME panel (stability, PPB, CYP)', required: true },
      { key: 'adme_massbal',   label: '[¹⁴C] mass balance (pre-NDA)',           required: false },
    ],
  },
  {
    category: 'Reproductive Toxicology',
    guideline: 'ICH S5(R3)',
    note: 'Fertility Seg I required before Phase 3. EFD (Seg II) rat + rabbit required before Phase 3 for WOCBP.',
    studies: [
      { key: 'repro_fertility',   label: 'Fertility & early embryonic dev. — rat (Seg I)', required: false },
      { key: 'repro_efd_rat',     label: 'Embryo-fetal development — rat (Seg II)',        required: false },
      { key: 'repro_efd_rabbit',  label: 'Embryo-fetal development — rabbit (Seg II)',     required: false },
      { key: 'repro_pnatal',      label: 'Pre/postnatal development — rat (Seg III)',      required: false },
    ],
  },
]

// ─── State ────────────────────────────────────────────────────────────────────

const selectedStudy = ref(null)
const activeTab     = ref('design')
const showCreateModal   = ref(false)
const showDeleteConfirm = ref(false)
const deleteTargetId    = ref(null)
const saving        = ref(false)
const savingResults = ref(false)
const saveMsg       = ref('')
const saveResultMsg = ref('')

const indChecklist  = ref({})

const newStudyForm = ref({
  study_type: 'acute_tox', title: '', glp: false,
  species: 'rat', dose_route: 'oral', dose_levels: '',
  duration_days: '', objective: '', primary_endpoints: [], success_criteria: '',
})

const studyForm = ref({
  study_type: '', title: '', glp: false,
  species: '', dose_route: '', dose_levels: '',
  duration_days: '', objective: '', primary_endpoints: [], success_criteria: '',
})

const resultsForm = ref({
  status: 'planned', conclusion: '',
  noael_mgkg: '', mtd_mgkg: '',
  results_summary: '', key_findings: {},
})

const newFindingKey   = ref('')
const newFindingValue = ref('')

// ─── Computed ─────────────────────────────────────────────────────────────────

const typeGroups = computed(() => {
  const groups = {}
  for (const s of store.studies) {
    if (!groups[s.study_type]) groups[s.study_type] = []
    groups[s.study_type].push(s)
  }
  return groups
})

const presetsForType = computed(() => STUDY_PRESETS[newStudyForm.value.study_type] || [])

const indProgress = computed(() => {
  const required = IND_PACKAGE.flatMap(c => c.studies.filter(s => s.required).map(s => s.key))
  const done = required.filter(k => indChecklist.value[k])
  return { done: done.length, total: required.length, pct: required.length ? Math.round(done.length / required.length * 100) : 0 }
})

// ─── Helpers ──────────────────────────────────────────────────────────────────

function studyLabel(type) { return STUDY_TYPES.find(t => t.value === type)?.label || type }

const STATUS_STYLE = {
  planned:   { bg: '#eff6ff', color: '#1d4ed8', border: '#bfdbfe' },
  ongoing:   { bg: '#fff7ed', color: '#c2410c', border: '#fed7aa' },
  completed: { bg: '#f0fdf4', color: '#166534', border: '#bbf7d0' },
  reported:  { bg: '#f5f3ff', color: '#5b21b6', border: '#ddd6fe' },
  failed:    { bg: '#fef2f2', color: '#991b1b', border: '#fecaca' },
}

const CONCLUSION_STYLE = {
  go:           { bg: '#f0fdf4', color: '#166534', border: '#bbf7d0', label: 'Go' },
  no_go:        { bg: '#fef2f2', color: '#991b1b', border: '#fecaca', label: 'No-Go' },
  inconclusive: { bg: '#fffbeb', color: '#92400e', border: '#fde68a', label: 'Inconclusive' },
}

function statusStyle(status) {
  const c = STATUS_STYLE[status] || { bg: '#f9fafb', color: '#374151', border: '#e5e7eb' }
  return `background:${c.bg};color:${c.color};border:1px solid ${c.border};border-radius:4px;padding:2px 8px;font-size:11px;font-weight:600;display:inline-block`
}

function conclusionStyle(k) {
  const c = CONCLUSION_STYLE[k]
  if (!c) return ''
  return `background:${c.bg};color:${c.color};border:1px solid ${c.border};border-radius:4px;padding:2px 8px;font-size:11px;font-weight:600`
}

function conclusionLabel(k) { return CONCLUSION_STYLE[k]?.label || k }

function showSaveMsg(target, msg) {
  if (target === 'design') { saveMsg.value = msg; setTimeout(() => saveMsg.value = '', 2500) }
  else { saveResultMsg.value = msg; setTimeout(() => saveResultMsg.value = '', 2500) }
}

// ─── Preset application ───────────────────────────────────────────────────────

function applyPreset(p) {
  newStudyForm.value.title            = p.title
  newStudyForm.value.species          = p.species
  newStudyForm.value.dose_route       = p.dose_route
  newStudyForm.value.dose_levels      = p.dose_levels.join(', ')
  newStudyForm.value.duration_days    = p.duration_days
  newStudyForm.value.glp              = p.glp
  newStudyForm.value.objective        = p.objective
  newStudyForm.value.primary_endpoints = [...p.primary_endpoints]
  newStudyForm.value.success_criteria = p.success_criteria
}

function resetNewForm() {
  newStudyForm.value = {
    study_type: 'acute_tox', title: '', glp: false,
    species: 'rat', dose_route: 'oral', dose_levels: '',
    duration_days: '', objective: '', primary_endpoints: [], success_criteria: '',
  }
}

function addNewEndpoint() { newStudyForm.value.primary_endpoints.push('') }
function removeNewEndpoint(i) { newStudyForm.value.primary_endpoints.splice(i, 1) }
function addEndpoint() { studyForm.value.primary_endpoints.push('') }
function removeEndpoint(i) { studyForm.value.primary_endpoints.splice(i, 1) }

// ─── CRUD ─────────────────────────────────────────────────────────────────────

function parseDoseLevels(raw) {
  if (Array.isArray(raw)) return raw
  return raw.split(',').map(s => parseFloat(s.trim())).filter(n => !isNaN(n))
}

async function createStudy() {
  saving.value = true
  try {
    const payload = {
      ...newStudyForm.value,
      dose_levels:  parseDoseLevels(newStudyForm.value.dose_levels),
      duration_days: parseInt(newStudyForm.value.duration_days) || null,
    }
    const study = await store.createStudy(projectId, payload)
    showCreateModal.value = false
    resetNewForm()
    await selectStudy(study)
  } finally {
    saving.value = false
  }
}

async function selectStudy(study) {
  const full = await store.fetchStudy(study.id)
  selectedStudy.value = full || store.studies.find(s => s.id === study.id)
  activeTab.value = 'design'
  syncForms()
}

function syncForms() {
  const s = selectedStudy.value
  if (!s) return
  studyForm.value = {
    study_type:        s.study_type,
    title:             s.title || '',
    glp:               s.glp || false,
    species:           s.species,
    dose_route:        s.dose_route,
    dose_levels:       Array.isArray(s.dose_levels) ? s.dose_levels.join(', ') : s.dose_levels || '',
    duration_days:     s.duration_days || '',
    objective:         s.objective || '',
    primary_endpoints: Array.isArray(s.primary_endpoints) ? [...s.primary_endpoints] : [],
    success_criteria:  s.success_criteria || '',
  }
  resultsForm.value = {
    status:          s.status || 'planned',
    conclusion:      s.conclusion || '',
    noael_mgkg:      s.noael_mgkg ?? '',
    mtd_mgkg:        s.mtd_mgkg ?? '',
    results_summary: s.results_summary || '',
    key_findings:    s.key_findings ? { ...s.key_findings } : {},
  }
}

async function saveDesign() {
  if (!selectedStudy.value) return
  saving.value = true
  try {
    const payload = {
      ...studyForm.value,
      dose_levels:  parseDoseLevels(studyForm.value.dose_levels),
      duration_days: parseInt(studyForm.value.duration_days) || null,
    }
    const updated = await store.updateStudy(selectedStudy.value.id, payload)
    selectedStudy.value = updated
    showSaveMsg('design', 'Saved')
  } finally {
    saving.value = false
  }
}

function addFinding() {
  if (!newFindingKey.value.trim()) return
  resultsForm.value.key_findings = {
    ...resultsForm.value.key_findings,
    [newFindingKey.value.trim()]: newFindingValue.value,
  }
  newFindingKey.value = ''
  newFindingValue.value = ''
}

function removeFinding(key) {
  const kf = { ...resultsForm.value.key_findings }
  delete kf[key]
  resultsForm.value.key_findings = kf
}

async function saveResults() {
  if (!selectedStudy.value) return
  savingResults.value = true
  try {
    const payload = {
      status:          resultsForm.value.status,
      conclusion:      resultsForm.value.conclusion,
      noael_mgkg:      resultsForm.value.noael_mgkg !== '' ? parseFloat(resultsForm.value.noael_mgkg) : null,
      mtd_mgkg:        resultsForm.value.mtd_mgkg !== '' ? parseFloat(resultsForm.value.mtd_mgkg) : null,
      results_summary: resultsForm.value.results_summary,
      key_findings:    resultsForm.value.key_findings,
    }
    const updated = await store.logResults(selectedStudy.value.id, payload)
    selectedStudy.value = updated
    showSaveMsg('results', 'Results saved')
  } finally {
    savingResults.value = false
  }
}

function confirmDelete(id) {
  deleteTargetId.value = id
  showDeleteConfirm.value = true
}

async function doDelete() {
  if (!deleteTargetId.value) return
  await store.deleteStudy(deleteTargetId.value)
  if (selectedStudy.value?.id === deleteTargetId.value) selectedStudy.value = null
  showDeleteConfirm.value = false
  deleteTargetId.value = null
}

onMounted(() => store.fetchStudies(projectId))
</script>

<template>
  <div>
    <PageHeader title="Preclinical Study Planner">
      <template #subtitle>ICH M3(R2) · S2(R1) · S5(R3) · S7A/B</template>
      <template #actions>
        <button class="btn btn-primary" @click="showCreateModal = true">+ New Study</button>
      </template>
    </PageHeader>

    <LoadingSpinner v-if="store.loading.studies" />

    <div v-else-if="store.studies.length || selectedStudy" style="display:flex;gap:16px;align-items:flex-start">

      <!-- ── Left: Study List ───────────────────────────────────────────── -->
      <div style="width:300px;flex-shrink:0">
        <div class="card" style="padding:0;overflow:hidden">
          <div style="padding:12px 16px;border-bottom:1px solid #e5e7eb;font-size:12px;font-weight:700;letter-spacing:.06em;color:#6b7280;text-transform:uppercase;background:#f9fafb">
            Studies ({{ store.studies.length }})
          </div>

          <template v-for="(studies, type) in typeGroups" :key="type">
            <div style="padding:6px 14px 2px;font-size:10px;font-weight:700;letter-spacing:.08em;color:#9ca3af;text-transform:uppercase;background:#f9fafb;border-bottom:1px solid #f3f4f6">
              {{ studyLabel(type) }}
            </div>
            <div
              v-for="study in studies" :key="study.id"
              @click="selectStudy(study)"
              style="padding:10px 14px;cursor:pointer;border-bottom:1px solid #f3f4f6;transition:background .15s"
              :style="selectedStudy?.id === study.id ? 'background:#eff6ff' : ''"
            >
              <div style="display:flex;align-items:center;justify-content:space-between;gap:6px">
                <span style="font-size:13px;font-weight:500;color:#111827;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1">
                  {{ study.title || studyLabel(study.study_type) }}
                </span>
                <span :style="statusStyle(study.status)">{{ study.status }}</span>
              </div>
              <div style="font-size:11px;color:#9ca3af;margin-top:3px;display:flex;gap:8px;flex-wrap:wrap">
                <span>{{ study.species }}</span>
                <span v-if="study.dose_route !== 'in_vitro'">{{ study.dose_route }}</span>
                <span v-if="study.duration_days">{{ study.duration_days }}d</span>
                <span v-if="study.glp" style="color:#7c3aed">GLP</span>
              </div>
            </div>
          </template>
        </div>

        <!-- IND Progress Card -->
        <div class="card" style="margin-top:12px;padding:14px">
          <div style="font-size:12px;font-weight:700;letter-spacing:.06em;color:#6b7280;text-transform:uppercase;margin-bottom:10px">
            IND Package (ICH M3)
          </div>
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
            <div style="flex:1;height:6px;background:#e5e7eb;border-radius:3px;overflow:hidden">
              <div :style="`width:${indProgress.pct}%;height:100%;background:#2563eb;border-radius:3px;transition:width .4s`" />
            </div>
            <span style="font-size:12px;color:#6b7280;white-space:nowrap">{{ indProgress.done }} / {{ indProgress.total }}</span>
          </div>
          <p style="font-size:11px;color:#9ca3af;margin:0">
            {{ indProgress.pct }}% of required IND studies checked. See IND Package tab for full checklist.
          </p>
        </div>
      </div>

      <!-- ── Right: Detail Panel ────────────────────────────────────────── -->
      <div style="flex:1;min-width:0">
        <div v-if="selectedStudy">

          <!-- Tab Bar -->
          <div style="display:flex;gap:0;border-bottom:2px solid #e5e7eb;margin-bottom:16px">
            <button
              v-for="tab in [{k:'design',l:'Study Design'},{k:'protocol',l:'Protocol & Endpoints'},{k:'results',l:'Results'},{k:'ind',l:'IND Package'}]"
              :key="tab.k"
              @click="activeTab = tab.k"
              style="padding:10px 18px;border:none;background:transparent;cursor:pointer;font-size:13px;font-weight:500;color:#6b7280;border-bottom:2px solid transparent;margin-bottom:-2px"
              :style="activeTab === tab.k ? 'color:#2563eb;border-bottom-color:#2563eb' : ''"
            >{{ tab.l }}</button>
          </div>

          <!-- ── TAB: Study Design ───────────────────────────────────────── -->
          <div v-if="activeTab === 'design'">
            <div style="display:flex;gap:12px;align-items:flex-start">
              <div class="card" style="flex:1">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
                  <h3 class="card-title" style="margin:0">Study Design</h3>
                  <div style="display:flex;align-items:center;gap:10px">
                    <span v-if="saveMsg" style="font-size:12px;color:#166534">{{ saveMsg }}</span>
                    <button class="btn btn-secondary btn-sm" style="color:#dc2626;border-color:#fca5a5" @click="confirmDelete(selectedStudy.id)">Delete</button>
                    <button class="btn btn-primary btn-sm" :disabled="saving" @click="saveDesign">{{ saving ? 'Saving…' : 'Save' }}</button>
                  </div>
                </div>

                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
                  <div class="form-group" style="grid-column:1/-1">
                    <label>Study Title</label>
                    <input v-model="studyForm.title" class="form-input" placeholder="E.g. 28-Day Repeat-Dose Oral Toxicology — Rat (GLP)" />
                  </div>
                  <div class="form-group">
                    <label>Study Type</label>
                    <select v-model="studyForm.study_type" class="form-input">
                      <option v-for="t in STUDY_TYPES" :key="t.value" :value="t.value">{{ t.label }}</option>
                    </select>
                  </div>
                  <div class="form-group">
                    <label>Status</label>
                    <select v-model="resultsForm.status" class="form-input">
                      <option value="planned">Planned</option>
                      <option value="ongoing">Ongoing</option>
                      <option value="completed">Completed</option>
                      <option value="reported">Reported</option>
                      <option value="failed">Failed / Terminated</option>
                    </select>
                  </div>
                  <div class="form-group">
                    <label>Species</label>
                    <select v-model="studyForm.species" class="form-input">
                      <option v-for="s in SPECIES_OPTIONS" :key="s" :value="s">{{ s }}</option>
                    </select>
                  </div>
                  <div class="form-group">
                    <label>Dose Route</label>
                    <select v-model="studyForm.dose_route" class="form-input">
                      <option v-for="r in ROUTE_OPTIONS" :key="r" :value="r">{{ r }}</option>
                    </select>
                  </div>
                  <div class="form-group">
                    <label>Dose Levels (mg/kg, comma-separated)</label>
                    <input v-model="studyForm.dose_levels" class="form-input" placeholder="10, 30, 100" />
                  </div>
                  <div class="form-group">
                    <label>Duration (days)</label>
                    <input v-model="studyForm.duration_days" type="number" class="form-input" min="1" />
                  </div>
                  <div class="form-group" style="grid-column:1/-1;display:flex;align-items:center;gap:8px">
                    <input type="checkbox" v-model="studyForm.glp" id="glp-edit" style="width:16px;height:16px" />
                    <label for="glp-edit" style="margin:0;cursor:pointer">GLP (Good Laboratory Practice) Compliant</label>
                    <span style="font-size:11px;color:#9ca3af">— required for IND regulatory submission</span>
                  </div>
                </div>

                <div class="form-group">
                  <label>Study Objective</label>
                  <textarea v-model="studyForm.objective" class="form-input" rows="3" placeholder="Describe scientific rationale, regulatory context, and specific aims…" />
                </div>
                <div class="form-group">
                  <label>Success Criteria</label>
                  <textarea v-model="studyForm.success_criteria" class="form-input" rows="2" placeholder="E.g. NOAEL ≥10× clinical AUC. No irreversible histopathological findings at NOAEL." />
                </div>
              </div>
            </div>

            <!-- Quick Results Summary if study has results -->
            <div v-if="selectedStudy.conclusion || selectedStudy.noael_mgkg" class="card" style="border-left:3px solid #2563eb">
              <div style="font-size:12px;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:.06em;margin-bottom:10px">Results Summary</div>
              <div style="display:flex;gap:20px;flex-wrap:wrap">
                <div v-if="selectedStudy.conclusion">
                  <span style="font-size:11px;color:#9ca3af;display:block;margin-bottom:2px">Conclusion</span>
                  <span :style="conclusionStyle(selectedStudy.conclusion)">{{ conclusionLabel(selectedStudy.conclusion) }}</span>
                </div>
                <div v-if="selectedStudy.noael_mgkg != null">
                  <span style="font-size:11px;color:#9ca3af;display:block;margin-bottom:2px">NOAEL</span>
                  <span style="font-weight:600;color:#111827">{{ selectedStudy.noael_mgkg }} mg/kg</span>
                </div>
                <div v-if="selectedStudy.mtd_mgkg != null">
                  <span style="font-size:11px;color:#9ca3af;display:block;margin-bottom:2px">MTD</span>
                  <span style="font-weight:600;color:#111827">{{ selectedStudy.mtd_mgkg }} mg/kg</span>
                </div>
              </div>
              <p v-if="selectedStudy.results_summary" style="font-size:13px;color:#374151;margin:10px 0 0">{{ selectedStudy.results_summary }}</p>
            </div>
          </div>

          <!-- ── TAB: Protocol & Endpoints ──────────────────────────────── -->
          <div v-if="activeTab === 'protocol'">
            <div class="card">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
                <h3 class="card-title" style="margin:0">Primary Endpoints</h3>
                <div style="display:flex;gap:8px;align-items:center">
                  <span v-if="saveMsg" style="font-size:12px;color:#166534">{{ saveMsg }}</span>
                  <button class="btn btn-secondary btn-sm" @click="addEndpoint">+ Add Endpoint</button>
                  <button class="btn btn-primary btn-sm" :disabled="saving" @click="saveDesign">{{ saving ? 'Saving…' : 'Save' }}</button>
                </div>
              </div>

              <div v-if="studyForm.primary_endpoints.length" style="display:flex;flex-direction:column;gap:8px">
                <div v-for="(ep, idx) in studyForm.primary_endpoints" :key="idx" style="display:flex;gap:8px;align-items:flex-start">
                  <span style="min-width:24px;height:24px;background:#eff6ff;color:#1d4ed8;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;flex-shrink:0;margin-top:8px">{{ idx + 1 }}</span>
                  <input v-model="studyForm.primary_endpoints[idx]" class="form-input" style="flex:1" placeholder="Endpoint description…" />
                  <button @click="removeEndpoint(idx)" style="background:none;border:none;color:#9ca3af;cursor:pointer;font-size:18px;padding:6px;line-height:1">×</button>
                </div>
              </div>
              <div v-else style="padding:16px;text-align:center;color:#9ca3af;font-size:13px;background:#f9fafb;border-radius:6px">
                No endpoints defined. Click "+ Add Endpoint" or apply a preset from the New Study modal.
              </div>
            </div>

            <!-- ICH Guideline Reference -->
            <div class="card" style="margin-top:12px">
              <div style="font-size:12px;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:.06em;margin-bottom:12px">ICH Guideline Reference</div>
              <table style="width:100%;border-collapse:collapse;font-size:12px">
                <thead>
                  <tr style="background:#f9fafb">
                    <th style="padding:8px 12px;text-align:left;font-size:11px;font-weight:700;letter-spacing:.06em;color:#6b7280;text-transform:uppercase;border-bottom:2px solid #e5e7eb">Study Type</th>
                    <th style="padding:8px 12px;text-align:left;font-size:11px;font-weight:700;letter-spacing:.06em;color:#6b7280;text-transform:uppercase;border-bottom:2px solid #e5e7eb">Guideline</th>
                    <th style="padding:8px 12px;text-align:left;font-size:11px;font-weight:700;letter-spacing:.06em;color:#6b7280;text-transform:uppercase;border-bottom:2px solid #e5e7eb">Minimum Requirement for IND</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in [
                    {type:'Safety Pharmacology (CNS, CV, Resp)', gl:'ICH S7A/S7B', req:'Core battery before FIH. hERG IC50 + in vivo CV telemetry + respiratory plethysmography + CNS Irwin.'},
                    {type:'Genotoxicity', gl:'ICH S2(R1)', req:'Ames + in vitro MN. In vivo MN if either positive. Must be completed before Phase 1.'},
                    {type:'Acute Toxicology', gl:'ICH M3(R2)', req:'DRF / limit test in rodent to guide repeat-dose design; non-rodent optional.'},
                    {type:'Repeat-Dose Toxicology', gl:'ICH M3(R2) Table 1', req:'28-day GLP in 2 species for Phase 1. 90-day for Phase 2 (3-month clinical dosing). 6-month for NDA.'},
                    {type:'Pharmacokinetics / TK', gl:'ICH M3(R2)', req:'Single-dose PK in 2 species + TK satellites in repeat-dose studies. Safety margin calculation required.'},
                    {type:'Reproductive Toxicology', gl:'ICH S5(R3)', req:'Fertility (Seg I) pre-Phase 3. EFD rat + rabbit (Seg II) pre-Phase 3 for WOCBP. PPND pre-NDA for paediatric use.'},
                    {type:'Carcinogenicity', gl:'ICH S1A/S1B', req:'Not required for IND. Required pre-NDA for drugs with ≥6 months continuous clinical use.'},
                    {type:'ADME / Mass Balance', gl:'ICH M3(R2)', req:'In vitro panel pre-IND. Radiolabelled mass balance ([14C]) pre-NDA/MAA.'},
                  ]" :key="row.type" style="border-bottom:1px solid #f3f4f6">
                    <td style="padding:8px 12px;font-weight:500;color:#111827">{{ row.type }}</td>
                    <td style="padding:8px 12px;color:#2563eb;white-space:nowrap">{{ row.gl }}</td>
                    <td style="padding:8px 12px;color:#374151">{{ row.req }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Species Selection Rationale Reference -->
            <div class="card" style="margin-top:12px">
              <div style="font-size:12px;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:.06em;margin-bottom:12px">Species Justification Reference</div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;font-size:12px">
                <div v-for="item in [
                  {species:'Rat', use:'Primary rodent species for repeat-dose tox, TK, reproductive tox, CNS safety pharm. Sprague-Dawley or Wistar preferred. CYP profile reasonably similar to human.'},
                  {species:'Mouse', use:'Genotoxicity (in vivo MN), acute DRF, and oncology efficacy models. CYP3A family less predictive of human than rat.'},
                  {species:'Beagle Dog', use:'Standard non-rodent for repeat-dose tox and CV safety pharmacology telemetry. GLP 28/90-day required alongside rat for IND. Good cardiac rhythm predictor.'},
                  {species:'Cynomolgus Monkey', use:'Non-rodent for biologics or when pharmacology does not translate to dog. Preferred for CNS, metabolite comparison, or receptor selectivity requiring primate homology.'},
                  {species:'Rabbit', use:'Embryo-fetal development Segment II (second species). Reproductive tox S5(R3). Skin sensitisation (Draize). Good eye irritation model.'},
                  {species:'In Vitro', use:'Genotoxicity (Ames, MN, CA), ADME profiling, hERG patch clamp, CYP inhibition/TDI. Not a species substitute — supplement in vivo data.'},
                ]" :key="item.species" style="padding:10px;background:#f9fafb;border-radius:6px;border:1px solid #e5e7eb">
                  <div style="font-weight:700;color:#111827;margin-bottom:4px">{{ item.species }}</div>
                  <div style="color:#6b7280;line-height:1.5">{{ item.use }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- ── TAB: Results ────────────────────────────────────────────── -->
          <div v-if="activeTab === 'results'">
            <div class="card">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
                <h3 class="card-title" style="margin:0">Results Log</h3>
                <div style="display:flex;gap:8px;align-items:center">
                  <span v-if="saveResultMsg" style="font-size:12px;color:#166534">{{ saveResultMsg }}</span>
                  <button class="btn btn-primary btn-sm" :disabled="savingResults" @click="saveResults">{{ savingResults ? 'Saving…' : 'Save Results' }}</button>
                </div>
              </div>

              <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
                <div class="form-group">
                  <label>Study Status</label>
                  <select v-model="resultsForm.status" class="form-input">
                    <option value="planned">Planned</option>
                    <option value="ongoing">Ongoing</option>
                    <option value="completed">Completed</option>
                    <option value="reported">Reported</option>
                    <option value="failed">Failed / Terminated</option>
                  </select>
                </div>
                <div class="form-group">
                  <label>Overall Conclusion</label>
                  <select v-model="resultsForm.conclusion" class="form-input">
                    <option value="">— Not yet determined —</option>
                    <option value="go">Go</option>
                    <option value="no_go">No-Go</option>
                    <option value="inconclusive">Inconclusive / Requires Further Study</option>
                  </select>
                </div>
                <div class="form-group">
                  <label>NOAEL (mg/kg)</label>
                  <input v-model="resultsForm.noael_mgkg" type="number" step="0.01" class="form-input" placeholder="e.g. 30" />
                  <p class="form-hint">No-Observed-Adverse-Effect Level — highest dose with no statistically or biologically significant adverse findings</p>
                </div>
                <div class="form-group">
                  <label>MTD (mg/kg)</label>
                  <input v-model="resultsForm.mtd_mgkg" type="number" step="0.01" class="form-input" placeholder="e.g. 300" />
                  <p class="form-hint">Maximum Tolerated Dose — highest dose without unacceptable toxicity or >10% body weight loss</p>
                </div>
              </div>

              <div class="form-group">
                <label>Results Summary</label>
                <textarea v-model="resultsForm.results_summary" class="form-input" rows="4"
                  placeholder="Narrative summary of key findings, dose-response, reversibility, histopathological conclusions, and safety margin calculations…" />
              </div>
            </div>

            <!-- Key Findings Dictionary -->
            <div class="card" style="margin-top:12px">
              <div style="font-size:12px;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:.06em;margin-bottom:12px">Key Findings (Structured)</div>

              <div v-if="Object.keys(resultsForm.key_findings).length" style="margin-bottom:12px">
                <table style="width:100%;border-collapse:collapse;font-size:13px">
                  <thead>
                    <tr style="background:#f9fafb">
                      <th style="padding:8px 12px;text-align:left;font-size:11px;font-weight:700;letter-spacing:.06em;color:#6b7280;text-transform:uppercase;border-bottom:2px solid #e5e7eb">Parameter</th>
                      <th style="padding:8px 12px;text-align:left;font-size:11px;font-weight:700;letter-spacing:.06em;color:#6b7280;text-transform:uppercase;border-bottom:2px solid #e5e7eb">Finding / Value</th>
                      <th style="padding:8px 12px;border-bottom:2px solid #e5e7eb;width:40px"></th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(value, key) in resultsForm.key_findings" :key="key" style="border-bottom:1px solid #f3f4f6">
                      <td style="padding:8px 12px;font-weight:500;color:#374151">{{ key }}</td>
                      <td style="padding:8px 12px;color:#111827">{{ value }}</td>
                      <td style="padding:8px 4px;text-align:center">
                        <button @click="removeFinding(key)" style="background:none;border:none;color:#d1d5db;cursor:pointer;font-size:16px;line-height:1;padding:2px">×</button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div style="display:grid;grid-template-columns:1fr 2fr auto;gap:8px;align-items:flex-end">
                <div class="form-group" style="margin:0">
                  <label style="font-size:11px">Parameter</label>
                  <input v-model="newFindingKey" class="form-input" placeholder="e.g. Liver weight change" @keydown.enter="addFinding" />
                </div>
                <div class="form-group" style="margin:0">
                  <label style="font-size:11px">Finding / Value</label>
                  <input v-model="newFindingValue" class="form-input" placeholder="e.g. +12% vs. control at 100 mg/kg, reversible by Day 14" @keydown.enter="addFinding" />
                </div>
                <button class="btn btn-secondary btn-sm" @click="addFinding" style="margin-bottom:1px">Add</button>
              </div>

              <p style="font-size:11px;color:#9ca3af;margin:8px 0 0">
                Suggested parameters: Liver weight %, ALT/AST change, haematology flags, histopathology grade, organ-specific observations, TK safety margin (AUC ratio), reversibility assessment.
              </p>
            </div>

            <!-- Safety Margin Calculator Reference -->
            <div class="card" style="margin-top:12px;background:#f0fdf4;border:1px solid #bbf7d0">
              <div style="font-size:12px;font-weight:700;color:#166534;text-transform:uppercase;letter-spacing:.06em;margin-bottom:10px">Safety Margin Guidance (ICH M3(R2))</div>
              <table style="width:100%;border-collapse:collapse;font-size:12px">
                <tbody>
                  <tr v-for="row in [
                    {label:'NOAEL-based HED', formula:'NOAEL (mg/kg) × (animal body weight / human body weight)^0.67', note:'FDA Guidance for Industry (2005) body surface area correction'},
                    {label:'AUC-based safety margin', formula:'AUC at NOAEL (ng·h/mL) ÷ AUC at clinical dose (ng·h/mL)', note:'Preferred approach per ICH M3(R2). Target ≥10× for chronic use.'},
                    {label:'Cmax-based margin', formula:'Free Cmax at NOAEL ÷ free Cmax at clinical dose', note:'Used for peak-concentration-driven toxicities (e.g. QTc, CNS).'},
                    {label:'HNSTD (non-rodent)', formula:'Highest non-severely toxic dose in non-rodent', note:'Starting dose for Phase 1 SAD in oncology per FDA Guidance (2010).'},
                  ]" :key="row.label" style="border-bottom:1px solid #bbf7d0">
                    <td style="padding:8px 10px;font-weight:600;color:#166534;white-space:nowrap">{{ row.label }}</td>
                    <td style="padding:8px 10px;font-family:monospace;font-size:11px;color:#14532d">{{ row.formula }}</td>
                    <td style="padding:8px 10px;color:#4ade80;font-size:11px">{{ row.note }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- ── TAB: IND Package ───────────────────────────────────────── -->
          <div v-if="activeTab === 'ind'">
            <div style="display:flex;align-items:center;gap:16px;margin-bottom:16px">
              <div style="flex:1;height:8px;background:#e5e7eb;border-radius:4px;overflow:hidden">
                <div :style="`width:${indProgress.pct}%;height:100%;background:#2563eb;border-radius:4px;transition:width .4s`" />
              </div>
              <span style="font-size:13px;font-weight:600;color:#2563eb;white-space:nowrap">{{ indProgress.done }} / {{ indProgress.total }} required ({{ indProgress.pct }}%)</span>
            </div>

            <div v-for="cat in IND_PACKAGE" :key="cat.category" class="card" style="margin-bottom:12px">
              <div style="display:flex;align-items:baseline;gap:10px;margin-bottom:4px">
                <span style="font-size:13px;font-weight:700;color:#111827">{{ cat.category }}</span>
                <span style="font-size:11px;color:#2563eb;font-weight:600">{{ cat.guideline }}</span>
              </div>
              <p style="font-size:11px;color:#9ca3af;margin:0 0 12px">{{ cat.note }}</p>
              <div style="display:flex;flex-direction:column;gap:8px">
                <label
                  v-for="study in cat.studies" :key="study.key"
                  style="display:flex;align-items:center;gap:10px;cursor:pointer;padding:8px 10px;border-radius:6px;border:1px solid #e5e7eb;transition:background .15s"
                  :style="indChecklist[study.key] ? 'background:#f0fdf4;border-color:#bbf7d0' : 'background:#fff'"
                >
                  <input
                    type="checkbox"
                    :checked="indChecklist[study.key]"
                    @change="() => (indChecklist[study.key] = !indChecklist[study.key])"
                    style="width:16px;height:16px;flex-shrink:0"
                  />
                  <span style="flex:1;font-size:13px" :style="indChecklist[study.key] ? 'color:#166534' : 'color:#374151'">{{ study.label }}</span>
                  <span v-if="study.required" style="font-size:10px;font-weight:700;background:#fef3c7;color:#92400e;border:1px solid #fde68a;border-radius:3px;padding:1px 6px">Required</span>
                  <span v-else style="font-size:10px;color:#9ca3af;border:1px solid #e5e7eb;border-radius:3px;padding:1px 6px">Recommended</span>
                </label>
              </div>
            </div>

            <div class="card" style="margin-top:4px;background:#eff6ff;border:1px solid #bfdbfe">
              <div style="font-size:12px;font-weight:700;color:#1e40af;text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px">IND Filing Checklist — FDA 21 CFR Part 312</div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:12px">
                <div v-for="item in [
                  'Cover sheet (Form FDA 1571)',
                  'Table of Contents',
                  'Introductory statement and general investigational plan',
                  'Investigator\'s Brochure (IB) — compiled from all preclinical data',
                  'Clinical protocol (Phase 1 SAD/MAD design)',
                  'Chemistry, Manufacturing & Controls (CMC) section',
                  'Pharmacology and Toxicology section — all GLP study reports',
                  'Previous human experience (if any)',
                ]" :key="item" style="display:flex;align-items:flex-start;gap:8px;padding:8px;background:#fff;border-radius:4px;border:1px solid #bfdbfe">
                  <span style="color:#2563eb;flex-shrink:0;margin-top:1px">▸</span>
                  <span style="color:#1e40af">{{ item }}</span>
                </div>
              </div>
            </div>
          </div>

        </div>

        <!-- No study selected yet -->
        <div v-else class="card" style="text-align:center;padding:40px;color:#9ca3af">
          <div style="font-size:32px;margin-bottom:12px">🧬</div>
          <p style="font-size:14px;font-weight:500;color:#374151;margin:0 0 6px">Select a study to view or edit</p>
          <p style="font-size:13px;margin:0">Click any study in the left panel, or create a new study to get started.</p>
        </div>
      </div>
    </div>

    <EmptyState v-else title="No preclinical studies" message="Plan and track in vivo and in vitro studies for toxicology, safety pharmacology, PK, and efficacy. ICH M3(R2) compliant IND package checklist included." />

    <!-- ── Create Study Modal ─────────────────────────────────────────────── -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false; resetNewForm()">
      <div class="modal-box">

        <div class="modal-header">
          <h3>New Preclinical Study</h3>
          <button class="modal-close" @click="showCreateModal = false; resetNewForm()">&#10005;</button>
        </div>

        <div class="modal-body">
          <!-- Study type selector -->
          <div class="form-group">
            <label>Study Type</label>
            <select v-model="newStudyForm.study_type" class="form-input">
              <option v-for="t in STUDY_TYPES" :key="t.value" :value="t.value">{{ t.label }} ({{ t.group }})</option>
            </select>
          </div>

          <!-- Presets -->
          <div v-if="presetsForType.length" class="preset-row">
            <div class="preset-label">ICH Presets</div>
            <div class="preset-buttons">
              <button
                v-for="p in presetsForType" :key="p.label"
                @click="applyPreset(p)"
                class="preset-btn"
              >{{ p.label }}</button>
            </div>
          </div>

          <div class="form-group">
            <label>Study Title <span class="req">*</span></label>
            <input v-model="newStudyForm.title" class="form-input" placeholder="Descriptive title for study report and IND" />
          </div>

          <div class="form-row-2">
            <div class="form-group">
              <label>Species</label>
              <select v-model="newStudyForm.species" class="form-input">
                <option v-for="s in SPECIES_OPTIONS" :key="s" :value="s">{{ s }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>Dose Route</label>
              <select v-model="newStudyForm.dose_route" class="form-input">
                <option v-for="r in ROUTE_OPTIONS" :key="r" :value="r">{{ r }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>Dose Levels (mg/kg, comma-separated)</label>
              <input v-model="newStudyForm.dose_levels" class="form-input" placeholder="10, 30, 100" />
            </div>
            <div class="form-group">
              <label>Duration (days)</label>
              <input v-model="newStudyForm.duration_days" type="number" class="form-input" min="1" />
            </div>
          </div>

          <div class="form-group glp-row">
            <input type="checkbox" v-model="newStudyForm.glp" id="glp-new" />
            <label for="glp-new" class="glp-label">GLP Compliant Study <span class="text-muted">(required for IND regulatory submission)</span></label>
          </div>

          <div class="form-group">
            <label>Objective <span class="req">*</span></label>
            <textarea v-model="newStudyForm.objective" class="form-input" rows="3" placeholder="Scientific rationale and specific aims…" />
          </div>

          <!-- Primary Endpoints -->
          <div class="form-group">
            <div class="ep-header">
              <label>Primary Endpoints</label>
              <button @click="addNewEndpoint" class="btn btn-secondary btn-sm">+ Add</button>
            </div>
            <div v-if="newStudyForm.primary_endpoints.length" class="ep-list">
              <div v-for="(ep, i) in newStudyForm.primary_endpoints" :key="i" class="ep-row">
                <input v-model="newStudyForm.primary_endpoints[i]" class="form-input" :placeholder="`Endpoint ${i+1}…`" />
                <button @click="removeNewEndpoint(i)" class="ep-remove">×</button>
              </div>
            </div>
            <p v-else class="text-muted" style="font-size:12px;margin:4px 0 0">Apply a preset above to auto-populate ICH-compliant endpoints.</p>
          </div>

          <div class="form-group">
            <label>Success Criteria</label>
            <textarea v-model="newStudyForm.success_criteria" class="form-input" rows="2" placeholder="Define go/no-go criteria for programme decision-making…" />
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-outline" @click="showCreateModal = false; resetNewForm()">Cancel</button>
          <button class="btn btn-primary" :disabled="!newStudyForm.objective || saving" @click="createStudy">
            {{ saving ? 'Creating…' : 'Create Study' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ── Delete Confirmation ────────────────────────────────────────────── -->
    <div v-if="showDeleteConfirm" class="modal-overlay" @click.self="showDeleteConfirm = false; deleteTargetId = null">
      <div class="confirm-box">
        <h3 class="confirm-title">Delete Study?</h3>
        <p class="confirm-body">This will permanently delete the study and all associated results. This action cannot be undone.</p>
        <div class="modal-footer">
          <button class="btn btn-outline" @click="showDeleteConfirm = false; deleteTargetId = null">Cancel</button>
          <button class="btn btn-danger" @click="doDelete">Delete</button>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
/* ── Modal ──────────────────────────────────────────────────────────── */
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
  width: 720px;
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
  flex-shrink: 0;
}
.modal-header h3 { margin: 0; font-size: 16px; font-weight: 700; color: #111827; }
.modal-close { background: none; border: none; font-size: 18px; cursor: pointer; color: #6b7280; line-height: 1; }
.modal-close:hover { color: #374151; }
.modal-body {
  padding: 20px 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
  flex-shrink: 0;
}

/* ── Confirm dialog ─────────────────────────────────────────────────── */
.confirm-box {
  background: #fff;
  border-radius: 12px;
  width: 400px;
  max-width: 96vw;
  box-shadow: 0 20px 60px rgba(0,0,0,.2);
  overflow: hidden;
}
.confirm-title { margin: 20px 24px 8px; font-size: 16px; font-weight: 700; color: #111827; }
.confirm-body  { margin: 0 24px 4px; font-size: 13px; color: #6b7280; line-height: 1.5; }

/* ── Form elements ──────────────────────────────────────────────────── */
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
  background: #fff;
  color: #111827;
}
.form-input:focus { border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37,99,235,.08); }
textarea.form-input { resize: vertical; }
.form-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.form-hint { font-size: 11px; color: #9ca3af; margin: 3px 0 0; }

/* GLP checkbox row */
.glp-row { flex-direction: row; align-items: center; gap: 8px; }
.glp-row input[type="checkbox"] { width: 16px; height: 16px; flex-shrink: 0; cursor: pointer; }
.glp-label { font-size: 13px; font-weight: 500; cursor: pointer; margin: 0; }

/* Required asterisk */
.req { color: #dc2626; }

/* ── Preset row ─────────────────────────────────────────────────────── */
.preset-row { display: flex; flex-direction: column; gap: 8px; }
.preset-label {
  font-size: 11px; font-weight: 700; color: #6b7280;
  text-transform: uppercase; letter-spacing: .06em;
}
.preset-buttons { display: flex; flex-wrap: wrap; gap: 8px; }
.preset-btn {
  padding: 5px 12px;
  font-size: 12px;
  font-weight: 500;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  color: #374151;
  cursor: pointer;
  transition: all .15s;
}
.preset-btn:hover { border-color: #2563eb; color: #2563eb; background: #eff6ff; }

/* ── Endpoint list ──────────────────────────────────────────────────── */
.ep-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.ep-header label { margin: 0; }
.ep-list { display: flex; flex-direction: column; gap: 6px; }
.ep-row { display: flex; gap: 8px; align-items: center; }
.ep-remove {
  background: none; border: none; color: #d1d5db;
  cursor: pointer; font-size: 20px; line-height: 1; padding: 2px 4px;
  flex-shrink: 0;
}
.ep-remove:hover { color: #dc2626; }

/* ── Buttons ────────────────────────────────────────────────────────── */
.btn { padding: 8px 18px; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; border: 1px solid transparent; transition: all .15s; }
.btn-primary { background: #2563eb; color: #fff; border-color: #2563eb; }
.btn-primary:hover:not(:disabled) { background: #1d4ed8; }
.btn-primary:disabled { opacity: 0.5; cursor: default; }
.btn-outline { background: #fff; color: #374151; border-color: #d1d5db; }
.btn-outline:hover { border-color: #9ca3af; }
.btn-danger { background: #dc2626; color: #fff; border-color: #dc2626; }
.btn-danger:hover { background: #b91c1c; }
.btn-sm { padding: 5px 10px; font-size: 12px; }

/* ── Misc ───────────────────────────────────────────────────────────── */
.text-muted { color: #9ca3af; }
</style>
