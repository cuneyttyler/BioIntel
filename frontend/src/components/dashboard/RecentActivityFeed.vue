<script setup>
defineProps({ activities: { type: Array, default: () => [] } })

const typeIcons = {
  formulation: '🧪',
  synthesis: '⚗️',
  analytical: '📊',
  stability: '🌡️',
}
</script>

<template>
  <div class="card">
    <div class="card-title">Recent Experiments</div>
    <div v-if="!activities.length" class="text-muted text-sm">No recent experiments.</div>
    <div v-else style="display:flex;flex-direction:column;gap:8px">
      <div
        v-for="exp in activities"
        :key="exp.id"
        style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid var(--border)"
      >
        <span style="font-size:20px">{{ typeIcons[exp.experiment_type] || '🔬' }}</span>
        <div style="flex:1;min-width:0">
          <div class="font-bold text-sm" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ exp.title }}</div>
          <div class="text-muted text-sm">{{ exp.experiment_type }}</div>
        </div>
        <span :class="['badge', `badge-${exp.status}`]">{{ exp.status }}</span>
      </div>
    </div>
  </div>
</template>
