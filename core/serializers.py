from rest_framework import serializers
from .models import (
    Project, Compound, CompoundProperty, Experiment, ExperimentResult,
    RiskAssessment, Document, ChatSession, ChatMessage,
)


class ProjectSerializer(serializers.ModelSerializer):
    experiment_count = serializers.SerializerMethodField()
    compound_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = '__all__'

    def get_experiment_count(self, obj):
        return obj.experiments.count()

    def get_compound_count(self, obj):
        return obj.compounds.count()


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


class ChatSessionListSerializer(serializers.ModelSerializer):
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = ['id', 'project', 'title', 'message_count', 'created_at', 'updated_at']

    def get_message_count(self, obj):
        return obj.messages.count()
