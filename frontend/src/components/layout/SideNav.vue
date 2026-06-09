<script setup>
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { computed, watch } from 'vue'
import { useProjectStore } from '@/stores/projects'
import { useUIStore } from '@/stores/ui'

const projectStore = useProjectStore()
const route = useRoute()
const router = useRouter()
const ui = useUIStore()

watch(() => route.fullPath, () => ui.closeSidenav())

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
const isAIDriven = computed(() => currentProject.value?.mode === 'ai_driven')
const isBiologic = computed(() => currentProject.value?.molecule_type === 'biologic')

function exitProject() {
  router.push('/')
}
</script>

<template>
  <nav class="side-nav" :class="{ collapsed: ui.navCollapsed }">
    <!-- Logo + collapse toggle -->
    <div class="nav-logo">
      <span class="nav-logo-text">BioIntel</span>
      <button class="nav-collapse-btn" :title="ui.navCollapsed ? 'Expand sidebar' : 'Collapse sidebar'" @click="ui.toggleNavCollapsed()">
        {{ ui.navCollapsed ? '›' : '‹' }}
      </button>
    </div>

    <!-- ── PROJECT MODE ──────────────────────────────────── -->
    <template v-if="isProjectRoute">
      <!-- Project chip -->
      <div class="nav-project-chip">
        <div class="nav-project-chip-inner">
          <span class="nav-project-icon">▣</span>
          <span class="nav-project-name">{{ currentProject?.name || `Project ${projectId}` }}</span>
          <button class="nav-project-exit" title="Exit project" @click="exitProject">×</button>
        </div>
        <div class="nav-project-badges">
          <span v-if="isAIDriven" class="nav-project-badge nav-badge-ai">AI-Driven</span>
          <span v-if="isBiologic" class="nav-project-badge nav-badge-bio">Biologic</span>
          <span v-if="currentProject?.pathway === 'novel_design'" class="nav-project-badge">Novel Design</span>
          <span v-else-if="!isAIDriven && !isBiologic" class="nav-project-badge" style="background:var(--primary-light);color:var(--primary)">Analog-Based</span>
        </div>
      </div>

      <!-- AI-Driven Plan link -->
      <div v-if="isAIDriven" class="nav-section">
        <div class="nav-section-label"><span class="nav-lbl">AI Plan</span></div>
        <RouterLink class="nav-link nav-ai-plan" :to="`/projects/${projectId}/ai-plan`" title="AI-Driven Plan">
          <span class="nav-ico">✦</span><span class="nav-lbl">AI-Driven Plan</span>
        </RouterLink>
      </div>

      <!-- Target Biology — novel design only -->
      <div v-if="isNovelDesign" class="nav-section">
        <div class="nav-section-label"><span class="nav-lbl">Target Biology</span></div>
        <RouterLink class="nav-link nav-subitem" to="/virtual-screening" title="Virtual Screening">
          <span class="nav-ico">VS</span><span class="nav-lbl">Virtual Screening</span>
        </RouterLink>
      </div>

      <!-- Pipeline -->
      <div class="nav-section">
        <div class="nav-section-label"><span class="nav-lbl">Pipeline</span></div>

        <div class="nav-phase-header"><span class="nav-stage-num">1</span><span class="nav-lbl">Drug Discovery</span></div>
        <RouterLink class="nav-link nav-subitem" :to="`/projects/${projectId}/edit`" title="Project Overview">
          <span class="nav-ico">PO</span><span class="nav-lbl">Project Overview</span>
        </RouterLink>
        <RouterLink class="nav-link nav-subitem" :to="`/analogs?project=${projectId}`" title="Analog Workspace">
          <span class="nav-ico">AW</span><span class="nav-lbl">Analog Workspace</span>
        </RouterLink>

        <div class="nav-phase-header"><span class="nav-stage-num">2</span><span class="nav-lbl">Lead Optimization</span></div>
        <RouterLink class="nav-link nav-subitem" :to="`/projects/${projectId}/sar`" title="SAR Tracker">
          <span class="nav-ico">SR</span><span class="nav-lbl">SAR Tracker</span>
        </RouterLink>

        <div class="nav-phase-header"><span class="nav-stage-num">3</span><span class="nav-lbl">Drug Substance Dev.</span></div>
        <RouterLink class="nav-link nav-subitem" :to="`/projects/${projectId}/synthesis`" title="Synthesis Hub">
          <span class="nav-ico">SH</span><span class="nav-lbl">Synthesis Hub</span>
        </RouterLink>
        <RouterLink class="nav-link nav-subitem" :to="`/projects/${projectId}/salt-screening`" title="Salt &amp; Polymorph Screen">
          <span class="nav-ico">SP</span><span class="nav-lbl">Salt &amp; Polymorph Screen</span>
        </RouterLink>
        <RouterLink class="nav-link nav-subitem" :to="`/projects/${projectId}/process-development`" title="Process Development">
          <span class="nav-ico">PD</span><span class="nav-lbl">Process Development</span>
        </RouterLink>

        <div class="nav-phase-header"><span class="nav-stage-num">4</span><span class="nav-lbl">Drug Product Dev.</span></div>
        <RouterLink class="nav-link nav-subitem" :to="`/projects/${projectId}/formulation`" title="Formulation Planning">
          <span class="nav-ico">FP</span><span class="nav-lbl">Formulation Planning</span>
        </RouterLink>
        <RouterLink class="nav-link nav-subitem" :to="`/projects/${projectId}/stability`" title="Stability Planning">
          <span class="nav-ico">ST</span><span class="nav-lbl">Stability Planning</span>
        </RouterLink>

        <div class="nav-phase-header"><span class="nav-stage-num">5</span><span class="nav-lbl">Analytical Dev.</span></div>
        <RouterLink class="nav-link nav-subitem" :to="`/projects/${projectId}/analytical`" title="Analytical Methods">
          <span class="nav-ico">AM</span><span class="nav-lbl">Methods</span>
        </RouterLink>
        <RouterLink class="nav-link nav-subitem" :to="`/projects/${projectId}/specifications`" title="Specifications">
          <span class="nav-ico">SB</span><span class="nav-lbl">Specifications</span>
        </RouterLink>

        <div class="nav-phase-header"><span class="nav-stage-num">6</span><span class="nav-lbl">Preclinical Dev.</span></div>
        <RouterLink class="nav-link nav-subitem" :to="`/projects/${projectId}/admet`" title="ADMET Dashboard">
          <span class="nav-ico">AD</span><span class="nav-lbl">ADMET Dashboard</span>
        </RouterLink>
        <RouterLink class="nav-link nav-subitem" :to="`/projects/${projectId}/preclinical`" title="Study Planner">
          <span class="nav-ico">PC</span><span class="nav-lbl">Study Planner</span>
        </RouterLink>

        <div class="nav-phase-header"><span class="nav-stage-num">7</span><span class="nav-lbl">Regulatory & Clinical</span></div>
        <RouterLink class="nav-link nav-subitem" :to="`/documents?project=${projectId}`" title="Documents">
          <span class="nav-ico">DC</span><span class="nav-lbl">Documents</span>
        </RouterLink>
      </div>

      <!-- Biologics section -->
      <div v-if="isBiologic" class="nav-section">
        <div class="nav-section-label"><span class="nav-lbl">Biologics</span></div>
        <RouterLink class="nav-link nav-subitem" :to="`/projects/${projectId}/cell-line`" title="Cell Line Development">
          <span class="nav-ico">CL</span><span class="nav-lbl">Cell Line Development</span>
        </RouterLink>
        <RouterLink class="nav-link nav-subitem" :to="`/projects/${projectId}/bioprocessing`" title="Upstream Bioprocessing">
          <span class="nav-ico">UP</span><span class="nav-lbl">Upstream Bioprocessing</span>
        </RouterLink>
        <RouterLink class="nav-link nav-subitem" :to="`/projects/${projectId}/purification`" title="Downstream Purification">
          <span class="nav-ico">DP</span><span class="nav-lbl">Downstream Purification</span>
        </RouterLink>
        <RouterLink class="nav-link nav-subitem" :to="`/projects/${projectId}/biologic-analytics`" title="Biologic Analytics">
          <span class="nav-ico">BA</span><span class="nav-lbl">Biologic Analytics</span>
        </RouterLink>
        <RouterLink class="nav-link nav-subitem" :to="`/projects/${projectId}/biologic-formulation`" title="Biologic Formulation">
          <span class="nav-ico">BF</span><span class="nav-lbl">Biologic Formulation</span>
        </RouterLink>
      </div>

      <!-- Tools -->
      <div class="nav-section">
        <div class="nav-section-label"><span class="nav-lbl">Tools</span></div>
        <RouterLink class="nav-link" to="/excipients" title="Excipient Library">
          <span class="nav-ico">EL</span><span class="nav-lbl">Excipient Library</span>
        </RouterLink>
        <RouterLink v-if="!isAIDriven" class="nav-link" to="/chat" title="AI Chat">
          <span class="nav-ico">AI</span><span class="nav-lbl">AI Chat</span>
        </RouterLink>
        <RouterLink class="nav-link" to="/literature" title="Literature">
          <span class="nav-ico">LT</span><span class="nav-lbl">Literature</span>
        </RouterLink>
        <RouterLink class="nav-link" :to="`/documents?project=${projectId}`" title="Documents">
          <span class="nav-ico">DC</span><span class="nav-lbl">Documents</span>
        </RouterLink>
      </div>
    </template>

    <!-- ── GLOBAL MODE ───────────────────────────────────── -->
    <template v-else>
      <div class="nav-section">
        <RouterLink class="nav-link nav-ai-lab" to="/ai-lab" title="AI Lab">
          <span class="nav-ico">✦</span><span class="nav-lbl">AI Lab</span>
        </RouterLink>
      </div>

      <div class="nav-section">
        <div class="nav-section-label"><span class="nav-lbl">Overview</span></div>
        <RouterLink class="nav-link" to="/" title="Dashboard">
          <span class="nav-ico">Da</span><span class="nav-lbl">Dashboard</span>
        </RouterLink>
        <RouterLink class="nav-link" to="/projects/new" title="New Project">
          <span class="nav-ico">NP</span><span class="nav-lbl">New Project</span>
        </RouterLink>
      </div>

      <div class="nav-section">
        <div class="nav-section-label"><span class="nav-lbl">Research</span></div>
        <RouterLink class="nav-link" to="/diseases" title="Disease Explorer">
          <span class="nav-ico">DE</span><span class="nav-lbl">Disease Explorer</span>
        </RouterLink>
        <RouterLink class="nav-link" to="/literature" title="Literature &amp; Trials">
          <span class="nav-ico">LT</span><span class="nav-lbl">Literature &amp; Trials</span>
        </RouterLink>
      </div>

      <div class="nav-section">
        <div class="nav-section-label"><span class="nav-lbl">Drug Discovery</span></div>
        <RouterLink class="nav-link" to="/drugs" title="Drug Intelligence">
          <span class="nav-ico">DI</span><span class="nav-lbl">Drug Intelligence</span>
        </RouterLink>
        <RouterLink class="nav-link" to="/patents" title="Patent Explorer">
          <span class="nav-ico">PE</span><span class="nav-lbl">Patent Explorer</span>
        </RouterLink>
        <RouterLink class="nav-link" to="/analogs" title="Analog Workspace">
          <span class="nav-ico">AW</span><span class="nav-lbl">Analog Workspace</span>
        </RouterLink>
      </div>

      <div class="nav-section">
        <div class="nav-section-label"><span class="nav-lbl">Target Biology</span></div>
        <RouterLink class="nav-link" to="/virtual-screening" title="Virtual Screening">
          <span class="nav-ico">VS</span><span class="nav-lbl">Virtual Screening</span>
        </RouterLink>
      </div>

      <div class="nav-section">
        <div class="nav-section-label"><span class="nav-lbl">Synthesis</span></div>
        <RouterLink class="nav-link" to="/synthesis" title="Synthesis Planning">
          <span class="nav-ico">SY</span><span class="nav-lbl">Synthesis Planning</span>
        </RouterLink>
        <RouterLink class="nav-link" to="/synthesis/compare" title="Compare Plans">
          <span class="nav-ico">CP</span><span class="nav-lbl">Compare Plans</span>
        </RouterLink>
        <RouterLink class="nav-link" to="/experiments/new" title="New Experiment">
          <span class="nav-ico">EX</span><span class="nav-lbl">New Experiment</span>
        </RouterLink>
      </div>

      <div class="nav-section">
        <div class="nav-section-label"><span class="nav-lbl">AI Assistant</span></div>
        <RouterLink class="nav-link" to="/chat" title="Chat">
          <span class="nav-ico">AI</span><span class="nav-lbl">Chat</span>
        </RouterLink>
        <RouterLink class="nav-link" to="/documents" title="Document Portal">
          <span class="nav-ico">DP</span><span class="nav-lbl">Document Portal</span>
        </RouterLink>
      </div>

      <div class="nav-section">
        <div class="nav-section-label"><span class="nav-lbl">System</span></div>
        <RouterLink class="nav-link" to="/settings" title="Settings">
          <span class="nav-ico">⚙</span><span class="nav-lbl">Settings</span>
        </RouterLink>
      </div>
    </template>
  </nav>
</template>

<style scoped>
.nav-badge-ai { background: #eff6ff; color: #1d4ed8; }
.nav-badge-bio { background: #d1fae5; color: #065f46; }
.nav-ai-lab {
  font-weight: 700;
  color: #3b82f6 !important;
}
.nav-ai-plan {
  font-weight: 700;
  color: #3b82f6 !important;
}
.nav-project-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 2px 10px 6px;
}
</style>
