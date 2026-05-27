import { defineStore } from 'pinia'
import { experiments as experimentsApi } from '@/services/api'

export const useExperimentStore = defineStore('experiments', {
  state: () => ({
    experiments: [],
    recentExperiments: [],
    currentExperiment: null,
    results: [],
    loading: false,
    error: null,
  }),

  actions: {
    async fetchRecent() {
      this.loading = true
      try {
        this.recentExperiments = await experimentsApi.recent()
      } catch (e) {
        this.error = e
      } finally {
        this.loading = false
      }
    },

    async fetchByProject(projectId) {
      this.loading = true
      try {
        this.experiments = await experimentsApi.list(projectId)
      } catch (e) {
        this.error = e
      } finally {
        this.loading = false
      }
    },

    async fetchExperiment(id) {
      this.loading = true
      try {
        this.currentExperiment = await experimentsApi.get(id)
        this.results = await experimentsApi.results(id)
      } catch (e) {
        this.error = e
      } finally {
        this.loading = false
      }
    },

    async createExperiment(data) {
      const exp = await experimentsApi.create(data)
      this.experiments.unshift(exp)
      return exp
    },

    async submitResults(expId, data) {
      const result = await experimentsApi.logResult(expId, data)
      this.results.unshift(result)
      return result
    },
  },
})
