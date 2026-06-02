<script setup>
defineProps({
  targets: { type: Array, default: () => [] },
})
</script>

<template>
  <div>
    <div v-if="!targets.length" class="text-muted" style="font-size:13px">No target data.</div>
    <div v-else>
      <div v-for="t in targets" :key="t.uniprot_id || t.gene_symbol" class="list-item" style="padding:6px 0">
        <strong>{{ t.gene_symbol || t.protein_name }}</strong>
        <span v-if="t.organism" class="text-muted" style="font-size:12px;margin-left:6px">({{ t.organism }})</span>
        <span v-if="t.activity_value" style="margin-left:8px;font-size:12px">
          {{ t.activity_type || 'Activity' }}: {{ t.activity_value }} {{ t.activity_unit }}
        </span>
      </div>
    </div>
  </div>
</template>
