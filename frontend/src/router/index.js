import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  // ─── Existing v1 routes ───────────────────────────────────────────────────
  { path: '/', name: 'Dashboard', component: () => import('@/views/DashboardPage.vue') },
  { path: '/projects/new', name: 'ProjectNew', component: () => import('@/views/ProjectSetupPage.vue') },
  { path: '/projects/:id/edit', name: 'ProjectEdit', component: () => import('@/views/ProjectSetupPage.vue') },
  { path: '/compounds/:id', name: 'CompoundProfile', component: () => import('@/views/CompoundProfilePage.vue') },
  { path: '/diseases', name: 'DiseaseExplorer', component: () => import('@/views/DiseaseExplorerPage.vue') },
  { path: '/experiments/new', name: 'ExperimentNew', component: () => import('@/views/ExperimentPlannerPage.vue') },
  { path: '/experiments/:id', name: 'ExperimentResults', component: () => import('@/views/ExperimentResultsPage.vue') },
  { path: '/projects/:id/risk', name: 'RiskAnalysis', component: () => import('@/views/RiskAnalysisPage.vue') },
  { path: '/synthesis', name: 'SynthesisPlanning', component: () => import('@/views/SynthesisPlanningPage.vue') },
  { path: '/synthesis/compare', name: 'SynthesisPlanComparison', component: () => import('@/views/SynthesisPlanComparisonPage.vue') },
  { path: '/literature', name: 'Literature', component: () => import('@/views/LiteraturePage.vue') },
  { path: '/chat', name: 'Chat', component: () => import('@/views/ChatPage.vue') },
  { path: '/projects/:id/documents', name: 'Documentation', component: () => import('@/views/DocumentationPage.vue') },
  { path: '/drugs', name: 'DrugIntelligence', component: () => import('@/views/DrugIntelligencePage.vue') },
  { path: '/drugs/:chembl_id', name: 'DrugProfile', component: () => import('@/views/DrugProfilePage.vue') },
  { path: '/patents', name: 'PatentExplorer', component: () => import('@/views/PatentExplorerPage.vue') },
  { path: '/analogs', name: 'AnalogWorkspace', component: () => import('@/views/AnalogWorkspacePage.vue') },
  { path: '/investigations/:id', name: 'Investigation', component: () => import('@/views/AnalogWorkspacePage.vue') },

  // ─── v2 routes ────────────────────────────────────────────────────────────
  { path: '/target-profiles/:id', name: 'TargetProfile', component: () => import('@/views/TargetProfilePage.vue') },
  { path: '/virtual-screening', name: 'VirtualScreening', component: () => import('@/views/VirtualScreeningPage.vue') },
  { path: '/projects/:id/sar', name: 'SARTracker', component: () => import('@/views/SARTrackerPage.vue') },
  { path: '/projects/:id/candidates', name: 'CandidateSelection', component: () => import('@/views/CandidateSelectionPage.vue') },
  { path: '/projects/:id/synthesis', name: 'SynthesisHub', component: () => import('@/views/SynthesisHubPage.vue') },
  { path: '/projects/:id/salt-screening', name: 'SaltPolymorphScreening', component: () => import('@/views/SaltPolymorphScreeningPage.vue') },
  { path: '/projects/:id/process-development', name: 'ProcessDevelopment', component: () => import('@/views/ProcessDevelopmentPage.vue') },
  { path: '/projects/:id/formulation', name: 'FormulationPlanning', component: () => import('@/views/FormulationPlanningPage.vue') },
  { path: '/excipients', name: 'ExcipientLibrary', component: () => import('@/views/ExcipientLibraryPage.vue') },
  { path: '/projects/:id/stability', name: 'StabilityPlanning', component: () => import('@/views/StabilityPlanningPage.vue') },
  { path: '/projects/:id/analytical/:method_id?', name: 'AnalyticalMethod', component: () => import('@/views/AnalyticalMethodPage.vue') },
  { path: '/projects/:id/specifications', name: 'SpecificationBuilder', component: () => import('@/views/SpecificationBuilderPage.vue') },
  { path: '/projects/:id/preclinical', name: 'PreclinicalStudyPlanner', component: () => import('@/views/PreclinicalStudyPlannerPage.vue') },
  { path: '/projects/:id/admet', name: 'ADMETDashboard', component: () => import('@/views/ADMETDashboardPage.vue') },

  // ─── v3 routes ────────────────────────────────────────────────────────────
  { path: '/ai-lab', name: 'AILab', component: () => import('@/views/AILabPage.vue') },
  { path: '/documents', name: 'DocumentPortal', component: () => import('@/views/DocumentPortalPage.vue') },
  { path: '/projects/:id/ai-plan', name: 'AIPlan', component: () => import('@/views/AIPlanDetailPage.vue') },
  { path: '/projects/:id/cell-line', name: 'CellLineDevelopment', component: () => import('@/views/CellLineDevelopmentPage.vue') },
  { path: '/projects/:id/bioprocessing', name: 'UpstreamBioprocessing', component: () => import('@/views/UpstreamBioprocessingPage.vue') },
  { path: '/projects/:id/purification', name: 'DownstreamPurification', component: () => import('@/views/DownstreamPurificationPage.vue') },
  { path: '/projects/:id/biologic-analytics', name: 'BiologicsAnalytics', component: () => import('@/views/BiologicsAnalyticsPage.vue') },
  { path: '/projects/:id/biologic-formulation', name: 'BiologicsFormulation', component: () => import('@/views/BiologicsFormulationPage.vue') },

  // ─── Settings ─────────────────────────────────────────────────────────────
  { path: '/settings', name: 'Settings', component: () => import('@/views/SettingsPage.vue') },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
