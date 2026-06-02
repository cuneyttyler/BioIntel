import { defineStore } from 'pinia'
import { apiClient as api } from '../services/api'

export const useStabilityStore = defineStore('stability', {
  state: () => ({
    plan: null,
    conditions: [],
    results: {},
    loading: {
      plan: false,
      conditions: false,
      results: false,
    },
    error: null,
  }),

  getters: {
    oosResults: (state) => {
      return Object.values(state.results).flat().filter(r => r.oos_flag)
    },
    matrixData: (state) => {
      const matrix = {}
      state.conditions.forEach(cond => {
        matrix[cond.id] = {
          condition: cond,
          timepoints: state.results[cond.id] || [],
        }
      })
      return matrix
    },
  },

  actions: {
    async fetchPlan(projectId) {
      this.loading.plan = true
      try {
        const plans = await api.stability.getByProject(projectId)
        if (plans.length > 0) {
          this.plan = plans[0]
          this.conditions = this.plan.conditions || []
          await this.fetchResults()
        } else {
          this.plan = null
          this.conditions = []
          this.results = {}
        }
      } catch (e) {
        this.error = e.message || 'Failed to fetch stability plan'
      } finally {
        this.loading.plan = false
      }
    },

    async savePlan(projectId, data) {
      this.loading.plan = true
      try {
        if (this.plan?.id) {
          this.plan = await api.stability.update(this.plan.id, data)
        } else {
          this.plan = await api.stability.create(projectId, data)
          this.conditions = []
          this.results = {}
        }
        return this.plan
      } catch (e) {
        this.error = e.message
        throw e
      } finally {
        this.loading.plan = false
      }
    },

    async addCondition(data) {
      if (!this.plan) return
      try {
        const condition = await api.stability.addCondition(this.plan.id, data)
        this.conditions.push(condition)
        this.results[condition.id] = []
        return condition
      } catch (e) {
        this.error = e.message
        throw e
      }
    },

    async buildMatrix() {
      if (!this.plan) return
      this.loading.conditions = true
      try {
        const matrix = await api.stability.matrix(this.plan.id)
        this.results = {}
        if (matrix.matrix) {
          Object.entries(matrix.matrix).forEach(([label, data]) => {
            const cond = this.conditions.find(c => c.condition_label === label)
            if (cond) {
              this.results[cond.id] = Object.values(data.timepoints)
            }
          })
        }
        return matrix
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading.conditions = false
      }
    },

    async fetchResults() {
      if (!this.plan) return
      this.loading.results = true
      try {
        const allResults = await api.stability.results(this.plan.id)
        this.results = {}
        allResults.forEach(r => {
          if (!this.results[r.condition]) this.results[r.condition] = []
          this.results[r.condition].push(r)
        })
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading.results = false
      }
    },

    async logResult(conditionId, data) {
      if (!this.plan) return
      try {
        const result = await api.stability.logResult(this.plan.id, { condition_id: conditionId, ...data })
        if (!this.results[conditionId]) this.results[conditionId] = []
        this.results[conditionId].push(result)
        return result
      } catch (e) {
        this.error = e.message
        throw e
      }
    },
  },
})
