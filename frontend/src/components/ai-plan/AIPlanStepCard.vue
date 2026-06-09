<template>
  <div class="step-card" :class="[`step-status-${step.status}`, { active: isActive }]">
    <div class="step-header" @click="toggleExpanded">
      <div class="step-meta">
        <span class="step-num">{{ step.step_number }}</span>
        <span class="phase-badge">{{ phaseName }}</span>
      </div>
      <div class="step-title">{{ step.title }}</div>
      <PlanStepStatusBadge :status="step.status" />
      <span class="expand-icon">{{ expanded ? '▲' : '▼' }}</span>
    </div>

    <div v-if="expanded" class="step-body">
      <div v-if="step.description" class="step-description">{{ step.description }}</div>

      <!-- Streaming recommendation -->
      <div v-if="isStreaming && planStore.streamingStepId === step.id" class="streaming-box">
        <div class="streaming-label">AI is generating recommendation…</div>
        <div class="streaming-text" v-html="renderMarkdown(planStore.streamingText)" />
        <span class="cursor" />
      </div>

      <!-- Completed recommendation -->
      <div v-else-if="step.ai_reasoning || step.ai_recommendation" class="recommendation-box">
        <div class="rec-header">AI Recommendation</div>
        <div class="rec-content" v-html="renderMarkdown(step.ai_reasoning)" />

        <div v-if="step.rag_sources?.length" class="rag-sources">
          <div class="rag-label">Sources</div>
          <div v-for="src in step.rag_sources" :key="src" class="rag-src">{{ src }}</div>
        </div>
      </div>

      <!-- Suggested actions -->
      <div v-if="pendingSuggestedActions.length" class="suggested-actions">
        <div class="suggested-label">Apply to project</div>
        <div class="suggested-list">
          <div
            v-for="action in pendingSuggestedActions"
            :key="action.id"
            class="suggested-action"
          >
            <span class="suggested-action-label">{{ action.label }}</span>
            <button
              class="btn btn-apply"
              :disabled="applyingAction === action.id"
              @click="applyAction(action)"
            >{{ applyingAction === action.id ? 'Applying…' : 'Apply' }}</button>
          </div>
        </div>
      </div>

      <!-- Action buttons -->
      <div class="action-row" v-if="!['abandoned', 'skipped', 'completed'].includes(step.status)">
        <button
          v-if="step.status === 'awaiting_approval'"
          class="btn btn-approve"
          @click="$emit('approve', step.id)"
        >Approve &amp; Proceed</button>

        <button
          v-if="['pending', 'in_progress', 'awaiting_approval', 'revision_needed'].includes(step.status)"
          class="btn btn-recommend"
          :disabled="planStore.isStreaming"
          @click="$emit('recommend', step.id)"
        >{{ step.status === 'revision_needed' ? 'Regenerate' : 'Generate Recommendation' }}</button>

        <button
          v-if="['in_progress', 'awaiting_approval'].includes(step.status)"
          class="btn btn-reject"
          @click="showRejectForm = !showRejectForm"
        >Request Revision</button>

        <button
          class="btn btn-discuss"
          @click="showDiscussion = !showDiscussion"
        >{{ showDiscussion ? 'Hide Discussion' : 'Discuss' }}</button>

        <button
          v-if="step.status !== 'pending'"
          class="btn btn-skip"
          @click="$emit('skip', step.id)"
        >Skip</button>
      </div>

      <!-- Reject form -->
      <div v-if="showRejectForm" class="reject-form">
        <textarea v-model="rejectFeedback" placeholder="Describe what needs to change…" rows="2" />
        <button class="btn btn-reject" @click="submitReject">Submit Revision Request</button>
      </div>

      <!-- Discussion panel -->
      <div v-if="showDiscussion" class="discussion-wrapper">
        <AIPlanDiscussionPanel :step-id="step.id" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAIPlanStore } from '@/stores/aiPlan'
import PlanStepStatusBadge from './PlanStepStatusBadge.vue'
import AIPlanDiscussionPanel from './AIPlanDiscussionPanel.vue'

const props = defineProps({
  step: { type: Object, required: true },
  initialExpanded: { type: Boolean, default: false },
})

const emit = defineEmits(['approve', 'reject', 'skip', 'recommend'])

const planStore = useAIPlanStore()
const expanded = ref(props.initialExpanded)
const showDiscussion = ref(false)
const showRejectForm = ref(false)
const rejectFeedback = ref('')

const isActive = computed(() => ['in_progress', 'awaiting_approval', 'revision_needed'].includes(props.step.status))
const isStreaming = computed(() => planStore.isStreaming)

const pendingSuggestedActions = computed(() =>
  (props.step.suggested_actions || []).filter((a) => !a.applied)
)

const applyingAction = ref(null)

async function applyAction(action) {
  applyingAction.value = action.id
  try {
    await planStore.executeAction(props.step.id, action)
  } finally {
    applyingAction.value = null
  }
}


const PHASE_NAMES = {
  discovery: 'Discovery',
  lead_optimization: 'Lead Optimization',
  drug_substance: 'Drug Substance',
  drug_product: 'Drug Product',
  analytical: 'Analytical',
  preclinical: 'Preclinical',
  regulatory: 'Regulatory',
}
const phaseName = computed(() => PHASE_NAMES[props.step.phase] || props.step.phase)

function toggleExpanded() {
  expanded.value = !expanded.value
  if (expanded.value && props.step.id) {
    planStore.fetchDiscussions(props.step.id)
  }
}

function submitReject() {
  emit('reject', props.step.id, rejectFeedback.value)
  showRejectForm.value = false
  rejectFeedback.value = ''
}

function renderMarkdown(text) {
  if (!text) return ''
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\[Source:(.*?)\]/g, '<span class="src-inline">[Source:$1]</span>')
    .replace(/\n/g, '<br>')
}
</script>

<style scoped>
.step-card {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
  transition: box-shadow 0.15s;
}
.step-card.active { border-color: #3b82f6; box-shadow: 0 0 0 2px #bfdbfe; }
.step-card.step-status-in_progress .step-header { border-left: 3px solid #3b82f6; }
.step-card.step-status-awaiting_approval .step-header { border-left: 3px solid #f59e0b; }
.step-card.step-status-completed .step-header { border-left: 3px solid #10b981; }
.step-card.step-status-revision_needed .step-header { border-left: 3px solid #ef4444; }
.step-card.step-status-abandoned { opacity: 0.45; }

.step-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  cursor: pointer;
  user-select: none;
}
.step-header:hover { background: #f9fafb; }
.step-meta { display: flex; gap: 6px; align-items: center; }
.step-num {
  width: 26px; height: 26px;
  background: #f3f4f6;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; color: #374151;
  flex-shrink: 0;
}
.phase-badge {
  font-size: 10px; font-weight: 600;
  color: #6b7280;
  background: #f3f4f6;
  padding: 2px 7px;
  border-radius: 8px;
}
.step-title { flex: 1; font-weight: 600; font-size: 14px; }
.expand-icon { color: #9ca3af; font-size: 10px; }

.step-body { padding: 14px 16px; border-top: 1px solid #f3f4f6; display: flex; flex-direction: column; gap: 14px; }
.step-description { color: #6b7280; font-size: 13px; }

.streaming-box, .recommendation-box {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
  padding: 12px 14px;
}
.streaming-label { font-size: 11px; font-weight: 600; color: #0284c7; margin-bottom: 6px; text-transform: uppercase; }
.streaming-text, .rec-content {
  font-size: 13px;
  line-height: 1.7;
  max-height: 280px;
  overflow-y: auto;
  padding-right: 4px;
}
.rec-header { font-size: 11px; font-weight: 700; color: #0284c7; margin-bottom: 8px; text-transform: uppercase; }
.cursor {
  display: inline-block; width: 2px; height: 1em;
  background: #374151; margin-left: 2px;
  animation: blink 1s step-end infinite;
}
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

.rag-sources { margin-top: 8px; }
.rag-label { font-size: 10px; font-weight: 600; color: #6b7280; margin-bottom: 4px; text-transform: uppercase; }
.rag-src { font-size: 11px; color: #6b7280; }

.suggested-actions {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
  padding: 12px 14px;
}
.suggested-label {
  font-size: 11px;
  font-weight: 700;
  color: #16a34a;
  text-transform: uppercase;
  margin-bottom: 8px;
}
.suggested-list { display: flex; flex-direction: column; gap: 6px; }
.suggested-action {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.suggested-action-label { font-size: 13px; color: #374151; flex: 1; }
.btn-apply {
  background: #16a34a;
  color: #fff;
  border: none;
  padding: 4px 12px;
  border-radius: 5px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
}
.btn-apply:disabled { opacity: 0.6; cursor: not-allowed; }

.action-row { display: flex; flex-wrap: wrap; gap: 8px; }
.btn {
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
}
.btn-approve { background: #10b981; color: #fff; }
.btn-recommend { background: #3b82f6; color: #fff; }
.btn-reject { background: #fff; color: #ef4444; border-color: #ef4444; }
.btn-discuss { background: #fff; color: #374151; border-color: #d1d5db; }
.btn-skip { background: #fff; color: #9ca3af; border-color: #e5e7eb; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.reject-form { display: flex; flex-direction: column; gap: 6px; }
.reject-form textarea {
  padding: 8px; border: 1px solid #d1d5db;
  border-radius: 6px; font-size: 13px;
  resize: vertical; font-family: inherit;
}

.discussion-wrapper {
  height: 320px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px;
  display: flex;
  flex-direction: column;
}
:deep(.src-inline) { color: #2563eb; font-size: 11px; }
</style>
