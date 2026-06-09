<template>
  <div class="biologics-page">
    <div class="page-header">
      <h1>Biologics Analytics</h1>
      <button class="btn btn-primary" @click="showForm = true">+ Add Method</button>
    </div>

    <div v-if="items.length === 0 && !loading" class="empty-state">No characterization methods defined yet.</div>

    <div class="cards">
      <div v-for="item in items" :key="item.id" class="card">
        <div class="card-header">
          <span class="badge type">{{ item.method_type }}</span>
          <span class="method-name">{{ item.method_name }}</span>
          <span class="badge" :class="`val-${item.validation_status}`">{{ item.validation_status }}</span>
        </div>
        <div class="card-body">
          <div v-if="item.analyte"><strong>Analyte:</strong> {{ item.analyte }}</div>
          <div v-if="item.instrument"><strong>Instrument:</strong> {{ item.instrument }}</div>
        </div>
        <div class="card-actions">
          <button class="btn btn-sm" @click="deleteItem(item.id)">Delete</button>
        </div>
      </div>
    </div>

    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal">
        <h3>Add Characterization Method</h3>
        <div class="form-grid">
          <div class="form-group">
            <label>Method Type</label>
            <select v-model="form.method_type">
              <option value="sec_hplc">SEC-HPLC (Aggregation)</option>
              <option value="icief">icIEF (Charge Variants)</option>
              <option value="glycan">Glycan Analysis</option>
              <option value="hcp_elisa">HCP ELISA</option>
              <option value="residual_dna">Residual DNA</option>
              <option value="bioassay">Bioassay / Cell-Based</option>
              <option value="spr">SPR (Binding Kinetics)</option>
              <option value="mass_spec">Mass Spectrometry</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div class="form-group">
            <label>Validation Status</label>
            <select v-model="form.validation_status">
              <option value="not_started">Not Started</option>
              <option value="in_progress">In Progress</option>
              <option value="validated">Validated</option>
              <option value="transferred">Transferred</option>
            </select>
          </div>
          <div class="form-group full">
            <label>Method Name</label>
            <input v-model="form.method_name" />
          </div>
          <div class="form-group">
            <label>Analyte</label>
            <input v-model="form.analyte" />
          </div>
          <div class="form-group">
            <label>Instrument</label>
            <input v-model="form.instrument" />
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn btn-primary" @click="save">Save</button>
          <button class="btn btn-cancel" @click="showForm = false">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { biologics as biologicsApi } from '@/services/api'

const route = useRoute()
const projectId = computed(() => parseInt(route.params.id))
const items = ref([])
const loading = ref(false)
const showForm = ref(false)
const form = ref({ method_type: 'sec_hplc', method_name: '', analyte: '', instrument: '', validation_status: 'not_started' })

onMounted(async () => {
  loading.value = true
  items.value = await biologicsApi.analytics.list(projectId.value)
  loading.value = false
})

async function save() {
  const item = await biologicsApi.analytics.create(projectId.value, form.value)
  items.value.unshift(item)
  showForm.value = false
  form.value = { method_type: 'sec_hplc', method_name: '', analyte: '', instrument: '', validation_status: 'not_started' }
}

async function deleteItem(id) {
  if (!confirm('Delete?')) return
  await biologicsApi.analytics.delete(id)
  items.value = items.value.filter((i) => i.id !== id)
}
</script>

<style scoped>
.biologics-page { padding: 24px; display: flex; flex-direction: column; gap: 20px; }
.page-header { display: flex; align-items: center; justify-content: space-between; }
.page-header h1 { margin: 0; font-size: 22px; }
.cards { display: flex; flex-direction: column; gap: 10px; }
.card { border: 1px solid #e5e7eb; border-radius: 10px; background: #fff; padding: 14px 16px; }
.card-header { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
.method-name { font-weight: 600; font-size: 14px; flex: 1; }
.badge { font-size: 11px; padding: 2px 8px; border-radius: 8px; font-weight: 600; background: #f3f4f6; color: #374151; }
.badge.type { background: #eff6ff; color: #1d4ed8; }
.val-validated { background: #d1fae5; color: #065f46; }
.val-in_progress { background: #fef3c7; color: #92400e; }
.val-transferred { background: #e0e7ff; color: #3730a3; }
.card-body { font-size: 13px; display: flex; flex-direction: column; gap: 4px; }
.card-actions { display: flex; justify-content: flex-end; margin-top: 8px; }
.btn { padding: 7px 16px; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; border: 1px solid transparent; }
.btn-primary { background: #3b82f6; color: #fff; }
.btn-cancel { background: #fff; color: #374151; border-color: #d1d5db; }
.btn-sm { padding: 4px 10px; font-size: 12px; background: #fff; color: #ef4444; border-color: #fee2e2; }
.empty-state { text-align: center; color: #6b7280; padding: 32px; border: 1px dashed #e5e7eb; border-radius: 10px; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.35); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: #fff; border-radius: 12px; padding: 24px; width: 500px; display: flex; flex-direction: column; gap: 16px; box-shadow: 0 20px 60px rgba(0,0,0,0.2); }
.modal h3 { margin: 0; font-size: 16px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-group { display: flex; flex-direction: column; gap: 4px; }
.form-group.full { grid-column: 1 / -1; }
.form-group label { font-size: 12px; font-weight: 600; color: #374151; }
.form-group input, .form-group select { padding: 7px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; font-family: inherit; }
.modal-actions { display: flex; gap: 10px; justify-content: flex-end; }
</style>
