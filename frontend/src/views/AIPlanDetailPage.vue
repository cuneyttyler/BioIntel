<template>
  <div class="ai-plan-page">
    <div class="page-header">
      <div class="header-left">
        <router-link :to="`/projects/${projectId}`" class="back-link">← Project</router-link>
        <h1>AI-Driven Plan</h1>
      </div>
      <div v-if="planStore.plan" class="plan-meta">
        <span class="badge" :class="`plan-status-${planStore.plan.status}`">{{ planStore.plan.status }}</span>
        <span class="badge mol">{{ planStore.plan.molecule_type }}</span>
        <span class="step-counter" v-if="planStore.completedSteps.length">
          {{ planStore.completedSteps.length }} / {{ planStore.activeSteps.length }} steps completed
        </span>
      </div>
    </div>

    <AIPlanTimeline :project-id="projectId" @create-plan="showCreateForm = true" />

    <!-- Create plan modal -->
    <div v-if="showCreateForm" class="modal-overlay" @click.self="showCreateForm = false">
      <div class="modal">
        <h3>Create AI-Driven Plan</h3>
        <div class="form-group">
          <label>Disease / Target Description</label>
          <textarea v-model="createForm.disease_description" rows="3"
            placeholder="Describe the disease or therapeutic target…" />
        </div>
        <div class="form-group">
          <label>Molecule Type</label>
          <select v-model="createForm.molecule_type">
            <option value="small_molecule">Small Molecule</option>
            <option value="biologic">Biologic</option>
            <option value="undetermined">Undetermined</option>
          </select>
        </div>
        <div class="modal-actions">
          <button class="btn btn-primary" :disabled="isCreating" @click="createPlan">
            {{ isCreating ? 'Creating…' : 'Create Plan' }}
          </button>
          <button class="btn btn-cancel" @click="showCreateForm = false">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAIPlanStore } from '@/stores/aiPlan'
import AIPlanTimeline from '@/components/ai-plan/AIPlanTimeline.vue'

const route = useRoute()
const planStore = useAIPlanStore()
const projectId = computed(() => parseInt(route.params.id))
const showCreateForm = ref(false)
const isCreating = ref(false)
const createForm = ref({ disease_description: '', molecule_type: 'small_molecule' })

async function createPlan() {
  isCreating.value = true
  try {
    await planStore.createPlan(projectId.value, createForm.value)
    showCreateForm.value = false
  } finally {
    isCreating.value = false
  }
}
</script>

<style scoped>
.ai-plan-page { padding: 24px; display: flex; flex-direction: column; gap: 20px; }
.page-header { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; }
.header-left { display: flex; align-items: center; gap: 16px; }
.back-link { color: #3b82f6; text-decoration: none; font-size: 13px; }
.page-header h1 { margin: 0; font-size: 22px; }
.plan-meta { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.badge {
  font-size: 11px; padding: 3px 10px; border-radius: 10px;
  font-weight: 600; background: #f3f4f6; color: #374151;
}
.plan-status-active { background: #d1fae5; color: #065f46; }
.plan-status-draft { background: #fef3c7; color: #92400e; }
.plan-status-completed { background: #a7f3d0; color: #065f46; }
.badge.mol { background: #eff6ff; color: #1d4ed8; }
.step-counter { font-size: 12px; color: #6b7280; }

.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.35);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.modal {
  background: #fff; border-radius: 12px; padding: 24px;
  width: 460px; display: flex; flex-direction: column; gap: 16px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.2);
}
.modal h3 { margin: 0; font-size: 16px; }
.form-group { display: flex; flex-direction: column; gap: 4px; }
.form-group label { font-size: 12px; font-weight: 600; color: #374151; }
.form-group textarea, .form-group select {
  padding: 8px 10px; border: 1px solid #d1d5db;
  border-radius: 6px; font-size: 13px; font-family: inherit;
}
.modal-actions { display: flex; gap: 10px; justify-content: flex-end; }
.btn { padding: 8px 18px; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; border: 1px solid transparent; }
.btn-primary { background: #3b82f6; color: #fff; }
.btn-cancel { background: #fff; color: #374151; border-color: #d1d5db; }
.btn:disabled { opacity: 0.5; }
</style>
