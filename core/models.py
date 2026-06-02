from django.db import models


class Project(models.Model):
    PHASE_CHOICES = [
        ('preclinical', 'Preclinical'),
        ('phase1', 'Phase 1'),
        ('phase2', 'Phase 2'),
        ('phase3', 'Phase 3'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]
    PATHWAY_CHOICES = [
        ('analog_based', 'Analog-Based Development'),
        ('novel_design', 'Novel Drug Design'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    phase = models.CharField(max_length=20, choices=PHASE_CHOICES, default='preclinical')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    pathway = models.CharField(max_length=20, choices=PATHWAY_CHOICES, default='analog_based')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Compound(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='compounds')
    name = models.CharField(max_length=255)
    chembl_id = models.CharField(max_length=20, blank=True)
    pubchem_cid = models.IntegerField(null=True, blank=True)
    smiles = models.TextField(blank=True)
    inchi_key = models.CharField(max_length=27, blank=True)
    molecular_formula = models.CharField(max_length=100, blank=True)
    molecular_weight = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class CompoundProperty(models.Model):
    PROPERTY_TYPE_CHOICES = [
        ('physicochemical', 'Physicochemical'),
        ('admet', 'ADMET'),
        ('toxicity', 'Toxicity'),
    ]
    SOURCE_CHOICES = [
        ('pubchem', 'PubChem'),
        ('pkcsm', 'pkCSM'),
        ('comptox', 'EPA CompTox'),
        ('chembl', 'ChEMBL'),
    ]

    compound = models.ForeignKey(Compound, on_delete=models.CASCADE, related_name='properties')
    property_type = models.CharField(max_length=30, choices=PROPERTY_TYPE_CHOICES)
    source = models.CharField(max_length=30, choices=SOURCE_CHOICES)
    data = models.JSONField(default=dict)
    fetched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.compound.name} — {self.property_type}"


class SynthesisPlan(models.Model):
    PLAN_TYPE_CHOICES = [
        ('retro', 'Single-Step Retro'),
        ('tree', 'Multi-Step Tree'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='synthesis_plans')
    analog_candidate = models.ForeignKey(
        'AnalogCandidate', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='synthesis_plans',
    )
    target_smiles = models.TextField()
    plan_type = models.CharField(max_length=10, choices=PLAN_TYPE_CHOICES, default='retro')
    route_data = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['analog_candidate', 'plan_type'],
                condition=models.Q(analog_candidate__isnull=False),
                name='unique_plan_type_per_analog',
            )
        ]

    def __str__(self):
        return f"SynthesisPlan({self.plan_type}) for project {self.project_id}"


class Experiment(models.Model):
    TYPE_CHOICES = [
        ('formulation', 'Formulation'),
        ('synthesis', 'Synthesis'),
        ('analytical', 'Analytical'),
        ('stability', 'Stability'),
        ('preclinical', 'Preclinical'),
    ]
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='experiments')
    compound = models.ForeignKey(Compound, on_delete=models.SET_NULL, null=True, blank=True, related_name='experiments')
    synthesis_plan = models.ForeignKey('SynthesisPlan', on_delete=models.SET_NULL, null=True, blank=True, related_name='experiments')
    formulation_plan = models.ForeignKey('FormulationPlan', on_delete=models.SET_NULL, null=True, blank=True, related_name='experiments')
    preclinical_study = models.ForeignKey('PreclinicalStudy', on_delete=models.SET_NULL, null=True, blank=True, related_name='experiments')
    title = models.CharField(max_length=255)
    experiment_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    objective = models.TextField()
    variables = models.JSONField(default=list)
    success_criteria = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class ExperimentResult(models.Model):
    DECISION_CHOICES = [
        ('optimize', 'Optimize'),
        ('reproduce', 'Reproduce'),
        ('scale', 'Scale Up'),
        ('abort', 'Abort'),
    ]

    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name='results')
    result_data = models.JSONField(default=dict)
    interpretation = models.TextField(blank=True)
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Result for {self.experiment.title}"


class RiskAssessment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='risk_assessments')
    risk_factors = models.JSONField(default=list)
    risk_heat_map = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Risk Assessment for {self.project.name}"


class Document(models.Model):
    DOC_TYPE_CHOICES = [
        ('process_summary', 'Process Summary'),
        ('risk_report', 'Risk Report'),
        ('handoff', 'Handoff Note'),
        ('analog_report', 'Analog Development Report'),
        ('formulation_report', 'Formulation Report'),
        ('stability_summary', 'Stability Summary'),
        ('admet_summary', 'ADMET Summary'),
        ('ind_cmc', 'IND CMC Section'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents')
    doc_type = models.CharField(max_length=30, choices=DOC_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class ChatSession(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True, related_name='chat_sessions')
    title = models.CharField(max_length=255, default='New Chat')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    sources = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"


class DrugInvestigation(models.Model):
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='investigations')
    chembl_id = models.CharField(max_length=20)
    name = models.CharField(max_length=255)
    smiles = models.TextField(blank=True)
    disease_name = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.chembl_id})"


class AnalogCandidate(models.Model):
    PATENT_STATUS_CHOICES = [
        ('free', 'Free to Operate'),
        ('covered', 'Patent Covered'),
        ('unknown', 'Unknown'),
    ]

    investigation = models.ForeignKey(DrugInvestigation, on_delete=models.CASCADE, related_name='candidates')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='analog_candidates')
    smiles = models.TextField()
    pubchem_cid = models.IntegerField(null=True, blank=True)
    chembl_id = models.CharField(max_length=20, blank=True)
    similarity_score = models.FloatField(default=0.0)
    patent_status = models.CharField(max_length=20, choices=PATENT_STATUS_CHOICES, default='unknown')
    patent_refs = models.JSONField(default=list)
    admet_data = models.JSONField(default=dict)
    shortlisted = models.BooleanField(default=False)
    selected = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analog {self.pubchem_cid or self.smiles[:20]} (score={self.similarity_score:.2f})"


class ExternalDataCache(models.Model):
    SOURCE_CHOICES = [
        ('pubchem', 'PubChem'),
        ('chembl', 'ChEMBL'),
        ('opentargets', 'Open Targets'),
        ('uniprot', 'UniProt'),
        ('pkcsm', 'pkCSM'),
        ('comptox', 'EPA CompTox'),
        ('pubmed', 'PubMed'),
        ('clinicaltrials', 'ClinicalTrials.gov'),
        ('openfda', 'OpenFDA'),
        ('dailymed', 'DailyMed'),
        ('askcos', 'ASKCOS'),
        ('nist', 'NIST WebBook'),
        ('openfda_guidance', 'OpenFDA Guidance'),
        ('surechembl', 'SureChEMBL'),
        ('espacenet', 'Espacenet'),
        ('pdb', 'RCSB PDB'),
        ('zinc', 'ZINC20'),
        ('ccdc', 'CCDC'),
    ]

    source = models.CharField(max_length=30, choices=SOURCE_CHOICES)
    query_key = models.CharField(max_length=512, db_index=True)
    response_data = models.JSONField(default=dict)
    fetched_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        unique_together = [('source', 'query_key')]

    def __str__(self):
        return f"{self.source}:{self.query_key[:40]}"


# ─── v2 Models ───────────────────────────────────────────────────────────────

class ProjectPhase(models.Model):
    PHASE_CHOICES = [
        ('discovery', 'Discovery'),
        ('lead_optimization', 'Lead Optimization'),
        ('drug_substance', 'Drug Substance Development'),
        ('drug_product', 'Drug Product Development'),
        ('analytical', 'Analytical Development'),
        ('preclinical', 'Preclinical Development'),
        ('regulatory', 'Regulatory'),
    ]
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('complete', 'Complete'),
        ('on_hold', 'On Hold'),
    ]
    DECISION_CHOICES = [
        ('go', 'Go'),
        ('no_go', 'No Go'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='phases')
    phase = models.CharField(max_length=30, choices=PHASE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    decision = models.CharField(max_length=10, choices=DECISION_CHOICES, blank=True)
    decision_rationale = models.TextField(blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('project', 'phase')]

    def __str__(self):
        return f"{self.project.name} — {self.phase}"


class TargetProfile(models.Model):
    uniprot_id = models.CharField(max_length=20)
    gene_symbol = models.CharField(max_length=50, blank=True)
    protein_name = models.CharField(max_length=255, blank=True)
    organism = models.CharField(max_length=100, blank=True)
    pdb_ids = models.JSONField(default=list)
    selected_pdb_id = models.CharField(max_length=10, blank=True)
    binding_site_definition = models.JSONField(default=dict)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.gene_symbol or self.uniprot_id}"


class VirtualScreeningRun(models.Model):
    LIBRARY_CHOICES = [
        ('fda_approved', 'FDA Approved'),
        ('clinical_candidates', 'Clinical Candidates'),
        ('fragments', 'Fragment Library'),
        ('custom', 'Custom SMILES'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('complete', 'Complete'),
        ('failed', 'Failed'),
    ]

    target_profile = models.ForeignKey(TargetProfile, on_delete=models.CASCADE, related_name='screening_runs')
    library = models.CharField(max_length=30, choices=LIBRARY_CHOICES)
    custom_smiles = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    result_count = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"ScreeningRun({self.library}) — {self.status}"


class VirtualScreeningHit(models.Model):
    PATENT_STATUS_CHOICES = [
        ('free', 'Free to Operate'),
        ('covered', 'Patent Covered'),
        ('unknown', 'Unknown'),
    ]

    run = models.ForeignKey(VirtualScreeningRun, on_delete=models.CASCADE, related_name='hits')
    smiles = models.TextField()
    name = models.CharField(max_length=255, blank=True)
    pubchem_cid = models.IntegerField(null=True, blank=True)
    binding_affinity = models.FloatField(null=True, blank=True)
    docking_score = models.FloatField(null=True, blank=True)
    admet_data = models.JSONField(default=dict)
    patent_status = models.CharField(max_length=20, choices=PATENT_STATUS_CHOICES, default='unknown')
    shortlisted = models.BooleanField(default=False)

    def __str__(self):
        return f"Hit {self.name or self.smiles[:20]} (score={self.docking_score})"


class SAREntry(models.Model):
    ACTIVITY_TYPE_CHOICES = [
        ('IC50', 'IC50'),
        ('EC50', 'EC50'),
        ('Ki', 'Ki'),
        ('Kd', 'Kd'),
        ('% inhibition', '% Inhibition'),
        ('other', 'Other'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='sar_entries')
    compound = models.ForeignKey(Compound, on_delete=models.SET_NULL, null=True, blank=True, related_name='sar_entries')
    smiles = models.TextField()
    r_group = models.CharField(max_length=255, blank=True)
    activity_value = models.FloatField(null=True, blank=True)
    activity_unit = models.CharField(max_length=20, blank=True)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPE_CHOICES, blank=True)
    assay_description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    logp = models.FloatField(null=True, blank=True)
    mw = models.FloatField(null=True, blank=True)
    selectivity_value = models.FloatField(null=True, blank=True)
    selectivity_target = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"SAR({self.r_group or self.smiles[:20]}, {self.activity_value} {self.activity_unit})"


class FormulationPlan(models.Model):
    DOSAGE_FORM_CHOICES = [
        ('tablet', 'Tablet'),
        ('capsule', 'Capsule'),
        ('solution', 'Solution'),
        ('suspension', 'Suspension'),
        ('injection', 'Injection'),
        ('topical', 'Topical'),
        ('other', 'Other'),
    ]
    ROUTE_CHOICES = [
        ('oral', 'Oral'),
        ('intravenous', 'Intravenous'),
        ('subcutaneous', 'Subcutaneous'),
        ('intramuscular', 'Intramuscular'),
        ('topical', 'Topical'),
        ('inhalation', 'Inhalation'),
        ('other', 'Other'),
    ]
    RELEASE_TYPE_CHOICES = [
        ('immediate', 'Immediate Release'),
        ('modified', 'Modified Release'),
        ('extended', 'Extended Release'),
        ('delayed', 'Delayed Release'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('finalized', 'Finalized'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='formulation_plans')
    dosage_form = models.CharField(max_length=30, choices=DOSAGE_FORM_CHOICES)
    route_of_administration = models.CharField(max_length=30, choices=ROUTE_CHOICES)
    target_dose_mg = models.FloatField(null=True, blank=True)
    release_type = models.CharField(max_length=30, choices=RELEASE_TYPE_CHOICES, default='immediate')
    manufacturing_process = models.TextField(blank=True)
    rationale = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Formulation({self.dosage_form}) for {self.project.name}"


class FormulationComponent(models.Model):
    COMPONENT_TYPE_CHOICES = [
        ('api', 'Active Pharmaceutical Ingredient'),
        ('diluent', 'Diluent/Filler'),
        ('binder', 'Binder'),
        ('disintegrant', 'Disintegrant'),
        ('lubricant', 'Lubricant'),
        ('coating', 'Coating'),
        ('preservative', 'Preservative'),
        ('solvent', 'Solvent'),
        ('other', 'Other'),
    ]

    formulation_plan = models.ForeignKey(FormulationPlan, on_delete=models.CASCADE, related_name='components')
    component_type = models.CharField(max_length=30, choices=COMPONENT_TYPE_CHOICES)
    name = models.CharField(max_length=255)
    function = models.CharField(max_length=255, blank=True)
    concentration = models.FloatField(null=True, blank=True)
    unit = models.CharField(max_length=20, blank=True)
    grade = models.CharField(max_length=100, blank=True)
    supplier = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.component_type})"


class CompatibilityFlag(models.Model):
    FLAG_TYPE_CHOICES = [
        ('chemical', 'Chemical Incompatibility'),
        ('physical', 'Physical Incompatibility'),
        ('microbiological', 'Microbiological Concern'),
        ('regulatory', 'Regulatory Concern'),
    ]
    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]

    formulation_plan = models.ForeignKey(FormulationPlan, on_delete=models.CASCADE, related_name='compatibility_flags')
    component_a = models.CharField(max_length=255)
    component_b = models.CharField(max_length=255)
    flag_type = models.CharField(max_length=30, choices=FLAG_TYPE_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='warning')
    evidence = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.component_a} × {self.component_b} ({self.severity})"


class Excipient(models.Model):
    name = models.CharField(max_length=255, unique=True)
    iig_limit = models.FloatField(null=True, blank=True)
    iig_unit = models.CharField(max_length=50, blank=True)
    function = models.CharField(max_length=255, blank=True)
    route = models.CharField(max_length=100, blank=True)
    gras_status = models.BooleanField(null=True, blank=True)
    incompatibilities = models.JSONField(default=list)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name


class SaltPolymorphScreen(models.Model):
    SCREEN_TYPE_CHOICES = [
        ('salt', 'Salt Screen'),
        ('polymorph', 'Polymorph Screen'),
        ('cocrystal', 'Co-Crystal Screen'),
    ]
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('complete', 'Complete'),
    ]
    HYGROSCOPICITY_CHOICES = [
        ('non_hygroscopic', 'Non-hygroscopic'),
        ('slightly', 'Slightly Hygroscopic'),
        ('hygroscopic', 'Hygroscopic'),
        ('very', 'Very Hygroscopic / Deliquescent'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='salt_screens')
    compound = models.ForeignKey(Compound, on_delete=models.SET_NULL, null=True, blank=True, related_name='salt_screens')
    screen_type = models.CharField(max_length=20, choices=SCREEN_TYPE_CHOICES, default='salt')
    objective = models.TextField(blank=True)
    rationale = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    # Baseline API properties
    baseline_pka = models.FloatField(null=True, blank=True)
    baseline_melting_point_c = models.FloatField(null=True, blank=True)
    baseline_hygroscopicity = models.CharField(max_length=20, choices=HYGROSCOPICITY_CHOICES, blank=True)
    baseline_solubility_mgml = models.FloatField(null=True, blank=True)
    baseline_logp = models.FloatField(null=True, blank=True)
    baseline_notes = models.TextField(blank=True)
    # Outcome
    selected_form = models.CharField(max_length=255, blank=True)
    selection_rationale = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.screen_type} screen for {self.project.name}"


class SaltScreenCandidate(models.Model):
    SOLUBILITY_IMPACT_CHOICES = [
        ('improved', 'Improved'),
        ('neutral', 'Neutral'),
        ('decreased', 'Decreased'),
        ('unknown', 'Unknown'),
    ]

    screen = models.ForeignKey(SaltPolymorphScreen, on_delete=models.CASCADE, related_name='candidates')
    name = models.CharField(max_length=255)
    cas_number = models.CharField(max_length=30, blank=True)
    smiles = models.TextField(blank=True)
    counterion_type = models.CharField(max_length=20, blank=True)
    pka_delta = models.FloatField(null=True, blank=True)
    theoretical_solubility_impact = models.CharField(max_length=20, choices=SOLUBILITY_IMPACT_CHOICES, default='unknown')
    notes = models.TextField(blank=True)
    selected = models.BooleanField(default=False)
    # Legacy columns retained so Django includes them in INSERTs (SQLite NOT NULL with no DB-level default)
    counterion_or_polymorph = models.CharField(max_length=255, blank=True, default='')
    hygroscopicity = models.CharField(max_length=50, blank=True, default='')
    solubility_mgml = models.FloatField(null=True, blank=True)
    melting_point = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name


class SaltScreenExperiment(models.Model):
    PREP_METHOD_CHOICES = [
        ('slurry', 'Slurry'),
        ('evaporation', 'Slow Evaporation'),
        ('grinding', 'Grinding / Mechanochemistry'),
        ('spray_dry', 'Spray Drying'),
        ('antisolvent', 'Antisolvent Precipitation'),
        ('cooling', 'Cooling Crystallization'),
        ('other', 'Other'),
    ]
    OBSERVED_FORM_CHOICES = [
        ('crystalline', 'Crystalline'),
        ('amorphous', 'Amorphous'),
        ('unchanged', 'Unchanged API'),
        ('mixed', 'Mixed / Unclear'),
        ('oily', 'Oil / Gum'),
    ]

    screen = models.ForeignKey(SaltPolymorphScreen, on_delete=models.CASCADE, related_name='experiments')
    candidate = models.ForeignKey(SaltScreenCandidate, on_delete=models.SET_NULL, null=True, blank=True, related_name='experiments')
    prep_method = models.CharField(max_length=20, choices=PREP_METHOD_CHOICES, default='slurry')
    solvent = models.CharField(max_length=200, blank=True)
    ratio = models.CharField(max_length=50, blank=True)
    temperature_c = models.FloatField(null=True, blank=True)
    # Characterization results
    results_xrpd = models.TextField(blank=True)
    results_dsc = models.TextField(blank=True)
    results_tga = models.TextField(blank=True)
    results_solubility = models.CharField(max_length=100, blank=True)
    results_appearance = models.CharField(max_length=200, blank=True)
    observed_form = models.CharField(max_length=20, choices=OBSERVED_FORM_CHOICES, blank=True)
    notes = models.TextField(blank=True)
    # Legacy fields kept for backward compatibility
    method = models.CharField(max_length=255, blank=True)
    conditions = models.JSONField(default=dict)
    results = models.JSONField(default=dict)
    outcome = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        candidate_name = self.candidate.name if self.candidate else 'unknown'
        return f"{self.prep_method} — {candidate_name}"


class StabilityPlan(models.Model):
    MATERIAL_TYPE_CHOICES = [
        ('api', 'API (Drug Substance)'),
        ('dp', 'Drug Product'),
        ('intermediate', 'Intermediate'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('complete', 'Complete'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='stability_plans')
    material_type = models.CharField(max_length=20, choices=MATERIAL_TYPE_CHOICES)
    intended_storage_condition = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Stability Plan ({self.material_type}) for {self.project.name}"


class StabilityCondition(models.Model):
    plan = models.ForeignKey(StabilityPlan, on_delete=models.CASCADE, related_name='conditions')
    condition_label = models.CharField(max_length=100)
    temperature_c = models.FloatField(null=True, blank=True)
    humidity_rh = models.FloatField(null=True, blank=True)
    light_exposure = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.condition_label


class StabilityResult(models.Model):
    condition = models.ForeignKey(StabilityCondition, on_delete=models.CASCADE, related_name='results')
    timepoint_weeks = models.FloatField()
    appearance = models.CharField(max_length=255, blank=True)
    assay_pct = models.FloatField(null=True, blank=True)
    degradants_pct = models.FloatField(null=True, blank=True)
    ph = models.FloatField(null=True, blank=True)
    water_content_pct = models.FloatField(null=True, blank=True)
    dissolution_pct = models.FloatField(null=True, blank=True)
    oos_flag = models.BooleanField(default=False)
    oot_flag = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.condition.condition_label} @ {self.timepoint_weeks}w"


class AnalyticalMethod(models.Model):
    METHOD_TYPE_CHOICES = [
        ('hplc', 'HPLC'),
        ('gc', 'GC'),
        ('nmr', 'NMR'),
        ('ms', 'Mass Spectrometry'),
        ('uv_vis', 'UV-Vis'),
        ('dissolution', 'Dissolution'),
        ('particle_size', 'Particle Size'),
        ('other', 'Other'),
    ]
    VALIDATION_STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('validated', 'Validated'),
        ('transferred', 'Transferred'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='analytical_methods')
    method_name = models.CharField(max_length=255)
    method_type = models.CharField(max_length=30, choices=METHOD_TYPE_CHOICES)
    analyte = models.CharField(max_length=255, blank=True)
    instrument = models.CharField(max_length=255, blank=True)
    principle = models.TextField(blank=True)
    validation_status = models.CharField(max_length=20, choices=VALIDATION_STATUS_CHOICES, default='not_started')
    protocol = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.method_name} ({self.method_type})"


class Specification(models.Model):
    SPEC_TYPE_CHOICES = [
        ('release', 'Release'),
        ('shelf_life', 'Shelf Life'),
        ('in_process', 'In-Process'),
        ('raw_material', 'Raw Material'),
    ]
    CRITERIA_TYPE_CHOICES = [
        ('NMT', 'NMT (Not More Than)'),
        ('NLT', 'NLT (Not Less Than)'),
        ('between', 'Between (Range)'),
        ('conforms', 'Conforms To'),
        ('report', 'Report Only'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='specifications')
    analytical_method = models.ForeignKey(AnalyticalMethod, on_delete=models.SET_NULL, null=True, blank=True, related_name='specifications')
    spec_type = models.CharField(max_length=20, choices=SPEC_TYPE_CHOICES, default='release')
    attribute = models.CharField(max_length=255)
    criteria_type = models.CharField(max_length=20, choices=CRITERIA_TYPE_CHOICES, default='NMT', blank=True)
    acceptance_criteria = models.CharField(max_length=500)
    test_method = models.CharField(max_length=255, blank=True)
    basis = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.attribute}: {self.acceptance_criteria}"


class PreclinicalStudy(models.Model):
    STUDY_TYPE_CHOICES = [
        ('acute_tox', 'Acute Toxicity'),
        ('repeat_dose', 'Repeat-Dose Toxicity'),
        ('genotox', 'Genotoxicity'),
        ('pk', 'Pharmacokinetics'),
        ('pd', 'Pharmacodynamics'),
        ('safety_pharm', 'Safety Pharmacology'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('complete', 'Complete'),
        ('reported', 'Reported'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='preclinical_studies')
    title = models.CharField(max_length=255, blank=True)
    study_type = models.CharField(max_length=30, choices=STUDY_TYPE_CHOICES)
    glp = models.BooleanField(default=False)
    species = models.CharField(max_length=100, blank=True)
    dose_route = models.CharField(max_length=100, blank=True)
    dose_levels = models.JSONField(default=list)
    duration_days = models.IntegerField(null=True, blank=True)
    objective = models.TextField(blank=True)
    primary_endpoints = models.JSONField(default=list)
    success_criteria = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    key_findings = models.JSONField(default=dict)
    results_summary = models.TextField(blank=True)
    conclusion = models.CharField(max_length=20, blank=True)
    mtd_mgkg = models.FloatField(null=True, blank=True)
    noael_mgkg = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.study_type} study for {self.project.name}"
