<script setup>
import { ref, onMounted } from 'vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { excipients } from '@/services/api'

const results = ref([])
const loading = ref(false)
const query = ref('')
const routeFilter = ref('')
const functionFilter = ref('')

async function search() {
  loading.value = true
  try {
    results.value = await excipients.search({ q: query.value, route: routeFilter.value, function: functionFilter.value })
  } finally {
    loading.value = false
  }
}

onMounted(() => search())
</script>

<template>
  <div>
    <PageHeader title="Excipient Library">
      <template #subtitle>
        FDA IIG-based pharmaceutical excipient reference
      </template>
    </PageHeader>

    <div class="card mb-4">
      <div class="grid-3" style="gap:12px">
        <div class="form-group">
          <label>Search by Name</label>
          <input v-model="query" class="form-input" placeholder="cellulose, povidone..." @keyup.enter="search" />
        </div>
        <div class="form-group">
          <label>Route</label>
          <input v-model="routeFilter" class="form-input" placeholder="oral, parenteral..." @keyup.enter="search" />
        </div>
        <div class="form-group">
          <label>Function</label>
          <input v-model="functionFilter" class="form-input" placeholder="binder, lubricant..." @keyup.enter="search" />
        </div>
      </div>
      <button class="btn btn-primary" :disabled="loading" @click="search">Search</button>
    </div>

    <LoadingSpinner v-if="loading" />

    <div v-else-if="results.length" class="card">
      <h3 class="card-title">{{ results.length }} excipients</h3>
      <table class="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Function</th>
            <th>Route</th>
            <th>IIG Limit</th>
            <th>GRAS</th>
            <th>Incompatibilities</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="e in results" :key="e.id">
            <td><strong>{{ e.name }}</strong></td>
            <td>{{ e.function || '-' }}</td>
            <td>{{ e.route || '-' }}</td>
            <td>
              <span v-if="e.iig_limit">{{ e.iig_limit }} {{ e.iig_unit }}</span>
              <span v-else class="text-muted">-</span>
            </td>
            <td>
              <span v-if="e.gras_status === true" class="badge badge-success">GRAS</span>
              <span v-else-if="e.gras_status === false" class="badge badge-danger">Not GRAS</span>
              <span v-else class="text-muted">-</span>
            </td>
            <td>
              <span v-if="e.incompatibilities?.length" class="text-warning" style="font-size:12px">
                {{ e.incompatibilities.slice(0, 2).join(', ') }}{{ e.incompatibilities.length > 2 ? '...' : '' }}
              </span>
              <span v-else class="text-muted">None known</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <EmptyState v-else title="No results" message="Try a different search term." />
  </div>
</template>
