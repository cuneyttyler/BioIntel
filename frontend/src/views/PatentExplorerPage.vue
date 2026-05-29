<script setup>
import { ref } from 'vue'
import { patents as patentsApi } from '@/services/api'
import PageHeader from '@/components/layout/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const searchMode = ref('name')
const query = ref('')
const smilesQuery = ref('')
const results = ref([])
const loading = ref(false)
const selectedPatent = ref(null)
const patentDetail = ref(null)
const detailLoading = ref(false)

const search = async () => {
  loading.value = true
  results.value = []
  try {
    if (searchMode.value === 'smiles') {
      results.value = await patentsApi.search(null, smilesQuery.value)
    } else {
      results.value = await patentsApi.search(query.value, null)
    }
  } finally {
    loading.value = false
  }
}

const viewPatent = async (patent) => {
  selectedPatent.value = patent
  const num = patent.patent_number || patent.document_id
  if (!num) { patentDetail.value = null; return }
  detailLoading.value = true
  try {
    patentDetail.value = await patentsApi.get(num)
  } catch {
    patentDetail.value = null
  } finally {
    detailLoading.value = false
  }
}

const patentExpiry = (patent) => {
  const filing = patent.filing_date || patent.date || ''
  if (!filing) return '—'
  try {
    const year = /^\d{4}$/.test(filing) ? parseInt(filing) : new Date(filing).getFullYear()
    return `~${year + 20}`
  } catch { return '—' }
}
</script>

<template>
  <div>
    <PageHeader title="Patent Explorer" />

    <div class="card mb-4">
      <div class="flex gap-2 mb-4">
        <button :class="['btn btn-sm', searchMode === 'name' ? 'btn-primary' : 'btn-secondary']" @click="searchMode = 'name'">By Drug Name</button>
        <button :class="['btn btn-sm', searchMode === 'smiles' ? 'btn-primary' : 'btn-secondary']" @click="searchMode = 'smiles'">By SMILES Structure</button>
      </div>

      <div v-if="searchMode === 'name'" class="flex gap-2">
        <input v-model="query" class="form-control" placeholder="e.g. metformin, aspirin..." @keyup.enter="search" />
        <button class="btn btn-primary" :disabled="loading || !query" @click="search">Search</button>
      </div>
      <div v-else class="flex gap-2">
        <input v-model="smilesQuery" class="form-control" placeholder="Paste SMILES string..." style="font-family:var(--mono);font-size:13px" @keyup.enter="search" />
        <button class="btn btn-primary" :disabled="loading || !smilesQuery" @click="search">Search</button>
      </div>
    </div>

    <div v-if="loading" style="text-align:center;padding:32px"><LoadingSpinner /></div>

    <div v-else-if="results.length" style="display:flex;flex-direction:column;gap:8px">
      <div
        v-for="p in results"
        :key="p.patent_number || p.document_id"
        class="card"
        style="cursor:pointer"
        :style="selectedPatent === p ? 'border-color:var(--primary)' : ''"
        @click="viewPatent(p)"
      >
        <div class="flex items-center justify-between mb-2">
          <a :href="`https://worldwide.espacenet.com/patent/search?q=pn%3D${p.patent_number || p.document_id}`" target="_blank" class="badge badge-completed" style="text-decoration:none">{{ p.patent_number || p.document_id || 'Unknown' }}</a>
          <span class="text-muted text-sm">Filed: {{ p.filing_date || p.date || '—' }} · Expiry: {{ patentExpiry(p) }}</span>
        </div>
        <div class="font-bold text-sm">{{ p.title || 'No title available' }}</div>
        <div v-if="p.assignee" class="text-muted text-sm" style="margin-top:4px">{{ p.assignee }}</div>
      </div>
    </div>

    <div v-else-if="!loading && query || smilesQuery" class="empty-state">
      <p>No patents found. Try a different name or structure.</p>
    </div>

    <div v-else-if="!results.length && !loading" class="empty-state">
      <div style="font-size:48px">📜</div>
      <h3>Search patent literature</h3>
      <p>Find patents covering a drug by name or by SMILES structure. Use this to understand the freedom-to-operate landscape before designing an analog.</p>
    </div>

    <!-- Patent detail drawer -->
    <div v-if="selectedPatent" class="panel-overlay" @click.self="selectedPatent = null; patentDetail = null">
      <div class="panel-drawer">
        <div class="flex items-center justify-between mb-4">
          <h2 style="font-size:16px">{{ selectedPatent.patent_number || selectedPatent.document_id }}</h2>
          <button class="btn btn-secondary btn-sm" @click="selectedPatent = null; patentDetail = null">✕ Close</button>
        </div>
        <div v-if="detailLoading"><LoadingSpinner /></div>
        <div v-else>
          <div class="text-muted text-sm mb-4">{{ selectedPatent.title }}</div>
          <div v-if="selectedPatent.assignee" class="text-sm mb-4"><strong>Assignee:</strong> {{ selectedPatent.assignee }}</div>
          <div v-if="patentDetail" class="text-sm">
            <pre style="white-space:pre-wrap;font-size:12px;overflow:auto;max-height:300px">{{ JSON.stringify(patentDetail, null, 2).slice(0, 2000) }}</pre>
          </div>
          <div v-else class="text-muted text-sm">No additional detail available.</div>
        </div>
      </div>
    </div>
  </div>
</template>
