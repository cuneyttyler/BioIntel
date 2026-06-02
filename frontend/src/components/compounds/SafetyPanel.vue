<script setup>
defineProps({
  safety: { type: Object, default: null },
})
</script>

<template>
  <div v-if="safety" class="card">
    <h4 class="card-title" style="font-size:14px">Safety Summary (CompTox)</h4>
    <div v-if="safety.acute_tox" style="margin-bottom:8px">
      <span class="text-muted" style="font-size:12px">Acute Tox</span>
      <p style="margin:2px 0">{{ safety.acute_tox }}</p>
    </div>
    <div v-if="safety.ames_mutagenicity !== undefined" style="margin-bottom:8px">
      <span class="text-muted" style="font-size:12px">Ames Mutagenicity</span>
      <p>
        <span :class="`badge badge-${safety.ames_mutagenicity ? 'danger' : 'success'}`">
          {{ safety.ames_mutagenicity ? 'Mutagen' : 'Non-mutagen' }}
        </span>
      </p>
    </div>
    <div v-if="safety.carcinogenicity !== undefined" style="margin-bottom:8px">
      <span class="text-muted" style="font-size:12px">Carcinogenicity</span>
      <p>
        <span :class="`badge badge-${safety.carcinogenicity ? 'danger' : 'success'}`">
          {{ safety.carcinogenicity ? 'Carcinogen' : 'Non-carcinogen' }}
        </span>
      </p>
    </div>
    <div v-if="safety.skin_sensitizer !== undefined">
      <span class="text-muted" style="font-size:12px">Skin Sensitizer</span>
      <p>
        <span :class="`badge badge-${safety.skin_sensitizer ? 'warning' : 'success'}`">
          {{ safety.skin_sensitizer ? 'Sensitizer' : 'Non-sensitizer' }}
        </span>
      </p>
    </div>
  </div>
  <div v-else class="card">
    <p class="text-muted" style="font-size:13px">No safety data available.</p>
  </div>
</template>
