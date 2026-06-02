<script setup>
defineProps({
  step: { type: Object, required: true },
  stepNumber: { type: Number, default: null },
})
</script>

<template>
  <div class="card mb-2" style="border-left:3px solid #6366f1">
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
      <span v-if="stepNumber" style="background:#6366f1;color:#fff;border-radius:50%;width:22px;height:22px;display:flex;align-items:center;justify-content:center;font-size:12px;flex-shrink:0">{{ stepNumber }}</span>
      <strong>{{ step.reaction_type || step.step_name || 'Step' }}</strong>
      <span v-if="step.yield_pct" class="badge badge-info" style="margin-left:auto">{{ step.yield_pct }}% yield</span>
    </div>
    <div v-if="step.reagents?.length || step.solvents?.length" style="font-size:12px;color:#6b7280;margin-bottom:4px">
      <span v-if="step.reagents?.length">Reagents: {{ step.reagents.join(', ') }}</span>
      <span v-if="step.reagents?.length && step.solvents?.length"> · </span>
      <span v-if="step.solvents?.length">Solvents: {{ step.solvents.join(', ') }}</span>
    </div>
    <div v-if="step.temperature || step.reaction_time" style="font-size:12px;color:#6b7280">
      <span v-if="step.temperature">{{ step.temperature }}</span>
      <span v-if="step.temperature && step.reaction_time"> · </span>
      <span v-if="step.reaction_time">{{ step.reaction_time }}</span>
    </div>
    <p v-if="step.notes" class="text-muted" style="font-size:12px;margin:4px 0 0">{{ step.notes }}</p>
  </div>
</template>
