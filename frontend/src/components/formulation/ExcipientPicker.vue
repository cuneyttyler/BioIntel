<script setup>
import { ref } from 'vue'
import { excipients } from '@/services/api'

const emit = defineEmits(['select'])

const query = ref('')
const results = ref([])
const loading = ref(false)

async function search() {
  if (!query.value.trim()) return
  loading.value = true
  try {
    results.value = await excipients.search({ q: query.value })
  } finally {
    loading.value = false
  }
}

function select(e) {
  emit('select', e)
  query.value = ''
  results.value = []
}
</script>

<template>
  <div>
    <div style="display:flex;gap:8px;margin-bottom:8px">
      <input v-model="query" class="form-input" placeholder="Search excipient..." @keyup.enter="search" style="flex:1" />
      <button class="btn btn-secondary" :disabled="loading" @click="search">Search</button>
    </div>
    <div v-if="results.length" style="border:1px solid #e5e7eb;border-radius:6px;max-height:200px;overflow-y:auto">
      <div
        v-for="e in results" :key="e.id"
        class="list-item"
        style="cursor:pointer;padding:8px 12px"
        @click="select(e)"
      >
        <strong>{{ e.name }}</strong>
        <span class="text-muted" style="font-size:12px;margin-left:8px">{{ e.function }} · {{ e.route }}</span>
      </div>
    </div>
  </div>
</template>
