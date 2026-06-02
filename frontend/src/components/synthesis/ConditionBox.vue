<script setup>
defineProps({
  temperature: { type: String, default: null },
  solvent: { type: String, default: null },
  time: { type: String, default: null },
  pressure: { type: String, default: null },
})
</script>

<template>
  <div style="display:inline-flex;gap:6px;flex-wrap:wrap;font-size:11px">
    <span v-if="temperature" style="background:#f3f4f6;border-radius:4px;padding:2px 6px">🌡 {{ temperature }}</span>
    <span v-if="solvent" style="background:#f3f4f6;border-radius:4px;padding:2px 6px">⚗ {{ solvent }}</span>
    <span v-if="time" style="background:#f3f4f6;border-radius:4px;padding:2px 6px">⏱ {{ time }}</span>
    <span v-if="pressure" style="background:#f3f4f6;border-radius:4px;padding:2px 6px">🔩 {{ pressure }}</span>
  </div>
</template>
