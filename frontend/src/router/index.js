import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Dashboard', component: () => import('@/views/DashboardPage.vue') },
  { path: '/projects/new', name: 'ProjectNew', component: () => import('@/views/ProjectSetupPage.vue') },
  { path: '/projects/:id/edit', name: 'ProjectEdit', component: () => import('@/views/ProjectSetupPage.vue') },
  { path: '/compounds/:id', name: 'CompoundProfile', component: () => import('@/views/CompoundProfilePage.vue') },
  { path: '/diseases', name: 'DiseaseExplorer', component: () => import('@/views/DiseaseExplorerPage.vue') },
  { path: '/experiments/new', name: 'ExperimentNew', component: () => import('@/views/ExperimentPlannerPage.vue') },
  { path: '/experiments/:id', name: 'ExperimentResults', component: () => import('@/views/ExperimentResultsPage.vue') },
  { path: '/projects/:id/risk', name: 'RiskAnalysis', component: () => import('@/views/RiskAnalysisPage.vue') },
  { path: '/synthesis', name: 'SynthesisPlanning', component: () => import('@/views/SynthesisPlanningPage.vue') },
  { path: '/literature', name: 'Literature', component: () => import('@/views/LiteraturePage.vue') },
  { path: '/chat', name: 'Chat', component: () => import('@/views/ChatPage.vue') },
  { path: '/projects/:id/documents', name: 'Documentation', component: () => import('@/views/DocumentationPage.vue') },
  { path: '/drugs', name: 'DrugIntelligence', component: () => import('@/views/DrugIntelligencePage.vue') },
  { path: '/drugs/:chembl_id', name: 'DrugProfile', component: () => import('@/views/DrugProfilePage.vue') },
  { path: '/patents', name: 'PatentExplorer', component: () => import('@/views/PatentExplorerPage.vue') },
  { path: '/analogs', name: 'AnalogWorkspace', component: () => import('@/views/AnalogWorkspacePage.vue') },
  { path: '/investigations/:id', name: 'Investigation', component: () => import('@/views/AnalogWorkspacePage.vue') },
  { path: '/synthesis/compare', name: 'SynthesisPlanComparison', component: () => import('@/views/SynthesisPlanComparisonPage.vue') },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
