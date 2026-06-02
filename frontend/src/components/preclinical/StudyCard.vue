<script setup>
defineProps({
  study: { type: Object, required: true },
})

const statusColor = s => s === 'completed' ? 'success' : s === 'ongoing' ? 'info' : s === 'failed' ? 'danger' : 'warning'
</script>

<template>
  <div class="card">
    <div style="display:flex;align-items:start;justify-content:space-between">
      <div>
        <h4 style="font-size:14px;margin:0 0 4px">{{ study.study_type?.replace('_', ' ').toUpperCase() }}</h4>
        <span class="text-muted" style="font-size:12px">{{ study.species }} · {{ study.dose_route }}</span>
      </div>
      <span :class="`badge badge-${statusColor(study.status)}`">{{ study.status }}</span>
    </div>
    <p v-if="study.objective" class="text-muted" style="font-size:12px;margin:8px 0 0">{{ study.objective }}</p>
    <div v-if="study.mtd_mgkg" style="margin-top:8px;font-size:13px">
      <span class="text-muted">MTD: </span><strong>{{ study.mtd_mgkg }} mg/kg</strong>
    </div>
  </div>
</template>
