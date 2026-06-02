<script setup>
defineProps({
  properties: { type: Array, required: true },
})
</script>

<template>
  <table class="data-table">
    <tbody>
      <tr v-for="row in properties" :key="row.label">
        <td class="text-muted" style="width:40%;font-size:13px">{{ row.label }}</td>
        <td>
          <span v-if="row.badge" :class="`badge badge-${row.badgeColor || 'info'}`">{{ row.value }}</span>
          <span v-else>{{ row.value ?? '-' }}</span>
          <span v-if="row.unit" class="text-muted" style="font-size:12px;margin-left:4px">{{ row.unit }}</span>
        </td>
      </tr>
    </tbody>
  </table>
</template>
