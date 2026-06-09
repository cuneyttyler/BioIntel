import { defineStore } from 'pinia'

const LS_KEY = 'biointel_ai_panel_histories'
const MAX_MESSAGES_PER_PAGE = 50

function loadFromLS() {
  try {
    const raw = localStorage.getItem(LS_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

function saveToLS(histories) {
  try {
    localStorage.setItem(LS_KEY, JSON.stringify(histories))
  } catch { /* quota exceeded */ }
}

async function apiGet(projectId, pageType) {
  const r = await fetch(`/api/projects/${projectId}/panel-history/${pageType}/`)
  if (!r.ok) throw new Error(r.status)
  return r.json()
}

async function apiPost(projectId, pageType, role, content, suggestion) {
  await fetch(`/api/projects/${projectId}/panel-history/${pageType}/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
    body: JSON.stringify({ role, content, suggestion: suggestion ?? null }),
  })
}

async function apiDelete(projectId, pageType) {
  await fetch(`/api/projects/${projectId}/panel-history/${pageType}/`, {
    method: 'DELETE',
    headers: { 'X-CSRFToken': getCsrf() },
  })
}

function getCsrf() {
  return document.cookie.match(/csrftoken=([^;]+)/)?.[1] ?? ''
}

export const useAIPanelContextStore = defineStore('aiPanelContext', {
  state: () => ({
    chatHistories: loadFromLS(),   // key = `${projectId}_${pageType}`
    historyLoaded: {},             // tracks which keys have been fetched from DB
    currentPageType: null,
    currentProjectId: null,
    currentEntityData: {},
    pendingSuggestions: null,
    applyTrigger: 0,
  }),

  getters: {
    pageKey: (state) =>
      state.currentProjectId && state.currentPageType
        ? `${state.currentProjectId}_${state.currentPageType}`
        : null,

    currentMessages: (state) => {
      const key =
        state.currentProjectId && state.currentPageType
          ? `${state.currentProjectId}_${state.currentPageType}`
          : null
      return key ? (state.chatHistories[key] || []) : []
    },
  },

  actions: {
    setPageContext(pageType, projectId, entityData) {
      const changing = this.currentPageType !== pageType || this.currentProjectId !== projectId
      if (changing) {
        this.pendingSuggestions = null
        this._fetchFromDB(projectId, pageType)
      }
      this.currentPageType = pageType
      this.currentProjectId = projectId
      this.currentEntityData = entityData || {}
    },

    async _fetchFromDB(projectId, pageType) {
      const key = `${projectId}_${pageType}`
      if (this.historyLoaded[key]) return
      this.historyLoaded[key] = true
      try {
        const data = await apiGet(projectId, pageType)
        const messages = data.messages || []
        if (messages.length > 0) {
          this.chatHistories[key] = messages
          saveToLS(this.chatHistories)
        }
        // If DB is empty, keep whatever is already in localStorage (migration fallback)
      } catch { /* network error — silently use localStorage */ }
    },

    addMessage(role, content, suggestion = null) {
      const key = this.pageKey
      if (!key) return
      if (!this.chatHistories[key]) this.chatHistories[key] = []
      this.chatHistories[key].push({ role, content, suggestion, ts: Date.now() })
      if (this.chatHistories[key].length > MAX_MESSAGES_PER_PAGE) {
        this.chatHistories[key] = this.chatHistories[key].slice(-MAX_MESSAGES_PER_PAGE)
      }
      saveToLS(this.chatHistories)
      // Fire-and-forget DB write
      if (this.currentProjectId && this.currentPageType) {
        apiPost(this.currentProjectId, this.currentPageType, role, content, suggestion).catch(() => {})
      }
    },

    setSuggestions(fields) {
      this.pendingSuggestions = fields
    },

    triggerApply(selectedFields) {
      this.pendingSuggestions = selectedFields
      this.applyTrigger++
    },

    clearSuggestions() {
      this.pendingSuggestions = null
    },

    clearHistory(pageType, projectId) {
      const key = `${projectId}_${pageType}`
      delete this.chatHistories[key]
      delete this.historyLoaded[key]
      saveToLS(this.chatHistories)
      apiDelete(projectId, pageType).catch(() => {})
    },
  },
})
