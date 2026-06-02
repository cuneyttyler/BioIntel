<script setup>
defineProps({
  candidates: { type: Array, default: () => [] },
})

const emit = defineEmits(['select'])
</script>

<template>
  <table class="data-table">
    <thead>
      <tr>
        <th>Name / ID</th>
        <th>SMILES</th>
        <th>Similarity</th>
        <th>MW</th>
        <th>LogP</th>
        <th>Best Activity</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="c in candidates" :key="c.id">
        <td><strong>{{ c.name || c.iupac_name || `#${c.id}` }}</strong></td>
        <td style="font-size:11px;font-family:monospace;max-width:150px;overflow:hidden;text-overflow:ellipsis">{{ c.smiles }}</td>
        <td>{{ c.similarity != null ? (c.similarity * 100).toFixed(1) + '%' : '-' }}</td>
        <td>{{ c.molecular_weight?.toFixed(1) ?? '-' }}</td>
        <td>{{ c.logp?.toFixed(2) ?? '-' }}</td>
        <td>
          <span v-if="c.best_activity">{{ c.best_activity }} {{ c.best_activity_unit }}</span>
          <span v-else class="text-muted">-</span>
        </td>
        <td>
          <button class="btn btn-sm btn-secondary" @click="emit('select', c)">Select</button>
        </td>
      </tr>
      <tr v-if="!candidates.length">
        <td colspan="7" class="text-muted" style="text-align:center;padding:16px">No candidates</td>
      </tr>
    </tbody>
  </table>
</template>
