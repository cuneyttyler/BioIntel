import { defineStore } from 'pinia'
import { drugs as drugsApi } from '@/services/api'

export const useDrugsStore = defineStore('drugs', {
  state: () => ({
    searchResults: [],
    selectedDrug: null,
    profile: {
      detail: null,
      synthesis: [],
      trials: [],
      patents: [],
    },
    loading: {
      search: false,
      detail: false,
      synthesis: false,
      trials: false,
      patents: false,
    },
    error: null,
  }),

  actions: {
    async searchDrugs(q) {
      if (!q) { this.searchResults = []; return }
      this.loading.search = true
      try {
        this.searchResults = await drugsApi.search(q)
      } catch (e) {
        this.error = e
        this.searchResults = []
      } finally {
        this.loading.search = false
      }
    },

    async loadProfile(chemblId) {
      this.profile = { detail: null, synthesis: [], trials: [], patents: [] }
      this.loading.detail = true
      this.loading.synthesis = true
      this.loading.trials = true
      this.loading.patents = true

      const [detail, synthesis, trials, patents] = await Promise.allSettled([
        drugsApi.get(chemblId),
        drugsApi.synthesis(chemblId),
        drugsApi.trials(chemblId),
        drugsApi.patents(chemblId),
      ])

      this.profile.detail = detail.status === 'fulfilled' ? detail.value : null
      this.profile.synthesis = synthesis.status === 'fulfilled' ? synthesis.value : []
      this.profile.trials = trials.status === 'fulfilled' ? trials.value : []
      this.profile.patents = patents.status === 'fulfilled' ? patents.value : []

      this.loading.detail = false
      this.loading.synthesis = false
      this.loading.trials = false
      this.loading.patents = false
    },
  },
})
