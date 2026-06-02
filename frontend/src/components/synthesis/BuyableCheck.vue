<script setup>
defineProps({
  buyable: { type: Boolean, default: null },
  costTier: { type: String, default: null },
  vendor: { type: String, default: null },
})
</script>

<template>
  <span>
    <span v-if="buyable === true" class="badge badge-success">Buyable</span>
    <span v-else-if="buyable === false" class="badge badge-danger">Not Buyable</span>
    <span v-else class="badge badge-warning">Unknown</span>
    <span v-if="costTier" class="text-muted" style="font-size:11px;margin-left:4px">${{ costTier }}</span>
    <span v-if="vendor" class="text-muted" style="font-size:11px;margin-left:4px">· {{ vendor }}</span>
  </span>
</template>
