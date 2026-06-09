import { defineStore } from 'pinia'
import { ragDocuments as ragApi } from '@/services/api'

export const useDocumentsStore = defineStore('documents', {
  state: () => ({
    documents: [],
    searchResults: [],
    isLoading: false,
    isSearching: false,
    error: null,
  }),

  actions: {
    async fetchDocuments(params = {}) {
      this.isLoading = true
      this.error = null
      try {
        this.documents = await ragApi.list(params)
      } catch (e) {
        this.error = e?.detail || 'Failed to load documents'
      } finally {
        this.isLoading = false
      }
    },

    async uploadDocument(formData) {
      this.isLoading = true
      this.error = null
      try {
        const response = await fetch('/api/documents/', {
          method: 'POST',
          body: formData,
        })
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        const doc = await response.json()
        this.documents.unshift(doc)
        return doc
      } catch (e) {
        this.error = e?.message || 'Upload failed'
        throw e
      } finally {
        this.isLoading = false
      }
    },

    async deleteDocument(id) {
      await ragApi.delete(id)
      this.documents = this.documents.filter((d) => d.id !== id)
    },

    async reIngest(id) {
      const result = await ragApi.ingest(id)
      const idx = this.documents.findIndex((d) => d.id === id)
      if (idx !== -1) {
        this.documents[idx] = { ...this.documents[idx], ...result }
      }
      return result
    },

    async search(query, params = {}) {
      this.isSearching = true
      this.error = null
      try {
        const result = await ragApi.search({ q: query, ...params })
        this.searchResults = result.results || []
      } catch (e) {
        this.error = e?.detail || 'Search failed'
        this.searchResults = []
      } finally {
        this.isSearching = false
      }
    },

    clearSearch() {
      this.searchResults = []
    },
  },
})
