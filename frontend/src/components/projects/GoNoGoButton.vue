<script setup>
import { ref } from 'vue'

const props = defineProps({
  phaseId: { type: [Number, String], required: true },
})

const emit = defineEmits(['decision'])
const rationale = ref('')
const saving = ref(false)
const show = ref(false)
const pendingDecision = ref(null)

function prompt(decision) {
  pendingDecision.value = decision
  show.value = true
}

async function confirm() {
  saving.value = true
  try {
    emit('decision', { decision: pendingDecision.value, rationale: rationale.value })
    show.value = false
    rationale.value = ''
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div>
    <div style="display:flex;gap:8px">
      <button class="btn btn-primary" @click="prompt('go')">Go</button>
      <button class="btn btn-danger" @click="prompt('no_go')">No-Go</button>
    </div>
    <div v-if="show" class="card mt-3" style="border:2px solid #6366f1">
      <h4 style="font-size:14px">Confirm {{ pendingDecision === 'go' ? 'Go' : 'No-Go' }} Decision</h4>
      <div class="form-group">
        <label>Rationale</label>
        <textarea v-model="rationale" class="form-input" rows="2" placeholder="Basis for decision..." />
      </div>
      <div style="display:flex;gap:8px">
        <button :class="`btn ${pendingDecision === 'go' ? 'btn-primary' : 'btn-danger'}`" :disabled="saving" @click="confirm">
          {{ saving ? 'Saving...' : 'Confirm' }}
        </button>
        <button class="btn btn-secondary" @click="show = false">Cancel</button>
      </div>
    </div>
  </div>
</template>
