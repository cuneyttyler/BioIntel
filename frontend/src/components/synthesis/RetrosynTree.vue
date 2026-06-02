<script setup>
import SynthesisTreeNode from './SynthesisTreeNode.vue'

defineProps({
  tree: { type: Object, default: null },
})
</script>

<template>
  <div>
    <div v-if="!tree" class="text-muted" style="font-size:13px">No retrosynthesis tree available.</div>
    <SynthesisTreeNode v-else :node="tree" :depth="0" />
  </div>
</template>
