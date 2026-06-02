import { defineStore } from 'pinia'
import { apiClient as api } from '../services/api'

export const useVirtualScreeningStore = defineStore('virtual_screening', {
  state: () => ({
    targetProfile: null,
    currentRun: null,
    hits: [],
    shortlisted: [],
    loading: {
      profile: false,
      run: false,
      hits: false,
      admet: false,
      patents: false,
    },
    error: null,
    pollInterval: null,
  }),

  getters: {
    isRunning: (state) => state.currentRun?.status === 'running' || state.currentRun?.status === 'pending',
    shortlistedHits: (state) => state.hits.filter(h => h.shortlisted),
  },

  actions: {
    async setupTarget(profileData) {
      this.loading.profile = true
      try {
        if (profileData.id) {
          this.targetProfile = profileData
        } else {
          this.targetProfile = await api.targets.createProfile(profileData)
        }
      } catch (e) {
        this.error = e.message || 'Failed to setup target'
      } finally {
        this.loading.profile = false
      }
    },

    async startScreening(library, customSmiles = null) {
      if (!this.targetProfile) return
      this.loading.run = true
      try {
        this.currentRun = await api.virtualScreening.createRun({
          target_profile: this.targetProfile.id,
          library,
          custom_smiles: customSmiles,
        })
        this.hits = []
        this._startPolling()
      } catch (e) {
        this.error = e.message || 'Failed to start screening'
      } finally {
        this.loading.run = false
      }
    },

    async pollStatus() {
      if (!this.currentRun) return
      try {
        const status = await api.virtualScreening.poll(this.currentRun.id)
        this.currentRun = { ...this.currentRun, ...status }
        if (status.status === 'complete') {
          this._stopPolling()
          await this.fetchHits()
        } else if (status.status === 'failed') {
          this._stopPolling()
        }
      } catch (e) {
        this.error = e.message
      }
    },

    async fetchHits() {
      if (!this.currentRun) return
      this.loading.hits = true
      try {
        this.hits = await api.virtualScreening.hits(this.currentRun.id)
        this.shortlisted = this.hits.filter(h => h.shortlisted)
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading.hits = false
      }
    },

    async checkADMET(hitIds) {
      this.loading.admet = true
      try {
        const smilesList = this.hits
          .filter(h => hitIds.includes(h.id))
          .map(h => h.smiles)
        const result = await api.analogs.admet(smilesList)
        const admetMap = {}
        if (result.predictions) {
          result.predictions.forEach((p, i) => { admetMap[smilesList[i]] = p })
        }
        this.hits = this.hits.map(h =>
          admetMap[h.smiles] ? { ...h, admet_data: admetMap[h.smiles] } : h
        )
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading.admet = false
      }
    },

    async checkPatents(hitIds) {
      this.loading.patents = true
      try {
        const candidates = this.hits
          .filter(h => hitIds.includes(h.id))
          .map(h => ({ smiles: h.smiles }))
        const result = await api.analogs.patentCheck(candidates)
        const patentMap = {}
        if (result.results) {
          result.results.forEach(r => { patentMap[r.smiles] = r })
        }
        this.hits = this.hits.map(h =>
          patentMap[h.smiles]
            ? { ...h, patent_status: patentMap[h.smiles].status, patent_refs: patentMap[h.smiles].refs }
            : h
        )
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading.patents = false
      }
    },

    async toggleShortlist(hit) {
      try {
        const updated = await api.virtualScreening.shortlistHit(hit.id, { shortlisted: !hit.shortlisted })
        this.hits = this.hits.map(h => h.id === hit.id ? updated : h)
        this.shortlisted = this.hits.filter(h => h.shortlisted)
      } catch (e) {
        this.error = e.message
      }
    },

    _startPolling() {
      this._stopPolling()
      this.pollInterval = setInterval(() => this.pollStatus(), 10000)
    },

    _stopPolling() {
      if (this.pollInterval) {
        clearInterval(this.pollInterval)
        this.pollInterval = null
      }
    },
  },
})
