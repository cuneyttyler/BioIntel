<script setup>
defineProps({
  property: { type: String, required: true },
  computed: { type: [Number, String], default: null },
  experimental: { type: [Number, String], default: null },
  benchmark: { type: [Number, String], default: null },
  unit: { type: String, default: '' },
  good: { type: Boolean, default: null },
})
</script>

<template>
  <tr>
    <td>{{ property }}</td>
    <td style="font-family:monospace">{{ computed != null ? `${computed} ${unit}` : '-' }}</td>
    <td style="font-family:monospace">{{ experimental != null ? `${experimental} ${unit}` : '-' }}</td>
    <td class="text-muted" style="font-size:12px">{{ benchmark ?? '-' }}</td>
    <td>
      <span v-if="good === true" class="badge badge-success">Good</span>
      <span v-else-if="good === false" class="badge badge-warning">Flag</span>
      <span v-else class="text-muted">—</span>
    </td>
  </tr>
</template>
