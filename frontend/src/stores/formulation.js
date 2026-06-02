import { defineStore } from 'pinia'
import { apiClient as api } from '../services/api'

export const useFormulationStore = defineStore('formulation', {
  state: () => ({
    plan: null,
    components: [],
    flags: [],
    excipientSearchResults: [],
    loading: {
      plan: false,
      components: false,
      compatibility: false,
      excipients: false,
    },
    error: null,
  }),

  getters: {
    criticalFlags: (state) => state.flags.filter(f => f.severity === 'critical'),
    warningFlags: (state) => state.flags.filter(f => f.severity === 'warning'),
    totalConcentration: (state) => {
      return state.components.reduce((sum, c) => sum + (parseFloat(c.concentration) || 0), 0)
    },
  },

  actions: {
    async fetchPlan(projectId) {
      this.loading.plan = true
      try {
        const plans = await api.formulation.getByProject(projectId)
        if (plans.length > 0) {
          this.plan = plans[0]
          this.components = this.plan.components || []
          this.flags = this.plan.compatibility_flags || []
        } else {
          this.plan = null
          this.components = []
          this.flags = []
        }
      } catch (e) {
        this.error = e.message || 'Failed to fetch formulation plan'
      } finally {
        this.loading.plan = false
      }
    },

    async savePlan(projectId, data) {
      this.loading.plan = true
      try {
        if (this.plan?.id) {
          this.plan = await api.formulation.update(this.plan.id, data)
        } else {
          this.plan = await api.formulation.create(projectId, data)
        }
        return this.plan
      } catch (e) {
        this.error = e.message
        throw e
      } finally {
        this.loading.plan = false
      }
    },

    async addComponent(data) {
      if (!this.plan) return
      this.loading.components = true
      try {
        const component = await api.formulation.addComponent(this.plan.id, data)
        this.components.push(component)
        return component
      } catch (e) {
        this.error = e.message
        throw e
      } finally {
        this.loading.components = false
      }
    },

    async removeComponent(componentId) {
      if (!this.plan) return
      try {
        await api.formulation.removeComponent(this.plan.id, componentId)
        this.components = this.components.filter(c => c.id !== componentId)
      } catch (e) {
        this.error = e.message
      }
    },

    async checkCompatibility() {
      if (!this.plan) return
      this.loading.compatibility = true
      try {
        const result = await api.formulation.checkCompatibility(this.plan.id)
        this.flags = result.total_flags || []
        return result
      } catch (e) {
        this.error = e.message
        throw e
      } finally {
        this.loading.compatibility = false
      }
    },

    async searchExcipients(query, route = '', functionType = '') {
      this.loading.excipients = true
      try {
        this.excipientSearchResults = await api.excipients.search({ q: query, route, function: functionType })
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading.excipients = false
      }
    },
  },
})
