<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { projects as projectsApi, synthesisPlan as synthesisPlanApi, experiments as experimentsApi } from '@/services/api'
import { useUIStore } from '@/stores/ui'
import PageHeader from '@/components/layout/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useAIPageContext } from '@/composables/useAIPageContext'

const route = useRoute()
const router = useRouter()
const ui = useUIStore()
const projectId = route.params.id

const project     = ref(null)
const synthPlans  = ref([])
const experiments = ref([])
const loading     = ref(true)
const selectedPlanIds = ref([])
const planningExps    = ref(null)
const showGreenChem   = ref(false)

const investigations   = computed(() => project.value?.investigations   || [])
const analogCandidates = computed(() => project.value?.analog_candidates || [])

// ─── Route helpers ───────────────────────────────────────────────────────────

const patentBadgeStyle = (status) => ({
  free:    'background:#d1fae5;color:#065f46',
  covered: 'background:#fee2e2;color:#991b1b',
  unknown: 'background:#f3f4f6;color:#6b7280',
}[status] || 'background:#f3f4f6;color:#6b7280')

const planTypeLabel  = (t) => t === 'retro' ? 'Single-Step' : 'Multi-Step'
const statusClass    = (s) => ({ planned: 'badge-active', in_progress: 'badge-active', completed: 'badge-completed', failed: 'badge-failed', draft: '', active: 'badge-active' }[s] || '')
const formatDate     = (dt) => dt ? new Date(dt).toLocaleDateString() : '—'
const smilesTrunc    = (s) => s ? (s.length > 36 ? s.slice(0, 36) + '…' : s) : '—'

function planStepCount(plan) {
  if (!plan.route_data) return null
  try {
    const rd = typeof plan.route_data === 'string' ? JSON.parse(plan.route_data) : plan.route_data
    return rd?.steps?.length || rd?.reactions?.length || rd?.route?.length || null
  } catch { return null }
}

function planYieldEst(plan) {
  if (!plan.route_data) return null
  try {
    const rd = typeof plan.route_data === 'string' ? JSON.parse(plan.route_data) : plan.route_data
    return rd?.estimated_yield || rd?.overall_yield || null
  } catch { return null }
}

function routeQuality(plan) {
  const steps = planStepCount(plan)
  if (steps == null) return null
  if (steps <= 3)  return { label: 'Short',  color: '#16a34a', bg: '#f0fdf4' }
  if (steps <= 6)  return { label: 'Medium', color: '#ca8a04', bg: '#fefce8' }
  return { label: 'Long', color: '#dc2626', bg: '#fef2f2' }
}

// ─── ICH Q3C solvent data ────────────────────────────────────────────────────

const ICH_SOLVENTS = {
  '1 — Avoid': {
    color: '#dc2626', bg: '#fef2f2',
    items: [
      { name: 'Benzene',             limit: '2 ppm',    note: 'Carcinogen' },
      { name: 'CCl₄',               limit: '4 ppm',    note: 'Toxic' },
      { name: '1,2-Dichloroethane',  limit: '5 ppm',    note: 'Toxic' },
      { name: '1,1-Dichloroethene',  limit: '8 ppm',    note: 'Toxic' },
      { name: '1,1,1-Trichloroethane', limit: '1500 ppm', note: 'Environmental' },
    ],
  },
  '2 — Limit': {
    color: '#ca8a04', bg: '#fefce8',
    items: [
      { name: 'DCM',     limit: '600 ppm',  note: 'Common; limit rigorously' },
      { name: 'THF',     limit: '720 ppm',  note: 'Peroxide risk; use fresh' },
      { name: 'MeOH',   limit: '3000 ppm', note: 'Toxic on inhalation/ingestion' },
      { name: 'Toluene', limit: '890 ppm',  note: 'Reproductive toxin concern' },
      { name: 'MeCN',    limit: '410 ppm',  note: 'Limit for inhalation' },
      { name: 'DMF',     limit: '880 ppm',  note: 'Reproductive toxin' },
      { name: 'DMAc',    limit: '1090 ppm', note: 'Reproductive toxin' },
      { name: 'NMP',     limit: '530 ppm',  note: 'Reproductive toxin' },
      { name: 'Hexane',  limit: '290 ppm',  note: 'Neurotoxic; use heptane' },
      { name: 'Pyridine',limit: '200 ppm',  note: 'Reproductive toxin' },
    ],
  },
  '3 — Acceptable': {
    color: '#16a34a', bg: '#f0fdf4',
    items: [
      { name: 'EtOH',    limit: '5000 ppm', note: 'Preferred' },
      { name: 'IPA',     limit: '5000 ppm', note: 'Preferred' },
      { name: 'EtOAc',   limit: '5000 ppm', note: 'Preferred' },
      { name: 'Acetone', limit: '5000 ppm', note: 'Preferred' },
      { name: 'DMSO',    limit: '5000 ppm', note: 'Preferred' },
      { name: 'Heptane', limit: '5000 ppm', note: 'Preferred (vs hexane)' },
      { name: 'MEK',     limit: '5000 ppm', note: 'Preferred' },
      { name: 'MTBE',    limit: '5000 ppm', note: 'Preferred' },
      { name: 'H₂O',    limit: '—',        note: 'Always preferred' },
    ],
  },
}

// ─── Summary stats ───────────────────────────────────────────────────────────

const summaryStats = computed(() => ({
  candidates: analogCandidates.value.length,
  plans: synthPlans.value.length,
  experiments: experiments.value.length,
  completedPlans: synthPlans.value.filter(p => p.status === 'completed').length,
}))

// ─── Actions ─────────────────────────────────────────────────────────────────

const planSynthesis = (analogId, type) =>
  router.push(`/synthesis?project=${projectId}&analog=${analogId}&type=${type}&autorun=1`)

const browseRoute = (plan) =>
  router.push(`/synthesis?project=${projectId}&plan=${plan.id}&type=${plan.plan_type}&smiles=${encodeURIComponent(plan.target_smiles)}`)

const expandToExperiments = async (plan) => {
  planningExps.value = plan.id
  try {
    const created = await synthesisPlanApi.planExperiments(plan.id)
    ui.addToast(`${created.length} experiment${created.length !== 1 ? 's' : ''} created.`, 'success')
    await loadExperiments()
  } catch {
    ui.addToast('Failed to create experiments.', 'error')
  } finally {
    planningExps.value = null
  }
}

const comparePlans = () => {
  if (selectedPlanIds.value.length < 2) return
  router.push(`/synthesis/compare?plans=${selectedPlanIds.value.join(',')}`)
}

const loadExperiments = async () => {
  try {
    experiments.value = (await experimentsApi.list(projectId)).filter(e => e.experiment_type === 'synthesis')
  } catch { experiments.value = [] }
}

const projectIdNum = computed(() => parseInt(projectId))
useAIPageContext({
  pageType: 'SynthesisHub',
  projectIdRef: projectIdNum,
  getEntity: () => ({ plan_count: synthPlans.value.length }),
  applyFn: (s) => {
    // Synthesis Hub has no editable form fields
  },
})

onMounted(async () => {
  try {
    const [proj, plans] = await Promise.all([
      projectsApi.get(projectId),
      synthesisPlanApi.list(projectId),
    ])
    project.value = proj
    synthPlans.value = plans
    await loadExperiments()
  } catch { /* non-critical */ } finally {
    loading.value = false
  }
})
</script>

<template>
  <div style="max-width:980px">
    <PageHeader title="Drug Substance — Synthesis Hub">
      <template #actions>
        <RouterLink :to="`/analogs?project=${projectId}`" class="btn btn-outline">+ Find More Analogs</RouterLink>
      </template>
    </PageHeader>

    <LoadingSpinner v-if="loading" />
    <template v-else>

      <!-- Summary strip -->
      <div class="summary-strip">
        <div class="stat-pill">
          <span class="stat-val">{{ summaryStats.candidates }}</span>
          <span class="stat-lbl">Shortlisted Analogs</span>
        </div>
        <div class="stat-pill">
          <span class="stat-val">{{ summaryStats.plans }}</span>
          <span class="stat-lbl">Synthesis Plans</span>
        </div>
        <div class="stat-pill">
          <span class="stat-val">{{ summaryStats.completedPlans }}</span>
          <span class="stat-lbl">Plans Complete</span>
        </div>
        <div class="stat-pill">
          <span class="stat-val">{{ summaryStats.experiments }}</span>
          <span class="stat-lbl">Experiments</span>
        </div>
      </div>

      <!-- Analog Candidates ── -->
      <div class="card mb-4">
        <div class="section-top">
          <div>
            <div class="card-title" style="margin-bottom:0">
              Analog Candidates
              <span v-if="investigations.length" class="text-muted text-sm" style="font-weight:400;margin-left:8px">
                — reference: <strong>{{ investigations[0].name }}</strong>
                <span v-if="investigations[0].chembl_id" class="badge badge-completed" style="font-size:10px;margin-left:6px">{{ investigations[0].chembl_id }}</span>
              </span>
            </div>
            <p class="text-muted text-sm" style="margin:4px 0 0">
              Shortlisted from analog search. Create a synthesis plan for each candidate to develop.
            </p>
          </div>
        </div>

        <EmptyState
          v-if="!analogCandidates.length"
          title="No analog candidates"
          message="Open the Analog Workspace to search for and shortlist analogs."
        >
          <template #action>
            <RouterLink :to="`/analogs?project=${projectId}`" class="btn btn-primary">Open Analog Workspace →</RouterLink>
          </template>
        </EmptyState>

        <table v-else class="data-table">
          <thead>
            <tr>
              <th>SMILES</th>
              <th style="text-align:right">Similarity</th>
              <th>Patent</th>
              <th style="text-align:center">Single-Step Route</th>
              <th style="text-align:center">Multi-Step Route</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="c in analogCandidates" :key="c.id"
              :style="c.selected ? 'background:#f0fdf4' : ''"
            >
              <td style="font-family:var(--mono);font-size:11px">
                {{ smilesTrunc(c.smiles) }}
                <span v-if="c.selected" style="margin-left:6px;color:#16a34a;font-size:10px;font-weight:600">★ dev candidate</span>
              </td>
              <td style="text-align:right;color:var(--text-muted)">
                {{ c.similarity_score ? (c.similarity_score * 100).toFixed(0) + '%' : '—' }}
              </td>
              <td>
                <span class="badge" style="font-size:10px" :style="patentBadgeStyle(c.patent_status)">
                  {{ c.patent_status || 'unknown' }}
                </span>
              </td>
              <td style="text-align:center">
                <span v-if="c.retro_plan_id" class="badge badge-completed" style="font-size:10px">✓ Done</span>
                <button v-else class="btn btn-secondary btn-sm" style="font-size:11px" @click="planSynthesis(c.id, 'retro')">Plan →</button>
              </td>
              <td style="text-align:center">
                <span v-if="c.tree_plan_id" class="badge badge-completed" style="font-size:10px">✓ Done</span>
                <button v-else class="btn btn-secondary btn-sm" style="font-size:11px" @click="planSynthesis(c.id, 'tree')">Plan →</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Synthesis Plans ── -->
      <div class="card mb-4">
        <div class="section-top">
          <div class="card-title" style="margin-bottom:0">Synthesis Plans</div>
          <div style="display:flex;align-items:center;gap:10px">
            <span v-if="synthPlans.length >= 2" class="text-muted text-sm" style="font-size:11px">
              {{ selectedPlanIds.length < 2 ? 'Select 2+ to compare' : `${selectedPlanIds.length} selected` }}
            </span>
            <button
              v-if="synthPlans.length >= 2"
              class="btn btn-sm"
              :class="selectedPlanIds.length >= 2 ? 'btn-primary' : 'btn-secondary'"
              :disabled="selectedPlanIds.length < 2"
              @click="comparePlans"
            >Compare Routes</button>
          </div>
        </div>

        <EmptyState v-if="!synthPlans.length" title="No synthesis plans" message="Use the Plan → buttons above to generate a synthesis route for an analog." />

        <table v-else class="data-table">
          <thead>
            <tr>
              <th style="width:32px"></th>
              <th>Target SMILES</th>
              <th>Type</th>
              <th>Route Quality</th>
              <th>Steps</th>
              <th>Est. Yield</th>
              <th>Status</th>
              <th style="text-align:right">Experiments</th>
              <th>Created</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="plan in synthPlans" :key="plan.id">
              <td><input type="checkbox" :value="plan.id" v-model="selectedPlanIds" style="cursor:pointer" /></td>
              <td style="font-family:var(--mono);font-size:11px">{{ smilesTrunc(plan.target_smiles) }}</td>
              <td><span class="badge">{{ planTypeLabel(plan.plan_type) }}</span></td>
              <td>
                <span
                  v-if="routeQuality(plan)"
                  class="badge"
                  :style="`background:${routeQuality(plan).bg};color:${routeQuality(plan).color}`"
                >{{ routeQuality(plan).label }}</span>
                <span v-else class="text-muted" style="font-size:11px">—</span>
              </td>
              <td>
                <span v-if="planStepCount(plan) != null" style="font-weight:600;font-size:13px">{{ planStepCount(plan) }}</span>
                <span v-else class="text-muted" style="font-size:11px">—</span>
              </td>
              <td style="color:var(--text-muted)">
                {{ planYieldEst(plan) != null ? planYieldEst(plan) + '%' : '—' }}
              </td>
              <td><span class="badge" :class="statusClass(plan.status)">{{ plan.status }}</span></td>
              <td style="text-align:right">{{ plan.experiment_count }}</td>
              <td style="color:var(--text-muted)">{{ formatDate(plan.created_at) }}</td>
              <td>
                <div style="display:flex;gap:6px;justify-content:flex-end">
                  <button class="btn btn-secondary btn-sm" @click="browseRoute(plan)">Browse</button>
                  <button
                    v-if="plan.experiment_count === 0"
                    class="btn btn-primary btn-sm"
                    :disabled="planningExps === plan.id"
                    @click="expandToExperiments(plan)"
                  >{{ planningExps === plan.id ? 'Creating…' : 'Plan Experiments' }}</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Route quality key -->
        <div v-if="synthPlans.length" class="quality-key">
          <span class="key-lbl">Route length:</span>
          <span class="key-chip" style="background:#f0fdf4;color:#16a34a">Short ≤3 steps</span>
          <span class="key-chip" style="background:#fefce8;color:#ca8a04">Medium 4–6 steps</span>
          <span class="key-chip" style="background:#fef2f2;color:#dc2626">Long ≥7 steps</span>
        </div>
      </div>

      <!-- Synthesis Experiments ── -->
      <div class="card mb-4">
        <div class="section-top">
          <div class="card-title" style="margin-bottom:0">Synthesis Experiments</div>
          <RouterLink :to="`/experiments/new?project=${projectId}&type=synthesis`" class="btn btn-secondary btn-sm">+ Log Experiment</RouterLink>
        </div>

        <EmptyState v-if="!experiments.length" title="No synthesis experiments" message="Click Plan Experiments on a synthesis plan, or log one manually." />
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Status</th>
              <th>Created</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="exp in experiments" :key="exp.id">
              <td>{{ exp.title }}</td>
              <td><span class="badge" :class="statusClass(exp.status)">{{ exp.status }}</span></td>
              <td style="color:var(--text-muted)">{{ formatDate(exp.created_at) }}</td>
              <td style="text-align:right">
                <RouterLink :to="`/experiments/${exp.id}`" class="btn btn-secondary btn-sm">View →</RouterLink>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Green Chemistry / ICH Q3C Reference ── -->
      <div class="card mb-4">
        <div class="section-top" style="cursor:pointer" @click="showGreenChem = !showGreenChem">
          <div>
            <div class="card-title" style="margin-bottom:0">Green Chemistry — ICH Q3C Solvent Guide</div>
            <p class="text-muted text-sm" style="margin:2px 0 0">
              Solvent classification for pharmaceutical manufacturing. Use Class 3 solvents wherever feasible.
            </p>
          </div>
          <span style="font-size:18px;color:var(--text-muted)">{{ showGreenChem ? '▲' : '▼' }}</span>
        </div>

        <div v-if="showGreenChem" style="margin-top:16px;display:flex;flex-direction:column;gap:16px">
          <div
            v-for="(data, cls) in ICH_SOLVENTS"
            :key="cls"
            class="solvent-class"
            :style="`border-left:3px solid ${data.color};background:${data.bg}`"
          >
            <div class="solvent-class-header" :style="`color:${data.color}`">Class {{ cls }}</div>
            <table class="solvent-table">
              <thead>
                <tr>
                  <th>Solvent</th>
                  <th>PDE Limit</th>
                  <th>Note</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="s in data.items" :key="s.name">
                  <td><strong>{{ s.name }}</strong></td>
                  <td>{{ s.limit }}</td>
                  <td class="text-muted">{{ s.note }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="green-tips">
            <div class="green-tips-title">Green Chemistry Principles for Synthesis Scale-Up</div>
            <ul class="green-tip-list">
              <li>Replace Class 2 solvents early: DCM → EtOAc/MTBE, DMF → DMAc/NMP (only if necessary), Hexane → Heptane</li>
              <li>Use catalytic reagents over stoichiometric; prefer Pd-free metal catalysis when possible</li>
              <li>Design step-efficient routes: convergent synthesis preferred over linear for complex targets</li>
              <li>Atom economy: aim for &gt;80% atom economy per step; monitor PMI (Process Mass Intensity)</li>
              <li>Aqueous workup: design reactions to allow aqueous wash rather than distillation where possible</li>
              <li>ICH Q3C limits apply at the drug substance stage; residual solvents tested by headspace GC</li>
            </ul>
          </div>
        </div>
      </div>

    </template>
  </div>
</template>

<style scoped>
.summary-strip { display: flex; gap: 14px; margin-bottom: 20px; flex-wrap: wrap; }
.stat-pill     { background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; padding: 10px 18px; display: flex; flex-direction: column; align-items: center; min-width: 120px; }
.stat-val      { font-size: 22px; font-weight: 700; color: #111827; line-height: 1.2; }
.stat-lbl      { font-size: 11px; color: #6b7280; margin-top: 2px; }

.section-top { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 14px; gap: 12px; }
.data-table  { width: 100%; font-size: 13px; border-collapse: collapse; }
.data-table th { text-align: left; padding: 6px 8px; font-weight: 600; border-bottom: 1px solid var(--border, #e5e7eb); }
.data-table td { padding: 6px 8px; border-bottom: 1px solid var(--border, #e5e7eb); }

.quality-key  { display: flex; align-items: center; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
.key-lbl      { font-size: 11px; color: #6b7280; font-weight: 600; }
.key-chip     { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 8px; }

.solvent-class { border-radius: 8px; padding: 12px 16px; }
.solvent-class-header { font-size: 13px; font-weight: 700; margin-bottom: 8px; }
.solvent-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.solvent-table th { text-align: left; padding: 5px 8px; font-weight: 600; color: #374151; border-bottom: 1px solid rgba(0,0,0,0.08); }
.solvent-table td { padding: 5px 8px; border-bottom: 1px solid rgba(0,0,0,0.06); }

.green-tips       { background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 14px 16px; }
.green-tips-title { font-size: 13px; font-weight: 700; color: #0369a1; margin-bottom: 8px; }
.green-tip-list   { margin: 0; padding-left: 18px; display: flex; flex-direction: column; gap: 4px; }
.green-tip-list li { font-size: 12px; color: #374151; }

.mb-4 { margin-bottom: 16px; }
</style>
