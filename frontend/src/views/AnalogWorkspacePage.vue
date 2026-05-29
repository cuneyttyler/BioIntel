<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAnalogsStore } from '@/stores/analogs'
import { useUIStore } from '@/stores/ui'
import { projects as projectsApi, compounds as compoundsApi, synthesisPlan as synthesisPlanApi } from '@/services/api'
import PageHeader from '@/components/layout/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const route = useRoute()
const router = useRouter()
const store = useAnalogsStore()
const ui = useUIStore()

const saving = ref(false)
const loadingProject = ref(false)

// Project mode: entered from project page ("Find Analog" button)
const projectMode = ref(false)
const projectId = ref(null)
// analog_candidates from project detail — carries retro_plan_id / tree_plan_id
const projectCandidates = ref([])
// Candidate pending unshortlist confirmation (has associated plans)
const pendingUnshortlist = ref(null)

// Drug search mode: project selector
const allProjects = ref([])
const selectedProjectId = ref(null)
const newProjectName = ref('')
const compoundConflict = ref(null)
const pendingSaveAction = ref(null)

const patentBadgeStyle = (status) => ({
  free: 'background:#d1fae5;color:#065f46',
  covered: 'background:#fee2e2;color:#991b1b',
  unknown: 'background:#f3f4f6;color:#6b7280',
}[status] || 'background:#f3f4f6;color:#6b7280')

const admetKeys = computed(() => {
  const keys = new Set()
  store.shortlisted.forEach(c => Object.keys(c.admet || {}).forEach(k => keys.add(k)))
  return [...keys].slice(0, 8)
})

const selectedProject = computed(() =>
  allProjects.value.find(p => p.id === selectedProjectId.value) || null
)

const saveButtonLabel = computed(() => {
  if (saving.value) return 'Saving...'
  return selectedProjectId.value ? 'Add to Project' : 'Save to New Project'
})

const canSave = computed(() =>
  store.shortlisted.length > 0 &&
  (selectedProjectId.value !== null || newProjectName.value.trim())
)

onMounted(async () => {
  const invId = route.params.id
  const projId = route.query.project ? Number(route.query.project) : null

  if (projId) {
    projectMode.value = true
    projectId.value = projId
    loadingProject.value = true
    try {
      const project = await projectsApi.get(projId)
      // Store analog_candidates with plan IDs so we can warn on unshortlist
      projectCandidates.value = project.analog_candidates || []
      const inv = project.investigations?.[0]
      if (inv?.id) {
        await store.loadInvestigation(inv.id)
      }
    } catch (e) {
      console.error(e)
    } finally {
      loadingProject.value = false
    }
  } else if (invId) {
    await store.loadInvestigation(invId)
  }

  if (!projectMode.value) {
    try { allProjects.value = await projectsApi.list() } catch { /* non-critical */ }
  }
})

const handleToggle = (candidate) => {
  if (projectMode.value) {
    const isCurrentlyShortlisted = candidate.shortlisted
    if (isCurrentlyShortlisted) {
      // Check if this candidate has associated synthesis plans
      const proj = projectCandidates.value.find(p => p.id === candidate.id)
      const planCount = (proj?.retro_plan_id ? 1 : 0) + (proj?.tree_plan_id ? 1 : 0)
      if (planCount > 0) {
        pendingUnshortlist.value = { candidate, planCount }
        return
      }
    }
    store.toggleShortlistPersisted(candidate, projectId.value)
  } else {
    store.toggleShortlist(candidate)
  }
}

const confirmUnshortlist = async () => {
  const { candidate } = pendingUnshortlist.value
  const proj = projectCandidates.value.find(p => p.id === candidate.id)
  pendingUnshortlist.value = null
  // Delete associated synthesis plans first
  if (proj) {
    const planIds = [proj.retro_plan_id, proj.tree_plan_id].filter(Boolean)
    await Promise.all(planIds.map(id => synthesisPlanApi.delete(id).catch(() => {})))
    // Update local cache so the plan count check won't trigger again on re-toggle
    const idx = projectCandidates.value.findIndex(p => p.id === candidate.id)
    if (idx !== -1) {
      projectCandidates.value[idx].retro_plan_id = null
      projectCandidates.value[idx].tree_plan_id = null
    }
  }
  store.toggleShortlistPersisted(candidate, projectId.value)
}

const cancelUnshortlist = () => {
  pendingUnshortlist.value = null
}

const doneWithProject = async () => {
  if (saving.value) return
  saving.value = true
  try {
    await store.saveNewCandidatesToProject(projectId.value)
    ui.addToast('Analogs saved to project.', 'success')
    router.push(`/projects/${projectId.value}/edit`)
  } catch {
    ui.addToast('Failed to save analogs.', 'error')
  } finally {
    saving.value = false
  }
}

const startSave = async () => {
  if (!canSave.value || saving.value) return

  if (selectedProjectId.value) {
    try {
      const existing = await compoundsApi.list(selectedProjectId.value)
      if (existing?.length) {
        compoundConflict.value = { project: selectedProject.value, existingCompounds: existing }
        pendingSaveAction.value = { projectId: selectedProjectId.value }
        return
      }
    } catch { /* ignore, proceed */ }
    await doSave({ projectId: selectedProjectId.value, compoundAction: 'add' })
  } else {
    await doSave({ projectName: newProjectName.value.trim() })
  }
}

const resolveConflict = async (action) => {
  const saved = pendingSaveAction.value
  compoundConflict.value = null
  pendingSaveAction.value = null
  await doSave({ ...saved, compoundAction: action })
}

const doSave = async (opts) => {
  saving.value = true
  try {
    const project = await store.saveToProject(opts)
    ui.addToast('Project saved — returning to project page.', 'success')
    router.push(`/projects/${project.id}/edit`)
  } catch {
    ui.addToast('Failed to save to project', 'error')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div>
    <PageHeader :title="store.referenceDrug ? `Analog Workspace — ${store.referenceDrug.name}` : 'Analog Workspace'" />

    <div v-if="loadingProject" style="text-align:center;padding:64px"><LoadingSpinner /></div>

    <div v-else-if="!store.referenceDrug" class="empty-state">
      <div style="font-size:48px">🧪</div>
      <h3>No reference drug selected</h3>
      <p v-if="!projectMode">
        Start from the <RouterLink to="/drugs" style="color:var(--primary)">Drug Intelligence</RouterLink> page — search for a drug and click "Start Analog Search".
      </p>
      <p v-else class="text-muted text-sm">This project has no linked drug investigation yet.</p>
    </div>

    <div v-else style="display:grid;grid-template-columns:240px 1fr 300px;gap:16px;height:calc(100vh - 56px - 100px);overflow:hidden">

      <!-- Panel 1: Reference Drug -->
      <div style="display:flex;flex-direction:column;gap:12px;overflow-y:auto">
        <div v-if="projectMode" class="card" style="padding:8px 12px;background:var(--primary,#2563eb);color:#fff;font-size:12px">
          Project mode — changes save immediately
        </div>

        <div class="card">
          <div class="card-title">Reference Drug</div>
          <div class="font-bold">{{ store.referenceDrug.name }}</div>
          <div class="badge badge-completed mt-4" style="margin-top:4px">{{ store.referenceDrug.chembl_id }}</div>
          <div class="text-muted text-sm" style="margin-top:8px;font-family:var(--mono);font-size:11px;word-break:break-all">
            {{ store.referenceDrug.smiles?.slice(0, 60) }}{{ store.referenceDrug.smiles?.length > 60 ? '...' : '' }}
          </div>
          <img
            v-if="store.referenceDrug.smiles"
            :src="`https://depict.chembl.io/svg/?smi=${encodeURIComponent(store.referenceDrug.smiles)}&molSize=150x100`"
            style="width:100%;margin-top:8px;border-radius:4px;background:#fff"
            @error="$event.target.style.display='none'"
          />
        </div>

        <div class="card">
          <label class="form-label">Similarity Threshold: {{ store.threshold }}</label>
          <input type="range" min="0.5" max="1.0" step="0.05" v-model.number="store.threshold" style="width:100%" />
          <button
            class="btn btn-primary w-full"
            style="margin-top:8px"
            :disabled="store.loading.candidates"
            @click="store.searchAnalogs()"
          >
            {{ store.loading.candidates ? 'Searching...' : '🔍 Find Analogs' }}
          </button>
        </div>

        <div v-if="store.candidates.length" style="display:flex;flex-direction:column;gap:6px">
          <button
            class="btn btn-secondary w-full"
            :disabled="store.loading.patents"
            @click="store.checkPatents()"
          >{{ store.loading.patents ? 'Checking...' : '📜 Check Patents' }}</button>
          <button
            class="btn btn-secondary w-full"
            :disabled="store.loading.admet || !store.candidates.some(c => c.patentStatus === 'free')"
            @click="store.runADMET()"
          >{{ store.loading.admet ? 'Running...' : '⚗️ Run ADMET (free only)' }}</button>
        </div>
      </div>

      <!-- Panel 2: Candidate Pool -->
      <div style="overflow-y:auto">
        <div v-if="store.loading.candidates" style="text-align:center;padding:32px"><LoadingSpinner /></div>
        <div v-else-if="!store.candidates.length" class="empty-state" style="height:auto;padding:32px">
          <p>{{ projectMode ? 'No analogs found for this investigation. Click "Find Analogs" to search.' : 'Click "Find Analogs" to search for structurally similar compounds.' }}</p>
        </div>
        <div v-else style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px">
          <div
            v-for="c in store.candidates"
            :key="c.smiles || c.cid"
            class="card"
            :style="c.shortlisted ? 'border-color:var(--primary)' : ''"
          >
            <img
              v-if="c.smiles"
              :src="`https://depict.chembl.io/svg/?smi=${encodeURIComponent(c.smiles)}&molSize=140x90`"
              style="width:100%;border-radius:4px;background:#fff;margin-bottom:8px"
              @error="$event.target.style.display='none'"
            />
            <div class="flex items-center justify-between mb-2">
              <span class="badge badge-active">{{ (c.score * 100).toFixed(0) }}% similar</span>
              <span
                class="badge"
                style="font-size:11px"
                :style="patentBadgeStyle(c.patentStatus)"
              >{{ c.patentStatus }}</span>
            </div>
            <div v-if="c.cid" class="text-muted text-sm">CID: {{ c.cid }}</div>
            <div v-if="c.admet && Object.keys(c.admet).length" class="text-sm" style="margin-top:4px">
              <div v-if="c.admet['Water Solubility']">Sol: {{ c.admet['Water Solubility'] }}</div>
              <div v-if="c.admet['hERG I inhibitor'] !== undefined">hERG: {{ c.admet['hERG I inhibitor'] ? 'Yes' : 'No' }}</div>
            </div>
            <button
              class="btn btn-sm w-full"
              style="margin-top:8px"
              :class="c.shortlisted ? 'btn-primary' : 'btn-secondary'"
              @click="handleToggle(c)"
            >{{ c.shortlisted ? '★ Shortlisted' : '☆ Shortlist' }}</button>
          </div>
        </div>
      </div>

      <!-- Panel 3: Shortlist + Save / Done -->
      <div style="display:flex;flex-direction:column;gap:12px;overflow-y:auto">
        <div class="card">
          <div class="card-title">Shortlist ({{ store.shortlisted.length }})</div>
          <div v-if="!store.shortlisted.length" class="text-muted text-sm">No candidates shortlisted yet.</div>
          <div v-else>
            <div v-for="c in store.shortlisted" :key="c.smiles" class="card" style="padding:8px;margin-bottom:6px">
              <div class="flex items-center justify-between">
                <span class="text-sm font-bold">CID {{ c.cid || '—' }}</span>
                <span class="badge" :style="patentBadgeStyle(c.patentStatus)">{{ c.patentStatus }}</span>
              </div>
              <div class="text-muted text-sm" style="font-family:var(--mono);font-size:10px;margin-top:2px;word-break:break-all">
                {{ c.smiles?.slice(0, 40) }}...
              </div>
            </div>

            <!-- ADMET comparison table -->
            <div v-if="admetKeys.length" style="margin-top:12px;overflow-x:auto">
              <div class="card-title" style="font-size:12px">ADMET Comparison</div>
              <table style="width:100%;font-size:11px">
                <thead>
                  <tr>
                    <th style="text-align:left;padding:2px">Endpoint</th>
                    <th v-for="(c, i) in store.shortlisted" :key="i" style="padding:2px">C{{ i + 1 }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="key in admetKeys" :key="key">
                    <td class="text-muted" style="padding:2px;white-space:nowrap">{{ key.slice(0, 18) }}</td>
                    <td v-for="(c, i) in store.shortlisted" :key="i" style="padding:2px;text-align:center">
                      {{ c.admet?.[key] !== undefined ? String(c.admet[key]).slice(0, 6) : '—' }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Drug search mode: project selector (only when shortlisted items exist) -->
            <div v-if="!projectMode" style="margin-top:16px">
              <div class="form-label">Save to project</div>
              <select v-model="selectedProjectId" class="form-control" style="margin-bottom:8px">
                <option :value="null">+ Create new project</option>
                <option v-for="p in allProjects" :key="p.id" :value="p.id">{{ p.name }}</option>
              </select>
              <input
                v-if="selectedProjectId === null"
                v-model="newProjectName"
                class="form-control"
                placeholder="New project name..."
                style="margin-bottom:8px"
              />
              <button
                class="btn btn-primary w-full"
                :disabled="saving || !canSave"
                @click="startSave"
              >{{ saveButtonLabel }}</button>
            </div>
          </div>

          <!-- Project mode: Done button — always visible regardless of shortlist state -->
          <div v-if="projectMode" style="margin-top:12px">
            <button
              class="btn btn-primary w-full"
              :disabled="saving"
              @click="doneWithProject"
            >{{ saving ? 'Saving...' : '✓ Done — Return to Project' }}</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Unshortlist warning: candidate has associated synthesis plans -->
    <div
      v-if="pendingUnshortlist"
      style="position:fixed;inset:0;background:rgba(0,0,0,0.4);display:flex;align-items:center;justify-content:center;z-index:1000"
    >
      <div class="card" style="max-width:420px;width:100%;padding:24px">
        <div class="card-title" style="margin-bottom:8px">Remove analog from project?</div>
        <p class="text-muted text-sm" style="margin-bottom:6px">
          This analog has <strong>{{ pendingUnshortlist.planCount }} synthesis plan{{ pendingUnshortlist.planCount > 1 ? 's' : '' }}</strong> attached to it.
        </p>
        <p class="text-muted text-sm" style="margin-bottom:16px">
          Removing it will <strong>permanently delete</strong> those plan{{ pendingUnshortlist.planCount > 1 ? 's' : '' }} and all associated data.
        </p>
        <div class="flex gap-2">
          <button class="btn btn-secondary" style="flex:1" @click="cancelUnshortlist">Keep it</button>
          <button class="btn btn-primary" style="flex:1;background:#dc2626;border-color:#dc2626" @click="confirmUnshortlist">Remove anyway</button>
        </div>
      </div>
    </div>

    <!-- Compound conflict dialog -->
    <div
      v-if="compoundConflict"
      style="position:fixed;inset:0;background:rgba(0,0,0,0.4);display:flex;align-items:center;justify-content:center;z-index:999"
    >
      <div class="card" style="max-width:400px;width:100%;padding:24px">
        <div class="card-title">Project already has a compound</div>
        <p class="text-muted text-sm" style="margin-bottom:16px">
          <strong>{{ compoundConflict.project.name }}</strong> already has {{ compoundConflict.existingCompounds.length }} compound{{ compoundConflict.existingCompounds.length > 1 ? 's' : '' }}. What would you like to do?
        </p>
        <div class="flex gap-2">
          <button class="btn btn-secondary" style="flex:1" @click="resolveConflict('add')">Add alongside</button>
          <button class="btn btn-primary" style="flex:1" @click="resolveConflict('replace')">Replace existing</button>
        </div>
        <button class="btn btn-secondary w-full" style="margin-top:8px" @click="compoundConflict = null; pendingSaveAction = null">Cancel</button>
      </div>
    </div>
  </div>
</template>
