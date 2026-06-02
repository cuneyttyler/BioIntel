import { defineStore } from 'pinia'
import { apiClient as api } from '../services/api'

export const useSARStore = defineStore('sar', {
  state: () => ({
    entries: [],
    heatmapData: null,
    loading: false,
    error: null,
  }),

  getters: {
    byActivityType: (state) => {
      const groups = {}
      state.entries.forEach(e => {
        const type = e.activity_type || 'other'
        if (!groups[type]) groups[type] = []
        groups[type].push(e)
      })
      return groups
    },
  },

  actions: {
    async fetchEntries(projectId) {
      this.loading = true
      try {
        this.entries = await api.sar.list(projectId)
      } catch (e) {
        this.error = e.message || 'Failed to fetch SAR entries'
      } finally {
        this.loading = false
      }
    },

    async addEntry(data) {
      try {
        const entry = await api.sar.create(data)
        this.entries.unshift(entry)
        return entry
      } catch (e) {
        this.error = e.message || 'Failed to add SAR entry'
        throw e
      }
    },

    async updateEntry(id, data) {
      try {
        const updated = await api.sar.update(id, data)
        this.entries = this.entries.map(e => e.id === id ? updated : e)
        return updated
      } catch (e) {
        this.error = e.message
        throw e
      }
    },

    async deleteEntry(id) {
      try {
        await api.sar.delete(id)
        this.entries = this.entries.filter(e => e.id !== id)
      } catch (e) {
        this.error = e.message
      }
    },

    async fetchHeatmap(projectId) {
      try {
        this.heatmapData = await api.sar.heatmap(projectId)
      } catch (e) {
        this.error = e.message
      }
    },
  },
})
