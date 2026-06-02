<script setup>
defineProps({
  admet: { type: Object, required: true },
})
</script>

<template>
  <div class="card">
    <h4 class="card-title" style="font-size:14px">ADMET Summary</h4>
    <div class="grid-3" style="gap:8px;font-size:13px">
      <div><span class="text-muted">MW</span><p>{{ admet.mw?.toFixed(1) ?? '-' }} Da</p></div>
      <div><span class="text-muted">LogP</span><p>{{ admet.logp?.toFixed(2) ?? '-' }}</p></div>
      <div><span class="text-muted">TPSA</span><p>{{ admet.tpsa?.toFixed(1) ?? '-' }} Å²</p></div>
      <div><span class="text-muted">HBD</span><p>{{ admet.hbd ?? '-' }}</p></div>
      <div><span class="text-muted">HBA</span><p>{{ admet.hba ?? '-' }}</p></div>
      <div>
        <span class="text-muted">Ro5</span>
        <p>
          <span v-if="admet.mw <= 500 && admet.logp <= 5 && admet.hbd <= 5 && admet.hba <= 10" class="badge badge-success">Pass</span>
          <span v-else class="badge badge-warning">Fail</span>
        </p>
      </div>
    </div>
    <div v-if="admet.herg_liability" style="margin-top:8px;font-size:12px">
      <span class="text-muted">hERG: </span>
      <span :class="admet.herg_liability === 'Low' ? 'text-success' : 'text-warning'">{{ admet.herg_liability }}</span>
    </div>
  </div>
</template>
