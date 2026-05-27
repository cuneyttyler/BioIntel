<script setup>
import { ref } from 'vue'
import { literature as litApi } from '@/services/api'
import PageHeader from '@/components/layout/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const activeTab = ref('literature')
const litQuery = ref('')
const litResults = ref([])
const litLoading = ref(false)
const expandedAbstract = ref(null)

const trialCondition = ref('')
const trialIntervention = ref('')
const trialPhase = ref('')
const trialResults = ref([])
const trialLoading = ref(false)

const searchLit = async () => {
  if (!litQuery.value) return
  litLoading.value = true
  try {
    litResults.value = await litApi.search(litQuery.value, 20)
  } finally { litLoading.value = false }
}

const searchTrials = async () => {
  trialLoading.value = true
  try {
    const data = await litApi.trials({
      condition: trialCondition.value || undefined,
      intervention: trialIntervention.value || undefined,
      phase: trialPhase.value || undefined,
    })
    trialResults.value = data.studies || []
  } finally { trialLoading.value = false }
}

const getAuthors = (s) => s.authors?.map(a => a.name).join(', ').slice(0, 60)
const formatDate = (s) => s.pubdate || s.sortdate || ''
</script>

<template>
  <div>
    <PageHeader title="Literature & Clinical Trials" />

    <div class="tabs mb-4">
      <button :class="['tab-btn', activeTab === 'literature' ? 'active' : '']" @click="activeTab = 'literature'">📚 PubMed Literature</button>
      <button :class="['tab-btn', activeTab === 'trials' ? 'active' : '']" @click="activeTab = 'trials'">🏥 Clinical Trials</button>
    </div>

    <div v-if="activeTab === 'literature'">
      <div class="card mb-4">
        <div class="flex gap-2">
          <input v-model="litQuery" class="form-control" placeholder="e.g. metformin type 2 diabetes formulation" @keyup.enter="searchLit" />
          <button class="btn btn-primary" :disabled="litLoading" @click="searchLit">Search</button>
        </div>
      </div>

      <div v-if="litLoading" style="text-align:center;padding:32px"><LoadingSpinner /></div>
      <div v-else style="display:flex;flex-direction:column;gap:12px">
        <div v-for="article in litResults" :key="article.uid" class="card">
          <div class="font-bold" style="margin-bottom:4px">{{ article.title }}</div>
          <div class="text-muted text-sm mb-2">{{ getAuthors(article) }} · {{ formatDate(article) }} · {{ article.source }}</div>
          <div class="text-sm" v-if="article.abstract">{{ article.abstract?.slice(0, 200) }}...</div>
          <div class="flex gap-2 mt-4" style="margin-top:8px">
            <a :href="`https://pubmed.ncbi.nlm.nih.gov/${article.uid}/`" target="_blank" class="btn btn-secondary btn-sm">PubMed ↗</a>
          </div>
        </div>
        <div v-if="!litResults.length && !litLoading" class="empty-state">
          <p>Search PubMed for biomedical literature.</p>
        </div>
      </div>
    </div>

    <div v-else>
      <div class="card mb-4">
        <div class="grid-2 mb-2">
          <input v-model="trialCondition" class="form-control" placeholder="Condition (e.g. diabetes)" />
          <input v-model="trialIntervention" class="form-control" placeholder="Intervention (e.g. metformin)" />
        </div>
        <div class="flex gap-2">
          <select v-model="trialPhase" class="form-control" style="max-width:200px">
            <option value="">All phases</option>
            <option value="PHASE1">Phase 1</option>
            <option value="PHASE2">Phase 2</option>
            <option value="PHASE3">Phase 3</option>
          </select>
          <button class="btn btn-primary" :disabled="trialLoading" @click="searchTrials">Search</button>
        </div>
      </div>

      <div v-if="trialLoading" style="text-align:center;padding:32px"><LoadingSpinner /></div>
      <div v-else style="display:flex;flex-direction:column;gap:12px">
        <div v-for="study in trialResults" :key="study.protocolSection?.identificationModule?.nctId" class="card">
          <div class="flex items-center gap-2 mb-2">
            <span class="badge badge-completed text-sm">{{ study.protocolSection?.identificationModule?.nctId }}</span>
            <span v-if="study.protocolSection?.designModule?.phases" class="badge badge-phase1">
              {{ study.protocolSection.designModule.phases.join(', ') }}
            </span>
          </div>
          <div class="font-bold text-sm">{{ study.protocolSection?.identificationModule?.briefTitle }}</div>
          <div class="text-muted text-sm mt-4" style="margin-top:4px">
            Status: {{ study.protocolSection?.statusModule?.overallStatus }}
          </div>
          <a
            :href="`https://clinicaltrials.gov/study/${study.protocolSection?.identificationModule?.nctId}`"
            target="_blank"
            class="btn btn-secondary btn-sm"
            style="margin-top:8px;display:inline-flex"
          >View on ClinicalTrials.gov ↗</a>
        </div>
        <div v-if="!trialResults.length && !trialLoading" class="empty-state">
          <p>Search ClinicalTrials.gov for clinical trial data.</p>
        </div>
      </div>
    </div>
  </div>
</template>
