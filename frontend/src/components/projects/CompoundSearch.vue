<script setup>
import { ref, watch } from 'vue'
import { compounds as compoundsApi } from '@/services/api'

const emit = defineEmits(['select'])
const query = ref('')
const results = ref({ pubchem: [], chembl: [] })
const loading = ref(false)
const showDropdown = ref(false)

let timer = null
watch(query, (val) => {
  clearTimeout(timer)
  if (val.length < 2) { results.value = { pubchem: [], chembl: [] }; return }
  loading.value = true
  timer = setTimeout(async () => {
    try {
      results.value = await compoundsApi.search(val)
    } catch { results.value = { pubchem: [], chembl: [] } }
    loading.value = false
    showDropdown.value = true
  }, 500)
})

const selectPubChem = (item) => {
  emit('select', {
    name: query.value,
    pubchem_cid: item.CID,
    smiles: item.IsomericSMILES || '',
    molecular_weight: item.MolecularWeight,
    molecular_formula: item.MolecularFormula,
    inchi_key: item.InChIKey || '',
  })
  showDropdown.value = false
}

const selectChEMBL = (item) => {
  emit('select', {
    name: item.pref_name || item.molecule_chembl_id,
    chembl_id: item.molecule_chembl_id,
    smiles: item.molecule_structures?.canonical_smiles || '',
    molecular_weight: item.molecule_properties?.full_mwt,
    molecular_formula: item.molecule_properties?.full_molformula || '',
  })
  showDropdown.value = false
}
</script>

<template>
  <div style="position:relative">
    <div class="form-group">
      <label class="form-label">Search Compound (PubChem / ChEMBL)</label>
      <input v-model="query" class="form-control" placeholder="Enter compound name, e.g. Aspirin..." @focus="showDropdown = true" />
    </div>
    <div
      v-if="showDropdown && (results.pubchem.length || results.chembl.length)"
      style="position:absolute;z-index:50;background:var(--surface);border:1px solid var(--border);border-radius:8px;box-shadow:var(--shadow-md);width:100%;max-height:300px;overflow-y:auto"
    >
      <div v-if="results.pubchem.length">
        <div style="padding:8px 12px;font-size:11px;font-weight:600;color:var(--text-muted);text-transform:uppercase">PubChem</div>
        <div
          v-for="item in results.pubchem.slice(0, 5)"
          :key="item.CID"
          style="padding:10px 12px;cursor:pointer;border-bottom:1px solid var(--border)"
          @click="selectPubChem(item)"
          @mouseenter="$event.currentTarget.style.background='var(--primary-light)'"
          @mouseleave="$event.currentTarget.style.background=''"
        >
          <div class="font-bold text-sm">CID: {{ item.CID }}</div>
          <div class="text-muted text-sm">{{ item.MolecularFormula }} | MW: {{ item.MolecularWeight }}</div>
        </div>
      </div>
      <div v-if="results.chembl.length">
        <div style="padding:8px 12px;font-size:11px;font-weight:600;color:var(--text-muted);text-transform:uppercase">ChEMBL</div>
        <div
          v-for="item in results.chembl"
          :key="item.molecule_chembl_id"
          style="padding:10px 12px;cursor:pointer;border-bottom:1px solid var(--border)"
          @click="selectChEMBL(item)"
          @mouseenter="$event.currentTarget.style.background='var(--primary-light)'"
          @mouseleave="$event.currentTarget.style.background=''"
        >
          <div class="font-bold text-sm">{{ item.pref_name || item.molecule_chembl_id }}</div>
          <div class="text-muted text-sm">{{ item.molecule_chembl_id }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
