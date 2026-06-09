import { defineStore } from 'pinia'
import { aiPlan as aiPlanApi, createSSEStream } from '@/services/api'

export const useAIPlanStore = defineStore('aiPlan', {
  state: () => ({
    plan: null,
    steps: [],
    discussions: {},
    streamingText: '',
    streamingStepId: null,
    isStreaming: false,
    generatingStep: 0,   // current step number being generated (plan-level)
    generatingTotal: 0,  // total steps to generate (plan-level)
    ragCitations: [],
    error: null,
  }),

  getters: {
    currentStep: (state) => {
      if (!state.plan?.current_step_number) return null
      return state.steps.find((s) => s.step_number === state.plan.current_step_number) || null
    },
    pendingSteps: (state) => state.steps.filter((s) => s.status === 'pending'),
    completedSteps: (state) => state.steps.filter((s) => s.status === 'completed'),
    activeSteps: (state) =>
      state.steps.filter((s) => !['abandoned', 'skipped'].includes(s.status)),
  },

  actions: {
    async fetchPlan(projectId) {
      try {
        const plan = await aiPlanApi.get(projectId)
        this.plan = plan
        this.steps = plan.steps || []
      } catch (e) {
        if (e?.status !== 404) this.error = e?.detail || 'Failed to load plan'
        this.plan = null
        this.steps = []
      }
    },

    async createPlan(projectId, data) {
      const plan = await aiPlanApi.create(projectId, data)
      this.plan = plan
      this.steps = plan.steps || []
      return plan
    },

    async fetchDiscussions(stepId) {
      const msgs = await aiPlanApi.getDiscussions(stepId)
      this.discussions[stepId] = msgs
    },

    async approveStep(stepId) {
      const step = await aiPlanApi.approveStep(stepId)
      this._updateStep(step)
      if (this.plan) {
        await this.fetchPlan(this.plan.project)
      }
    },

    async rejectStep(stepId, feedback = '') {
      const step = await aiPlanApi.rejectStep(stepId, feedback)
      this._updateStep(step)
    },

    async skipStep(stepId) {
      const step = await aiPlanApi.skipStep(stepId)
      this._updateStep(step)
      if (this.plan) await this.fetchPlan(this.plan.project)
    },

    async goBack(stepId, targetStepNumber) {
      const result = await aiPlanApi.goBack(stepId, targetStepNumber)
      if (this.plan) await this.fetchPlan(this.plan.project)
      return result
    },

    async executeAction(stepId, action) {
      const result = await aiPlanApi.executeAction(stepId, action.id, action.action_type, action.data)
      // Mark the action as applied in local state immediately
      const step = this.steps.find((s) => s.id === stepId)
      if (step?.suggested_actions) {
        step.suggested_actions = step.suggested_actions.map((a) =>
          a.id === action.id ? { ...a, applied: true } : a
        )
      }
      return result
    },

    async streamGenerate(planId) {
      this.isStreaming = true
      this.streamingText = ''
      this.streamingStepId = null
      this.generatingStep = 0
      this.generatingTotal = 0
      this.ragCitations = []
      this.error = null

      try {
        const stream = createSSEStream(`/api/ai-plans/${planId}/generate/`, { method: 'POST', body: {} })
        for await (const event of stream) {
          this._handleStreamEvent(event)
        }
      } catch (e) {
        this.error = e?.message || 'Streaming failed'
      } finally {
        this.isStreaming = false
        this.streamingStepId = null
        this.streamingText = ''
        this.generatingStep = 0
        this.generatingTotal = 0
        if (this.plan) await this.fetchPlan(this.plan.project)
      }
    },

    async streamRecommend(stepId) {
      this.isStreaming = true
      this.streamingStepId = stepId
      this.streamingText = ''
      this.ragCitations = []
      this.error = null

      const step = this.steps.find((s) => s.id === stepId)
      if (step) step.status = 'in_progress'

      try {
        const stream = createSSEStream(`/api/ai-plan-steps/${stepId}/recommend/`, { method: 'POST', body: {} })
        for await (const event of stream) {
          this._handleStreamEvent(event)
        }
      } catch (e) {
        this.error = e?.message || 'Streaming failed'
      } finally {
        this.isStreaming = false
        // Persist streamed text to step immediately so recommendation box shows without a blank flash
        if (this.streamingText) {
          const step = this.steps.find((s) => s.id === stepId)
          if (step) step.ai_reasoning = this.streamingText
        }
        this.streamingStepId = null
        // Refresh step from server to get canonical data
        try {
          const updated = await aiPlanApi.getStep(stepId)
          this._updateStep(updated)
        } catch {}
      }
    },

    async streamDiscuss(stepId, message) {
      this.isStreaming = true
      this.streamingText = ''
      this.ragCitations = []
      this.error = null

      if (!this.discussions[stepId]) this.discussions[stepId] = []
      this.discussions[stepId].push({ role: 'scientist', content: message, created_at: new Date().toISOString() })

      const responseChunks = []
      try {
        const stream = createSSEStream(`/api/ai-plan-steps/${stepId}/discuss/`, {
          method: 'POST',
          body: { message },
        })
        for await (const event of stream) {
          this._handleStreamEvent(event)
          if (event.type === 'text_delta') responseChunks.push(event.text)
        }
      } catch (e) {
        this.error = e?.message || 'Streaming failed'
      } finally {
        this.isStreaming = false
        const fullText = responseChunks.join('')
        if (fullText) {
          this.discussions[stepId].push({
            role: 'ai',
            content: fullText,
            created_at: new Date().toISOString(),
          })
        }
      }
    },

    async streamAnalyzeResults(stepId, results) {
      this.isStreaming = true
      this.streamingText = ''
      this.ragCitations = []
      this.error = null
      let action = null

      try {
        const stream = createSSEStream(`/api/ai-plan-steps/${stepId}/analyze-results/`, {
          method: 'POST',
          body: { results },
        })
        for await (const event of stream) {
          this._handleStreamEvent(event)
          if (event.type === 'result_action') action = event.action
        }
      } catch (e) {
        this.error = e?.message || 'Streaming failed'
      } finally {
        this.isStreaming = false
      }
      return action
    },

    _handleStreamEvent(event) {
      if (event.type === 'text_delta') {
        this.streamingText += event.text
      } else if (event.type === 'steps_reset') {
        this.steps = event.steps || []
        this.generatingTotal = event.total || event.steps?.length || 0
      } else if (event.type === 'plan_step') {
        // Progress update: backend is starting the next step
        this.generatingStep = event.current || event.step_number || 0
      } else if (event.type === 'tool_result') {
        // When update_plan_step succeeds, mark that step awaiting_approval in the UI immediately
        if (event.name === 'update_plan_step' && event.result?.step_id) {
          const step = this.steps.find((s) => s.id === event.result.step_id)
          if (step) step.status = event.result.status || 'awaiting_approval'
        }
      } else if (event.type === 'rag_citation') {
        this.ragCitations = event.chunks || []
      } else if (event.type === 'step_complete') {
        const step = this.steps.find((s) => s.id === event.step_id)
        if (step) {
          step.status = event.status
          if (this.streamingText && !step.ai_reasoning) {
            step.ai_reasoning = this.streamingText
          }
        }
      } else if (event.type === 'plan_complete') {
        // handled in finally
      }
    },

    _updateStep(updatedStep) {
      const idx = this.steps.findIndex((s) => s.id === updatedStep.id)
      if (idx !== -1) {
        const existing = this.steps[idx]
        // Never overwrite a populated ai_reasoning with an empty server value
        // (can happen if the server hasn't finished writing yet)
        if (!updatedStep.ai_reasoning && existing.ai_reasoning) {
          updatedStep = { ...updatedStep, ai_reasoning: existing.ai_reasoning }
        }
        this.steps[idx] = updatedStep
      }
    },

    reset() {
      this.plan = null
      this.steps = []
      this.discussions = {}
      this.streamingText = ''
      this.isStreaming = false
      this.ragCitations = []
      this.error = null
    },
  },
})
