<script setup>
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { computed } from 'vue'
import { useProjectStore } from '@/stores/projects'

const projectStore = useProjectStore()
const route = useRoute()
const router = useRouter()

const projectId = computed(() => route.params.id || route.query.project || null)
const isProjectRoute = computed(() => !!projectId.value)

const currentProject = computed(() => {
  if (!projectId.value) return null
  return (
    projectStore.projects.find(p => String(p.id) === String(projectId.value)) ||
    projectStore.currentProject
  )
})

const isNovelDesign = computed(() => currentProject.value?.pathway === 'novel_design')

function exitProject() {
  router.push('/')
}
</script>

<template>
  <nav class="side-nav">
    <div class="nav-logo">BioIntel</div>

    <!-- ── PROJECT MODE ──────────────────────────────────── -->
    <template v-if="isProjectRoute">
      <!-- Project chip -->
      <div class="nav-project-chip">
        <div class="nav-project-chip-inner">
          <span class="nav-project-icon">▣</span>
          <span class="nav-project-name">{{ currentProject?.name || `Project ${projectId}` }}</span>
          <button class="nav-project-exit" title="Exit project" @click="exitProject">×</button>
        </div>
        <span v-if="currentProject?.pathway === 'novel_design'" class="nav-project-badge">Novel Design</span>
        <span v-else class="nav-project-badge" style="background:var(--primary-light);color:var(--primary)">Analog-Based</span>
      </div>

      <!-- Target Biology — novel design only -->
      <div v-if="isNovelDesign" class="nav-section">
        <div class="nav-section-label">Target Biology</div>
        <RouterLink class="nav-link nav-subitem" to="/virtual-screening">Virtual Screening</RouterLink>
      </div>

      <!-- Pipeline — 7 grouped phases with sub-items -->
      <div class="nav-section">
        <div class="nav-section-label">Pipeline</div>

        <!-- 1. Discovery -->
        <div class="nav-phase-header"><span class="nav-stage-num">1</span>Discovery</div>
        <RouterLink class="nav-link nav-subitem" :to="`/projects/${projectId}/edit`">Project Overview</RouterLink>
        <RouterLink class="nav-link nav-subitem" :to="`/analogs?project=${projectId}`">Analog Workspace</RouterLink>

        <!-- 2. Lead Optimization -->
        <div class="nav-phase-header"><span class="nav-stage-num">2</span>Lead Optimization</div>
        <RouterLink class="nav-link nav-subitem" :to="`/projects/${projectId}/sar`">SAR Tracker</RouterLink>

        <!-- 3. Drug Substance -->
        <div class="nav-phase-header"><span class="nav-stage-num">3</span>Drug Substance</div>
        <RouterLink class="nav-link nav-subitem" :to="`/projects/${projectId}/synthesis`">Synthesis Hub</RouterLink>
        <RouterLink class="nav-link nav-subitem" :to="`/projects/${projectId}/salt-screening`">Salt & Polymorph Screen</RouterLink>
        <RouterLink class="nav-link nav-subitem" :to="`/projects/${projectId}/process-development`">Process Development</RouterLink>

        <!-- 4. Drug Product -->
        <div class="nav-phase-header"><span class="nav-stage-num">4</span>Drug Product</div>
        <RouterLink class="nav-link nav-subitem" :to="`/projects/${projectId}/formulation`">Formulation Planning</RouterLink>
        <RouterLink class="nav-link nav-subitem" :to="`/projects/${projectId}/stability`">Stability Planning</RouterLink>

        <!-- 5. Analytical -->
        <div class="nav-phase-header"><span class="nav-stage-num">5</span>Analytical</div>
        <RouterLink class="nav-link nav-subitem" :to="`/projects/${projectId}/analytical`">Methods</RouterLink>
        <RouterLink class="nav-link nav-subitem" :to="`/projects/${projectId}/specifications`">Specifications</RouterLink>

        <!-- 6. Preclinical -->
        <div class="nav-phase-header"><span class="nav-stage-num">6</span>Preclinical</div>
        <RouterLink class="nav-link nav-subitem" :to="`/projects/${projectId}/admet`">ADMET Dashboard</RouterLink>
        <RouterLink class="nav-link nav-subitem" :to="`/projects/${projectId}/preclinical`">Study Planner</RouterLink>

        <!-- 7. Regulatory -->
        <div class="nav-phase-header"><span class="nav-stage-num">7</span>Regulatory</div>
        <RouterLink class="nav-link nav-subitem" :to="`/projects/${projectId}/documents`">Documents</RouterLink>
      </div>

      <!-- Tools -->
      <div class="nav-section">
        <div class="nav-section-label">Tools</div>
        <RouterLink class="nav-link" to="/excipients">Excipient Library</RouterLink>
        <RouterLink class="nav-link" to="/chat">AI Chat</RouterLink>
        <RouterLink class="nav-link" to="/literature">Literature</RouterLink>
      </div>
    </template>

    <!-- ── GLOBAL MODE ───────────────────────────────────── -->
    <template v-else>
      <div class="nav-section">
        <div class="nav-section-label">Overview</div>
        <RouterLink class="nav-link" to="/">Dashboard</RouterLink>
        <RouterLink class="nav-link" to="/projects/new">New Project</RouterLink>
      </div>

      <div class="nav-section">
        <div class="nav-section-label">Research</div>
        <RouterLink class="nav-link" to="/diseases">Disease Explorer</RouterLink>
        <RouterLink class="nav-link" to="/literature">Literature & Trials</RouterLink>
      </div>

      <div class="nav-section">
        <div class="nav-section-label">Drug Discovery</div>
        <RouterLink class="nav-link" to="/drugs">Drug Intelligence</RouterLink>
        <RouterLink class="nav-link" to="/patents">Patent Explorer</RouterLink>
        <RouterLink class="nav-link" to="/analogs">Analog Workspace</RouterLink>
      </div>

      <div class="nav-section">
        <div class="nav-section-label">Target Biology</div>
        <RouterLink class="nav-link" to="/virtual-screening">Virtual Screening</RouterLink>
      </div>

      <div class="nav-section">
        <div class="nav-section-label">Synthesis</div>
        <RouterLink class="nav-link" to="/synthesis">Synthesis Planning</RouterLink>
        <RouterLink class="nav-link" to="/synthesis/compare">Compare Plans</RouterLink>
        <RouterLink class="nav-link" to="/experiments/new">New Experiment</RouterLink>
      </div>

      <div class="nav-section">
        <div class="nav-section-label">AI Assistant</div>
        <RouterLink class="nav-link" to="/chat">Chat</RouterLink>
      </div>
    </template>
  </nav>
</template>
