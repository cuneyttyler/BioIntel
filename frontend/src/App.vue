<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import SideNav from '@/components/layout/SideNav.vue'
import TopBar from '@/components/layout/TopBar.vue'
import ToastNotification from '@/components/common/ToastNotification.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import AIPagePanel from '@/components/ai-plan/AIPagePanel.vue'
import { useUIStore } from '@/stores/ui'

const ui = useUIStore()
const route = useRoute()

const panelOpen = ref(false)
const panelWidth = ref(300)
const resizing = ref(false)

const projectId = computed(() => {
  const id = route.params.id
  return id ? parseInt(id) : null
})

const showPanelToggle = computed(() => !!projectId.value)

// Panel resize logic
let _startX = 0
let _startW = 0

function startResize(e) {
  resizing.value = true
  _startX = e.clientX
  _startW = panelWidth.value
  e.preventDefault()
}

function onMouseMove(e) {
  if (!resizing.value) return
  const delta = _startX - e.clientX
  panelWidth.value = Math.max(260, Math.min(600, _startW + delta))
}

function onMouseUp() {
  resizing.value = false
}

onMounted(() => {
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
})

onUnmounted(() => {
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', onMouseUp)
})

const panelWidthCss = computed(() => `${panelWidth.value}px`)
</script>

<template>
  <div class="app-shell" :class="{ 'with-panel': panelOpen && showPanelToggle }">
    <div v-if="ui.sidenavOpen" class="sidenav-backdrop" @click="ui.closeSidenav()" />
    <SideNav :class="{ 'sidenav-open': ui.sidenavOpen }" />
    <div class="main-area">
      <TopBar>
        <template v-if="showPanelToggle" #actions>
          <button
            class="panel-toggle-btn"
            :class="{ active: panelOpen }"
            @click="panelOpen = !panelOpen"
            title="Toggle AI Panel"
          >✦ AI Assistant</button>
        </template>
      </TopBar>
      <main class="page-content">
        <router-view :key="$route.fullPath" />
      </main>
    </div>
    <template v-if="showPanelToggle && projectId && panelOpen">
      <div
        class="panel-resize-handle"
        :class="{ resizing }"
        @mousedown="startResize"
      />
      <AIPagePanel
        :open="panelOpen"
        :project-id="projectId"
        :page-type="route.name || 'unknown'"
        :page-entity="{}"
        @close="panelOpen = false"
      />
    </template>
    <ToastNotification />
    <ConfirmDialog />
  </div>
</template>

<style scoped>
.app-shell.with-panel {
  display: grid;
  grid-template-columns: auto 1fr 4px v-bind(panelWidthCss);
}
.panel-toggle-btn {
  padding: 4px 12px;
  background: #eff6ff;
  color: #3b82f6;
  border: 1px solid #bfdbfe;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}
.panel-toggle-btn.active {
  background: #3b82f6;
  color: #fff;
  border-color: #3b82f6;
}
</style>
