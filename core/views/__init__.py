from .projects import ProjectListCreateView, ProjectDetailView
from .compounds import (
    CompoundSearchView, CompoundListCreateView, CompoundDetailView,
    CompoundPropertiesView, CompoundADMETView, CompoundSafetyView,
    CompoundTargetsView, CompoundStructureView, CompoundSimilarView,
    CompoundSpectraView,
)
from .diseases import DiseaseSearchView, DiseaseTargetsView, DiseaseDrugsView, TargetDetailView
from .experiments import (
    RecentExperimentsView, ExperimentListCreateView, ExperimentDetailView,
    ExperimentResultsView, ExperimentInterpretView,
)
from .risk import RiskAssessmentView, GenerateRiskAssessmentView
from .synthesis import (
    RetroSynthesisView, SynthesisTreeView, ForwardPredictionView,
    ConditionRecommendView, BuyableCheckView,
)
from .literature import LiteratureSearchView, ArticleDetailView, TrialSearchView, TrialDetailView
from .regulatory import GuidanceSearchView, DrugLabelsView, NDCView, ExcipientsView
from .chat import ChatSessionListCreateView, ChatSessionDetailView, ChatMessageView
from .documents import (
    ProjectDocumentListCreateView, GenerateDocumentView,
    DocumentDetailView, DocumentExportView,
)
from .drugs import (
    DrugSearchView, DrugDetailView, DrugSynthesisView,
    DrugTrialsView, DrugPatentsView,
)
from .patents import PatentSearchView, PatentDetailView
from .analogs import (
    AnalogSearchView, AnalogPatentCheckView, AnalogADMETView,
    InvestigationListCreateView, InvestigationDetailView, InvestigationLinkProjectView,
    AnalogCandidateView, AnalogCandidateDetailView,
)
from .synthesis_plans import (
    SynthesisPlanListCreateView, SynthesisPlanDetailView, SynthesisPlanExperimentsView,
)
from .project_phases import ProjectPhaseListView, ProjectPhaseDetailView, ProjectPhaseDecisionView
from .targets import TargetProfileListCreateView, TargetProfileDetailView, TargetPDBView, TargetBindingSitesView, TargetUniProtView
from .virtual_screening import (
    VirtualScreeningRunListCreateView, VirtualScreeningRunDetailView,
    VirtualScreeningRunPollView, VirtualScreeningHitListView, VirtualScreeningHitShortlistView,
)
from .sar import SAREntryListCreateView, SAREntryDetailView, ProjectSARHeatmapView
from .formulation import (
    FormulationPlanListCreateView, FormulationPlanDetailView, FormulationComponentView,
    CompatibilityCheckView, FormulationContextView, ExcipientSearchView,
)
from .salt_screening import (
    SaltScreenListCreateView, SaltScreenDetailView, SaltScreenCandidateView,
    SaltScreenCandidateDetailView, SaltScreenExperimentView, SaltScreenExperimentDetailView,
    CCDCLookupView,
)
from .stability import (
    StabilityPlanListCreateView, StabilityPlanDetailView, StabilityConditionView,
    StabilityResultView, StabilityMatrixView, StabilityContextView,
)
from .analytical import (
    AnalyticalMethodListCreateView, AnalyticalMethodDetailView,
    AnalyticalMethodValidationView, SpecificationListCreateView, SpecificationDetailView,
)
from .preclinical import (
    PreclinicalStudyListCreateView, PreclinicalStudyDetailView,
    PreclinicalStudyResultsView, ADMETDashboardView, PreclinicalContextView,
)
from .context import (
    ProjectContextView, CompoundContextView, SynthesisPlanContextView,
    FormulationPlanContextView, StabilityPlanContextView, PreclinicalStudyContextView,
)
