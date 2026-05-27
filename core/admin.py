from django.contrib import admin
from .models import (
    Project, Compound, CompoundProperty, Experiment, ExperimentResult,
    RiskAssessment, Document, ChatSession, ChatMessage, ExternalDataCache,
)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'phase', 'status', 'created_at']
    list_filter = ['phase', 'status']
    search_fields = ['name']


@admin.register(Compound)
class CompoundAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'chembl_id', 'pubchem_cid', 'molecular_weight']
    list_filter = ['project']
    search_fields = ['name', 'chembl_id']


@admin.register(CompoundProperty)
class CompoundPropertyAdmin(admin.ModelAdmin):
    list_display = ['compound', 'property_type', 'source', 'fetched_at']
    list_filter = ['property_type', 'source']


@admin.register(Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'experiment_type', 'status', 'created_at']
    list_filter = ['experiment_type', 'status', 'project']
    search_fields = ['title']


@admin.register(ExperimentResult)
class ExperimentResultAdmin(admin.ModelAdmin):
    list_display = ['experiment', 'decision', 'recorded_at']
    list_filter = ['decision']


@admin.register(RiskAssessment)
class RiskAssessmentAdmin(admin.ModelAdmin):
    list_display = ['project', 'created_at', 'updated_at']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'doc_type', 'created_at']
    list_filter = ['doc_type', 'project']
    search_fields = ['title']


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'created_at', 'updated_at']
    list_filter = ['project']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session', 'role', 'created_at']
    list_filter = ['role', 'session']


@admin.register(ExternalDataCache)
class ExternalDataCacheAdmin(admin.ModelAdmin):
    list_display = ['source', 'query_key', 'fetched_at', 'expires_at']
    list_filter = ['source']
