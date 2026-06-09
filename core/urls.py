from django.urls import path
from core.views.ai_plan import (
    ProjectAIPlanView, AIPlanDetailView, AIPlanGenerateView, AIPlanCompressContextView,
    AIPlanStepDetailView, AIPlanStepApproveView, AIPlanStepRejectView, AIPlanStepSkipView,
    AIPlanStepRecommendView, AIPlanStepDiscussView, AIPlanStepAnalyzeResultsView,
    AIPlanStepGoBackView, AIPlanDiscussionListView, AIPlanStepExecuteActionView,
)
from core.views.ai_lab import (
    AILabSessionListCreateView, AILabSessionDetailView,
    AILabSessionMessageView, AILabSessionCreateProjectView,
)
from core.views.ai_panel import AIPanelChatView
from core.views.panel_history import PanelHistoryView
from core.views.rag_documents import (
    RagDocumentListCreateView, RagDocumentDetailView,
    RagDocumentIngestView, RagDocumentSearchView,
)
from core.views.settings_view import AppSettingsView
from core.views.biologics import (
    ProjectCellLineView, CellLineDevelopmentDetailView,
    ProjectBioprocessView, BioprocessDevelopmentDetailView,
    ProjectPurificationView, DownstreamPurificationDetailView,
    ProjectBiologicsFormulationView, BiologicsFormulationDetailView,
    ProjectBiologicsAnalyticsView, BiologicsCharacterizationMethodDetailView,
)
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
    # v2
    ProjectPhaseListView, ProjectPhaseDetailView, ProjectPhaseDecisionView,
    TargetProfileListCreateView, TargetProfileDetailView, TargetPDBView,
    TargetBindingSitesView, TargetUniProtView,
    VirtualScreeningRunListCreateView, VirtualScreeningRunDetailView,
    VirtualScreeningRunPollView, VirtualScreeningHitListView, VirtualScreeningHitShortlistView,
    SAREntryListCreateView, SAREntryDetailView, ProjectSARHeatmapView,
    FormulationPlanListCreateView, FormulationPlanDetailView, FormulationComponentView,
    CompatibilityCheckView, FormulationContextView, ExcipientSearchView,
    SaltScreenListCreateView, SaltScreenDetailView, SaltScreenCandidateView,
    SaltScreenCandidateDetailView, SaltScreenExperimentView, SaltScreenExperimentDetailView,
    CCDCLookupView,
    StabilityPlanListCreateView, StabilityPlanDetailView, StabilityConditionView,
    StabilityResultView, StabilityMatrixView, StabilityContextView,
    AnalyticalMethodListCreateView, AnalyticalMethodDetailView,
    AnalyticalMethodValidationView, SpecificationListCreateView, SpecificationDetailView,
    PreclinicalStudyListCreateView, PreclinicalStudyDetailView,
    PreclinicalStudyResultsView, ADMETDashboardView, PreclinicalContextView,
    ProjectContextView, CompoundContextView, SynthesisPlanContextView,
    FormulationPlanContextView, StabilityPlanContextView, PreclinicalStudyContextView,
)

urlpatterns = [
    # Projects
    path('projects/', ProjectListCreateView.as_view()),
    path('projects/<int:pk>/', ProjectDetailView.as_view()),
    path('projects/<int:pk>/risk-assessment/', RiskAssessmentView.as_view()),
    path('projects/<int:pk>/risk-assessment/generate/', GenerateRiskAssessmentView.as_view()),
    path('projects/<int:pk>/documents/', ProjectDocumentListCreateView.as_view()),
    path('projects/<int:pk>/documents/generate/', GenerateDocumentView.as_view()),
    path('projects/<int:pk>/context/', ProjectContextView.as_view()),

    # Project Phases (v2)
    path('projects/<int:pk>/phases/', ProjectPhaseListView.as_view()),
    path('projects/<int:pk>/phases/<int:phase_pk>/', ProjectPhaseDetailView.as_view()),
    path('projects/<int:pk>/phases/<int:phase_pk>/decision/', ProjectPhaseDecisionView.as_view()),

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
    path('compounds/<int:pk>/context/', CompoundContextView.as_view()),

    # Diseases & Targets
    path('diseases/search/', DiseaseSearchView.as_view()),
    path('diseases/<str:efo_id>/targets/', DiseaseTargetsView.as_view()),
    path('diseases/<str:efo_id>/drugs/', DiseaseDrugsView.as_view()),
    path('targets/<str:gene_symbol>/', TargetDetailView.as_view()),

    # Target Profiles (v2)
    path('target-profiles/', TargetProfileListCreateView.as_view()),
    path('target-profiles/<int:pk>/', TargetProfileDetailView.as_view()),
    path('target-profiles/<int:pk>/pdb/', TargetPDBView.as_view()),
    path('target-profiles/<int:pk>/binding-sites/', TargetBindingSitesView.as_view()),
    path('target-profiles/<int:pk>/uniprot/', TargetUniProtView.as_view()),

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

    # Synthesis Plans
    path('synthesis-plans/', SynthesisPlanListCreateView.as_view()),
    path('synthesis-plans/<int:pk>/', SynthesisPlanDetailView.as_view()),
    path('synthesis-plans/<int:pk>/plan-experiments/', SynthesisPlanExperimentsView.as_view()),
    path('synthesis-plans/<int:pk>/context/', SynthesisPlanContextView.as_view()),

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

    # Virtual Screening (v2)
    path('virtual-screening/runs/', VirtualScreeningRunListCreateView.as_view()),
    path('virtual-screening/runs/<int:pk>/', VirtualScreeningRunDetailView.as_view()),
    path('virtual-screening/runs/<int:pk>/poll/', VirtualScreeningRunPollView.as_view()),
    path('virtual-screening/runs/<int:pk>/hits/', VirtualScreeningHitListView.as_view()),
    path('virtual-screening/hits/<int:pk>/shortlist/', VirtualScreeningHitShortlistView.as_view()),

    # SAR Tracker (v2)
    path('projects/<int:pk>/sar/', SAREntryListCreateView.as_view()),
    path('projects/<int:pk>/sar/heatmap/', ProjectSARHeatmapView.as_view()),
    path('sar-entries/<int:pk>/', SAREntryDetailView.as_view()),

    # Formulation (v2)
    path('projects/<int:pk>/formulation/', FormulationPlanListCreateView.as_view()),
    path('formulation-plans/<int:pk>/', FormulationPlanDetailView.as_view()),
    path('formulation-plans/<int:pk>/components/', FormulationComponentView.as_view()),
    path('formulation-plans/<int:pk>/components/<int:component_pk>/', FormulationComponentView.as_view()),
    path('formulation-plans/<int:pk>/compatibility/', CompatibilityCheckView.as_view()),
    path('formulation-plans/<int:pk>/context/', FormulationPlanContextView.as_view()),
    path('excipients/search/', ExcipientSearchView.as_view()),

    # Salt/Polymorph Screening (v2)
    path('projects/<int:pk>/salt-screens/', SaltScreenListCreateView.as_view()),
    path('salt-screens/<int:pk>/', SaltScreenDetailView.as_view()),
    path('salt-screens/<int:pk>/candidates/', SaltScreenCandidateView.as_view()),
    path('salt-screen-candidates/<int:pk>/', SaltScreenCandidateDetailView.as_view()),
    path('salt-screens/<int:pk>/experiments/', SaltScreenExperimentView.as_view()),
    path('salt-screen-experiments/<int:pk>/', SaltScreenExperimentDetailView.as_view()),
    path('ccdc/lookup/', CCDCLookupView.as_view()),

    # Stability (v2)
    path('projects/<int:pk>/stability/', StabilityPlanListCreateView.as_view()),
    path('stability-plans/<int:pk>/', StabilityPlanDetailView.as_view()),
    path('stability-plans/<int:pk>/conditions/', StabilityConditionView.as_view()),
    path('stability-plans/<int:pk>/results/', StabilityResultView.as_view()),
    path('stability-plans/<int:pk>/matrix/', StabilityMatrixView.as_view()),
    path('stability-plans/<int:pk>/context/', StabilityPlanContextView.as_view()),

    # Analytical Methods & Specifications (v2)
    path('projects/<int:pk>/analytical-methods/', AnalyticalMethodListCreateView.as_view()),
    path('analytical-methods/<int:pk>/', AnalyticalMethodDetailView.as_view()),
    path('analytical-methods/<int:pk>/validation/', AnalyticalMethodValidationView.as_view()),
    path('projects/<int:pk>/specifications/', SpecificationListCreateView.as_view()),
    path('specifications/<int:pk>/', SpecificationDetailView.as_view()),

    # Preclinical Studies & ADMET Dashboard (v2)
    path('projects/<int:pk>/preclinical/', PreclinicalStudyListCreateView.as_view()),
    path('preclinical-studies/<int:pk>/', PreclinicalStudyDetailView.as_view()),
    path('preclinical-studies/<int:pk>/results/', PreclinicalStudyResultsView.as_view()),
    path('preclinical-studies/<int:pk>/context/', PreclinicalStudyContextView.as_view()),
    path('projects/<int:pk>/admet-dashboard/', ADMETDashboardView.as_view()),

    # ─── v3: AI Plan ─────────────────────────────────────────────────────────
    path('projects/<int:pk>/ai-plan/', ProjectAIPlanView.as_view()),
    path('ai-plans/<int:pk>/', AIPlanDetailView.as_view()),
    path('ai-plans/<int:pk>/generate/', AIPlanGenerateView.as_view()),
    path('ai-plans/<int:pk>/compress-context/', AIPlanCompressContextView.as_view()),
    path('ai-plan-steps/<int:pk>/', AIPlanStepDetailView.as_view()),
    path('ai-plan-steps/<int:pk>/approve/', AIPlanStepApproveView.as_view()),
    path('ai-plan-steps/<int:pk>/reject/', AIPlanStepRejectView.as_view()),
    path('ai-plan-steps/<int:pk>/skip/', AIPlanStepSkipView.as_view()),
    path('ai-plan-steps/<int:pk>/recommend/', AIPlanStepRecommendView.as_view()),
    path('ai-plan-steps/<int:pk>/discuss/', AIPlanStepDiscussView.as_view()),
    path('ai-plan-steps/<int:pk>/analyze-results/', AIPlanStepAnalyzeResultsView.as_view()),
    path('ai-plan-steps/<int:pk>/go-back/', AIPlanStepGoBackView.as_view()),
    path('ai-plan-steps/<int:pk>/discussions/', AIPlanDiscussionListView.as_view()),
    path('ai-plan-steps/<int:pk>/execute-action/', AIPlanStepExecuteActionView.as_view()),

    # ─── v3: AI Lab ──────────────────────────────────────────────────────────
    path('ai-lab/sessions/', AILabSessionListCreateView.as_view()),
    path('ai-lab/sessions/<int:pk>/', AILabSessionDetailView.as_view()),
    path('ai-lab/sessions/<int:pk>/messages/', AILabSessionMessageView.as_view()),
    path('ai-lab/sessions/<int:pk>/create-project/', AILabSessionCreateProjectView.as_view()),

    # ─── v3: Per-page AI Panel ───────────────────────────────────────────────
    path('projects/<int:pk>/ai-panel/chat/', AIPanelChatView.as_view()),
    path('projects/<int:pk>/panel-history/<str:page_type>/', PanelHistoryView.as_view()),

    # ─── v3: Document Portal (RAG) ───────────────────────────────────────────
    path('documents/', RagDocumentListCreateView.as_view()),
    path('documents/search/', RagDocumentSearchView.as_view()),
    path('documents/<int:pk>/', RagDocumentDetailView.as_view()),
    path('documents/<int:pk>/ingest/', RagDocumentIngestView.as_view()),

    # ─── v3: Biologics ───────────────────────────────────────────────────────
    path('projects/<int:pk>/cell-line/', ProjectCellLineView.as_view()),
    path('cell-line/<int:pk>/', CellLineDevelopmentDetailView.as_view()),
    path('projects/<int:pk>/bioprocessing/', ProjectBioprocessView.as_view()),
    path('bioprocessing/<int:pk>/', BioprocessDevelopmentDetailView.as_view()),
    path('projects/<int:pk>/purification/', ProjectPurificationView.as_view()),
    path('purification/<int:pk>/', DownstreamPurificationDetailView.as_view()),
    path('projects/<int:pk>/biologic-formulation/', ProjectBiologicsFormulationView.as_view()),
    path('biologic-formulation/<int:pk>/', BiologicsFormulationDetailView.as_view()),
    path('projects/<int:pk>/biologic-analytics/', ProjectBiologicsAnalyticsView.as_view()),
    path('biologic-analytics/<int:pk>/', BiologicsCharacterizationMethodDetailView.as_view()),

    # ─── App Settings ─────────────────────────────────────────────────────────
    path('settings/', AppSettingsView.as_view()),
]
