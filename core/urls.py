from django.urls import path
from core.views import (
    ProjectListCreateView, ProjectDetailView,
    CompoundSearchView, CompoundListCreateView, CompoundDetailView,
    CompoundPropertiesView, CompoundADMETView, CompoundSafetyView,
    CompoundTargetsView, CompoundStructureView, CompoundSimilarView,
    CompoundSpectraView,
    DiseaseSearchView, DiseaseTargetsView, DiseaseDrugsView, TargetDetailView,
    RecentExperimentsView, ExperimentListCreateView, ExperimentDetailView,
    ExperimentResultsView, ExperimentInterpretView,
    RiskAssessmentView, GenerateRiskAssessmentView,
    RetroSynthesisView, SynthesisTreeView, ForwardPredictionView,
    ConditionRecommendView, BuyableCheckView,
    LiteratureSearchView, ArticleDetailView, TrialSearchView, TrialDetailView,
    GuidanceSearchView, DrugLabelsView, NDCView, ExcipientsView,
    ChatSessionListCreateView, ChatSessionDetailView, ChatMessageView,
    ProjectDocumentListCreateView, GenerateDocumentView,
    DocumentDetailView, DocumentExportView,
)

urlpatterns = [
    # Projects
    path('projects/', ProjectListCreateView.as_view()),
    path('projects/<int:pk>/', ProjectDetailView.as_view()),
    path('projects/<int:pk>/risk-assessment/', RiskAssessmentView.as_view()),
    path('projects/<int:pk>/risk-assessment/generate/', GenerateRiskAssessmentView.as_view()),
    path('projects/<int:pk>/documents/', ProjectDocumentListCreateView.as_view()),
    path('projects/<int:pk>/documents/generate/', GenerateDocumentView.as_view()),

    # Compounds
    path('compounds/search/', CompoundSearchView.as_view()),
    path('compounds/spectra/', CompoundSpectraView.as_view()),
    path('compounds/', CompoundListCreateView.as_view()),
    path('compounds/<int:pk>/', CompoundDetailView.as_view()),
    path('compounds/<int:pk>/properties/', CompoundPropertiesView.as_view()),
    path('compounds/<int:pk>/admet/', CompoundADMETView.as_view()),
    path('compounds/<int:pk>/safety/', CompoundSafetyView.as_view()),
    path('compounds/<int:pk>/targets/', CompoundTargetsView.as_view()),
    path('compounds/<int:pk>/structure/', CompoundStructureView.as_view()),
    path('compounds/<int:pk>/similar/', CompoundSimilarView.as_view()),

    # Diseases & Targets
    path('diseases/search/', DiseaseSearchView.as_view()),
    path('diseases/<str:efo_id>/targets/', DiseaseTargetsView.as_view()),
    path('diseases/<str:efo_id>/drugs/', DiseaseDrugsView.as_view()),
    path('targets/<str:gene_symbol>/', TargetDetailView.as_view()),

    # Experiments
    path('experiments/recent/', RecentExperimentsView.as_view()),
    path('experiments/', ExperimentListCreateView.as_view()),
    path('experiments/<int:pk>/', ExperimentDetailView.as_view()),
    path('experiments/<int:pk>/results/', ExperimentResultsView.as_view()),
    path('experiments/<int:pk>/interpret/', ExperimentInterpretView.as_view()),

    # Synthesis
    path('synthesis/retro/', RetroSynthesisView.as_view()),
    path('synthesis/tree/', SynthesisTreeView.as_view()),
    path('synthesis/forward/', ForwardPredictionView.as_view()),
    path('synthesis/conditions/', ConditionRecommendView.as_view()),
    path('synthesis/buyables/', BuyableCheckView.as_view()),

    # Literature & Clinical Trials
    path('literature/search/', LiteratureSearchView.as_view()),
    path('literature/<str:pmid>/', ArticleDetailView.as_view()),
    path('trials/search/', TrialSearchView.as_view()),
    path('trials/<str:nct_id>/', TrialDetailView.as_view()),

    # Regulatory
    path('regulatory/guidance/', GuidanceSearchView.as_view()),
    path('regulatory/labels/', DrugLabelsView.as_view()),
    path('regulatory/ndc/', NDCView.as_view()),
    path('regulatory/excipients/', ExcipientsView.as_view()),

    # Chat
    path('chat/sessions/', ChatSessionListCreateView.as_view()),
    path('chat/sessions/<int:pk>/', ChatSessionDetailView.as_view()),
    path('chat/sessions/<int:pk>/messages/', ChatMessageView.as_view()),

    # Documents
    path('documents/<int:pk>/', DocumentDetailView.as_view()),
    path('documents/<int:pk>/export/', DocumentExportView.as_view()),
]
