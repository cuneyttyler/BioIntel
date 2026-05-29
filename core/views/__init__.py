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
