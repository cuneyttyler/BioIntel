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
    DrugSearchView, DrugDetailView, DrugSynthesisView, DrugTrialsView, DrugPatentsView,
    PatentSearchView, PatentDetailView,
    AnalogSearchView, AnalogPatentCheckView, AnalogADMETView,
    InvestigationListCreateView, InvestigationDetailView, InvestigationLinkProjectView,
    AnalogCandidateView, AnalogCandidateDetailView,
    SynthesisPlanListCreateView, SynthesisPlanDetailView, SynthesisPlanExperimentsView,
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

    # Drug Intelligence
    path('drugs/search/', DrugSearchView.as_view()),
    path('drugs/<str:chembl_id>/synthesis/', DrugSynthesisView.as_view()),
    path('drugs/<str:chembl_id>/trials/', DrugTrialsView.as_view()),
    path('drugs/<str:chembl_id>/patents/', DrugPatentsView.as_view()),
    path('drugs/<str:chembl_id>/', DrugDetailView.as_view()),

    # Patents
    path('patents/', PatentSearchView.as_view()),
    path('patents/<str:patent_number>/', PatentDetailView.as_view()),

    # Analogs & Investigations
    path('analogs/search/', AnalogSearchView.as_view()),
    path('analogs/patent-check/', AnalogPatentCheckView.as_view()),
    path('analogs/admet/', AnalogADMETView.as_view()),
    path('investigations/', InvestigationListCreateView.as_view()),
    path('investigations/<int:pk>/', InvestigationDetailView.as_view()),
    path('investigations/<int:pk>/link-project/', InvestigationLinkProjectView.as_view()),
    path('investigations/<int:pk>/candidates/', AnalogCandidateView.as_view()),
    path('analog-candidates/<int:pk>/', AnalogCandidateDetailView.as_view()),

    # Synthesis Plans
    path('synthesis-plans/', SynthesisPlanListCreateView.as_view()),
    path('synthesis-plans/<int:pk>/', SynthesisPlanDetailView.as_view()),
    path('synthesis-plans/<int:pk>/plan-experiments/', SynthesisPlanExperimentsView.as_view()),
]
