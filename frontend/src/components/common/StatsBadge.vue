<script setup>
defineProps({ value: [String, Number], label: String, color: { type: String, default: 'primary' } })
</script>

<template>
  <div :style="`display:inline-flex;flex-direction:column;align-items:center;padding:12px 20px;background:var(--surface);border:1px solid var(--border);border-radius:8px;`">
    <span :style="`font-size:24px;font-weight:700;color:var(--${color === 'primary' ? 'primary' : color})`">{{ value }}</span>
    <span class="text-muted text-sm">{{ label }}</span>
  </div>
</template>
