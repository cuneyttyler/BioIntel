import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

const api = axios.create({ baseURL: '/api' })
api.interceptors.response.use((r) => r.data, (err) => Promise.reject(err.response?.data || err.message))

export const useSettingsStore = defineStore('settings', () => {
  const provider = ref('claude')
  const model = ref('claude-sonnet-4-6')
  const anthropicApiKey = ref('')
  const openaiApiKey = ref('')
  const mistralApiKey = ref('')
  const customEndpoint = ref('')
  const customApiKey = ref('')
  const loading = ref(false)
  const saving = ref(false)
  const loaded = ref(false)

  async function fetch() {
    loading.value = true
    try {
      const data = await api.get('/api/settings/')
      provider.value = data.provider
      model.value = data.model
      anthropicApiKey.value = data.anthropic_api_key
      openaiApiKey.value = data.openai_api_key
      mistralApiKey.value = data.mistral_api_key
      customEndpoint.value = data.custom_endpoint
      customApiKey.value = data.custom_api_key
      loaded.value = true
    } finally {
      loading.value = false
    }
  }

  async function save(payload) {
    saving.value = true
    try {
      await api.put('/api/settings/', payload)
    } finally {
      saving.value = false
    }
  }

  return {
    provider, model,
    anthropicApiKey, openaiApiKey, mistralApiKey,
    customEndpoint, customApiKey,
    loading, saving, loaded,
    fetch, save,
  }
})
