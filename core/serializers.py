from rest_framework import serializers
from .models import (
    Project, Compound, CompoundProperty, Experiment, ExperimentResult,
    RiskAssessment, Document, ChatSession, ChatMessage,
    DrugInvestigation, AnalogCandidate, SynthesisPlan,
    ProjectPhase, TargetProfile, VirtualScreeningRun, VirtualScreeningHit,
    SAREntry, FormulationPlan, FormulationComponent, CompatibilityFlag, Excipient,
    SaltPolymorphScreen, SaltScreenCandidate, SaltScreenExperiment,
    StabilityPlan, StabilityCondition, StabilityResult,
    AnalyticalMethod, Specification, PreclinicalStudy,
    AIPlan, AIPlanStep, AIPlanDiscussion, AILabSession,
    RagDocument, RagChunk,
    CellLineDevelopment, BioprocessDevelopment, DownstreamPurification,
    BiologicsFormulation, BiologicsCharacterizationMethod,
)


class SynthesisPlanSerializer(serializers.ModelSerializer):
    experiment_count = serializers.SerializerMethodField()

    class Meta:
        model = SynthesisPlan
        fields = ['id', 'project', 'analog_candidate', 'target_smiles', 'plan_type', 'route_data', 'status', 'created_at', 'experiment_count']
        extra_kwargs = {'analog_candidate': {'required': False, 'allow_null': True}}

    def get_experiment_count(self, obj):
        return obj.experiments.count()


class SynthesisPlanMinimalSerializer(serializers.ModelSerializer):
    experiment_count = serializers.SerializerMethodField()

    class Meta:
        model = SynthesisPlan
        fields = ['id', 'analog_candidate', 'target_smiles', 'plan_type', 'status', 'created_at', 'experiment_count']

    def get_experiment_count(self, obj):
        return obj.experiments.count()


class ProjectSerializer(serializers.ModelSerializer):
    experiment_count = serializers.SerializerMethodField()
    compound_count = serializers.SerializerMethodField()
    synthesis_plans = SynthesisPlanMinimalSerializer(many=True, read_only=True)
    investigations = serializers.SerializerMethodField()
    analog_candidates = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = '__all__'

    def get_experiment_count(self, obj):
        return obj.experiments.count()

    def get_compound_count(self, obj):
        return obj.compounds.count()

    def get_investigations(self, obj):
        return [
            {'id': inv.id, 'name': inv.name, 'chembl_id': inv.chembl_id, 'smiles': inv.smiles, 'disease_name': inv.disease_name}
            for inv in obj.investigations.all()
        ]

    def get_analog_candidates(self, obj):
        result = []
        for c in obj.analog_candidates.filter(shortlisted=True):
            plans = {p.plan_type: p.id for p in c.synthesis_plans.all()}
            result.append({
                'id': c.id, 'smiles': c.smiles, 'pubchem_cid': c.pubchem_cid,
                'similarity_score': c.similarity_score, 'patent_status': c.patent_status,
                'shortlisted': c.shortlisted,
                'retro_plan_id': plans.get('retro'),
                'tree_plan_id': plans.get('tree'),
            })
        return result


class CompoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Compound
        fields = '__all__'


class CompoundPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = CompoundProperty
        fields = '__all__'


class ExperimentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experiment
        fields = '__all__'
        extra_kwargs = {'synthesis_plan': {'required': False, 'allow_null': True}}


class ExperimentResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperimentResult
        fields = '__all__'


class RiskAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskAssessment
        fields = '__all__'


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = '__all__'


class ChatSessionSerializer(serializers.ModelSerializer):
    message_count = serializers.SerializerMethodField()
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = '__all__'

    def get_message_count(self, obj):
        return obj.messages.count()


class AnalogCandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalogCandidate
        fields = '__all__'


class DrugInvestigationSerializer(serializers.ModelSerializer):
    candidate_count = serializers.SerializerMethodField()

    class Meta:
        model = DrugInvestigation
        fields = '__all__'

    def get_candidate_count(self, obj):
        return obj.candidates.count()


class ChatSessionListSerializer(serializers.ModelSerializer):
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = ['id', 'project', 'title', 'message_count', 'created_at', 'updated_at']

    def get_message_count(self, obj):
        return obj.messages.count()


# ─── v2 Serializers ───────────────────────────────────────────────────────────

class ProjectPhaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPhase
        fields = '__all__'
        extra_kwargs = {'project': {'required': False}}


class TargetProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TargetProfile
        fields = '__all__'


class VirtualScreeningHitSerializer(serializers.ModelSerializer):
    class Meta:
        model = VirtualScreeningHit
        fields = '__all__'


class VirtualScreeningRunSerializer(serializers.ModelSerializer):
    hit_count = serializers.SerializerMethodField()

    class Meta:
        model = VirtualScreeningRun
        fields = '__all__'

    def get_hit_count(self, obj):
        return obj.hits.count()


class SAREntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = SAREntry
        fields = '__all__'
        read_only_fields = ('project', 'created_at')
        extra_kwargs = {'compound': {'required': False, 'allow_null': True}}


class FormulationComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormulationComponent
        fields = '__all__'
        extra_kwargs = {'formulation_plan': {'required': False}}


class CompatibilityFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompatibilityFlag
        fields = '__all__'
        extra_kwargs = {'formulation_plan': {'required': False}}


class FormulationPlanSerializer(serializers.ModelSerializer):
    components = FormulationComponentSerializer(many=True, read_only=True)
    compatibility_flags = CompatibilityFlagSerializer(many=True, read_only=True)

    class Meta:
        model = FormulationPlan
        fields = '__all__'
        read_only_fields = ('project', 'created_at', 'updated_at')


class ExcipientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Excipient
        fields = '__all__'


class SaltScreenCandidateSerializer(serializers.ModelSerializer):
    experiment_count = serializers.SerializerMethodField()

    def get_experiment_count(self, obj):
        return obj.experiments.count()

    class Meta:
        model = SaltScreenCandidate
        fields = '__all__'
        extra_kwargs = {'screen': {'required': False}}


class SaltScreenExperimentSerializer(serializers.ModelSerializer):
    candidate_name = serializers.SerializerMethodField()

    def get_candidate_name(self, obj):
        return obj.candidate.name if obj.candidate else None

    class Meta:
        model = SaltScreenExperiment
        fields = '__all__'
        extra_kwargs = {'screen': {'required': False}}


class SaltPolymorphScreenSerializer(serializers.ModelSerializer):
    candidates = SaltScreenCandidateSerializer(many=True, read_only=True)

    class Meta:
        model = SaltPolymorphScreen
        fields = '__all__'
        read_only_fields = ('project', 'compound', 'created_at', 'updated_at')


class StabilityConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StabilityCondition
        fields = '__all__'
        extra_kwargs = {'plan': {'required': False}}


class StabilityResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = StabilityResult
        fields = '__all__'
        extra_kwargs = {'condition': {'required': False}}


class StabilityPlanSerializer(serializers.ModelSerializer):
    conditions = StabilityConditionSerializer(many=True, read_only=True)

    class Meta:
        model = StabilityPlan
        fields = '__all__'
        read_only_fields = ('project', 'created_at', 'updated_at')


class AnalyticalMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticalMethod
        fields = '__all__'
        read_only_fields = ('project', 'created_at', 'updated_at')


class SpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specification
        fields = '__all__'
        read_only_fields = ('project', 'created_at')
        extra_kwargs = {'analytical_method': {'required': False, 'allow_null': True}}


class PreclinicalStudySerializer(serializers.ModelSerializer):
    class Meta:
        model = PreclinicalStudy
        fields = '__all__'
        read_only_fields = ('project', 'created_at', 'updated_at')


# ─── v3 Serializers ───────────────────────────────────────────────────────────

class AIPlanStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIPlanStep
        fields = '__all__'
        read_only_fields = ('plan', 'created_at', 'updated_at')


class AIPlanDiscussionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIPlanDiscussion
        fields = '__all__'
        read_only_fields = ('plan', 'created_at')


class AIPlanSerializer(serializers.ModelSerializer):
    steps = AIPlanStepSerializer(many=True, read_only=True)
    discussion_count = serializers.SerializerMethodField()

    class Meta:
        model = AIPlan
        fields = '__all__'
        read_only_fields = ('project', 'created_at', 'updated_at')

    def get_discussion_count(self, obj):
        return obj.discussions.count()


class AIPlanListSerializer(serializers.ModelSerializer):
    step_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = AIPlan
        fields = ['id', 'project', 'status', 'molecule_type', 'step_count', 'current_step_number', 'created_at', 'updated_at']


class AILabSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AILabSession
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class RagDocumentSerializer(serializers.ModelSerializer):
    chunk_count = serializers.SerializerMethodField()

    class Meta:
        model = RagDocument
        fields = '__all__'
        read_only_fields = ('created_at', 'ingestion_status', 'page_count', 'file_path', 'uploaded_by')

    def get_chunk_count(self, obj):
        return obj.chunks.count()


class CellLineDevelopmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CellLineDevelopment
        fields = '__all__'
        read_only_fields = ('project', 'created_at', 'updated_at')


class BioprocessDevelopmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BioprocessDevelopment
        fields = '__all__'
        read_only_fields = ('project', 'created_at', 'updated_at')


class DownstreamPurificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DownstreamPurification
        fields = '__all__'
        read_only_fields = ('project', 'created_at', 'updated_at')


class BiologicsFormulationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BiologicsFormulation
        fields = '__all__'
        read_only_fields = ('project', 'created_at', 'updated_at')


class BiologicsCharacterizationMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = BiologicsCharacterizationMethod
        fields = '__all__'
        read_only_fields = ('project', 'created_at', 'updated_at')
