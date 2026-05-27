<script setup>
import { ref } from 'vue'
import { synthesis as synthesisApi } from '@/services/api'
import PageHeader from '@/components/layout/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const smiles = ref('')
const retroResult = ref(null)
const treeResult = ref(null)
const forwardResult = ref(null)
const conditionsResult = ref(null)
const loading = ref({})

const run = async (action) => {
  if (!smiles.value) return
  loading.value[action] = true
  try {
    if (action === 'retro') retroResult.value = await synthesisApi.retro({ smiles: smiles.value })
    else if (action === 'tree') treeResult.value = await synthesisApi.tree({ smiles: smiles.value })
    else if (action === 'forward') forwardResult.value = await synthesisApi.forward({ reactants: smiles.value })
  } catch (e) {
    console.error(e)
  } finally {
    loading.value[action] = false
  }
}
</script>

<template>
  <div>
    <PageHeader title="Synthesis Planning" />

    <div class="card mb-4">
      <div class="form-group">
        <label class="form-label">Target SMILES</label>
        <input v-model="smiles" class="form-control" placeholder="e.g. CC(=O)Oc1ccccc1C(=O)O" />
      </div>
      <div class="flex gap-2" style="flex-wrap:wrap">
        <button class="btn btn-primary" :disabled="loading.retro || !smiles" @click="run('retro')">
          {{ loading.retro ? 'Running...' : '⚗️ Single-Step Retro' }}
        </button>
        <button class="btn btn-secondary" :disabled="loading.tree || !smiles" @click="run('tree')">
          {{ loading.tree ? 'Running...' : '🌳 Multi-Step Tree' }}
        </button>
        <button class="btn btn-secondary" :disabled="loading.forward || !smiles" @click="run('forward')">
          {{ loading.forward ? 'Running...' : '→ Forward Prediction' }}
        </button>
      </div>
    </div>

    <div v-if="retroResult" class="card mb-4">
      <div class="card-title">Single-Step Retrosynthesis Results</div>
      <div v-if="retroResult.error" class="text-muted">{{ retroResult.error }}</div>
      <div v-else>
        <div v-for="(r, i) in (retroResult.results || []).slice(0, 5)" :key="i" class="card" style="padding:12px;margin-bottom:8px">
          <div class="flex items-center justify-between mb-2">
            <span class="font-bold text-sm">Precursor {{ i + 1 }}</span>
            <span class="badge badge-active">Score: {{ r.score?.toFixed(3) }}</span>
          </div>
          <code style="font-size:12px;word-break:break-all;display:block">{{ r.smiles || JSON.stringify(r).slice(0, 150) }}</code>
        </div>
      </div>
    </div>

    <div v-if="forwardResult" class="card mb-4">
      <div class="card-title">Forward Prediction Result</div>
      <div v-if="forwardResult.error" class="text-muted">{{ forwardResult.error }}</div>
      <pre v-else style="font-size:13px;overflow:auto">{{ JSON.stringify(forwardResult, null, 2).slice(0, 500) }}</pre>
    </div>

    <div v-if="treeResult" class="card">
      <div class="card-title">Multi-Step Retrosynthesis Tree</div>
      <div v-if="treeResult.error" class="text-muted">{{ treeResult.error }}</div>
      <pre v-else style="font-size:12px;overflow:auto;max-height:400px">{{ JSON.stringify(treeResult, null, 2).slice(0, 1000) }}</pre>
    </div>
  </div>
</template>
