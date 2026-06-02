<script setup>
import OOSFlag from './OOSFlag.vue'

const props = defineProps({
  conditions: { type: Array, default: () => [] },
  results: { type: Object, default: () => ({}) },
})

const allTimepoints = () => {
  const tps = new Set()
  Object.values(props.results).forEach(arr => arr.forEach(r => tps.add(r.timepoint_weeks)))
  return [...tps].sort((a, b) => a - b)
}

function getResult(conditionId, tp) {
  return props.results[conditionId]?.find(r => r.timepoint_weeks === tp) || null
}
</script>

<template>
  <div style="overflow-x:auto">
    <table class="data-table">
      <thead>
        <tr>
          <th>Condition</th>
          <th v-for="tp in allTimepoints()" :key="tp">{{ tp }}w</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="c in conditions" :key="c.id">
          <td><strong>{{ c.condition_label }}</strong><br><span class="text-muted" style="font-size:11px">{{ c.temperature_c }}°C/{{ c.humidity_rh }}%</span></td>
          <td v-for="tp in allTimepoints()" :key="tp">
            <template v-if="getResult(c.id, tp)">
              <div style="font-size:12px">{{ getResult(c.id, tp).assay_pct ?? '-' }}%</div>
              <OOSFlag :oos="getResult(c.id, tp).oos_flag" :oot="getResult(c.id, tp).oot_flag" />
            </template>
            <span v-else class="text-muted">—</span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
