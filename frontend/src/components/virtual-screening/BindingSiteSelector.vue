<script setup>
import { ref } from 'vue'

const props = defineProps({
  pdbId: { type: String, default: null },
})

const emit = defineEmits(['update:bindingSite'])

const site = ref({ center_x: '', center_y: '', center_z: '', size_x: 20, size_y: 20, size_z: 20 })

function apply() {
  emit('update:bindingSite', {
    center_x: parseFloat(site.value.center_x),
    center_y: parseFloat(site.value.center_y),
    center_z: parseFloat(site.value.center_z),
    size_x: parseFloat(site.value.size_x),
    size_y: parseFloat(site.value.size_y),
    size_z: parseFloat(site.value.size_z),
  })
}
</script>

<template>
  <div class="card">
    <h4 class="card-title" style="font-size:14px">Docking Box — {{ pdbId || 'No PDB' }}</h4>
    <div class="grid-3" style="gap:8px">
      <div class="form-group">
        <label>Center X</label>
        <input v-model="site.center_x" type="number" class="form-input" />
      </div>
      <div class="form-group">
        <label>Center Y</label>
        <input v-model="site.center_y" type="number" class="form-input" />
      </div>
      <div class="form-group">
        <label>Center Z</label>
        <input v-model="site.center_z" type="number" class="form-input" />
      </div>
      <div class="form-group">
        <label>Box X (Å)</label>
        <input v-model="site.size_x" type="number" class="form-input" />
      </div>
      <div class="form-group">
        <label>Box Y (Å)</label>
        <input v-model="site.size_y" type="number" class="form-input" />
      </div>
      <div class="form-group">
        <label>Box Z (Å)</label>
        <input v-model="site.size_z" type="number" class="form-input" />
      </div>
    </div>
    <button class="btn btn-secondary" @click="apply">Apply Box</button>
  </div>
</template>
