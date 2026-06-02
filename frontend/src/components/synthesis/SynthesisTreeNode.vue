<script setup>
import { ref } from 'vue'

const props = defineProps({
  node: { type: Object, required: true },
  depth: { type: Number, default: 0 },
})

const expanded = ref(true)
</script>

<template>
  <div :style="{ paddingLeft: depth * 20 + 'px' }">
    <div
      class="list-item"
      style="cursor:pointer;display:flex;align-items:center;gap:8px"
      @click="expanded = !expanded"
    >
      <span v-if="node.children?.length" style="font-size:12px;color:#9ca3af">{{ expanded ? '▼' : '▶' }}</span>
      <span v-else style="width:14px"></span>
      <strong style="font-size:13px">{{ node.smiles || node.name || 'Compound' }}</strong>
      <span v-if="node.buyable" class="badge badge-success" style="font-size:10px">Buyable</span>
      <span v-if="node.yield_pct" class="text-muted" style="font-size:11px">{{ node.yield_pct }}%</span>
    </div>
    <div v-if="expanded && node.children?.length">
      <SynthesisTreeNode
        v-for="(child, i) in node.children"
        :key="i"
        :node="child"
        :depth="depth + 1"
      />
    </div>
  </div>
</template>
