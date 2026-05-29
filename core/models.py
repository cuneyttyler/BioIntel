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

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    phase = models.CharField(max_length=20, choices=PHASE_CHOICES, default='preclinical')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
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
