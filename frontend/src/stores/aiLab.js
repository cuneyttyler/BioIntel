import { defineStore } from 'pinia'
import { aiLab as aiLabApi, createSSEStream } from '@/services/api'

export const useAILabStore = defineStore('aiLab', {
  state: () => ({
    sessions: [],
    currentSession: null,
    messages: [],
    proposal: null,
    streamingText: '',
    isStreaming: false,
    error: null,
  }),

  actions: {
    async fetchSessions() {
      this.sessions = await aiLabApi.sessions()
    },

    async createSession() {
      const session = await aiLabApi.createSession({ title: 'New AI Lab Session' })
      this.sessions.unshift(session)
      this.currentSession = session
      this.messages = []
      this.proposal = null
      return session
    },

    async loadSession(id) {
      const session = await aiLabApi.getSession(id)
      this.currentSession = session
      this.messages = session.messages || []
      this.proposal = session.proposal && Object.keys(session.proposal).length ? session.proposal : null
    },

    async sendMessage(sessionId, message) {
      this.messages.push({ role: 'user', content: message })
      this.streamingText = ''
      this.isStreaming = true
      this.error = null

      const responseChunks = []
      try {
        const stream = createSSEStream(`/api/ai-lab/sessions/${sessionId}/messages/`, {
          method: 'POST',
          body: { message },
        })

        for await (const event of stream) {
          if (event.type === 'text_delta') {
            this.streamingText += event.text
            responseChunks.push(event.text)
          } else if (event.type === 'proposal') {
            this.proposal = event.proposal
          }
        }
      } catch (e) {
        this.error = e?.message || 'Streaming failed'
      } finally {
        this.isStreaming = false
        const fullText = responseChunks.join('')
        if (fullText) {
          this.messages.push({ role: 'assistant', content: fullText })
        }
        this.streamingText = ''
      }
    },

    async createProject(sessionId, overrides = {}) {
      const result = await aiLabApi.createProject(sessionId, overrides)
      if (this.currentSession) {
        this.currentSession.status = 'completed'
      }
      return result
    },

    reset() {
      this.currentSession = null
      this.messages = []
      this.proposal = null
      this.streamingText = ''
      this.isStreaming = false
      this.error = null
    },
  },
})
