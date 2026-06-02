<script setup>
defineProps({
  oos: { type: Boolean, default: false },
  oot: { type: Boolean, default: false },
})
</script>

<template>
  <span>
    <span v-if="oos" class="badge badge-danger" style="margin-right:4px">OOS</span>
    <span v-if="oot" class="badge badge-warning">OOT</span>
  </span>
</template>
