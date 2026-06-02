<script setup>
import { computed } from 'vue'

const props = defineProps({
  conditions: { type: Array, default: () => [] },
  results: { type: Object, default: () => ({}) },
})

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']

const datasets = computed(() =>
  props.conditions.map((c, i) => ({
    label: c.condition_label,
    color: COLORS[i % COLORS.length],
    points: (props.results[c.id] || [])
      .filter(r => r.assay_pct != null)
      .sort((a, b) => a.timepoint_weeks - b.timepoint_weeks)
      .map(r => ({ x: r.timepoint_weeks, y: r.assay_pct })),
  })).filter(d => d.points.length)
)

const allTimepoints = computed(() => {
  const tps = new Set()
  datasets.value.forEach(d => d.points.forEach(p => tps.add(p.x)))
  return [...tps].sort((a, b) => a - b)
})
</script>

<template>
  <div>
    <div v-if="!datasets.length" class="text-muted" style="font-size:13px">No assay data to chart.</div>
    <div v-else>
      <div v-for="ds in datasets" :key="ds.label" style="display:flex;align-items:center;gap:6px;margin-bottom:4px;font-size:12px">
        <span :style="{ background: ds.color, width: '12px', height: '12px', borderRadius: '2px', display: 'inline-block' }"></span>
        {{ ds.label }}:
        <span v-for="pt in ds.points" :key="pt.x" style="margin-left:6px">
          {{ pt.x }}w → {{ pt.y }}%
        </span>
      </div>
      <p class="text-muted" style="font-size:11px;margin-top:8px">Full chart visualization requires a charting library (e.g., Chart.js). Data points shown above.</p>
    </div>
  </div>
</template>
