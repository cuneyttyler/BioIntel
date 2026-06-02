<script setup>
import { ref } from 'vue'

const props = defineProps({
  projectId: { type: [Number, String], required: true },
})

const emit = defineEmits(['submit', 'cancel'])

const form = ref({
  study_type: 'acute_tox',
  species: 'rat',
  dose_route: 'oral',
  dose_levels: '',
  duration_days: '',
  objective: '',
})

const studyTypes = [
  { value: 'acute_tox', label: 'Acute Toxicology' },
  { value: 'repeat_dose_tox', label: 'Repeat-Dose Toxicology' },
  { value: 'genotoxicity', label: 'Genotoxicity' },
  { value: 'safety_pharmacology', label: 'Safety Pharmacology' },
  { value: 'pk', label: 'Pharmacokinetics' },
  { value: 'efficacy', label: 'Efficacy (In Vivo)' },
  { value: 'adme', label: 'ADME' },
]

function submit() {
  emit('submit', {
    ...form.value,
    dose_levels: form.value.dose_levels.split(',').map(s => s.trim()).filter(Boolean),
    duration_days: parseInt(form.value.duration_days) || null,
  })
}
</script>

<template>
  <div class="card">
    <h3 class="card-title">New Preclinical Study</h3>
    <div class="grid-3" style="gap:12px">
      <div class="form-group">
        <label>Study Type</label>
        <select v-model="form.study_type" class="form-input">
          <option v-for="t in studyTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
        </select>
      </div>
      <div class="form-group">
        <label>Species</label>
        <input v-model="form.species" class="form-input" />
      </div>
      <div class="form-group">
        <label>Dose Route</label>
        <input v-model="form.dose_route" class="form-input" />
      </div>
      <div class="form-group">
        <label>Dose Levels (mg/kg, comma-separated)</label>
        <input v-model="form.dose_levels" class="form-input" placeholder="10, 30, 100" />
      </div>
      <div class="form-group">
        <label>Duration (days)</label>
        <input v-model="form.duration_days" type="number" class="form-input" />
      </div>
    </div>
    <div class="form-group">
      <label>Objective</label>
      <textarea v-model="form.objective" class="form-input" rows="2" />
    </div>
    <div style="display:flex;gap:8px">
      <button class="btn btn-primary" :disabled="!form.objective" @click="submit">Create</button>
      <button class="btn btn-secondary" @click="emit('cancel')">Cancel</button>
    </div>
  </div>
</template>
