<script setup>
defineProps({ size: { type: String, default: 'md' } })
</script>

<template>
  <div :class="['spinner', size === 'sm' ? 'spinner-sm' : size === 'lg' ? 'spinner-lg' : '']" />
</template>
