<template>
  <div class="biologics-page">
    <div class="page-header">
      <h1>Cell Line Development</h1>
      <button class="btn btn-primary" @click="showForm = true">+ New Record</button>
    </div>

    <div v-if="items.length === 0 && !loading" class="empty-state">No cell line development records yet.</div>

    <div class="cards">
      <div v-for="item in items" :key="item.id" class="card">
        <div class="card-header">
          <span class="field-label">Expression System</span>
          <span class="badge">{{ item.expression_system }}</span>
          <span class="badge status">{{ item.status }}</span>
        </div>
        <div class="card-body">
          <div v-if="item.transfection_strategy"><strong>Transfection:</strong> {{ item.transfection_strategy }}</div>
          <div v-if="item.selection_marker"><strong>Marker:</strong> {{ item.selection_marker }}</div>
          <div v-if="item.target_expression_level"><strong>Target Titer:</strong> {{ item.target_expression_level }}</div>
          <div v-if="item.notes" class="notes">{{ item.notes }}</div>
        </div>
        <div class="card-actions">
          <button class="btn btn-sm" @click="deleteItem(item.id)">Delete</button>
        </div>
      </div>
    </div>

    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal">
        <h3>Cell Line Development</h3>
        <div class="form-grid">
          <div class="form-group">
            <label>Expression System</label>
            <select v-model="form.expression_system">
              <option value="cho">CHO</option>
              <option value="hek293">HEK293</option>
              <option value="ecoli">E. coli</option>
              <option value="yeast">Yeast (P. pastoris)</option>
              <option value="baculovirus">Baculovirus/Sf9</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div class="form-group">
            <label>Status</label>
            <select v-model="form.status">
              <option value="planned">Planned</option>
              <option value="in_progress">In Progress</option>
              <option value="complete">Complete</option>
            </select>
          </div>
          <div class="form-group full">
            <label>Transfection Strategy</label>
            <textarea v-model="form.transfection_strategy" rows="2" />
          </div>
          <div class="form-group">
            <label>Selection Marker</label>
            <input v-model="form.selection_marker" />
          </div>
          <div class="form-group">
            <label>Target Expression Level</label>
            <input v-model="form.target_expression_level" placeholder="e.g. ≥1 g/L" />
          </div>
          <div class="form-group full">
            <label>Notes</label>
            <textarea v-model="form.notes" rows="2" />
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
const form = ref({ expression_system: 'cho', status: 'planned', transfection_strategy: '', selection_marker: '', target_expression_level: '', notes: '' })

onMounted(async () => {
  loading.value = true
  items.value = await biologicsApi.cellLine.list(projectId.value)
  loading.value = false
})

async function save() {
  const item = await biologicsApi.cellLine.create(projectId.value, form.value)
  items.value.unshift(item)
  showForm.value = false
  form.value = { expression_system: 'cho', status: 'planned', transfection_strategy: '', selection_marker: '', target_expression_level: '', notes: '' }
}

async function deleteItem(id) {
  if (!confirm('Delete this record?')) return
  await biologicsApi.cellLine.delete(id)
  items.value = items.value.filter((i) => i.id !== id)
}
</script>

<style scoped>
.biologics-page { padding: 24px; display: flex; flex-direction: column; gap: 20px; }
.page-header { display: flex; align-items: center; justify-content: space-between; }
.page-header h1 { margin: 0; font-size: 22px; }
.cards { display: flex; flex-direction: column; gap: 12px; }
.card { border: 1px solid #e5e7eb; border-radius: 10px; background: #fff; padding: 16px; }
.card-header { display: flex; gap: 8px; align-items: center; margin-bottom: 10px; }
.field-label { font-size: 12px; font-weight: 600; color: #6b7280; margin-right: 4px; }
.badge { font-size: 11px; padding: 2px 8px; border-radius: 8px; background: #eff6ff; color: #1d4ed8; font-weight: 600; }
.badge.status { background: #d1fae5; color: #065f46; }
.card-body { font-size: 13px; display: flex; flex-direction: column; gap: 4px; color: #374151; }
.notes { color: #6b7280; margin-top: 4px; }
.card-actions { display: flex; justify-content: flex-end; margin-top: 10px; }

.btn { padding: 7px 16px; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; border: 1px solid transparent; }
.btn-primary { background: #3b82f6; color: #fff; }
.btn-cancel { background: #fff; color: #374151; border-color: #d1d5db; }
.btn-sm { padding: 4px 10px; font-size: 12px; background: #fff; color: #ef4444; border-color: #fee2e2; }
.empty-state { text-align: center; color: #6b7280; padding: 32px; border: 1px dashed #e5e7eb; border-radius: 10px; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.35); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: #fff; border-radius: 12px; padding: 24px; width: 520px; display: flex; flex-direction: column; gap: 16px; box-shadow: 0 20px 60px rgba(0,0,0,0.2); }
.modal h3 { margin: 0; font-size: 16px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-group { display: flex; flex-direction: column; gap: 4px; }
.form-group.full { grid-column: 1 / -1; }
.form-group label { font-size: 12px; font-weight: 600; color: #374151; }
.form-group input, .form-group select, .form-group textarea {
  padding: 7px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; font-family: inherit;
}
.modal-actions { display: flex; gap: 10px; justify-content: flex-end; }
</style>
