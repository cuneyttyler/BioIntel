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
