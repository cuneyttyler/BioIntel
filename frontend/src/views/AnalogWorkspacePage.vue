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
const store  = useAnalogsStore()
const ui     = useUIStore()

const saving        = ref(false)
const loadingProject = ref(false)

// Project mode: entered from project page
const projectMode   = ref(false)
const projectId     = ref(null)
const projectCandidates = ref([])
const pendingUnshortlist = ref(null)

// Drug search mode
const allProjects    = ref([])
const selectedProjectId = ref(null)
const newProjectName    = ref('')
const compoundConflict  = ref(null)
const pendingSaveAction = ref(null)

// Pool filter / sort
const sortMode    = ref('similarity') // 'similarity' | 'patent_free' | 'admet'
const filterPat   = ref('all')        // 'all' | 'free' | 'covered' | 'unknown'
const copiedSmiles = ref(null)

const patentBadgeStyle = (status) => ({
  free:    'background:#d1fae5;color:#065f46',
  covered: 'background:#fee2e2;color:#991b1b',
  unknown: 'background:#f3f4f6;color:#6b7280',
}[status] || 'background:#f3f4f6;color:#6b7280')

// ─── Lipinski Ro5 from ADMET data ─────────────────────────────────────────

function ro5Check(candidate) {
  const a = candidate.admet
  if (!a) return null
  const mw   = a['Molecular Weight'] != null ? parseFloat(a['Molecular Weight']) : null
  const logP = a['Lipophilicity (LogP)'] != null ? parseFloat(a['Lipophilicity (LogP)']) : null
  const hbd  = a['Hydrogen Bond Donors'] != null ? parseInt(a['Hydrogen Bond Donors']) : null
  const hba  = a['Hydrogen Bond Acceptors'] != null ? parseInt(a['Hydrogen Bond Acceptors']) : null
  if (mw == null && logP == null && hbd == null && hba == null) return null
  const violations = [
    mw   != null && mw   > 500,
    logP != null && logP > 5,
    hbd  != null && hbd  > 5,
    hba  != null && hba  > 10,
  ].filter(Boolean).length
  return { mw, logP, hbd, hba, violations }
}

function ro5Style(v) {
  if (v == null) return null
  if (v.violations === 0) return { color: '#16a34a', label: 'Ro5 ✓' }
  if (v.violations === 1) return { color: '#ca8a04', label: '1 viol.' }
  return { color: '#dc2626', label: `${v.violations} viol.` }
}

// ─── Filtered / sorted pool ───────────────────────────────────────────────

const filteredCandidates = computed(() => {
  let list = filterPat.value === 'all'
    ? [...store.candidates]
    : store.candidates.filter(c => c.patentStatus === filterPat.value)

  if (sortMode.value === 'similarity') {
    list.sort((a, b) => (b.score || 0) - (a.score || 0))
  } else if (sortMode.value === 'patent_free') {
    const rank = { free: 0, unknown: 1, covered: 2 }
    list.sort((a, b) => (rank[a.patentStatus] ?? 1) - (rank[b.patentStatus] ?? 1))
  } else if (sortMode.value === 'admet') {
    // Sort by number of Ro5 violations ascending (best first)
    list.sort((a, b) => {
      const ra = ro5Check(a), rb = ro5Check(b)
      const va = ra?.violations ?? 99, vb = rb?.violations ?? 99
      return va - vb
    })
  }
  return list
})

// ─── ADMET comparison table (enhanced with color coding) ──────────────────

const ADMET_DISPLAY = [
  { key: 'Lipophilicity (LogP)',       label: 'LogP',         good: v => v >= 0 && v <= 5,   warn: v => v > 5 },
  { key: 'Molecular Weight',           label: 'MW (g/mol)',   good: v => v <= 500,            warn: v => v > 500 },
  { key: 'Water Solubility',           label: 'Solubility',   good: null, warn: null },
  { key: 'Caco-2 Permeability',        label: 'Caco-2',       good: v => v > -5.15, warn: v => v <= -5.15 },
  { key: 'hERG I inhibitor',           label: 'hERG I',       good: v => !v,         warn: v => !!v },
  { key: 'hERG II inhibitor',          label: 'hERG II',      good: v => !v,         warn: v => !!v },
  { key: 'AMES toxicity',              label: 'AMES',         good: v => !v,         warn: v => !!v },
  { key: 'Hepatotoxicity',             label: 'Hepatotox.',   good: v => !v,         warn: v => !!v },
  { key: 'BBB penetrant',              label: 'BBB',          good: null, warn: null },
  { key: 'Pgp-substrate',              label: 'P-gp',         good: null, warn: null },
  { key: 'CYP3A4 substrate',           label: 'CYP3A4',       good: null, warn: null },
]

const admetDisplayKeys = computed(() => {
  const present = new Set()
  store.shortlisted.forEach(c => Object.keys(c.admet || {}).forEach(k => present.add(k)))
  return ADMET_DISPLAY.filter(d => present.has(d.key))
})

function admetCellStyle(key, value) {
  const def = ADMET_DISPLAY.find(d => d.key === key)
  if (!def || value === undefined || value === null) return {}
  const numVal = parseFloat(value)
  if (!isNaN(numVal)) {
    if (def.good && def.good(numVal)) return { color: '#16a34a', fontWeight: '600' }
    if (def.warn && def.warn(numVal)) return { color: '#dc2626', fontWeight: '600' }
  } else {
    if (def.good && def.good(value)) return { color: '#16a34a', fontWeight: '600' }
    if (def.warn && def.warn(value)) return { color: '#dc2626', fontWeight: '600' }
  }
  return {}
}

function fmtAdmet(value) {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (typeof value === 'number') return value.toFixed(2)
  return String(value).slice(0, 10)
}

// ─── Actions ─────────────────────────────────────────────────────────────

function copySmiles(smiles) {
  navigator.clipboard.writeText(smiles).catch(() => {})
  copiedSmiles.value = smiles
  setTimeout(() => { copiedSmiles.value = null }, 1500)
}

const handleToggle = (candidate) => {
  if (projectMode.value) {
    if (candidate.shortlisted) {
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
  if (proj) {
    const planIds = [proj.retro_plan_id, proj.tree_plan_id].filter(Boolean)
    await Promise.all(planIds.map(id => synthesisPlanApi.delete(id).catch(() => {})))
    const idx = projectCandidates.value.findIndex(p => p.id === candidate.id)
    if (idx !== -1) {
      projectCandidates.value[idx].retro_plan_id = null
      projectCandidates.value[idx].tree_plan_id  = null
    }
  }
  store.toggleShortlistPersisted(candidate, projectId.value)
}

const cancelUnshortlist = () => { pendingUnshortlist.value = null }

const doneWithProject = async () => {
  if (saving.value) return
  saving.value = true
  try {
    await store.saveNewCandidatesToProject(projectId.value)
    ui.addToast('Analogs saved to project.', 'success')
    router.push(`/projects/${projectId.value}/candidates`)
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
    } catch { /* ignore */ }
    await doSave({ projectId: selectedProjectId.value, compoundAction: 'add' })
  } else {
    await doSave({ projectName: newProjectName.value.trim() })
  }
}

const resolveConflict = async (action) => {
  const saved = pendingSaveAction.value
  compoundConflict.value  = null
  pendingSaveAction.value = null
  await doSave({ ...saved, compoundAction: action })
}

const doSave = async (opts) => {
  saving.value = true
  try {
    const project = await store.saveToProject(opts)
    ui.addToast('Project saved — returning to project page.', 'success')
    router.push(`/projects/${project.id}/candidates`)
  } catch {
    ui.addToast('Failed to save to project', 'error')
  } finally {
    saving.value = false
  }
}

const selectedProject = computed(() => allProjects.value.find(p => p.id === selectedProjectId.value) || null)
const saveButtonLabel = computed(() => saving.value ? 'Saving...' : selectedProjectId.value ? 'Add to Project' : 'Save to New Project')
const canSave         = computed(() => store.shortlisted.length > 0 && (selectedProjectId.value !== null || newProjectName.value.trim()))

onMounted(async () => {
  const invId  = route.params.id
  const projId = route.query.project ? Number(route.query.project) : null

  if (projId) {
    projectMode.value  = true
    projectId.value    = projId
    loadingProject.value = true
    try {
      const project = await projectsApi.get(projId)
      projectCandidates.value = project.analog_candidates || []
      const inv = project.investigations?.[0]
      if (inv?.id) await store.loadInvestigation(inv.id)
    } catch (e) { console.error(e) } finally { loadingProject.value = false }
  } else if (invId) {
    await store.loadInvestigation(invId)
  }

  if (!projectMode.value) {
    try { allProjects.value = await projectsApi.list() } catch { /* non-critical */ }
  }
})
</script>

<template>
  <div>
    <PageHeader :title="store.referenceDrug ? `Analog Workspace — ${store.referenceDrug.name}` : 'Analog Workspace'">
      <template v-if="projectMode" #actions>
        <RouterLink :to="`/projects/${projectId}/candidates`" class="btn btn-secondary">← Back to Discovery</RouterLink>
      </template>
    </PageHeader>

    <div v-if="loadingProject" style="text-align:center;padding:64px"><LoadingSpinner /></div>

    <div v-else-if="!store.referenceDrug" class="empty-state">
      <div style="font-size:48px">🧪</div>
      <h3>No reference drug selected</h3>
      <p v-if="!projectMode">
        Start from the <RouterLink to="/drugs" style="color:var(--primary)">Drug Intelligence</RouterLink> page — search for a drug and click "Start Analog Search".
      </p>
      <p v-else class="text-muted text-sm">This project has no linked drug investigation yet.</p>
    </div>

    <div v-else class="workspace-grid">

      <!-- Panel 1: Reference Drug + Search Controls -->
      <div class="left-col">
        <div v-if="projectMode" class="project-mode-banner">Project mode — changes save immediately</div>

        <div class="card">
          <div class="card-title">Reference Drug</div>
          <div class="font-bold">{{ store.referenceDrug.name }}</div>
          <div class="badge badge-completed" style="margin-top:4px">{{ store.referenceDrug.chembl_id }}</div>
          <div class="text-muted text-sm" style="margin-top:8px;font-family:var(--mono);font-size:11px;word-break:break-all">
            {{ store.referenceDrug.smiles?.slice(0, 60) }}{{ store.referenceDrug.smiles?.length > 60 ? '…' : '' }}
          </div>
          <img
            v-if="store.referenceDrug.smiles"
            :src="`https://depict.chembl.io/svg/?smi=${encodeURIComponent(store.referenceDrug.smiles)}&molSize=160x110`"
            style="width:100%;margin-top:8px;border-radius:4px;background:#fff"
            @error="$event.target.style.display='none'"
          />
        </div>

        <div class="card">
          <label class="form-label" style="font-size:12px;font-weight:600">Similarity Threshold: {{ store.threshold }}</label>
          <input type="range" min="0.5" max="1.0" step="0.05" v-model.number="store.threshold" style="width:100%;margin:6px 0" />
          <div class="thresh-labels">
            <span>Broad (0.5)</span>
            <span>Tight (1.0)</span>
          </div>
          <button
            class="btn btn-primary w-full"
            style="margin-top:10px"
            :disabled="store.loading.candidates"
            @click="store.searchAnalogs()"
          >{{ store.loading.candidates ? 'Searching…' : '🔍 Find Analogs' }}</button>
        </div>

        <div v-if="store.candidates.length" class="card action-buttons">
          <button
            class="btn btn-secondary w-full"
            :disabled="store.loading.patents"
            @click="store.checkPatents()"
          >{{ store.loading.patents ? 'Checking…' : '📜 Check Patents' }}</button>
          <button
            class="btn btn-secondary w-full"
            :disabled="store.loading.admet || !store.candidates.some(c => c.patentStatus === 'free')"
            @click="store.runADMET()"
          >{{ store.loading.admet ? 'Running…' : '⚗️ Run ADMET (free only)' }}</button>
          <div class="admet-note">ADMET run on patent-free candidates only. Provides Ro5, solubility, hERG, toxicity flags.</div>
        </div>

        <!-- Lipinski Ro5 legend -->
        <div v-if="store.candidates.some(c => ro5Check(c))" class="card">
          <div class="card-title" style="font-size:12px">Ro5 Color Key</div>
          <div style="display:flex;flex-direction:column;gap:4px;font-size:11px">
            <div><span style="color:#16a34a;font-weight:600">Green</span> — 0 violations (Ro5 compliant)</div>
            <div><span style="color:#ca8a04;font-weight:600">Amber</span> — 1 violation (borderline)</div>
            <div><span style="color:#dc2626;font-weight:600">Red</span> — 2+ violations (concern)</div>
            <div style="color:#6b7280;margin-top:4px">MW≤500, LogP≤5, HBD≤5, HBA≤10</div>
          </div>
        </div>
      </div>

      <!-- Panel 2: Candidate Pool -->
      <div class="center-col">
        <!-- Sort & filter toolbar -->
        <div v-if="store.candidates.length" class="pool-toolbar">
          <div class="toolbar-group">
            <span class="toolbar-lbl">Sort:</span>
            <button
              v-for="opt in [{v:'similarity',l:'Similarity'},{v:'patent_free',l:'Patent-Free First'},{v:'admet',l:'Ro5 (ADMET)'}]"
              :key="opt.v"
              :class="['sort-btn', { active: sortMode === opt.v }]"
              @click="sortMode = opt.v"
            >{{ opt.l }}</button>
          </div>
          <div class="toolbar-group">
            <span class="toolbar-lbl">Filter:</span>
            <button
              v-for="opt in [{v:'all',l:'All'},{v:'free',l:'Free'},{v:'unknown',l:'Unknown'},{v:'covered',l:'Covered'}]"
              :key="opt.v"
              :class="['sort-btn', { active: filterPat === opt.v }]"
              @click="filterPat = opt.v"
            >{{ opt.l }}</button>
          </div>
          <span class="pool-count">{{ filteredCandidates.length }} / {{ store.candidates.length }}</span>
        </div>

        <div v-if="store.loading.candidates" style="text-align:center;padding:32px"><LoadingSpinner /></div>
        <div v-else-if="!store.candidates.length" class="empty-state" style="height:auto;padding:32px">
          <p>{{ projectMode ? 'Click "Find Analogs" to search for structurally similar compounds.' : 'Click "Find Analogs" to search for structurally similar compounds.' }}</p>
        </div>

        <div v-else class="candidate-grid">
          <div
            v-for="c in filteredCandidates"
            :key="c.smiles || c.cid"
            class="candidate-card"
            :class="{ shortlisted: c.shortlisted }"
          >
            <img
              v-if="c.smiles"
              :src="`https://depict.chembl.io/svg/?smi=${encodeURIComponent(c.smiles)}&molSize=140x90`"
              class="candidate-img"
              @error="$event.target.style.display='none'"
            />
            <div class="candidate-badges">
              <span class="badge badge-active">{{ (c.score * 100).toFixed(0) }}%</span>
              <span class="badge" style="font-size:11px" :style="patentBadgeStyle(c.patentStatus)">{{ c.patentStatus }}</span>
              <span
                v-if="ro5Check(c)"
                class="badge"
                style="font-size:11px"
                :style="`color:${ro5Style(ro5Check(c)).color};background:#f9fafb;border:1px solid currentColor`"
              >{{ ro5Style(ro5Check(c)).label }}</span>
            </div>
            <div v-if="c.cid" class="text-muted text-sm" style="font-size:11px">PubChem: {{ c.cid }}</div>
            <!-- Ro5 details when ADMET available -->
            <div v-if="ro5Check(c)" class="ro5-grid">
              <span v-if="ro5Check(c).mw != null">MW {{ ro5Check(c).mw.toFixed(0) }}</span>
              <span v-if="ro5Check(c).logP != null">LogP {{ ro5Check(c).logP?.toFixed(1) }}</span>
              <span v-if="ro5Check(c).hbd != null">HBD {{ ro5Check(c).hbd }}</span>
              <span v-if="ro5Check(c).hba != null">HBA {{ ro5Check(c).hba }}</span>
            </div>
            <div v-else-if="c.admet && Object.keys(c.admet).length" class="admet-mini">
              <div v-if="c.admet['Water Solubility']">Sol: {{ c.admet['Water Solubility'] }}</div>
              <div v-if="c.admet['hERG I inhibitor'] !== undefined"
                :style="c.admet['hERG I inhibitor'] ? 'color:#dc2626' : 'color:#16a34a'">
                hERG: {{ c.admet['hERG I inhibitor'] ? 'Yes ⚠' : 'No ✓' }}
              </div>
            </div>
            <div class="candidate-footer">
              <button
                class="btn btn-sm w-full"
                :class="c.shortlisted ? 'btn-primary' : 'btn-secondary'"
                @click="handleToggle(c)"
              >{{ c.shortlisted ? '★ Shortlisted' : '☆ Shortlist' }}</button>
              <button
                class="btn btn-sm btn-secondary copy-btn"
                :title="'Copy SMILES'"
                @click.stop="copySmiles(c.smiles)"
              >{{ copiedSmiles === c.smiles ? '✓' : '⎘' }}</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Panel 3: Shortlist + Save -->
      <div class="right-col">
        <div class="card">
          <div class="card-title">Shortlist ({{ store.shortlisted.length }})</div>
          <div v-if="!store.shortlisted.length" class="text-muted text-sm">No candidates shortlisted yet.</div>
          <div v-else>
            <div v-for="c in store.shortlisted" :key="c.smiles" class="shortlist-item">
              <div style="display:flex;align-items:center;justify-content:space-between">
                <span class="text-sm font-bold">CID {{ c.cid || '—' }}</span>
                <span class="badge" :style="patentBadgeStyle(c.patentStatus)">{{ c.patentStatus }}</span>
              </div>
              <div
                v-if="ro5Check(c)"
                class="ro5-inline"
                :style="`color:${ro5Style(ro5Check(c)).color}`"
              >{{ ro5Style(ro5Check(c)).label }} · Ro5</div>
              <div class="text-muted text-sm" style="font-family:var(--mono);font-size:10px;margin-top:2px;word-break:break-all">
                {{ c.smiles?.slice(0, 40) }}…
              </div>
            </div>

            <!-- ADMET comparison table -->
            <div v-if="admetDisplayKeys.length" style="margin-top:12px;overflow-x:auto">
              <div class="card-title" style="font-size:12px;margin-bottom:6px">ADMET Comparison</div>
              <table class="admet-table">
                <thead>
                  <tr>
                    <th>Endpoint</th>
                    <th v-for="(c, i) in store.shortlisted" :key="i">C{{ i + 1 }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="def in admetDisplayKeys" :key="def.key">
                    <td class="admet-lbl">{{ def.label }}</td>
                    <td
                      v-for="(c, i) in store.shortlisted" :key="i"
                      style="text-align:center"
                      :style="admetCellStyle(def.key, c.admet?.[def.key])"
                    >{{ fmtAdmet(c.admet?.[def.key]) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Save — drug search mode -->
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
                placeholder="New project name…"
                style="margin-bottom:8px"
              />
              <button class="btn btn-primary w-full" :disabled="saving || !canSave" @click="startSave">{{ saveButtonLabel }}</button>
            </div>
          </div>

          <!-- Project mode: Done -->
          <div v-if="projectMode" style="margin-top:12px">
            <button class="btn btn-primary w-full" :disabled="saving" @click="doneWithProject">
              {{ saving ? 'Saving…' : '✓ Done — Return to Project' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Unshortlist warning -->
    <div v-if="pendingUnshortlist" class="modal-overlay">
      <div class="card confirm-card">
        <div class="card-title" style="margin-bottom:8px">Remove analog from project?</div>
        <p class="text-muted text-sm" style="margin-bottom:6px">
          This analog has <strong>{{ pendingUnshortlist.planCount }} synthesis plan{{ pendingUnshortlist.planCount > 1 ? 's' : '' }}</strong> attached to it.
        </p>
        <p class="text-muted text-sm" style="margin-bottom:16px">
          Removing it will <strong>permanently delete</strong> those plan{{ pendingUnshortlist.planCount > 1 ? 's' : '' }} and all associated data.
        </p>
        <div style="display:flex;gap:10px">
          <button class="btn btn-secondary" style="flex:1" @click="cancelUnshortlist">Keep it</button>
          <button class="btn btn-danger"    style="flex:1" @click="confirmUnshortlist">Remove anyway</button>
        </div>
      </div>
    </div>

    <!-- Compound conflict dialog -->
    <div v-if="compoundConflict" class="modal-overlay">
      <div class="card confirm-card">
        <div class="card-title">Project already has a compound</div>
        <p class="text-muted text-sm" style="margin-bottom:16px">
          <strong>{{ compoundConflict.project.name }}</strong> already has {{ compoundConflict.existingCompounds.length }} compound{{ compoundConflict.existingCompounds.length > 1 ? 's' : '' }}. What would you like to do?
        </p>
        <div style="display:flex;gap:8px">
          <button class="btn btn-secondary" style="flex:1" @click="resolveConflict('add')">Add alongside</button>
          <button class="btn btn-primary"   style="flex:1" @click="resolveConflict('replace')">Replace existing</button>
        </div>
        <button class="btn btn-secondary w-full" style="margin-top:8px" @click="compoundConflict = null; pendingSaveAction = null">Cancel</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ── Grid ── */
.workspace-grid { display: grid; grid-template-columns: 220px 1fr 260px; gap: 16px; height: calc(100vh - 56px - 110px); overflow: hidden; }
.left-col  { display: flex; flex-direction: column; gap: 10px; overflow-y: auto; }
.center-col{ overflow-y: auto; }
.right-col { display: flex; flex-direction: column; gap: 12px; overflow-y: auto; }

/* ── Left panel ── */
.project-mode-banner { background: var(--primary, #2563eb); color: #fff; font-size: 12px; padding: 8px 12px; border-radius: 8px; }
.thresh-labels { display: flex; justify-content: space-between; font-size: 10px; color: #9ca3af; }
.action-buttons { display: flex; flex-direction: column; gap: 8px; }
.admet-note { font-size: 10px; color: #9ca3af; line-height: 1.4; margin-top: 2px; }

/* ── Pool toolbar ── */
.pool-toolbar  { display: flex; align-items: center; gap: 16px; padding: 8px 0 10px; flex-wrap: wrap; }
.toolbar-group { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.toolbar-lbl   { font-size: 11px; font-weight: 600; color: #6b7280; margin-right: 2px; }
.sort-btn      { font-size: 11px; padding: 3px 8px; border: 1px solid #d1d5db; border-radius: 12px; background: #fff; cursor: pointer; color: #374151; transition: all 0.15s; }
.sort-btn.active { background: #2563eb; color: #fff; border-color: #2563eb; }
.pool-count    { font-size: 11px; color: #9ca3af; margin-left: auto; }

/* ── Candidate grid ── */
.candidate-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 12px; }
.candidate-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; padding: 10px; display: flex; flex-direction: column; gap: 6px; transition: border-color 0.15s; }
.candidate-card:hover     { border-color: #93c5fd; }
.candidate-card.shortlisted { border-color: var(--primary, #2563eb); background: #eff6ff; }
.candidate-img  { width: 100%; border-radius: 4px; background: #fff; }
.candidate-badges { display: flex; flex-wrap: wrap; gap: 4px; }

.ro5-grid  { display: flex; flex-wrap: wrap; gap: 4px; }
.ro5-grid span { font-size: 10px; background: #f3f4f6; color: #374151; border-radius: 4px; padding: 1px 5px; }
.admet-mini { font-size: 11px; color: #374151; }

.candidate-footer { display: flex; gap: 6px; margin-top: 2px; }
.copy-btn { flex-shrink: 0; width: 32px; padding: 0; text-align: center; }

/* ── Shortlist ── */
.shortlist-item { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 8px; margin-bottom: 6px; }
.ro5-inline { font-size: 11px; font-weight: 600; margin-top: 2px; }

/* ── ADMET comparison ── */
.admet-table    { width: 100%; border-collapse: collapse; font-size: 11px; }
.admet-table th { text-align: left; padding: 4px 6px; background: #f3f4f6; font-weight: 600; color: #374151; border-bottom: 1px solid #e5e7eb; }
.admet-table td { padding: 4px 6px; border-bottom: 1px solid #f3f4f6; }
.admet-lbl      { color: #6b7280; white-space: nowrap; }

/* ── Modal overlay ── */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.4); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.confirm-card  { max-width: 420px; width: 92vw; padding: 24px; }

/* ── Btn danger ── */
.btn-danger { background: #dc2626; border-color: #dc2626; color: #fff; }
.btn-danger:hover { background: #b91c1c; }
</style>
