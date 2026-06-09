<script setup>
import { reactive, ref, watch } from 'vue'

const props = defineProps({ initial: { type: Object, default: () => ({}) } })
const emit = defineEmits(['submit', 'update:pathway'])

const formEl = ref(null)

const form = reactive({
  name: props.initial.name || '',
  description: props.initial.description || '',
  phase: props.initial.phase || 'preclinical',
  status: props.initial.status || 'active',
  pathway: props.initial.pathway || 'analog_based',
  mode: props.initial.mode || 'manual',
  molecule_type: props.initial.molecule_type || 'small_molecule',
})

watch(() => form.pathway, (val) => emit('update:pathway', val))

const submit = () => {
  if (formEl.value?.checkValidity() === false) {
    formEl.value.reportValidity()
    return
  }
  emit('submit', { ...form })
}

function setField(key, value) {
  if (key in form) form[key] = value
}

defineExpose({ triggerSubmit: submit, setField })
</script>

<template>
  <form ref="formEl" @submit.prevent="submit">
    <div class="form-group">
      <label class="form-label">Project Name *</label>
      <input v-model="form.name" class="form-control" required placeholder="e.g. COMP-001 Formulation Development" />
    </div>
    <div class="form-group">
      <label class="form-label">Description</label>
      <textarea v-model="form.description" class="form-control" rows="3" placeholder="Brief description of the project goals..." />
    </div>
    <div class="grid-2">
      <div class="form-group">
        <label class="form-label">Development Pathway</label>
        <select v-model="form.pathway" class="form-control">
          <option value="analog_based">Analog-Based (known scaffold)</option>
          <option value="novel_design">Novel Design (target-first)</option>
        </select>
        <p style="font-size:11px;color:var(--text-muted);margin:4px 0 0">
          Novel Design enables virtual screening and target biology tools.
        </p>
      </div>
      <div class="form-group">
        <label class="form-label">Development Phase</label>
        <select v-model="form.phase" class="form-control">
          <option value="preclinical">Preclinical</option>
          <option value="phase1">Phase 1</option>
          <option value="phase2">Phase 2</option>
          <option value="phase3">Phase 3</option>
        </select>
      </div>
    </div>
    <div class="grid-2">
      <div class="form-group">
        <label class="form-label">Status</label>
        <select v-model="form.status" class="form-control">
          <option value="active">Active</option>
          <option value="on_hold">On Hold</option>
          <option value="completed">Completed</option>
          <option value="archived">Archived</option>
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">Molecule Type</label>
        <select v-model="form.molecule_type" class="form-control">
          <option value="small_molecule">Small Molecule</option>
          <option value="biologic">Biologic (mAb, protein, ADC…)</option>
          <option value="undetermined">Undetermined</option>
        </select>
      </div>
    </div>
    <div class="form-group">
      <label class="form-label">Project Mode</label>
      <select v-model="form.mode" class="form-control">
        <option value="manual">Manual — standard v2 workflow</option>
        <option value="ai_driven">AI-Driven — autonomous plan with human-in-the-loop gates</option>
      </select>
      <p style="font-size:11px;color:var(--text-muted);margin:4px 0 0">
        AI-Driven mode adds an AI-authored development plan to your project. You can switch from Manual to AI-Driven at any time.
      </p>
    </div>
  </form>
</template>
