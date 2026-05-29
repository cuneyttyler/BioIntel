<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { drugs as drugsApi } from '@/services/api'
import PageHeader from '@/components/layout/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const router = useRouter()
const query = ref('')
const results = ref([])
const loading = ref(false)

let timer = null
const onInput = () => {
  clearTimeout(timer)
  if (query.value.length < 2) { results.value = []; return }
  timer = setTimeout(search, 400)
}

const search = async () => {
  loading.value = true
  try {
    results.value = await drugsApi.search(query.value)
  } finally {
    loading.value = false
  }
}

const selectDrug = (drug) => {
  const id = drug.molecule_chembl_id
  router.push(`/drugs/${id}`)
}
</script>

<template>
  <div>
    <PageHeader title="Drug Intelligence" />

    <div class="card mb-4">
      <div class="form-group" style="margin-bottom:0;position:relative">
        <label class="form-label">Search Approved Drug or Compound</label>
        <input
          v-model="query"
          class="form-control"
          placeholder="e.g. metformin, ibuprofen, atorvastatin..."
          @input="onInput"
        />
        <div v-if="loading" style="padding:12px;text-align:center"><LoadingSpinner /></div>
        <div
          v-else-if="results.length"
          style="position:absolute;z-index:50;background:var(--surface);border:1px solid var(--border);border-radius:8px;box-shadow:var(--shadow-md);width:100%;max-height:320px;overflow-y:auto;top:calc(100% + 4px)"
        >
          <div
            v-for="drug in results"
            :key="drug.molecule_chembl_id"
            style="padding:12px;cursor:pointer;border-bottom:1px solid var(--border)"
            @click="selectDrug(drug)"
          >
            <div class="font-bold text-sm">{{ drug.pref_name || drug.molecule_chembl_id }}</div>
            <div class="flex gap-2 mt-4" style="margin-top:4px;flex-wrap:wrap">
              <span class="badge badge-completed">{{ drug.molecule_chembl_id }}</span>
              <span v-if="drug.max_phase" class="badge badge-phase1">Phase {{ drug.max_phase }}</span>
              <span v-if="drug.molecule_type" class="text-muted text-sm">{{ drug.molecule_type }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="!results.length && !loading && query.length < 2" class="empty-state">
      <div style="font-size:48px">🔬</div>
      <h3>Search for an existing drug</h3>
      <p>Enter a drug name to explore its chemical profile, mechanism of action, clinical trial history, and patent landscape — then find structurally distinct analogs.</p>
    </div>
  </div>
</template>
