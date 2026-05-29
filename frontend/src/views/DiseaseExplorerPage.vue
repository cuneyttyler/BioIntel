<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { diseases as diseasesApi, targets as targetsApi } from '@/services/api'
import PageHeader from '@/components/layout/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const router = useRouter()
const query = ref('')
const searchResults = ref([])
const selectedDisease = ref(null)
const diseaseTargets = ref([])
const diseaseDrugs = ref([])
const selectedTarget = ref(null)
const targetDetail = ref(null)
const loading = ref(false)
const targetLoading = ref(false)

let timer = null
const onQueryChange = () => {
  clearTimeout(timer)
  if (query.value.length < 2) return
  timer = setTimeout(search, 400)
}

const search = async () => {
  loading.value = true
  try {
    searchResults.value = await diseasesApi.search(query.value)
  } finally { loading.value = false }
}

const selectDisease = async (disease) => {
  selectedDisease.value = disease
  searchResults.value = []
  loading.value = true
  const [t, d] = await Promise.allSettled([
    diseasesApi.targets(disease.id),
    diseasesApi.drugs(disease.id),
  ])
  diseaseTargets.value = t.value?.associatedTargets?.rows || []
  diseaseDrugs.value = d.value?.drugAndClinicalCandidates?.rows || []
  loading.value = false
}

const showTarget = async (target) => {
  selectedTarget.value = target
  targetLoading.value = true
  try {
    targetDetail.value = await targetsApi.detail(target.target.approvedSymbol)
  } catch { targetDetail.value = null }
  targetLoading.value = false
}
</script>

<template>
  <div>
    <PageHeader title="Disease & Target Explorer" />

    <div class="card mb-4">
      <div class="form-group" style="margin-bottom:0;position:relative">
        <label class="form-label">Search Disease</label>
        <input v-model="query" class="form-control" placeholder="e.g. type 2 diabetes, breast cancer..." @input="onQueryChange" />
        <div v-if="searchResults.length" style="position:absolute;z-index:50;background:var(--surface);border:1px solid var(--border);border-radius:8px;box-shadow:var(--shadow-md);width:100%;max-height:280px;overflow-y:auto;top:100%">
          <div
            v-for="d in searchResults"
            :key="d.id"
            style="padding:12px;cursor:pointer;border-bottom:1px solid var(--border)"
            @click="selectDisease(d)"
          >
            <div class="font-bold text-sm">{{ d.name }}</div>
            <div class="text-muted text-sm">{{ d.id }} · {{ d.description?.slice(0, 80) }}</div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="loading" style="text-align:center;padding:32px"><LoadingSpinner /></div>

    <div v-else-if="selectedDisease">
      <div class="card mb-4">
        <div class="flex items-center gap-3 mb-2">
          <h2 style="font-size:18px">{{ selectedDisease.name }}</h2>
          <span class="badge badge-completed">{{ selectedDisease.id }}</span>
        </div>
        <p class="text-muted text-sm">{{ selectedDisease.description }}</p>
      </div>

      <div class="grid-2 mb-4" style="align-items:start">
        <div class="card">
          <div class="card-title">Associated Targets ({{ diseaseTargets.length }})</div>
          <div class="table-wrap">
            <table>
              <thead><tr><th>Gene</th><th>Protein</th><th>Score</th></tr></thead>
              <tbody>
                <tr v-for="row in diseaseTargets" :key="row.target.id" style="cursor:pointer" @click="showTarget(row)">
                  <td><strong>{{ row.target.approvedSymbol }}</strong></td>
                  <td class="text-sm">{{ row.target.approvedName }}</td>
                  <td>
                    <div class="progress-bar" style="width:80px">
                      <div class="progress-bar-fill" :style="`width:${(row.score*100).toFixed(0)}%`" />
                    </div>
                    <span class="text-sm text-muted">{{ (row.score).toFixed(3) }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="card">
          <div class="card-title">Known Drugs ({{ diseaseDrugs.length }})</div>
          <div class="table-wrap">
            <table>
              <thead><tr><th>Drug</th><th>Stage</th></tr></thead>
              <tbody>
                <tr v-for="row in diseaseDrugs" :key="row.drug.id" style="cursor:pointer" @click="router.push(`/drugs/${row.drug.id}`)">
                  <td><strong>{{ row.drug.name }}</strong></td>
                  <td><span class="badge badge-phase1">{{ row.maxClinicalStage?.replace('_', ' ') || '—' }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div v-if="selectedTarget" class="panel-overlay" @click.self="selectedTarget = null">
        <div class="panel-drawer">
          <div class="flex items-center justify-between mb-4">
            <h2 style="font-size:16px">{{ selectedTarget.target.approvedSymbol }}</h2>
            <button class="btn btn-secondary btn-sm" @click="selectedTarget = null">✕ Close</button>
          </div>
          <div v-if="targetLoading"><LoadingSpinner /></div>
          <div v-else-if="targetDetail">
            <p class="text-sm text-muted mb-4">UniProt: {{ targetDetail.primaryAccession }}</p>
            <div v-if="targetDetail.comments" style="display:flex;flex-direction:column;gap:12px">
              <div v-for="(comment, i) in targetDetail.comments?.slice(0,5)" :key="i" class="card" style="padding:12px">
                <div class="font-bold text-sm" style="text-transform:capitalize">{{ comment.commentType?.replace(/_/g,' ') }}</div>
                <div v-if="comment.disease?.diseaseId" class="text-muted text-sm" style="margin-top:2px">{{ comment.disease.diseaseId }}</div>
                <p class="text-sm mt-4" style="margin-top:4px">
                  {{ comment.texts?.[0]?.value?.slice(0,200) || comment.disease?.description?.slice(0,200) || comment.note?.texts?.[0]?.value?.slice(0,200) }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
