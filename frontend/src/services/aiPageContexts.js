/**
 * Per-page field schemas for the AI panel.
 * Each entry drives both the backend system prompt (field names + hints)
 * and the frontend SuggestionCard label resolution.
 */
export const PAGE_FIELD_SCHEMAS = {
  ProjectEdit: {
    label: 'Project Overview',
    fields: [
      // Project-level fields
      { key: 'description', label: 'Project Description' },
      { key: 'pathway', label: 'Development Pathway', hint: 'analog_based or novel_design' },
      { key: 'phase', label: 'Development Phase', hint: 'preclinical / phase1 / phase2 / phase3' },
      { key: 'molecule_type', label: 'Molecule Type', hint: 'small_molecule / biologic / undetermined' },
      // Target Product Profile (TPP) fields
      { key: 'tpp_indication', label: 'TPP — Target Indication' },
      { key: 'tpp_patient_population', label: 'TPP — Patient Population' },
      { key: 'tpp_route', label: 'TPP — Route of Administration' },
      { key: 'tpp_dosage_form', label: 'TPP — Dosage Form' },
      { key: 'tpp_dose', label: 'TPP — Target Dose' },
      { key: 'tpp_frequency', label: 'TPP — Dosing Frequency' },
      { key: 'tpp_comparator', label: 'TPP — Comparator / Standard of Care' },
      { key: 'tpp_primary_efficacy', label: 'TPP — Primary Efficacy Endpoint' },
      { key: 'tpp_primary_safety', label: 'TPP — Primary Safety Target' },
      { key: 'tpp_target_claims', label: 'TPP — Target Label Claims' },
      { key: 'tpp_special_populations', label: 'TPP — Special Populations' },
      { key: 'tpp_contraindications', label: 'TPP — Contraindications' },
    ],
  },

  SARTracker: {
    label: 'SAR Tracker',
    fields: [
      { key: 'activity_type', label: 'Activity Type', hint: 'e.g., IC50, Ki, EC50' },
      { key: 'activity_unit', label: 'Activity Unit', hint: 'e.g., nM, µM' },
      { key: 'assay_description', label: 'Assay Description' },
      { key: 'r_group', label: 'R-Group Annotation', hint: 'Structural position being modified' },
      { key: 'notes', label: 'SAR Notes / Optimization Goals' },
    ],
  },

  SynthesisHub: {
    label: 'Synthesis Hub',
    fields: [
      { key: 'plan_type', label: 'Route Strategy', hint: 'e.g., linear, convergent, retrosynthetic' },
      { key: 'notes', label: 'Synthesis Notes' },
    ],
  },

  SaltPolymorphScreening: {
    label: 'Salt & Polymorph Screening',
    fields: [
      { key: 'screen_type', label: 'Screen Type', hint: 'e.g., salt, polymorph, cocrystal' },
      { key: 'objective', label: 'Screening Objective' },
      { key: 'baseline_pka', label: 'API pKa' },
      { key: 'baseline_logp', label: 'API LogP' },
      { key: 'baseline_solubility_mgml', label: 'Baseline Solubility (mg/mL)' },
      { key: 'baseline_hygroscopicity', label: 'Hygroscopicity Observation' },
      { key: 'baseline_melting_point_c', label: 'Melting Point (°C)' },
    ],
  },

  ProcessDevelopment: {
    label: 'Process Development',
    fields: [
      { key: 'cppNotes', label: 'Critical Process Parameters (CPPs)' },
      { key: 'yield_target', label: 'Target Yield (%)' },
      { key: 'purity_target', label: 'Purity Target (%)' },
    ],
  },

  FormulationPlanning: {
    label: 'Formulation Planning',
    fields: [
      { key: 'dosage_form', label: 'Dosage Form', hint: 'e.g., oral_tablet, capsule, iv_solution' },
      { key: 'route_of_administration', label: 'Route of Administration', hint: 'e.g., oral, intravenous, topical' },
      { key: 'target_dose_mg', label: 'Target Dose (mg)' },
      { key: 'release_type', label: 'Release Profile', hint: 'immediate_release / modified_release / extended_release / delayed_release' },
      { key: 'manufacturing_process', label: 'Manufacturing Process', hint: 'e.g., wet_granulation, direct_compression, hot_melt_extrusion' },
      { key: 'rationale', label: 'Formulation Rationale' },
    ],
  },

  StabilityPlanning: {
    label: 'Stability Planning',
    fields: [
      { key: 'material_type', label: 'Material Type', hint: 'drug_substance or drug_product' },
      { key: 'intended_storage_condition', label: 'Intended Storage Condition', hint: 'e.g., 25°C/60%RH, refrigerated, frozen' },
      { key: 'condition_label', label: 'Study Condition Label', hint: 'e.g., Long-Term, Accelerated, Intermediate' },
      { key: 'temperature_c', label: 'Temperature (°C)' },
      { key: 'humidity_rh', label: 'Humidity (%RH)' },
      { key: 'light_exposure', label: 'Light Exposure Condition', hint: 'e.g., Protected from light / ICH Q1B / Dark' },
      { key: 'ich_category', label: 'ICH Category', hint: 'e.g., Zone IVb, Accelerated' },
      { key: 'timepoints_months', label: 'Time Points (months)', hint: 'comma-separated, e.g., 0,3,6,9,12,18,24' },
    ],
  },

  AnalyticalMethod: {
    label: 'Analytical Methods',
    fields: [
      { key: 'method_name', label: 'Method Name' },
      { key: 'method_type', label: 'Method Type', hint: 'e.g., hplc_uv, lc_ms, gc, nmr, dissolution, karl_fischer' },
      { key: 'analyte', label: 'Analyte' },
      { key: 'instrument', label: 'Instrument / Platform' },
      { key: 'principle', label: 'Method Principle / Description' },
      { key: 'validation_status', label: 'Validation Status', hint: 'development / validated / compendial' },
    ],
  },

  SpecificationBuilder: {
    label: 'Specifications',
    fields: [
      { key: 'spec_type', label: 'Spec Type', hint: 'drug_substance or drug_product' },
      { key: 'attribute', label: 'Attribute Name', hint: 'e.g., Appearance, Assay, Related Substances, Dissolution' },
      { key: 'criteria_type', label: 'Criteria Type', hint: 'release or shelf_life' },
      { key: 'acceptance_criteria', label: 'Acceptance Criteria', hint: 'e.g., 98.0–102.0% label claim' },
      { key: 'test_method', label: 'Test Method', hint: 'e.g., HPLC-UV per validated method' },
      { key: 'basis', label: 'Specification Basis', hint: 'e.g., ICH Q6A, clinical batch data, pharmacopoeia' },
    ],
  },

  ADMETDashboard: {
    label: 'ADMET Dashboard',
    fields: [
      { key: 'mw_target', label: 'Target MW (Da)', hint: 'Lipinski: ≤500' },
      { key: 'logp_range', label: 'Target LogP Range', hint: 'Lipinski: ≤5; CNS: 1–3' },
      { key: 'tpsa_target', label: 'Target TPSA (Å²)', hint: 'Oral: <140; CNS: <90' },
      { key: 'solubility_target', label: 'Solubility Target (µg/mL)' },
      { key: 'herg_safety_limit', label: 'hERG Safety Limit (µM)', hint: '>10 µM preferred' },
      { key: 'bioavailability_target', label: 'Oral Bioavailability Target (%)' },
      { key: 'half_life_target', label: 'Half-Life Target (h)' },
    ],
  },

  PreclinicalStudyPlanner: {
    label: 'Preclinical Study Planner',
    fields: [
      { key: 'study_type', label: 'Study Type', hint: 'e.g., single_dose_tox, repeat_dose_tox, genotoxicity, safety_pharmacology, pk' },
      { key: 'title', label: 'Study Title' },
      { key: 'species', label: 'Species', hint: 'e.g., rat, mouse, dog, monkey' },
      { key: 'dose_route', label: 'Dose Route', hint: 'e.g., oral, iv, sc, ip' },
      { key: 'dose_levels', label: 'Dose Levels', hint: 'e.g., 10, 50, 200 mg/kg' },
      { key: 'duration_days', label: 'Duration (days)', hint: 'ICH M3: 28 days for Phase I' },
      { key: 'objective', label: 'Study Objective' },
      { key: 'primary_endpoints', label: 'Primary Endpoints' },
      { key: 'success_criteria', label: 'Success Criteria' },
    ],
  },
}

/**
 * Look up the human-readable label for a field key on a given page.
 */
export function getFieldLabel(pageType, key) {
  const schema = PAGE_FIELD_SCHEMAS[pageType]
  if (!schema) return key.replace(/_/g, ' ')
  const field = schema.fields.find((f) => f.key === key)
  return field ? field.label : key.replace(/_/g, ' ')
}
