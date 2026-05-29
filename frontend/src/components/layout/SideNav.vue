<script setup>
import { RouterLink } from 'vue-router'
import { useProjectStore } from '@/stores/projects'
import { onMounted } from 'vue'

const projectStore = useProjectStore()
onMounted(() => projectStore.fetchProjects())
</script>

<template>
  <nav class="side-nav">
    <div class="nav-logo">🧬 BioIntel</div>

    <div class="nav-section">
      <div class="nav-section-label">Overview</div>
      <RouterLink class="nav-link" to="/">📊 Dashboard</RouterLink>
    </div>

    <div class="nav-section">
      <div class="nav-section-label">Projects</div>
      <RouterLink class="nav-link" to="/projects/new">➕ New Project</RouterLink>
    </div>

    <div class="nav-section">
      <div class="nav-section-label">Research</div>
      <RouterLink class="nav-link" to="/diseases">🔬 Disease Explorer</RouterLink>
      <RouterLink class="nav-link" to="/literature">📚 Literature & Trials</RouterLink>
    </div>

    <div class="nav-section">
      <div class="nav-section-label">Experiments</div>
      <RouterLink class="nav-link" to="/experiments/new">🧪 New Experiment</RouterLink>
      <RouterLink class="nav-link" to="/synthesis">⚗️ Synthesis Planning</RouterLink>
    </div>

    <div class="nav-section">
      <div class="nav-section-label">AI Assistant</div>
      <RouterLink class="nav-link" to="/chat">💬 Chat</RouterLink>
    </div>

    <div class="nav-section">
      <div class="nav-section-label">Drug Discovery</div>
      <RouterLink class="nav-link" to="/drugs">🔬 Drug Intelligence</RouterLink>
      <RouterLink class="nav-link" to="/patents">📜 Patent Explorer</RouterLink>
      <RouterLink class="nav-link" to="/analogs">🧪 Analog Workspace</RouterLink>
    </div>
  </nav>
</template>
