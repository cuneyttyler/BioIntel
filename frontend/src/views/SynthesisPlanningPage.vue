<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { synthesis as synthesisApi, synthesisPlan as synthesisPlanApi, projects as projectsApi } from '@/services/api'
import { useUIStore } from '@/stores/ui'
import PageHeader from '@/components/layout/PageHeader.vue'

const route = useRoute()
const router = useRouter()
const ui = useUIStore()

const smiles = ref('')
const retroResult = ref(null)
const treeResult = ref(null)
const loading = ref({ retro: false, tree: false, saveRoute: false, planExperiments: false, delete: false })
const stepConditions = ref({})
const stepBuyability = ref({})

const linkedProjectId = ref(null)
const linkedAnalogId = ref(null)
const linkedPlanId = ref(null)
const allProjects = ref([])
const projectDetail = ref(null)

// Saved plan state
const savedPlan = ref(null)
const resultSynced = ref(false)
const activeAnalysisType = ref(null)  // 'retro' | 'tree'

// When entering via ?type=retro|tree (from project page), lock to that type
const lockedType = ref(null)   // 'retro' | 'tree' | null

// Advanced tools
const showAdvanced = ref(false)
const reactant1 = ref('')
const reactant2 = ref('')
const forwardResult = ref(null)
const loadingForward = ref(false)

// Delete confirmation
const showDeleteConfirm = ref(false)

// Recursive tree node — self-registers so recursive template references resolve correctly
const SynthesisTreeNode = {
  name: 'SynthesisTreeNode',
  props: { node: Object, depth: { type: Number, default: 0 } },
  template: `
    <div :style="{ paddingLeft: depth * 16 + 'px', borderLeft: depth ? '2px solid var(--border)' : 'none', marginLeft: depth ? '8px' : '0', paddingTop: '4px' }">
      <div class="flex items-center gap-2" style="flex-wrap:wrap;margin-bottom:4px">
        <code style="font-size:11px;background:var(--surface-2,#f3f4f6);padding:2px 8px;border-radius:4px;word-break:break-all">{{ node.smiles }}</code>
        <span v-if="node.terminal" class="badge badge-completed" style="font-size:10px">starting material</span>
      </div>
      <div v-for="(child, i) in node.children" :key="i" style="margin-top:4px">
        <div class="text-muted text-sm" style="font-size:11px;margin-bottom:2px">↓ {{ child.transform }}</div>
        <SynthesisTreeNode v-for="(p, j) in child.precursors" :key="j" :node="p" :depth="depth + 1" />
      </div>
    </div>
  `,
}
SynthesisTreeNode.components = { SynthesisTreeNode }

// --- Computed ---

const referenceInvestigation = computed(() => projectDetail.value?.investigations?.[0] || null)
const analogCandidates = computed(() => projectDetail.value?.analog_candidates || [])

// Show locked context panel: project is linked AND a target SMILES is set
// (investigation is not required — pre-selected analog via ?analog param may arrive without one)
const smilesLocked = computed(() => !!(linkedProjectId.value && smiles.value))

// Show analog picker: project is linked, has analogs, but no target SMILES chosen yet
const showAnalogPicker = computed(() =>
  !!(linkedProjectId.value && analogCandidates.value.length && !smiles.value)
)

const hasResults = computed(() =>
  (retroResult.value && !retroResult.value.error && retroResult.value.results?.length) ||
  (treeResult.value && !treeResult.value.error && treeResult.value.tree)
)

const showSavePlanButton = computed(() =>
  hasResults.value && linkedProjectId.value && !resultSynced.value && !loading.value.saveRoute
)

// --- Lifecycle ---

onMounted(async () => {
  if (route.query.smiles) smiles.value = route.query.smiles
  if (route.query.project) linkedProjectId.value = Number(route.query.project)
  if (route.query.analog) linkedAnalogId.value = Number(route.query.analog)
  if (route.query.plan) linkedPlanId.value = Number(route.query.plan)
  if (route.query.type) lockedType.value = route.query.type   // 'retro' | 'tree'

  try { allProjects.value = await projectsApi.list() } catch { /* non-critical */ }

  if (linkedProjectId.value) {
    await loadProjectDetail()
    await loadExistingPlan()
  }

  // One-time autorun: strip flag immediately to prevent re-trigger on refresh
  const autorun = route.query.autorun === '1'
  if (autorun) {
    const cleanQuery = { ...route.query }
    delete cleanQuery.autorun
    router.replace({ query: cleanQuery })
    const type = lockedType.value || 'retro'
    await runRetro(type, /* autoSave */ true)
  }

  // Legacy from=analog flag (still supported for backward compat)
  if (route.query.from === 'analog') {
    router.replace({ query: { smiles: route.query.smiles, project: route.query.project } })
    await runRetro('retro', /* autoSave */ true)
  }
})

// --- Data loading ---

const loadProjectDetail = async () => {
  try {
    projectDetail.value = await projectsApi.get(linkedProjectId.value)
    // When a specific analog is pre-selected via ?analog=ID, resolve its SMILES
    // so the analog picker is skipped and the locked context panel is shown instead.
    if (linkedAnalogId.value && !smiles.value) {
      const candidate = projectDetail.value?.analog_candidates?.find(c => c.id === linkedAnalogId.value)
      if (candidate?.smiles) smiles.value = candidate.smiles
    }
  } catch { /* non-critical */ }
}

const loadExistingPlan = async () => {
  try {
    let plan = null
    if (linkedPlanId.value) {
      // Browsing a specific saved plan — load it directly
      plan = await synthesisPlanApi.get(linkedPlanId.value)
    } else {
      const params = { project: linkedProjectId.value }
      if (linkedAnalogId.value) params.analog = linkedAnalogId.value
      const plans = await synthesisPlanApi.list(params)
      const filtered = lockedType.value ? plans.filter(p => p.plan_type === lockedType.value) : plans
      plan = filtered[filtered.length - 1] || null
    }
    if (!plan) return
    savedPlan.value = plan
    // Lock the type to whatever this plan is
    if (!lockedType.value) lockedType.value = plan.plan_type
    // Hydrate the result panel from saved route_data so the route is visible immediately
    if (plan.route_data) {
      if (plan.plan_type === 'retro') {
        retroResult.value = plan.route_data
        const steps = retroResult.value?.results || []
        steps.forEach((step, i) => fetchStepConditions(step, i))
      } else {
        treeResult.value = plan.route_data
      }
      activeAnalysisType.value = plan.plan_type
      resultSynced.value = true
    }
  } catch { /* non-critical */ }
}

// --- Analog selection ---

const selectAnalog = (candidate) => {
  smiles.value = candidate.smiles
  retroResult.value = null
  treeResult.value = null
  resultSynced.value = false
  activeAnalysisType.value = null
}

// --- Analysis ---

const runRetro = async (action, autoSave = false) => {
  if (!smiles.value) return
  loading.value[action] = true
  retroResult.value = null
  treeResult.value = null
  resultSynced.value = false
  stepConditions.value = {}
  stepBuyability.value = {}
  try {
    if (action === 'retro') {
      retroResult.value = await synthesisApi.retro({ smiles: smiles.value })
      const steps = retroResult.value?.results || []
      steps.forEach((step, i) => fetchStepConditions(step, i))
    } else {
      treeResult.value = await synthesisApi.tree({ smiles: smiles.value })
    }
    activeAnalysisType.value = action
    if (autoSave && linkedProjectId.value && hasResults.value) {
      await saveRoute(action)
    }
  } catch (e) {
    console.error(e)
    ui.addToast('Retrosynthesis failed.', 'error')
  } finally {
    loading.value[action] = false
  }
}

const fetchStepConditions = async (step, index) => {
  stepConditions.value[index] = null
  try {
    const res = await synthesisApi.conditions({
      reactants: step.precursors?.join('.') || '',
      products: smiles.value,
      reaction_type: step.transform,
    })
    stepConditions.value[index] = res.conditions?.[0] || false
  } catch {
    stepConditions.value[index] = false
  }
}

const checkBuyability = async (smilesVal, key) => {
  stepBuyability.value[key] = null
  try {
    stepBuyability.value[key] = await synthesisApi.buyables(smilesVal)
  } catch {
    stepBuyability.value[key] = false
  }
}

// --- Save / delete plan ---

const saveRoute = async (planType) => {
  if (!linkedProjectId.value) { ui.addToast('Select a project first.', 'error'); return }
  const result = planType === 'retro' ? retroResult.value : treeResult.value
  if (!result) return
  loading.value.saveRoute = true
  try {
    savedPlan.value = await synthesisPlanApi.create({
      project: linkedProjectId.value,
      target_smiles: smiles.value,
      plan_type: planType,
      route_data: result,
      ...(linkedAnalogId.value ? { analog_candidate: linkedAnalogId.value } : {}),
    })
    resultSynced.value = true
    ui.addToast('Synthesis plan saved.', 'success')
  } catch (e) {
    console.error(e)
    ui.addToast('Failed to save plan.', 'error')
  } finally {
    loading.value.saveRoute = false
  }
}

const confirmDelete = () => { showDeleteConfirm.value = true }
const cancelDelete = () => { showDeleteConfirm.value = false }

const deletePlan = async () => {
  if (!savedPlan.value) return
  loading.value.delete = true
  try {
    await synthesisPlanApi.delete(savedPlan.value.id)
    savedPlan.value = null
    resultSynced.value = false
    showDeleteConfirm.value = false
    ui.addToast('Synthesis plan deleted.', 'success')
  } catch {
    ui.addToast('Failed to delete plan.', 'error')
  } finally {
    loading.value.delete = false
  }
}

// --- Plan experiments ---

const planExperiments = async () => {
  if (!savedPlan.value) { ui.addToast('Save a plan first.', 'error'); return }
  loading.value.planExperiments = true
  try {
    const exps = await synthesisPlanApi.planExperiments(savedPlan.value.id)
    ui.addToast(`${exps.length} experiment${exps.length !== 1 ? 's' : ''} created.`, 'success')
    router.push(`/projects/${linkedProjectId.value}/edit`)
  } catch {
    ui.addToast('Failed to create experiments.', 'error')
  } finally {
    loading.value.planExperiments = false
  }
}

// --- Forward prediction ---

const runForward = async () => {
  if (!reactant1.value || !reactant2.value) return
  loadingForward.value = true
  forwardResult.value = null
  try {
    forwardResult.value = await synthesisApi.forward({ reactants: `${reactant1.value}.${reactant2.value}` })
  } catch (e) { console.error(e) }
  finally { loadingForward.value = false }
}

const useAsReactant = (smilesVal) => {
  if (!reactant1.value) reactant1.value = smilesVal
  else reactant2.value = smilesVal
  showAdvanced.value = true
  document.getElementById('advanced-section')?.scrollIntoView({ behavior: 'smooth' })
}
</script>

<template>
  <div style="padding-top:16px">
    <PageHeader title="Synthesis Planning">
      <template v-if="linkedProjectId" #actions>
        <RouterLink
          :to="`/projects/${linkedProjectId}/edit`"
          class="btn btn-secondary btn-sm"
          style="display:inline-flex;align-items:center;gap:6px"
        >← Back to Project</RouterLink>
      </template>
    </PageHeader>

    <!-- ── 1. Analog picker: project linked, investigation exists, no target chosen yet ── -->
    <div v-if="showAnalogPicker" class="card mb-4">
      <div class="card-title mb-1">Select Target Analog</div>
      <div class="text-muted text-sm mb-4">
        This project has shortlisted analog candidates from the drug investigation for
        <strong>{{ referenceInvestigation.name }}</strong>.
        Select the analog you want to plan a synthesis route for.
      </div>

      <div v-for="c in analogCandidates" :key="c.id" class="card mb-2" style="padding:12px;cursor:pointer" @click="selectAnalog(c)">
        <div class="flex items-start justify-between gap-3">
          <div style="flex:1;min-width:0">
            <code style="font-size:11px;background:var(--surface-2,#f3f4f6);padding:3px 8px;border-radius:4px;word-break:break-all;display:block">{{ c.smiles }}</code>
          </div>
          <div class="flex items-center gap-2" style="white-space:nowrap;flex-shrink:0">
            <span v-if="c.similarity_score" class="badge badge-active" style="font-size:10px">{{ Math.round(c.similarity_score * 100) }}% similar</span>
            <span
              class="badge"
              :class="c.patent_status === 'free' ? 'badge-completed' : c.patent_status === 'protected' ? 'badge-failed' : 'badge-pending'"
              style="font-size:10px"
            >{{ c.patent_status || 'unknown' }}</span>
            <button class="btn btn-primary btn-sm" style="font-size:11px" @click.stop="selectAnalog(c)">Select →</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ── 2. Synthesis context: locked target after analog is selected ── -->
    <div v-else-if="smilesLocked" class="card mb-4">
      <div class="flex items-center justify-between mb-3">
        <div class="card-title" style="margin-bottom:0">Synthesis Context</div>
        <button
          v-if="showAnalogPicker === false && analogCandidates.length"
          class="btn btn-secondary btn-sm"
          style="font-size:11px"
          @click="smiles = ''; retroResult = null; treeResult = null; activeAnalysisType = null"
        >← Change Analog</button>
      </div>

      <div class="flex items-start gap-6" style="flex-wrap:wrap">
        <!-- Reference drug (only shown when investigation context is available) -->
        <template v-if="referenceInvestigation">
          <div style="flex:1;min-width:180px">
            <div class="text-muted text-sm" style="font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:0.04em;margin-bottom:6px">Reference Drug</div>
            <div class="font-bold text-sm mb-1">{{ referenceInvestigation.name }}</div>
            <div v-if="referenceInvestigation.chembl_id" class="text-muted text-sm mb-2" style="font-size:11px">{{ referenceInvestigation.chembl_id }}</div>
            <code style="font-size:11px;background:var(--surface-2,#f3f4f6);padding:4px 8px;border-radius:4px;word-break:break-all;display:block">{{ referenceInvestigation.smiles }}</code>
          </div>
          <div style="display:flex;align-items:center;padding-top:30px;color:var(--text-muted);font-size:18px;flex-shrink:0">→</div>
        </template>

        <!-- Target analog -->
        <div style="flex:1;min-width:180px">
          <div class="text-muted text-sm" style="font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:0.04em;margin-bottom:6px">Target Analog</div>
          <div class="font-bold text-sm mb-2" style="color:var(--primary)">Selected for Synthesis</div>
          <code style="font-size:11px;background:var(--surface-2,#f3f4f6);padding:4px 8px;border-radius:4px;word-break:break-all;display:block;border:1px solid var(--primary,#2563eb)">{{ smiles }}</code>
        </div>
      </div>

      <!-- Analysis type toggle -->
      <div style="margin-top:20px;padding-top:16px;border-top:1px solid var(--border)">
        <div class="text-muted text-sm mb-2" style="font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:0.04em">Analysis Type</div>
        <div class="flex gap-2">
          <button
            class="btn"
            :class="activeAnalysisType === 'retro' ? 'btn-primary' : 'btn-secondary'"
            :disabled="loading.retro || (lockedType && lockedType !== 'retro')"
            @click="runRetro('retro')"
          >
            <span v-if="loading.retro">Analyzing…</span>
            <span v-else>⚗️ Single-Step Retro</span>
          </button>
          <button
            class="btn"
            :class="activeAnalysisType === 'tree' ? 'btn-primary' : 'btn-secondary'"
            :disabled="loading.tree || (lockedType && lockedType !== 'tree')"
            @click="runRetro('tree')"
          >
            <span v-if="loading.tree">Building tree…</span>
            <span v-else>🌳 Multi-Step Tree</span>
          </button>
        </div>
        <div v-if="lockedType" class="text-muted text-sm" style="margin-top:6px;font-size:11px">
          Plan type locked to {{ lockedType === 'retro' ? 'Single-Step Retro' : 'Multi-Step Tree' }} for this analog.
        </div>
      </div>
    </div>

    <!-- ── 3. Standalone mode: free SMILES input ── -->
    <div v-else class="card mb-4">
      <div class="card-title">Target Molecule</div>
      <div class="text-muted text-sm mb-3">
        Enter the SMILES of the molecule you want to synthesize. The planner will find disconnection routes working backwards from the target to available starting materials.
      </div>

      <div class="form-group mb-3">
        <label class="form-label">Target SMILES</label>
        <input
          v-model="smiles"
          class="form-control"
          placeholder="e.g. CC(=O)Oc1ccccc1C(=O)O"
          style="font-family:var(--mono);font-size:13px"
        />
      </div>

      <!-- Project linker -->
      <div class="flex items-center gap-3 mb-4">
        <label class="form-label" style="margin:0;white-space:nowrap;min-width:120px">Link to project</label>
        <select v-model="linkedProjectId" class="form-control" style="max-width:320px">
          <option :value="null">— none —</option>
          <option v-for="p in allProjects" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
        <span v-if="linkedProjectId" class="badge badge-active" style="font-size:11px">linked</span>
      </div>

      <!-- Analysis type toggle -->
      <div class="flex gap-2" style="padding-top:4px">
        <button
          class="btn"
          :class="activeAnalysisType === 'retro' ? 'btn-primary' : 'btn-secondary'"
          :disabled="loading.retro || !smiles"
          @click="runRetro('retro')"
        >
          <span v-if="loading.retro">Analyzing…</span>
          <span v-else>⚗️ Single-Step Retro</span>
        </button>
        <button
          class="btn"
          :class="activeAnalysisType === 'tree' ? 'btn-primary' : 'btn-secondary'"
          :disabled="loading.tree || !smiles"
          @click="runRetro('tree')"
        >
          <span v-if="loading.tree">Building tree…</span>
          <span v-else>🌳 Multi-Step Tree</span>
        </button>
      </div>
    </div>

    <!-- ── Single-step route results ── -->
    <div v-if="retroResult" class="card mb-4">
      <div class="card-title mb-2">Synthesis Route</div>

      <div v-if="retroResult.error" class="text-muted text-sm">{{ retroResult.error }}</div>
      <div v-else-if="!retroResult.results?.length" class="text-muted text-sm">
        {{ retroResult.message || 'No disconnections found for this structure.' }}
      </div>

      <div v-else>
        <!-- Molecular properties -->
        <div v-if="retroResult.descriptors" class="flex gap-4 text-sm text-muted mb-4" style="flex-wrap:wrap;padding:8px 12px;background:var(--surface-2,#f8f9fa);border-radius:6px">
          <span><b>MW</b> {{ retroResult.descriptors.mw }} Da</span>
          <span><b>LogP</b> {{ retroResult.descriptors.logp }}</span>
          <span><b>HBD</b> {{ retroResult.descriptors.hbd }}</span>
          <span><b>HBA</b> {{ retroResult.descriptors.hba }}</span>
          <span><b>TPSA</b> {{ retroResult.descriptors.tpsa }} Å²</span>
          <span><b>RotBonds</b> {{ retroResult.descriptors.rotatable_bonds }}</span>
        </div>

        <div class="text-muted text-sm mb-3">{{ retroResult.results.length }} disconnection{{ retroResult.results.length !== 1 ? 's' : '' }} found — each step below is a candidate synthetic route from commercially available starting materials to your target.</div>

        <div v-for="(step, i) in retroResult.results" :key="i" class="card mb-3" style="padding:14px">
          <div class="flex items-center gap-2 mb-1">
            <span class="badge badge-active" style="font-size:11px">Step {{ i + 1 }}</span>
            <span class="font-bold text-sm">{{ step.transform }}</span>
          </div>
          <div class="text-muted text-sm mb-3">{{ step.forward_reaction }}</div>

          <!-- Precursors -->
          <div class="mb-3">
            <div class="text-muted text-sm" style="margin-bottom:6px;font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:0.04em">Starting Materials</div>
            <div class="flex items-center gap-2" style="flex-wrap:wrap">
              <template v-for="(p, j) in step.precursors" :key="j">
                <div style="display:inline-flex;align-items:center;gap:4px">
                  <code style="font-size:11px;background:var(--surface-2,#f3f4f6);padding:3px 8px;border-radius:4px;word-break:break-all;max-width:220px">{{ p }}</code>
                  <button
                    class="btn btn-secondary btn-sm"
                    style="font-size:10px;padding:2px 6px;white-space:nowrap"
                    :disabled="stepBuyability[`step-${i}-${j}`] === null"
                    @click="checkBuyability(p, `step-${i}-${j}`)"
                  >
                    <template v-if="stepBuyability[`step-${i}-${j}`] === null">checking…</template>
                    <template v-else-if="stepBuyability[`step-${i}-${j}`]">
                      <span :style="stepBuyability[`step-${i}-${j}`].buyable ? 'color:#16a34a' : 'color:#dc2626'">
                        {{ stepBuyability[`step-${i}-${j}`].buyable ? '✓ Available' : '✗ Custom' }}
                      </span>
                    </template>
                    <template v-else>🛒 Check availability</template>
                  </button>
                </div>
                <span v-if="j < step.precursors.length - 1" class="text-muted font-bold">+</span>
              </template>
              <span class="text-muted">→</span>
              <code style="font-size:11px;background:var(--surface-2,#f3f4f6);padding:3px 8px;border-radius:4px;color:var(--primary)">target</code>
            </div>
          </div>

          <!-- Inline conditions -->
          <div style="padding:10px 12px;background:var(--surface-2,#f8f9fa);border-radius:6px;margin-bottom:10px">
            <div class="text-muted text-sm" style="font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:0.04em;margin-bottom:6px">Reaction Conditions</div>
            <div v-if="stepConditions[i] === undefined || stepConditions[i] === null" class="text-muted text-sm">Fetching conditions…</div>
            <div v-else-if="stepConditions[i] === false" class="text-muted text-sm">Conditions not available for this reaction type.</div>
            <div v-else class="flex gap-4 text-sm" style="flex-wrap:wrap">
              <span><b>Reagents:</b> {{ stepConditions[i].reagents }}</span>
              <span><b>Solvent:</b> {{ stepConditions[i].solvent }}</span>
              <span><b>Temp:</b> {{ stepConditions[i].temp }}</span>
              <span><b>Time:</b> {{ stepConditions[i].time }}</span>
            </div>
          </div>

          <div class="flex gap-2">
            <button class="btn btn-secondary btn-sm" style="font-size:11px" @click="step.precursors.forEach(p => useAsReactant(p))">→ Use in Forward Prediction</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Multi-step tree results ── -->
    <div v-if="treeResult" class="card mb-4">
      <div class="card-title mb-2">Multi-Step Synthesis Tree</div>
      <div class="text-muted text-sm mb-3">Each level shows a retrosynthetic disconnection. Leaf nodes (labeled "starting material") are the commercially available building blocks you need to obtain.</div>
      <div v-if="treeResult.error" class="text-muted text-sm">{{ treeResult.error }}</div>
      <div v-else-if="treeResult.tree">
        <SynthesisTreeNode :node="treeResult.tree" />
      </div>
    </div>

    <!-- ── Advanced Tools (collapsed) ── -->
    <div id="advanced-section" class="card mb-4">
      <button
        class="flex items-center gap-2 w-full"
        style="background:none;border:none;cursor:pointer;padding:0;text-align:left"
        @click="showAdvanced = !showAdvanced"
      >
        <span class="card-title" style="margin-bottom:0">Advanced Tools</span>
        <span class="text-muted text-sm" style="margin-left:4px">{{ showAdvanced ? '▲' : '▼' }}</span>
        <span class="text-muted text-sm" style="margin-left:8px">Forward Prediction</span>
      </button>

      <div v-if="showAdvanced" style="margin-top:16px">
        <div class="text-muted text-sm mb-3">
          Given two specific reactants, predict the likely product. Useful when you have specific starting materials in hand and want to confirm what they will produce before running the reaction — or to verify a retrosynthetic step.
        </div>
        <div class="grid-2 mb-3">
          <div class="form-group" style="margin-bottom:0">
            <label class="form-label">Reactant 1</label>
            <input v-model="reactant1" class="form-control" placeholder="SMILES" style="font-family:var(--mono);font-size:13px" />
          </div>
          <div class="form-group" style="margin-bottom:0">
            <label class="form-label">Reactant 2</label>
            <input v-model="reactant2" class="form-control" placeholder="SMILES" style="font-family:var(--mono);font-size:13px" />
          </div>
        </div>
        <div class="flex gap-2 items-center">
          <button class="btn btn-primary" :disabled="loadingForward || !reactant1 || !reactant2" @click="runForward">
            {{ loadingForward ? 'Predicting…' : '→ Predict Product' }}
          </button>
          <button v-if="reactant1 || reactant2" class="btn btn-secondary btn-sm" @click="reactant1 = ''; reactant2 = ''; forwardResult = null">Clear</button>
        </div>

        <div v-if="forwardResult" style="margin-top:16px">
          <div v-if="forwardResult.error" class="text-muted text-sm">{{ forwardResult.error }}</div>
          <div v-else-if="forwardResult.message && !forwardResult.results?.length" class="text-muted text-sm">{{ forwardResult.message }}</div>
          <div v-else>
            <div class="card-title" style="font-size:13px;margin-bottom:8px">Predicted Products</div>
            <div v-for="(r, i) in forwardResult.results" :key="i" class="card" style="padding:10px;margin-bottom:6px">
              <div class="flex items-center justify-between mb-1">
                <span class="font-bold text-sm">{{ r.reaction }}</span>
                <span class="badge badge-active">Score {{ r.score?.toFixed(2) }}</span>
              </div>
              <code style="font-size:12px;word-break:break-all">{{ r.product }}</code>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Bottom actions bar ── -->
    <div v-if="linkedProjectId && (showSavePlanButton || savedPlan)" class="card mb-4">
      <div class="flex items-center justify-between" style="flex-wrap:wrap;gap:12px">
        <div class="text-sm">
          <span v-if="resultSynced" style="color:var(--success,#16a34a);font-weight:500">✓ Plan saved</span>
          <span v-else-if="savedPlan && !hasResults" class="text-muted">
            Saved plan: {{ savedPlan.plan_type === 'retro' ? 'Single-Step Retro' : 'Multi-Step Tree' }}
          </span>
        </div>

        <div class="flex items-center gap-2">
          <button
            v-if="showSavePlanButton"
            class="btn btn-primary btn-sm"
            :disabled="loading.saveRoute"
            @click="saveRoute(activeAnalysisType)"
          >{{ loading.saveRoute ? 'Saving…' : '💾 Save Plan' }}</button>

          <button
            v-if="savedPlan"
            class="btn btn-primary btn-sm"
            :disabled="loading.planExperiments"
            @click="planExperiments"
          >{{ loading.planExperiments ? 'Creating…' : '🧪 Plan Experiments' }}</button>

          <button
            v-if="savedPlan"
            class="btn btn-secondary btn-sm"
            style="color:#dc2626"
            @click="confirmDelete"
          >🗑 Delete Plan</button>
        </div>
      </div>
    </div>

    <!-- Delete confirmation modal -->
    <div v-if="showDeleteConfirm" style="position:fixed;inset:0;background:rgba(0,0,0,0.4);display:flex;align-items:center;justify-content:center;z-index:1000">
      <div class="card" style="max-width:400px;width:90%;padding:24px">
        <div class="card-title" style="margin-bottom:8px">Delete Synthesis Plan?</div>
        <div class="text-muted text-sm mb-4">This will permanently delete the saved plan and its link to the project. Any experiments already created from this plan are not affected.</div>
        <div class="flex gap-2 justify-end">
          <button class="btn btn-secondary" @click="cancelDelete">Cancel</button>
          <button class="btn btn-primary" style="background:#dc2626;border-color:#dc2626" :disabled="loading.delete" @click="deletePlan">
            {{ loading.delete ? 'Deleting…' : 'Delete' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>
