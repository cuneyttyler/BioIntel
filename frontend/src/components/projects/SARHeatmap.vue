<script setup>
import { computed } from 'vue'

const props = defineProps({
  entries: { type: Array, default: () => [] },
})

const rGroups = computed(() => [...new Set(props.entries.map(e => e.r_group).filter(Boolean))])
const activityTypes = computed(() => [...new Set(props.entries.map(e => e.activity_type).filter(Boolean))])

function getValue(rGroup, actType) {
  return props.entries.find(e => e.r_group === rGroup && e.activity_type === actType)?.activity_value
}

function cellColor(value) {
  if (value == null) return '#f9fafb'
  const v = parseFloat(value)
  if (isNaN(v)) return '#f9fafb'
  if (v < 10) return '#10b981'
  if (v < 100) return '#f59e0b'
  return '#ef4444'
}
</script>

<template>
  <div v-if="rGroups.length && activityTypes.length" style="overflow-x:auto">
    <table class="data-table">
      <thead>
        <tr>
          <th>R-group</th>
          <th v-for="at in activityTypes" :key="at">{{ at }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="rg in rGroups" :key="rg">
          <td>{{ rg }}</td>
          <td
            v-for="at in activityTypes" :key="at"
            :style="{ background: cellColor(getValue(rg, at)), textAlign: 'center', fontSize: '12px' }"
          >
            {{ getValue(rg, at) ?? '—' }}
          </td>
        </tr>
      </tbody>
    </table>
    <p class="text-muted" style="font-size:11px;margin-top:4px">Green &lt;10 nM · Yellow 10–100 nM · Red &gt;100 nM</p>
  </div>
  <p v-else class="text-muted" style="font-size:13px">Not enough SAR data for heatmap.</p>
</template>
