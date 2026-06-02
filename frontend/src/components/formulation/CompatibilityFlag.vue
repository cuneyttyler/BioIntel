<script setup>
defineProps({
  flag: { type: Object, required: true },
})
</script>

<template>
  <div class="list-item" :style="{ borderLeft: `3px solid ${flag.severity === 'critical' ? '#ef4444' : '#f59e0b'}`, paddingLeft: '10px' }">
    <div style="display:flex;align-items:center;gap:8px">
      <strong style="font-size:13px">{{ flag.component_a }} × {{ flag.component_b }}</strong>
      <span :class="`badge badge-${flag.severity === 'critical' ? 'danger' : 'warning'}`">{{ flag.severity }}</span>
    </div>
    <p v-if="flag.evidence" class="text-muted" style="font-size:12px;margin:4px 0 0">{{ flag.evidence }}</p>
  </div>
</template>
