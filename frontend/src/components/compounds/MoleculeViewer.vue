<script setup>
const props = defineProps({
  compoundId: { type: [Number, String], required: true },
  width: { type: Number, default: 200 },
  height: { type: Number, default: 150 },
})

const src = `/api/compounds/${props.compoundId}/structure/?width=${props.width}&height=${props.height}`
</script>

<template>
  <div class="molecule-viewer">
    <img :src="src" :width="width" :height="height" alt="Structure" style="max-width:100%;border-radius:4px;background:#fff" />
  </div>
</template>
