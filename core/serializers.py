from rest_framework import serializers
from .models import (
    Project, Compound, CompoundProperty, Experiment, ExperimentResult,
    RiskAssessment, Document, ChatSession, ChatMessage,
    DrugInvestigation, AnalogCandidate, SynthesisPlan,
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
