<template>
  <div class="biologics-page">
    <div class="page-header">
      <h1>Upstream Bioprocessing</h1>
      <button class="btn btn-primary" @click="showForm = true">+ New Record</button>
    </div>

    <div v-if="items.length === 0 && !loading" class="empty-state">No bioprocessing records yet.</div>

    <div class="cards">
      <div v-for="item in items" :key="item.id" class="card">
        <div class="card-header">
          <span class="badge">{{ item.bioreactor_type }}</span>
          <span v-if="item.working_volume_l" class="meta">{{ item.working_volume_l }}L</span>
          <span class="badge status">{{ item.status }}</span>
        </div>
        <div class="card-body">
          <div class="cpp-grid">
            <div v-if="item.cpp_ph_target"><span class="cpp-label">pH</span><span>{{ item.cpp_ph_target }} {{ item.cpp_ph_range ? `(${item.cpp_ph_range})` : '' }}</span></div>
            <div v-if="item.cpp_do_target_pct"><span class="cpp-label">DO</span><span>{{ item.cpp_do_target_pct }}%</span></div>
            <div v-if="item.cpp_temperature_c"><span class="cpp-label">Temp</span><span>{{ item.cpp_temperature_c }}°C</span></div>
            <div v-if="item.cpp_agitation_rpm"><span class="cpp-label">Agitation</span><span>{{ item.cpp_agitation_rpm }} RPM</span></div>
          </div>
          <div v-if="item.cqa_titer_target"><strong>Titer Target:</strong> {{ item.cqa_titer_target }}</div>
          <div v-if="item.notes" class="notes">{{ item.notes }}</div>
        </div>
        <div class="card-actions">
          <button class="btn btn-sm" @click="deleteItem(item.id)">Delete</button>
        </div>
      </div>
    </div>

    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal">
        <h3>Upstream Bioprocessing</h3>
        <div class="form-grid">
          <div class="form-group">
            <label>Bioreactor Type</label>
            <select v-model="form.bioreactor_type">
              <option value="stirred_tank">Stirred-Tank</option>
              <option value="wave">Wave/Rocking</option>
              <option value="hollow_fiber">Hollow Fiber</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div class="form-group">
            <label>Working Volume (L)</label>
            <input v-model.number="form.working_volume_l" type="number" step="0.1" />
          </div>
          <div class="form-group">
            <label>pH Target</label>
            <input v-model.number="form.cpp_ph_target" type="number" step="0.1" />
          </div>
          <div class="form-group">
            <label>pH Range</label>
            <input v-model="form.cpp_ph_range" placeholder="e.g. 6.8–7.2" />
          </div>
          <div class="form-group">
            <label>DO Target (%)</label>
            <input v-model.number="form.cpp_do_target_pct" type="number" />
          </div>
          <div class="form-group">
            <label>Temperature (°C)</label>
            <input v-model.number="form.cpp_temperature_c" type="number" step="0.1" />
          </div>
          <div class="form-group">
            <label>Agitation (RPM)</label>
            <input v-model.number="form.cpp_agitation_rpm" type="number" />
          </div>
          <div class="form-group">
            <label>Titer Target</label>
            <input v-model="form.cqa_titer_target" placeholder="e.g. ≥2 g/L" />
          </div>
          <div class="form-group full">
            <label>Media / Feed Strategy</label>
            <textarea v-model="form.media_composition" rows="2" />
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
  bioreactor_type: 'stirred_tank', working_volume_l: null,
  cpp_ph_target: null, cpp_ph_range: '', cpp_do_target_pct: null,
  cpp_temperature_c: null, cpp_agitation_rpm: null,
  cqa_titer_target: '', media_composition: '', notes: '', status: 'planned',
})

onMounted(async () => {
  loading.value = true
  items.value = await biologicsApi.bioprocessing.list(projectId.value)
  loading.value = false
})

async function save() {
  const item = await biologicsApi.bioprocessing.create(projectId.value, form.value)
  items.value.unshift(item)
  showForm.value = false
}

async function deleteItem(id) {
  if (!confirm('Delete?')) return
  await biologicsApi.bioprocessing.delete(id)
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
.meta { font-size: 13px; color: #374151; }
.badge { font-size: 11px; padding: 2px 8px; border-radius: 8px; background: #eff6ff; color: #1d4ed8; font-weight: 600; }
.badge.status { background: #d1fae5; color: #065f46; }
.card-body { font-size: 13px; display: flex; flex-direction: column; gap: 6px; }
.cpp-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin-bottom: 6px; }
.cpp-label { font-size: 10px; font-weight: 700; color: #6b7280; display: block; }
.notes { color: #6b7280; margin-top: 4px; }
.card-actions { display: flex; justify-content: flex-end; margin-top: 10px; }
.btn { padding: 7px 16px; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; border: 1px solid transparent; }
.btn-primary { background: #3b82f6; color: #fff; }
.btn-cancel { background: #fff; color: #374151; border-color: #d1d5db; }
.btn-sm { padding: 4px 10px; font-size: 12px; background: #fff; color: #ef4444; border-color: #fee2e2; }
.empty-state { text-align: center; color: #6b7280; padding: 32px; border: 1px dashed #e5e7eb; border-radius: 10px; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.35); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: #fff; border-radius: 12px; padding: 24px; width: 560px; display: flex; flex-direction: column; gap: 16px; box-shadow: 0 20px 60px rgba(0,0,0,0.2); max-height: 90vh; overflow-y: auto; }
.modal h3 { margin: 0; font-size: 16px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-group { display: flex; flex-direction: column; gap: 4px; }
.form-group.full { grid-column: 1 / -1; }
.form-group label { font-size: 12px; font-weight: 600; color: #374151; }
.form-group input, .form-group select, .form-group textarea { padding: 7px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; font-family: inherit; }
.modal-actions { display: flex; gap: 10px; justify-content: flex-end; }
</style>
