<template>
  <div class="timeline">
    <div class="timeline-header">
      <h3>AI-Driven Plan</h3>
      <div class="header-actions">
        <button
          v-if="plan && !planStore.isStreaming"
          class="btn btn-generate"
          @click="plan.step_count ? showConfirm = true : generatePlan()"
        >{{ plan.step_count ? 'Regenerate Plan' : 'Generate Plan' }}</button>
        <span v-if="planStore.isStreaming" class="streaming-indicator">
          {{ planStore.generatingTotal
              ? `Generating step ${planStore.generatingStep} of ${planStore.generatingTotal}…`
              : 'Generating…' }}
        </span>
      </div>
    </div>

    <div v-if="!plan" class="empty-state">
      <p>No AI-Driven Plan yet.</p>
      <button class="btn btn-primary" @click="$emit('create-plan')">Create AI-Driven Plan</button>
    </div>

    <!-- Regenerate confirmation modal -->
    <div v-if="showConfirm" class="confirm-overlay" @click.self="showConfirm = false">
      <div class="confirm-modal">
        <div class="confirm-icon">⚠</div>
        <h4>Regenerate Plan?</h4>
        <p>This will delete all existing steps and recommendations and generate the plan from scratch. This cannot be undone.</p>
        <div class="confirm-actions">
          <button class="btn btn-danger" @click="confirmRegenerate">Yes, Regenerate</button>
          <button class="btn btn-cancel" @click="showConfirm = false">Cancel</button>
        </div>
      </div>
    </div>

    <div v-if="plan" class="steps-list">
      <AIPlanStepCard
        v-for="step in activeSteps"
        :key="step.id"
        :step="step"
        :initial-expanded="step.status === 'in_progress' || step.status === 'awaiting_approval'"
        @approve="handleApprove"
        @reject="handleReject"
        @skip="handleSkip"
        @recommend="handleRecommend"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useAIPlanStore } from '@/stores/aiPlan'
import AIPlanStepCard from './AIPlanStepCard.vue'

const props = defineProps({
  projectId: { type: Number, required: true },
})

const emit = defineEmits(['create-plan'])
const planStore = useAIPlanStore()

const plan = computed(() => planStore.plan)
const activeSteps = computed(() => planStore.activeSteps)
const showConfirm = ref(false)


onMounted(async () => {
  await planStore.fetchPlan(props.projectId)
})

async function generatePlan() {
  if (!plan.value) return
  await planStore.streamGenerate(plan.value.id)
}

async function confirmRegenerate() {
  showConfirm.value = false
  await generatePlan()
}

async function handleApprove(stepId) {
  await planStore.approveStep(stepId)
}

async function handleReject(stepId, feedback) {
  await planStore.rejectStep(stepId, feedback)
}

async function handleSkip(stepId) {
  await planStore.skipStep(stepId)
}

async function handleRecommend(stepId) {
  await planStore.streamRecommend(stepId)
}
</script>

<style scoped>
.timeline { display: flex; flex-direction: column; gap: 16px; }
.timeline-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.timeline-header h3 { margin: 0; font-size: 16px; font-weight: 700; }
.header-actions { display: flex; align-items: center; gap: 10px; }
.steps-list { display: flex; flex-direction: column; gap: 10px; }
.empty-state { text-align: center; padding: 32px; color: #6b7280; }

.btn {
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: none;
}
.btn-generate { background: #3b82f6; color: #fff; }
.btn-primary { background: #3b82f6; color: #fff; }

.streaming-indicator {
  font-size: 13px;
  color: #3b82f6;
  font-weight: 600;
  animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

.confirm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}
.confirm-modal {
  background: #fff;
  border-radius: 12px;
  padding: 28px 32px;
  width: 420px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}
.confirm-icon { font-size: 32px; }
.confirm-modal h4 { margin: 0; font-size: 17px; }
.confirm-modal p { margin: 0; font-size: 13px; color: #6b7280; line-height: 1.6; }
.confirm-actions { display: flex; gap: 10px; margin-top: 4px; }
.btn-danger { background: #ef4444; color: #fff; border: none; }
.btn-cancel { background: #fff; color: #374151; border: 1px solid #d1d5db; }

</style>
