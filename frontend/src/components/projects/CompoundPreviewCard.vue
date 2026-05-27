<script setup>
defineProps({ compound: Object })
</script>

<template>
  <div v-if="compound" class="card" style="background:var(--primary-light)">
    <div class="card-title">Selected Compound</div>
    <div class="grid-2 text-sm">
      <div><span class="text-muted">Name:</span> <strong>{{ compound.name }}</strong></div>
      <div v-if="compound.pubchem_cid"><span class="text-muted">PubChem CID:</span> {{ compound.pubchem_cid }}</div>
      <div v-if="compound.chembl_id"><span class="text-muted">ChEMBL:</span> {{ compound.chembl_id }}</div>
      <div v-if="compound.molecular_weight"><span class="text-muted">MW:</span> {{ compound.molecular_weight }} Da</div>
      <div v-if="compound.molecular_formula"><span class="text-muted">Formula:</span> {{ compound.molecular_formula }}</div>
    </div>
    <div v-if="compound.smiles" style="margin-top:8px">
      <span class="text-muted text-sm">SMILES: </span>
      <code style="font-size:12px;word-break:break-all">{{ compound.smiles }}</code>
    </div>
  </div>
</template>
