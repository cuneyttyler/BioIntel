<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/projects'
import { useExperimentStore } from '@/stores/experiments'
import { synthesis as synthesisApi } from '@/services/api'
import { useUIStore } from '@/stores/ui'
import PageHeader from '@/components/layout/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const router = useRouter()
const projectStore = useProjectStore()
const expStore = useExperimentStore()
const ui = useUIStore()

onMounted(() => projectStore.fetchProjects())

const form = ref({
  title: '',
  experiment_type: 'formulation',
  objective: '',
  project: null,
  compound: null,
  success_criteria: '',
  variables: [],
  status: 'planned',
})

const compounds = ref([])
const retro = ref(null)
const retroLoading = ref(false)
const saving = ref(false)

const projectCompounds = computed(() => {
  if (!form.value.project) return []
  const proj = projectStore.projects.find(p => p.id === Number(form.value.project))
  return proj?.compounds || compounds.value
})

const addVariable = () => {
  form.value.variables.push({ name: '', unit: '', min: '', max: '', control: '' })
}
const removeVariable = (i) => form.value.variables.splice(i, 1)

const runRetro = async () => {
  const smiles = prompt('Enter target SMILES for retrosynthesis:')
  if (!smiles) return
  retroLoading.value = true
  try {
    retro.value = await synthesisApi.retro({ smiles })
  } catch { retro.value = null }
  retroLoading.value = false
}

const submit = async () => {
  saving.value = true
  try {
    const payload = {
      ...form.value,
      project: Number(form.value.project),
      compound: form.value.compound ? Number(form.value.compound) : null,
    }
    const exp = await expStore.createExperiment(payload)
    ui.addToast('Experiment created', 'success')
    router.push(`/experiments/${exp.id}`)
  } catch {
    ui.addToast('Failed to create experiment', 'error')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div style="max-width:800px">
    <PageHeader title="New Experiment">
      <template #actions>
        <RouterLink
          v-if="form.project"
          :to="`/projects/${form.project}/edit`"
          class="btn btn-secondary btn-sm"
          style="display:inline-flex;align-items:center;gap:6px"
        >← Back to Project</RouterLink>
        <button class="btn btn-primary" :disabled="saving" @click="submit">
          {{ saving ? 'Saving...' : 'Create Experiment' }}
        </button>
      </template>
    </PageHeader>

    <div class="card mb-4">
      <div class="grid-2">
        <div class="form-group">
          <label class="form-label">Title *</label>
          <input v-model="form.title" class="form-control" required placeholder="e.g. pH Optimization Study" />
        </div>
        <div class="form-group">
          <label class="form-label">Type *</label>
          <select v-model="form.experiment_type" class="form-control">
            <option value="formulation">Formulation</option>
            <option value="synthesis">Synthesis</option>
            <option value="analytical">Analytical</option>
            <option value="stability">Stability</option>
          </select>
        </div>
      </div>

      <div class="grid-2">
        <div class="form-group">
          <label class="form-label">Project *</label>
          <select v-model="form.project" class="form-control" required>
            <option value="">Select project...</option>
            <option v-for="p in projectStore.projects" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Status</label>
          <select v-model="form.status" class="form-control">
            <option value="planned">Planned</option>
            <option value="in_progress">In Progress</option>
          </select>
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">Objective *</label>
        <textarea v-model="form.objective" class="form-control" rows="3" required placeholder="Describe what this experiment aims to determine..." />
      </div>

      <div class="form-group">
        <label class="form-label">Success Criteria</label>
        <textarea v-model="form.success_criteria" class="form-control" rows="2" placeholder="Define measurable criteria for success..." />
      </div>
    </div>

    <div class="card mb-4">
      <div class="flex items-center justify-between mb-4">
        <div class="card-title" style="margin-bottom:0">Variables</div>
        <button class="btn btn-secondary btn-sm" @click="addVariable">+ Add Variable</button>
      </div>
      <div v-if="!form.variables.length" class="text-muted text-sm">No variables defined yet.</div>
      <div v-for="(v, i) in form.variables" :key="i" style="display:flex;gap:8px;align-items:center;margin-bottom:8px;flex-wrap:wrap">
        <input v-model="v.name" class="form-control" placeholder="Name" style="flex:2;min-width:100px" />
        <input v-model="v.unit" class="form-control" placeholder="Unit" style="flex:1;min-width:60px" />
        <input v-model="v.min" type="number" class="form-control" placeholder="Min" style="flex:1;min-width:70px" />
        <input v-model="v.max" type="number" class="form-control" placeholder="Max" style="flex:1;min-width:70px" />
        <button class="btn btn-danger btn-sm" @click="removeVariable(i)">✕</button>
      </div>
    </div>

    <div v-if="form.experiment_type === 'synthesis'" class="card mb-4">
      <div class="flex items-center justify-between mb-4">
        <div class="card-title" style="margin-bottom:0">Retrosynthesis Preview (ASKCOS)</div>
        <button class="btn btn-secondary btn-sm" :disabled="retroLoading" @click="runRetro">
          {{ retroLoading ? 'Running...' : '⚗️ Run Retrosynthesis' }}
        </button>
      </div>
      <div v-if="retroLoading"><LoadingSpinner /></div>
      <div v-else-if="retro">
        <div v-if="retro.error" class="text-muted text-sm">{{ retro.error }}</div>
        <div v-else>
          <div v-for="(result, i) in (retro.results || []).slice(0, 3)" :key="i" class="card" style="padding:12px;margin-bottom:8px">
            <div class="font-bold text-sm">Option {{ i + 1 }}</div>
            <div class="text-sm text-muted">Score: {{ result.score?.toFixed(3) }}</div>
            <code style="font-size:11px;word-break:break-all;display:block;margin-top:4px">{{ result.smiles || JSON.stringify(result).slice(0, 100) }}</code>
          </div>
        </div>
      </div>
      <div v-else class="text-muted text-sm">Enter a target SMILES to preview retrosynthesis routes.</div>
    </div>
  </div>
</template>
