<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { compounds as compoundsApi } from '@/services/api'
import PageHeader from '@/components/layout/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const route = useRoute()
const id = route.params.id

const compound = ref(null)
const properties = ref({})
const admet = ref({})
const safety = ref({})
const targets = ref([])
const similar = ref([])
const loading = ref(true)

const admetColors = (val) => {
  if (typeof val === 'boolean') return val ? '#d1fae5' : '#fee2e2'
  return '#f3f4f6'
}

onMounted(async () => {
  const [c, props, ad, saf, targ, sim] = await Promise.allSettled([
    compoundsApi.get(id),
    compoundsApi.properties(id),
    compoundsApi.admet(id),
    compoundsApi.safety(id),
    compoundsApi.targets(id),
    compoundsApi.similar(id),
  ])
  compound.value = c.value
  properties.value = props.value || {}
  admet.value = ad.value || {}
  safety.value = saf.value || {}
  targets.value = targ.value?.targets || []
  similar.value = sim.value || []
  loading.value = false
})
</script>

<template>
  <div>
    <PageHeader :title="compound?.name || 'Compound Profile'" />

    <div v-if="loading" style="text-align:center;padding:48px"><LoadingSpinner size="lg" /></div>

    <div v-else-if="compound">
      <div class="grid-2 mb-4" style="align-items:start">
        <div class="card">
          <div class="flex gap-4 items-center mb-4">
            <div>
              <h2 style="font-size:18px">{{ compound.name }}</h2>
              <div class="flex gap-2 mt-2">
                <span v-if="compound.chembl_id" class="badge badge-phase1">{{ compound.chembl_id }}</span>
                <span v-if="compound.pubchem_cid" class="badge badge-preclinical">CID: {{ compound.pubchem_cid }}</span>
              </div>
            </div>
          </div>
          <img
            v-if="compound.pubchem_cid"
            :src="compoundsApi.structureUrl(compound.id)"
            alt="Structure"
            style="max-width:200px;border:1px solid var(--border);border-radius:8px"
            onerror="this.style.display='none'"
          />
        </div>

        <div class="card">
          <div class="card-title">Physicochemical Properties</div>
          <table>
            <tr v-if="properties.MolecularWeight"><td class="text-muted">MW</td><td>{{ properties.MolecularWeight }} Da</td></tr>
            <tr v-if="properties.XLogP"><td class="text-muted">LogP</td><td>{{ properties.XLogP }}</td></tr>
            <tr v-if="properties.TPSA"><td class="text-muted">TPSA</td><td>{{ properties.TPSA }} Å²</td></tr>
            <tr v-if="properties.HBondDonorCount !== undefined"><td class="text-muted">HBD</td><td>{{ properties.HBondDonorCount }}</td></tr>
            <tr v-if="properties.HBondAcceptorCount !== undefined"><td class="text-muted">HBA</td><td>{{ properties.HBondAcceptorCount }}</td></tr>
            <tr v-if="compound.molecular_formula"><td class="text-muted">Formula</td><td>{{ compound.molecular_formula }}</td></tr>
            <tr v-if="compound.smiles">
              <td class="text-muted">SMILES</td>
              <td><code style="font-size:11px;word-break:break-all">{{ compound.smiles.slice(0, 60) }}{{ compound.smiles.length > 60 ? '...' : '' }}</code></td>
            </tr>
          </table>
        </div>
      </div>

      <div class="grid-2 mb-4" style="align-items:start">
        <div class="card">
          <div class="card-title">ADMET Profile (pkCSM)</div>
          <div v-if="!Object.keys(admet).length" class="text-muted text-sm">Not available (SMILES required)</div>
          <div v-else style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
            <div v-for="(val, key) in admet" :key="key" :style="`padding:8px;border-radius:6px;background:${admetColors(val)};font-size:13px`">
              <div class="text-muted" style="font-size:11px">{{ key.replace(/_/g,' ') }}</div>
              <div class="font-bold">{{ typeof val === 'boolean' ? (val ? '✓' : '✗') : val }}</div>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-title">Pharmacological Targets</div>
          <div v-if="!targets.length" class="text-muted text-sm">No target data available.</div>
          <div v-else style="display:flex;flex-direction:column;gap:8px">
            <div v-for="t in targets" :key="t.mechanism?.mechanism_of_action" class="card" style="padding:12px">
              <div class="font-bold text-sm">{{ t.mechanism?.mechanism_of_action || 'Unknown' }}</div>
              <div class="text-muted text-sm">{{ t.mechanism?.target_chembl_id }}</div>
              <div v-if="t.uniprot?.primaryAccession" class="text-sm mt-4">
                UniProt: <a :href="`https://www.uniprot.org/uniprotkb/${t.uniprot.primaryAccession}`" target="_blank">{{ t.uniprot.primaryAccession }}</a>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="similar.length" class="card">
        <div class="card-title">Similar Compounds (PubChem)</div>
        <div class="flex gap-2" style="flex-wrap:wrap">
          <a
            v-for="cid in similar.slice(0, 20)"
            :key="cid"
            :href="`https://pubchem.ncbi.nlm.nih.gov/compound/${cid}`"
            target="_blank"
            class="badge badge-completed"
          >CID {{ cid }}</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { compounds as compoundsApi } from '@/services/api'
export default { setup() { return { compoundsApi } } }
</script>
