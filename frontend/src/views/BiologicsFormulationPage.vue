<template>
  <div class="biologics-page">
    <div class="page-header">
      <h1>Biologics Formulation</h1>
      <button class="btn btn-primary" @click="showForm = true">+ New Formulation</button>
    </div>

    <div v-if="items.length === 0 && !loading" class="empty-state">No biologics formulation records yet.</div>

    <div class="cards">
      <div v-for="item in items" :key="item.id" class="card">
        <div class="card-header">
          <span class="badge">{{ item.buffer_system || 'Buffer TBD' }}</span>
          <span v-if="item.ph_target" class="badge">pH {{ item.ph_target }}</span>
          <span v-if="item.container_closure" class="badge">{{ item.container_closure }}</span>
          <span class="badge status">{{ item.status }}</span>
        </div>
        <div class="card-body">
          <div v-if="item.surfactant"><strong>Surfactant:</strong> {{ item.surfactant }} {{ item.surfactant_concentration_pct ? `${item.surfactant_concentration_pct}%` : '' }}</div>
          <div v-if="item.stabilizer"><strong>Stabilizer:</strong> {{ item.stabilizer }} {{ item.stabilizer_concentration_mm ? `${item.stabilizer_concentration_mm} mM` : '' }}</div>
          <div v-if="item.protein_concentration_mgml"><strong>Protein conc.:</strong> {{ item.protein_concentration_mgml }} mg/mL</div>
          <div v-if="item.is_lyophilized" class="badge lyoph">Lyophilized</div>
          <div v-if="item.notes" class="notes">{{ item.notes }}</div>
        </div>
        <div class="card-actions">
          <button class="btn btn-sm" @click="deleteItem(item.id)">Delete</button>
        </div>
      </div>
    </div>

    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal">
        <h3>Biologics Formulation</h3>
        <div class="form-grid">
          <div class="form-group full">
            <label>Buffer System</label>
            <input v-model="form.buffer_system" placeholder="e.g. 20 mM Histidine, 150 mM NaCl" />
          </div>
          <div class="form-group">
            <label>pH Target</label>
            <input v-model.number="form.ph_target" type="number" step="0.1" />
          </div>
          <div class="form-group">
            <label>pH Range</label>
            <input v-model="form.ph_range" placeholder="e.g. 5.8–6.2" />
          </div>
          <div class="form-group">
            <label>Surfactant</label>
            <input v-model="form.surfactant" placeholder="Polysorbate 80" />
          </div>
          <div class="form-group">
            <label>Surfactant Conc. (%)</label>
            <input v-model.number="form.surfactant_concentration_pct" type="number" step="0.001" />
          </div>
          <div class="form-group">
            <label>Stabilizer</label>
            <input v-model="form.stabilizer" placeholder="Sucrose" />
          </div>
          <div class="form-group">
            <label>Stabilizer Conc. (mM)</label>
            <input v-model.number="form.stabilizer_concentration_mm" type="number" />
          </div>
          <div class="form-group">
            <label>Protein Conc. (mg/mL)</label>
            <input v-model.number="form.protein_concentration_mgml" type="number" step="0.1" />
          </div>
          <div class="form-group">
            <label>Container Closure</label>
            <select v-model="form.container_closure">
              <option value="">— Select —</option>
              <option value="vial">Glass Vial</option>
              <option value="pfs">Pre-filled Syringe</option>
              <option value="cartridge">Cartridge</option>
              <option value="bag">Flexible Bag</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div class="form-group">
            <label>Lyophilized</label>
            <select v-model="form.is_lyophilized">
              <option :value="false">No</option>
              <option :value="true">Yes</option>
            </select>
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
const form = ref({
  buffer_system: '', ph_target: null, ph_range: '',
  surfactant: '', surfactant_concentration_pct: null,
  stabilizer: '', stabilizer_concentration_mm: null,
  protein_concentration_mgml: null, container_closure: '',
  is_lyophilized: false, notes: '', status: 'draft',
})

onMounted(async () => {
  loading.value = true
  items.value = await biologicsApi.formulation.list(projectId.value)
  loading.value = false
})

async function save() {
  const item = await biologicsApi.formulation.create(projectId.value, form.value)
  items.value.unshift(item)
  showForm.value = false
}

async function deleteItem(id) {
  if (!confirm('Delete?')) return
  await biologicsApi.formulation.delete(id)
  items.value = items.value.filter((i) => i.id !== id)
}
</script>

<style scoped>
.biologics-page { padding: 24px; display: flex; flex-direction: column; gap: 20px; }
.page-header { display: flex; align-items: center; justify-content: space-between; }
.page-header h1 { margin: 0; font-size: 22px; }
.cards { display: flex; flex-direction: column; gap: 12px; }
.card { border: 1px solid #e5e7eb; border-radius: 10px; background: #fff; padding: 16px; }
.card-header { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-bottom: 10px; }
.badge { font-size: 11px; padding: 2px 8px; border-radius: 8px; background: #eff6ff; color: #1d4ed8; font-weight: 600; }
.badge.status { background: #d1fae5; color: #065f46; }
.badge.lyoph { background: #fef3c7; color: #92400e; }
.card-body { font-size: 13px; display: flex; flex-direction: column; gap: 4px; }
.notes { color: #6b7280; margin-top: 4px; }
.card-actions { display: flex; justify-content: flex-end; margin-top: 10px; }
.btn { padding: 7px 16px; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; border: 1px solid transparent; }
.btn-primary { background: #3b82f6; color: #fff; }
.btn-cancel { background: #fff; color: #374151; border-color: #d1d5db; }
.btn-sm { padding: 4px 10px; font-size: 12px; background: #fff; color: #ef4444; border-color: #fee2e2; }
.empty-state { text-align: center; color: #6b7280; padding: 32px; border: 1px dashed #e5e7eb; border-radius: 10px; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.35); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: #fff; border-radius: 12px; padding: 24px; width: 540px; max-height: 90vh; overflow-y: auto; display: flex; flex-direction: column; gap: 16px; box-shadow: 0 20px 60px rgba(0,0,0,0.2); }
.modal h3 { margin: 0; font-size: 16px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-group { display: flex; flex-direction: column; gap: 4px; }
.form-group.full { grid-column: 1 / -1; }
.form-group label { font-size: 12px; font-weight: 600; color: #374151; }
.form-group input, .form-group select, .form-group textarea { padding: 7px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; font-family: inherit; }
.modal-actions { display: flex; gap: 10px; justify-content: flex-end; }
</style>
