<script setup>
import { useRoute, useRouter } from 'vue-router'
import { computed } from 'vue'
import { useProjectStore } from '@/stores/projects'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()

const projectId = computed(() => route.params.id || route.query.project || null)

const currentProject = computed(() => {
  if (!projectId.value) return null
  return (
    projectStore.projects.find(p => String(p.id) === String(projectId.value)) ||
    projectStore.currentProject
  )
})

const pageTitle = computed(() => {
  const map = {
    Dashboard: 'Dashboard',
    ProjectNew: 'New Project',
    ProjectEdit: 'Edit Project',
    CompoundProfile: 'Compound Profile',
    DiseaseExplorer: 'Disease & Target Explorer',
    ExperimentNew: 'New Experiment',
    ExperimentResults: 'Experiment Results',
    RiskAnalysis: 'Risk Analysis',
    SynthesisPlanning: 'Synthesis Planning',
    SynthesisPlanComparison: 'Compare Plans',
    Literature: 'Literature & Clinical Trials',
    Chat: 'AI Chat Assistant',
    Documentation: 'Regulatory Documents',
    FormulationPlanning: 'Formulation Planning',
    StabilityPlanning: 'Stability Planning',
    AnalyticalMethod: 'Analytical Methods',
    SpecificationBuilder: 'Specifications',
    PreclinicalStudyPlanner: 'Preclinical Studies',
    ADMETDashboard: 'ADMET Dashboard',
    SARTracker: 'SAR Tracker',
    CandidateSelection: 'Candidate Selection',
    SynthesisHub: 'Drug Substance — Synthesis',
    SaltPolymorphScreening: 'Salt / Polymorph Screen',
    ProcessDevelopment: 'Process Development',
    ExcipientLibrary: 'Excipient Library',
    VirtualScreening: 'Virtual Screening',
    TargetProfile: 'Target Profile',
  }
  return map[route.name] || 'BioIntel'
})

function openProject() {
  if (currentProject.value) {
    router.push(`/projects/${projectId.value}`)
  }
}
</script>

<template>
  <header class="top-bar">
    <span class="page-title">{{ pageTitle }}</span>
    <span class="spacer" />

    <!-- Active project chip -->
    <div v-if="currentProject" class="topbar-project-chip" @click="openProject">
      <span class="topbar-project-dot"></span>
      <span class="topbar-project-label">{{ currentProject.name }}</span>
      <span v-if="currentProject.phase" class="topbar-project-phase">{{ currentProject.phase }}</span>
    </div>

    <span class="text-muted text-sm" style="font-size:12px">Drug Development AI</span>
  </header>
</template>
