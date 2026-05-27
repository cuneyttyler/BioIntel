import { defineStore } from 'pinia'
import { chat as chatApi, createSSEStream } from '@/services/api'

export const useChatStore = defineStore('chat', {
  state: () => ({
    sessions: [],
    currentSession: null,
    messages: [],
    streamingText: '',
    isStreaming: false,
    toolCalls: [],
    sources: [],
    error: null,
  }),

  actions: {
    async fetchSessions(projectId = null) {
      this.sessions = await chatApi.sessions(projectId)
    },

    async loadSession(id) {
      const session = await chatApi.session(id)
      this.currentSession = session
      this.messages = session.messages || []
      this.streamingText = ''
      this.toolCalls = []
      this.sources = []
    },

    async createSession(data) {
      const session = await chatApi.createSession(data)
      this.sessions.unshift(session)
      this.currentSession = session
      this.messages = []
      return session
    },

    async deleteSession(id) {
      await chatApi.deleteSession(id)
      this.sessions = this.sessions.filter((s) => s.id !== id)
      if (this.currentSession?.id === id) {
        this.currentSession = null
        this.messages = []
      }
    },

    async sendMessage(sessionId, content) {
      this.messages.push({ role: 'user', content, created_at: new Date().toISOString() })
      this.streamingText = ''
      this.toolCalls = []
      this.sources = []
      this.isStreaming = true
      this.error = null

      try {
        const stream = createSSEStream(`/api/chat/sessions/${sessionId}/messages/`, {
          method: 'POST',
          body: { content },
        })

        for await (const event of stream) {
          if (event.type === 'text_delta') {
            this.streamingText += event.text
          } else if (event.type === 'tool_use') {
            this.toolCalls.push({ type: 'use', name: event.name, input: event.input })
          } else if (event.type === 'tool_result') {
            this.toolCalls.push({ type: 'result', name: event.name })
          } else if (event.type === 'sources') {
            this.sources = event.sources || []
          } else if (event.type === 'message_stop') {
            this.messages.push({
              role: 'assistant',
              content: this.streamingText,
              sources: this.sources,
              created_at: new Date().toISOString(),
            })
            this.streamingText = ''
          }
        }
      } catch (e) {
        this.error = e
      } finally {
        this.isStreaming = false
      }
    },
  },
})
