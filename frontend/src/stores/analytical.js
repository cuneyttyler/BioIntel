import { defineStore } from 'pinia'
import { apiClient as api } from '../services/api'

export const useAnalyticalStore = defineStore('analytical', {
  state: () => ({
    methods: [],
    specifications: [],
    currentMethod: null,
    validationStatus: null,
    loading: {
      methods: false,
      specs: false,
      validation: false,
    },
    error: null,
  }),

  getters: {
    byMethodType: (state) => {
      const groups = {}
      state.methods.forEach(m => {
        const type = m.method_type || 'other'
        if (!groups[type]) groups[type] = []
        groups[type].push(m)
      })
      return groups
    },
    releaseSpecs: (state) => state.specifications.filter(s => s.spec_type === 'release'),
    shelfLifeSpecs: (state) => state.specifications.filter(s => s.spec_type === 'shelf_life'),
  },

  actions: {
    async fetchMethods(projectId) {
      this.loading.methods = true
      try {
        this.methods = await api.analytical.list(projectId)
      } catch (e) {
        this.error = e.message || 'Failed to fetch analytical methods'
      } finally {
        this.loading.methods = false
      }
    },

    async createMethod(projectId, data) {
      try {
        const method = await api.analytical.create(projectId, data)
        this.methods.unshift(method)
        return method
      } catch (e) {
        this.error = e.message
        throw e
      }
    },

    async updateMethod(id, data) {
      try {
        const updated = await api.analytical.update(id, data)
        this.methods = this.methods.map(m => m.id === id ? updated : m)
        if (this.currentMethod?.id === id) this.currentMethod = updated
        return updated
      } catch (e) {
        this.error = e.message
        throw e
      }
    },

    async deleteMethod(id) {
      try {
        await api.analytical.delete(id)
        this.methods = this.methods.filter(m => m.id !== id)
        if (this.currentMethod?.id === id) {
          this.currentMethod = this.methods[0] || null
          this.validationStatus = null
        }
      } catch (e) {
        this.error = e.message
      }
    },

    async fetchValidationStatus(methodId) {
      this.loading.validation = true
      try {
        this.validationStatus = await api.analytical.validation(methodId)
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading.validation = false
      }
    },

    async fetchSpecifications(projectId) {
      this.loading.specs = true
      try {
        this.specifications = await api.specifications.list(projectId)
      } catch (e) {
        this.error = e.message || 'Failed to fetch specifications'
      } finally {
        this.loading.specs = false
      }
    },

    async saveSpecification(projectId, data) {
      try {
        if (data.id) {
          const updated = await api.specifications.update(data.id, data)
          this.specifications = this.specifications.map(s => s.id === data.id ? updated : s)
          return updated
        } else {
          const spec = await api.specifications.create(projectId, data)
          this.specifications.push(spec)
          return spec
        }
      } catch (e) {
        this.error = e.message
        throw e
      }
    },

    async deleteSpecification(id) {
      try {
        await api.specifications.delete(id)
        this.specifications = this.specifications.filter(s => s.id !== id)
      } catch (e) {
        this.error = e.message
      }
    },
  },
})
