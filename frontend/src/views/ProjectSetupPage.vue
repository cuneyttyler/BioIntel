<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/projects'
import { experiments as experimentsApi, synthesisPlan as synthesisPlanApi } from '@/services/api'
import { useUIStore } from '@/stores/ui'
import PageHeader from '@/components/layout/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ProjectForm from '@/components/projects/ProjectForm.vue'
import CompoundSearch from '@/components/projects/CompoundSearch.vue'
import CompoundPreviewCard from '@/components/projects/CompoundPreviewCard.vue'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const ui = useUIStore()

const isEdit = !!route.params.id
const existingProject = ref(null)
const selectedCompound = ref(null)
const saving = ref(false)

// Edit-mode supplementary data
const synthPlans = ref([])
const allExperiments = ref([])
const planningExps = ref(null)
const selectedPlanIds = ref([])   // for multi-select compare

const investigations = computed(() => existingProject.value?.investigations || [])
const analogCandidates = computed(() => existingProject.value?.analog_candidates || [])
const patentBadgeStyle = (status) => ({
  free: 'background:#d1fae5;color:#065f46',
  covered: 'background:#fee2e2;color:#991b1b',
  unknown: 'background:#f3f4f6;color:#6b7280',
}[status] || 'background:#f3f4f6;color:#6b7280')

const planTypeBadge = (t) => t === 'retro' ? 'Single-Step' : 'Multi-Step'
const statusBadgeClass = (s) => ({ planned: 'badge-active', in_progress: 'badge-active', completed: 'badge-completed', failed: 'badge-failed', draft: '', active: 'badge-active' }[s] || '')

onMounted(async () => {
  if (isEdit) {
    await projectStore.fetchProject(route.params.id)
    existingProject.value = projectStore.currentProject
    await loadEditData()
  }
})

const loadEditData = async () => {
  const id = route.params.id
  try {
    synthPlans.value = await synthesisPlanApi.list(id)
  } catch { synthPlans.value = [] }
  try {
    allExperiments.value = await experimentsApi.list(id)
  } catch { allExperiments.value = [] }
}

const handleSubmit = async (formData) => {
  saving.value = true
  try {
    let project
    if (isEdit) {
      project = await projectStore.updateProject(route.params.id, formData)
    } else {
      project = await projectStore.createProject(formData)
    }

    if (selectedCompound.value && !isEdit) {
      await compoundsApi.create({ ...selectedCompound.value, project: project.id })
    }

    ui.addToast(`Project ${isEdit ? 'updated' : 'created'} successfully`, 'success')
    router.push('/')
  } catch (e) {
    ui.addToast('Failed to save project', 'error')
  } finally {
    saving.value = false
  }
}

const browseRoute = (plan) => {
  router.push(
    `/synthesis?project=${route.params.id}&plan=${plan.id}&type=${plan.plan_type}&smiles=${encodeURIComponent(plan.target_smiles)}`
  )
}

const expandToExperiments = async (plan) => {
  planningExps.value = plan.id
  try {
    const created = await synthesisPlanApi.planExperiments(plan.id)
    ui.addToast(`${created.length} experiment${created.length !== 1 ? 's' : ''} created.`, 'success')
    await loadEditData()
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

const planSynthesis = (analogId, type) => {
  router.push(`/synthesis?project=${route.params.id}&analog=${analogId}&type=${type}&autorun=1`)
}

const formatDate = (dt) => dt ? new Date(dt).toLocaleDateString() : '—'
const smilesTrunc = (s) => s ? (s.length > 32 ? s.slice(0, 32) + '…' : s) : '—'
</script>

<template>
  <div style="max-width:860px">
    <PageHeader :title="isEdit ? 'Edit Project' : 'New Project'" />

    <!-- Project form -->
    <div v-if="!isEdit || existingProject" class="card mb-4">
      <ProjectForm :initial="existingProject || {}" @submit="handleSubmit" />
    </div>
    <div v-else class="card mb-4" style="padding:32px;text-align:center">
      <LoadingSpinner />
    </div>

    <!-- Attach compound (create mode only) -->
    <div v-if="!isEdit" class="card mb-4">
      <div class="card-title">Attach Compound</div>
      <CompoundSearch @select="selectedCompound = $event" />
      <CompoundPreviewCard :compound="selectedCompound" />
    </div>

    <!-- Edit-mode sections -->
    <template v-if="isEdit && existingProject">

      <!-- Analogs -->
      <div class="card mb-4">
        <div class="flex items-center justify-between mb-3">
          <div>
            <div class="card-title" style="margin-bottom:0">
              Analogs
              <span v-if="investigations.length" class="text-muted text-sm" style="font-weight:400;margin-left:8px">
                — reference: <strong>{{ investigations[0].name }}</strong>
                <span v-if="investigations[0].chembl_id" class="badge badge-completed" style="font-size:10px;margin-left:6px">{{ investigations[0].chembl_id }}</span>
              </span>
            </div>
          </div>
          <RouterLink :to="`/analogs?project=${route.params.id}`" class="btn btn-secondary btn-sm">+ Find Analog</RouterLink>
        </div>

        <div v-if="!analogCandidates.length" class="text-muted text-sm">
          No analogs yet. <RouterLink :to="`/analogs?project=${route.params.id}`" style="color:var(--primary)">Find analogs</RouterLink> for this project.
        </div>
        <table v-else style="width:100%;font-size:13px">
          <thead>
            <tr style="border-bottom:1px solid var(--border)">
              <th style="text-align:left;padding:6px 8px;font-weight:600">SMILES</th>
              <th style="text-align:right;padding:6px 8px;font-weight:600">Sim.</th>
              <th style="text-align:left;padding:6px 8px;font-weight:600">Patent</th>
              <th style="text-align:center;padding:6px 8px;font-weight:600">Single-Step</th>
              <th style="text-align:center;padding:6px 8px;font-weight:600">Multi-Step</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in analogCandidates" :key="c.id" style="border-bottom:1px solid var(--border)">
              <td style="padding:6px 8px;font-family:var(--mono);font-size:11px">{{ smilesTrunc(c.smiles) }}</td>
              <td style="padding:6px 8px;text-align:right;color:var(--text-muted)">{{ c.similarity_score ? (c.similarity_score * 100).toFixed(0) + '%' : '—' }}</td>
              <td style="padding:6px 8px"><span class="badge" style="font-size:10px" :style="patentBadgeStyle(c.patent_status)">{{ c.patent_status || 'unknown' }}</span></td>
              <td style="padding:6px 8px;text-align:center">
                <span v-if="c.retro_plan_id" class="badge badge-completed" style="font-size:10px">✓ Done</span>
                <button v-else class="btn btn-secondary btn-sm" style="font-size:11px" @click="planSynthesis(c.id, 'retro')">Plan →</button>
              </td>
              <td style="padding:6px 8px;text-align:center">
                <span v-if="c.tree_plan_id" class="badge badge-completed" style="font-size:10px">✓ Done</span>
                <button v-else class="btn btn-secondary btn-sm" style="font-size:11px" @click="planSynthesis(c.id, 'tree')">Plan →</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Synthesis Plans -->
      <div class="card mb-4">
        <div class="flex items-center justify-between mb-3">
          <div class="card-title" style="margin-bottom:0">Synthesis Plans</div>
          <div v-if="synthPlans.length >= 2" class="flex items-center gap-2">
            <span class="text-muted text-sm" style="font-size:11px">
              {{ selectedPlanIds.length < 2 ? 'Select 2+ to compare' : `${selectedPlanIds.length} selected` }}
            </span>
            <button
              class="btn btn-sm"
              :class="selectedPlanIds.length >= 2 ? 'btn-primary' : 'btn-secondary'"
              :disabled="selectedPlanIds.length < 2"
              @click="comparePlans"
            >Compare</button>
          </div>
        </div>

        <div v-if="!synthPlans.length" class="text-muted text-sm">
          No synthesis plans yet. Use the "Plan →" buttons in the Analogs table above to create plans.
        </div>
        <table v-else style="width:100%;font-size:13px">
          <thead>
            <tr style="border-bottom:1px solid var(--border)">
              <th style="padding:6px 8px;width:32px"></th>
              <th style="text-align:left;padding:6px 8px;font-weight:600">Target SMILES</th>
              <th style="text-align:left;padding:6px 8px;font-weight:600">Type</th>
              <th style="text-align:left;padding:6px 8px;font-weight:600">Status</th>
              <th style="text-align:right;padding:6px 8px;font-weight:600">Steps</th>
              <th style="text-align:left;padding:6px 8px;font-weight:600">Created</th>
              <th style="padding:6px 8px"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="plan in synthPlans" :key="plan.id" style="border-bottom:1px solid var(--border)">
              <td style="padding:6px 8px">
                <input
                  type="checkbox"
                  :value="plan.id"
                  v-model="selectedPlanIds"
                  style="cursor:pointer"
                />
              </td>
              <td style="padding:6px 8px;font-family:var(--mono);font-size:11px">{{ smilesTrunc(plan.target_smiles) }}</td>
              <td style="padding:6px 8px"><span class="badge">{{ planTypeBadge(plan.plan_type) }}</span></td>
              <td style="padding:6px 8px"><span class="badge" :class="statusBadgeClass(plan.status)">{{ plan.status }}</span></td>
              <td style="padding:6px 8px;text-align:right">{{ plan.experiment_count }}</td>
              <td style="padding:6px 8px;color:var(--text-muted)">{{ formatDate(plan.created_at) }}</td>
              <td style="padding:6px 8px">
                <div class="flex gap-2" style="justify-content:flex-end">
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
      </div>

      <!-- Experiments -->
      <div class="card mb-4">
        <div class="flex items-center justify-between mb-3">
          <div class="card-title" style="margin-bottom:0">Experiments</div>
          <RouterLink to="/experiments/new" class="btn btn-secondary btn-sm">+ New Experiment</RouterLink>
        </div>

        <div v-if="!allExperiments.length" class="text-muted text-sm">No experiments yet.</div>
        <table v-else style="width:100%;font-size:13px">
          <thead>
            <tr style="border-bottom:1px solid var(--border)">
              <th style="text-align:left;padding:6px 8px;font-weight:600">Title</th>
              <th style="text-align:left;padding:6px 8px;font-weight:600">Type</th>
              <th style="text-align:left;padding:6px 8px;font-weight:600">Status</th>
              <th style="text-align:left;padding:6px 8px;font-weight:600">Created</th>
              <th style="padding:6px 8px"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="exp in allExperiments" :key="exp.id" style="border-bottom:1px solid var(--border)">
              <td style="padding:6px 8px">{{ exp.title }}</td>
              <td style="padding:6px 8px"><span class="badge">{{ exp.experiment_type }}</span></td>
              <td style="padding:6px 8px"><span class="badge" :class="statusBadgeClass(exp.status)">{{ exp.status }}</span></td>
              <td style="padding:6px 8px;color:var(--text-muted)">{{ formatDate(exp.created_at) }}</td>
              <td style="padding:6px 8px;text-align:right">
                <RouterLink :to="`/experiments/${exp.id}`" class="btn btn-secondary btn-sm">View</RouterLink>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

    </template>
  </div>
</template>
