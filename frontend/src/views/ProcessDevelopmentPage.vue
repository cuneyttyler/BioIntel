<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { synthesisPlan as synthesisPlanApi } from '@/services/api'
import PageHeader from '@/components/layout/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useAIPageContext } from '@/composables/useAIPageContext'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id

const synthPlans = ref([])
const selectedPlanId = ref(null)
const cppNotes = ref('')
const impurities = ref([])
const showImpurityForm = ref(false)
const newImpurity = ref({ name: '', type: 'by_product', ich_class: 'unspecified', limit: '' })

const selectedPlan = computed(() => synthPlans.value.find(p => p.id === selectedPlanId.value) || null)

const smilesTrunc = (s) => s ? (s.length > 48 ? s.slice(0, 48) + '…' : s) : '—'

const milestones = ref([
  { stage: 'Lab', range: '1–10 g', batch_size: '', equipment: '', yield_pct: '', status: 'planned', notes: '' },
  { stage: 'Pilot', range: '100 g–1 kg', batch_size: '', equipment: '', yield_pct: '', status: 'planned', notes: '' },
  { stage: 'Manufacturing', range: '1 kg+', batch_size: '', equipment: '', yield_pct: '', status: 'planned', notes: '' },
])

const statusOptions = ['planned', 'in_progress', 'complete', 'on_hold']
const impurityTypes = ['by_product', 'starting_material', 'degradant', 'solvent_residue', 'other']
const ichClasses = ['specified', 'unspecified', 'genotoxic']

const viewRoute = () => {
  if (!selectedPlan.value) return
  router.push(`/synthesis?project=${projectId}&plan=${selectedPlan.value.id}&type=${selectedPlan.value.plan_type}&smiles=${encodeURIComponent(selectedPlan.value.target_smiles)}`)
}

const addImpurity = () => {
  if (!newImpurity.value.name.trim()) return
  impurities.value.push({ ...newImpurity.value, id: Date.now() })
  newImpurity.value = { name: '', type: 'by_product', ich_class: 'unspecified', limit: '' }
  showImpurityForm.value = false
}

const removeImpurity = (id) => {
  impurities.value = impurities.value.filter(i => i.id !== id)
}

const projectIdNum = computed(() => parseInt(projectId))
useAIPageContext({
  pageType: 'ProcessDevelopment',
  projectIdRef: projectIdNum,
  getEntity: () => ({ cppNotes: cppNotes.value }),
  applyFn: (s) => {
    if (s.cppNotes !== undefined) cppNotes.value = s.cppNotes
  },
})

onMounted(async () => {
  try {
    synthPlans.value = await synthesisPlanApi.list(projectId)
    if (synthPlans.value.length === 1) selectedPlanId.value = synthPlans.value[0].id
  } catch { synthPlans.value = [] }
})
</script>

<template>
  <div style="max-width:900px">
    <PageHeader title="Process Development">
      <template #actions>
        <RouterLink :to="`/projects/${projectId}/synthesis`" class="btn btn-secondary">← Synthesis Hub</RouterLink>
      </template>
    </PageHeader>

    <p class="text-muted text-sm mb-4">
      Translates the bench-scale synthesis route into a process suitable for manufacturing. Documents critical process parameters, scale-up milestones, and impurity profiles.
    </p>

    <!-- Section 1: Select Synthesis Route -->
    <div class="card mb-4">
      <div class="card-title">Process Route</div>
      <p class="text-muted text-sm mb-3">
        Select the synthesis plan you are scaling up. This becomes the reference route for all process development work.
      </p>

      <EmptyState
        v-if="!synthPlans.length"
        title="No synthesis plans yet"
        message="Create a synthesis plan in the Synthesis Hub first, then return here to begin process development."
      />
      <template v-else>
        <div style="display:flex;gap:8px;align-items:center;margin-bottom:12px">
          <select v-model="selectedPlanId" class="form-control" style="max-width:420px">
            <option :value="null">— Select a synthesis plan —</option>
            <option v-for="p in synthPlans" :key="p.id" :value="p.id">
              {{ p.plan_type === 'retro' ? 'Single-Step' : 'Multi-Step' }} — {{ smilesTrunc(p.target_smiles) }}
            </option>
          </select>
          <button v-if="selectedPlan" class="btn btn-secondary btn-sm" @click="viewRoute">View Route →</button>
        </div>

        <div v-if="selectedPlan" style="padding:10px 14px;background:var(--surface-raised,#f8f9fa);border-radius:6px;font-size:13px">
          <div class="flex gap-4" style="flex-wrap:wrap">
            <span><b>Type:</b> {{ selectedPlan.plan_type === 'retro' ? 'Single-Step Retro' : 'Multi-Step Tree' }}</span>
            <span><b>Status:</b> {{ selectedPlan.status }}</span>
            <span><b>Experiments:</b> {{ selectedPlan.experiment_count }}</span>
          </div>
          <div style="margin-top:6px;font-family:var(--mono);font-size:11px;color:var(--text-muted)">{{ selectedPlan.target_smiles }}</div>
        </div>
      </template>
    </div>

    <!-- Section 2: Scale-Up Milestones -->
    <div class="card mb-4">
      <div class="card-title">Scale-Up Milestones</div>
      <p class="text-muted text-sm mb-3">
        Define targets and track progress for each scale stage: lab bench → pilot plant → manufacturing.
      </p>
      <div style="overflow-x:auto">
        <table style="width:100%;font-size:13px;border-collapse:collapse">
          <thead>
            <tr style="border-bottom:2px solid var(--border)">
              <th style="text-align:left;padding:8px;font-weight:600;white-space:nowrap">Stage</th>
              <th style="text-align:left;padding:8px;font-weight:600;white-space:nowrap">Typical Scale</th>
              <th style="text-align:left;padding:8px;font-weight:600;white-space:nowrap">Target Batch Size</th>
              <th style="text-align:left;padding:8px;font-weight:600">Equipment Notes</th>
              <th style="text-align:right;padding:8px;font-weight:600;white-space:nowrap">Target Yield %</th>
              <th style="text-align:left;padding:8px;font-weight:600">Status</th>
              <th style="text-align:left;padding:8px;font-weight:600">Notes / Risk Factors</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="m in milestones" :key="m.stage" style="border-bottom:1px solid var(--border);vertical-align:top">
              <td style="padding:8px;font-weight:600;white-space:nowrap">{{ m.stage }}</td>
              <td style="padding:8px;color:var(--text-muted);white-space:nowrap;font-size:11px">{{ m.range }}</td>
              <td style="padding:8px">
                <input v-model="m.batch_size" class="form-control" placeholder="e.g. 5 g" style="font-size:12px;min-width:80px" />
              </td>
              <td style="padding:8px">
                <textarea v-model="m.equipment" class="form-control" rows="2" placeholder="Reactor type, stirrer…" style="font-size:12px;min-width:140px;resize:vertical" />
              </td>
              <td style="padding:8px">
                <input v-model="m.yield_pct" type="number" min="0" max="100" class="form-control" placeholder="80" style="font-size:12px;width:70px;text-align:right" />
              </td>
              <td style="padding:8px">
                <select v-model="m.status" class="form-control" style="font-size:12px;min-width:110px">
                  <option v-for="s in statusOptions" :key="s" :value="s">{{ s.replace('_', ' ') }}</option>
                </select>
              </td>
              <td style="padding:8px">
                <textarea v-model="m.notes" class="form-control" rows="2" placeholder="Go/no-go criteria, known risks…" style="font-size:12px;min-width:160px;resize:vertical" />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Section 3: CPP / CQA Notes -->
    <div class="card mb-4">
      <div class="card-title">Critical Process Parameters & Quality Attributes</div>
      <p class="text-muted text-sm mb-3">
        Document CPPs (reaction time, temperature, agitation, addition order, equivalents) and CQAs (purity, yield, residual solvents, particle size) for each synthesis step.
      </p>
      <textarea
        v-model="cppNotes"
        class="form-control"
        rows="8"
        placeholder="Step 1 — Acylation:&#10;  CPPs: temperature 0–5°C, addition rate ≤ 0.5 mL/min&#10;  CQAs: purity ≥ 98%, residual DCM ≤ 600 ppm&#10;&#10;Step 2 — …"
        style="font-family:var(--mono);font-size:12px;resize:vertical"
      />
    </div>

    <!-- Section 4: Impurity Profile -->
    <div class="card mb-4">
      <div class="flex items-center justify-between mb-3">
        <div>
          <div class="card-title" style="margin-bottom:0">Impurity Profile</div>
          <p class="text-muted text-sm" style="margin:4px 0 0">
            Track known and potential impurities per synthesis step with ICH classification and acceptable limits.
          </p>
        </div>
        <button class="btn btn-secondary btn-sm" @click="showImpurityForm = !showImpurityForm">
          {{ showImpurityForm ? 'Cancel' : '+ Add Impurity' }}
        </button>
      </div>

      <!-- Add form -->
      <div v-if="showImpurityForm" style="padding:14px;background:var(--surface-raised,#f8f9fa);border-radius:6px;margin-bottom:14px">
        <div class="grid-2" style="gap:10px;margin-bottom:10px">
          <div class="form-group" style="margin:0">
            <label class="form-label">Impurity Name</label>
            <input v-model="newImpurity.name" class="form-control" placeholder="e.g. N-oxide byproduct" />
          </div>
          <div class="form-group" style="margin:0">
            <label class="form-label">Type</label>
            <select v-model="newImpurity.type" class="form-control">
              <option v-for="t in impurityTypes" :key="t" :value="t">{{ t.replace('_', ' ') }}</option>
            </select>
          </div>
          <div class="form-group" style="margin:0">
            <label class="form-label">ICH Classification</label>
            <select v-model="newImpurity.ich_class" class="form-control">
              <option v-for="c in ichClasses" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>
          <div class="form-group" style="margin:0">
            <label class="form-label">Acceptable Limit</label>
            <input v-model="newImpurity.limit" class="form-control" placeholder="e.g. ≤ 0.15%" />
          </div>
        </div>
        <button class="btn btn-primary btn-sm" :disabled="!newImpurity.name.trim()" @click="addImpurity">Add</button>
      </div>

      <EmptyState
        v-if="!impurities.length"
        title="No impurities logged"
        message="Add impurity entries once synthesis experiments are complete and analytical data is available."
      />
      <table v-else style="width:100%;font-size:13px">
        <thead>
          <tr style="border-bottom:1px solid var(--border)">
            <th style="text-align:left;padding:6px 8px;font-weight:600">Impurity</th>
            <th style="text-align:left;padding:6px 8px;font-weight:600">Type</th>
            <th style="text-align:left;padding:6px 8px;font-weight:600">ICH Class</th>
            <th style="text-align:left;padding:6px 8px;font-weight:600">Limit</th>
            <th style="padding:6px 8px"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="imp in impurities" :key="imp.id" style="border-bottom:1px solid var(--border)">
            <td style="padding:6px 8px">{{ imp.name }}</td>
            <td style="padding:6px 8px"><span class="badge">{{ imp.type.replace('_', ' ') }}</span></td>
            <td style="padding:6px 8px"><span class="badge" :class="imp.ich_class === 'genotoxic' ? 'badge-failed' : ''">{{ imp.ich_class }}</span></td>
            <td style="padding:6px 8px;color:var(--text-muted)">{{ imp.limit || '—' }}</td>
            <td style="padding:6px 8px;text-align:right">
              <button class="btn btn-sm btn-secondary" style="color:#dc2626" @click="removeImpurity(imp.id)">Remove</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

  </div>
</template>
