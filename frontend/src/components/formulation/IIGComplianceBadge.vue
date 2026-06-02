<script setup>
defineProps({
  concentration: { type: Number, default: null },
  iigLimit: { type: Number, default: null },
  unit: { type: String, default: '' },
})
</script>

<template>
  <span v-if="concentration != null && iigLimit != null">
    <span :class="`badge badge-${concentration <= iigLimit ? 'success' : 'danger'}`">
      {{ concentration <= iigLimit ? 'IIG OK' : 'Exceeds IIG' }}
    </span>
    <span class="text-muted" style="font-size:11px;margin-left:4px">
      {{ concentration }} / {{ iigLimit }} {{ unit }}
    </span>
  </span>
  <span v-else class="text-muted" style="font-size:12px">No IIG limit</span>
</template>
