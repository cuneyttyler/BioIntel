<script setup>
import { reactive } from 'vue'

const props = defineProps({ initial: { type: Object, default: () => ({}) } })
const emit = defineEmits(['submit'])

const form = reactive({
  name: props.initial.name || '',
  description: props.initial.description || '',
  phase: props.initial.phase || 'preclinical',
  status: props.initial.status || 'active',
})

const submit = () => emit('submit', { ...form })
</script>

<template>
  <form @submit.prevent="submit">
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
        <label class="form-label">Development Phase</label>
        <select v-model="form.phase" class="form-control">
          <option value="preclinical">Preclinical</option>
          <option value="phase1">Phase 1</option>
          <option value="phase2">Phase 2</option>
          <option value="phase3">Phase 3</option>
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">Status</label>
        <select v-model="form.status" class="form-control">
          <option value="active">Active</option>
          <option value="on_hold">On Hold</option>
          <option value="completed">Completed</option>
          <option value="archived">Archived</option>
        </select>
      </div>
    </div>
    <button type="submit" class="btn btn-primary">Save Project</button>
  </form>
</template>
