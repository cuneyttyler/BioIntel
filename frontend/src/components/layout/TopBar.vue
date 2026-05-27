<script setup>
import { useRoute } from 'vue-router'
import { computed } from 'vue'

const route = useRoute()

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
    Literature: 'Literature & Clinical Trials',
    Chat: 'AI Chat Assistant',
    Documentation: 'Process Documentation',
  }
  return map[route.name] || 'BioIntel'
})
</script>

<template>
  <header class="top-bar">
    <span class="page-title">{{ pageTitle }}</span>
    <span class="spacer" />
    <span class="text-muted text-sm">Drug Development AI</span>
  </header>
</template>
