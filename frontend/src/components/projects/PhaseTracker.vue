<script setup>
defineProps({
  phases: { type: Array, default: () => [] },
  currentPhase: { type: String, default: null },
})

const PHASE_ORDER = ['discovery', 'lead_optimization', 'preclinical', 'ind_filing', 'phase1', 'phase2', 'phase3']
const LABELS = {
  discovery: 'Discovery',
  lead_optimization: 'Lead Opt',
  preclinical: 'Preclinical',
  ind_filing: 'IND Filing',
  phase1: 'Phase I',
  phase2: 'Phase II',
  phase3: 'Phase III',
}

const statusColor = s => s === 'completed' ? '#10b981' : s === 'active' ? '#6366f1' : '#e5e7eb'
const statusText = s => s === 'completed' ? '#fff' : s === 'active' ? '#fff' : '#9ca3af'
</script>

<template>
  <div style="display:flex;align-items:center;overflow-x:auto;padding:8px 0;gap:0">
    <template v-for="(phase, i) in PHASE_ORDER" :key="phase">
      <div style="display:flex;flex-direction:column;align-items:center;min-width:80px">
        <div
          :style="{
            width: '32px', height: '32px', borderRadius: '50%',
            background: statusColor(phases.find(p => p.phase === phase)?.status),
            color: statusText(phases.find(p => p.phase === phase)?.status),
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '12px', fontWeight: '600',
            border: currentPhase === phase ? '3px solid #6366f1' : '2px solid #e5e7eb',
          }"
        >{{ i + 1 }}</div>
        <span style="font-size:10px;margin-top:4px;text-align:center;color:#6b7280">{{ LABELS[phase] }}</span>
      </div>
      <div v-if="i < PHASE_ORDER.length - 1" style="flex:1;height:2px;background:#e5e7eb;min-width:12px;margin-bottom:16px"></div>
    </template>
  </div>
</template>
