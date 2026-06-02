<script setup>
defineProps({
  hits: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['shortlist'])
</script>

<template>
  <div>
    <div v-if="loading" class="text-muted" style="padding:12px;text-align:center">Loading results...</div>
    <table v-else-if="hits.length" class="data-table">
      <thead>
        <tr>
          <th>Name / ID</th>
          <th>SMILES</th>
          <th>Affinity (kcal/mol)</th>
          <th>ADMET</th>
          <th>Patent</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="h in hits" :key="h.id">
          <td>{{ h.name || h.pubchem_cid || `Hit ${h.id}` }}</td>
          <td style="font-size:11px;font-family:monospace;max-width:140px;overflow:hidden;text-overflow:ellipsis">{{ h.smiles }}</td>
          <td style="font-family:monospace">{{ h.binding_affinity ?? h.docking_score ?? '-' }}</td>
          <td>
            <span v-if="h.admet_data?.ro5 === true" class="badge badge-success">Ro5 ✓</span>
            <span v-else-if="h.admet_data?.ro5 === false" class="badge badge-warning">Ro5 ✗</span>
            <span v-else class="text-muted">-</span>
          </td>
          <td>
            <span v-if="h.patent_status" :class="`badge badge-${h.patent_status === 'clean' ? 'success' : 'warning'}`">{{ h.patent_status }}</span>
            <span v-else class="text-muted">-</span>
          </td>
          <td>
            <button v-if="!h.shortlisted" class="btn btn-sm btn-secondary" @click="emit('shortlist', h.id)">Shortlist</button>
            <span v-else class="badge badge-success">Shortlisted</span>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else class="text-muted" style="font-size:13px">No hits yet.</p>
  </div>
</template>
