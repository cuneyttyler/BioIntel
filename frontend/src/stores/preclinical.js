import { defineStore } from 'pinia'
import { apiClient as api } from '../services/api'

export const usePreclinicalStore = defineStore('preclinical', {
  state: () => ({
    studies: [],
    admetData: null,
    benchmarks: {},
    loading: {
      studies: false,
      admet: false,
    },
    error: null,
  }),

  getters: {
    completedStudies: (state) => state.studies.filter(s => s.status === 'complete' || s.status === 'reported'),
    studyByType: (state) => {
      const groups = {}
      state.studies.forEach(s => {
        if (!groups[s.study_type]) groups[s.study_type] = []
        groups[s.study_type].push(s)
      })
      return groups
    },
  },

  actions: {
    async fetchStudies(projectId) {
      this.loading.studies = true
      try {
        this.studies = await api.preclinical.list(projectId)
      } catch (e) {
        this.error = e.message || 'Failed to fetch preclinical studies'
      } finally {
        this.loading.studies = false
      }
    },

    async createStudy(projectId, data) {
      try {
        const study = await api.preclinical.create(projectId, data)
        this.studies.unshift(study)
        return study
      } catch (e) {
        this.error = e.message
        throw e
      }
    },

    async updateStudy(id, data) {
      try {
        const updated = await api.preclinical.update(id, data)
        this.studies = this.studies.map(s => s.id === id ? updated : s)
        return updated
      } catch (e) {
        this.error = e.message
        throw e
      }
    },

    async fetchStudy(id) {
      try {
        const study = await api.preclinical.get(id)
        this.studies = this.studies.map(s => s.id === id ? study : s)
        return study
      } catch (e) {
        this.error = e.message
      }
    },

    async deleteStudy(id) {
      try {
        await api.preclinical.delete(id)
        this.studies = this.studies.filter(s => s.id !== id)
      } catch (e) {
        this.error = e.message
        throw e
      }
    },

    async logResults(studyId, data) {
      try {
        const updated = await api.preclinical.logResults(studyId, data)
        this.studies = this.studies.map(s => s.id === studyId ? updated : s)
        return updated
      } catch (e) {
        this.error = e.message
        throw e
      }
    },

    async fetchADMETDashboard(projectId) {
      this.loading.admet = true
      try {
        this.admetData = await api.preclinical.admetDashboard(projectId)
      } catch (e) {
        this.error = e.message || 'Failed to fetch ADMET dashboard'
      } finally {
        this.loading.admet = false
      }
    },

    setBenchmark(property, value) {
      this.benchmarks[property] = value
    },
  },
})
