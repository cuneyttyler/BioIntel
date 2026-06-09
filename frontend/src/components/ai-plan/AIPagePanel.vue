<template>
  <transition name="panel-slide">
    <div v-if="open" class="ai-panel">
      <!-- Header -->
      <div class="panel-header">
        <div class="panel-title">
          <span class="panel-icon">✦</span>
          AI Assistant
          <span v-if="pageLabel" class="page-label">· {{ pageLabel }}</span>
        </div>
        <div class="header-actions">
          <button class="clear-btn" title="Clear chat" @click="clearChat">↺</button>
          <button class="collapse-btn" @click="$emit('close')">✕</button>
        </div>
      </div>

      <!-- Messages -->
      <div class="panel-messages" ref="messagesEl">
        <div v-if="messages.length === 0" class="empty-hint">
          Ask me anything about this page — I can suggest values for the form fields.
        </div>

        <template v-for="(msg, i) in messages" :key="i">
          <div class="panel-message" :class="msg.role">
            <div class="role-label">{{ msg.role === 'assistant' ? 'BioIntel AI' : 'You' }}</div>
            <div class="content" v-html="renderMarkdown(msg.content)" />
          </div>
          <SuggestionCard
            v-if="msg.role === 'assistant' && msg.suggestion"
            :fields="msg.suggestion"
            :page-type="pageType"
            @apply="handleApply"
            @dismiss="dismissSuggestion(i)"
          />
        </template>

        <!-- Streaming in progress -->
        <div v-if="isStreaming" class="panel-message assistant streaming">
          <div class="role-label">BioIntel AI</div>
          <div class="content" v-html="renderMarkdown(streamingText)" />
          <span class="cursor" />
        </div>

        <!-- RAG citations -->
        <div v-if="ragCitations.length" class="rag-bar">
          <span v-for="(c, i) in ragCitations" :key="i" class="rag-pill">{{ c.document }}</span>
        </div>
      </div>

      <!-- Input -->
      <div class="panel-input">
        <textarea
          v-model="input"
          :disabled="isStreaming"
          placeholder="Ask about this page… (Ctrl+Enter to send)"
          rows="3"
          @keydown.ctrl.enter="send"
          @keydown.meta.enter="send"
        />
        <button class="send-btn" :disabled="isStreaming || !input.trim()" @click="send">
          {{ isStreaming ? '…' : '↑' }}
        </button>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { createSSEStream } from '@/services/api'
import { useAIPanelContextStore } from '@/stores/aiPanelContext'
import { PAGE_FIELD_SCHEMAS } from '@/services/aiPageContexts'
import SuggestionCard from './SuggestionCard.vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  projectId: { type: Number, required: true },
  pageType: { type: String, default: 'unknown' },
  pageEntity: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['close'])

const panelCtx = useAIPanelContextStore()

// Messages are backed by the store — per-page, persisted across navigation
const messages = computed(() => panelCtx.currentMessages)

const pageLabel = computed(() => PAGE_FIELD_SCHEMAS[props.pageType]?.label || null)

const input = ref('')
const isStreaming = ref(false)
const streamingText = ref('')
const ragCitations = ref([])
const messagesEl = ref(null)

// Scroll to bottom on new message
watch(
  () => messages.value.length,
  () => nextTick(() => {
    if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }),
)

// When the panel opens, scroll to bottom of existing history
watch(
  () => props.open,
  (val) => {
    if (val) nextTick(() => {
      if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
    })
  },
)

const sessionMessages = computed(() =>
  messages.value.map((m) => ({ role: m.role, content: m.content })),
)

function clearChat() {
  panelCtx.clearHistory(props.pageType, props.projectId)
}

async function send() {
  const msg = input.value.trim()
  if (!msg || isStreaming.value) return

  panelCtx.addMessage('user', msg)
  input.value = ''
  isStreaming.value = true
  streamingText.value = ''
  ragCitations.value = []

  const chunks = []
  try {
    const stream = createSSEStream(`/api/projects/${props.projectId}/ai-panel/chat/`, {
      method: 'POST',
      body: {
        message: msg,
        page_type: props.pageType,
        page_entity: panelCtx.currentEntityData,
        session_messages: sessionMessages.value.slice(-20), // last 20 to cap context
      },
    })

    for await (const event of stream) {
      if (event.type === 'text_delta') {
        streamingText.value += event.text
        chunks.push(event.text)
        nextTick(() => {
          if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
        })
      } else if (event.type === 'rag_citation') {
        ragCitations.value = event.chunks || []
      }
    }
  } finally {
    isStreaming.value = false
    const fullText = chunks.join('')
    if (fullText) {
      const { displayText, suggestion } = parseSuggestion(fullText)
      panelCtx.addMessage('assistant', displayText, suggestion)
    }
    streamingText.value = ''
  }
}

function parseSuggestion(text) {
  const match = text.match(/<suggestion>([\s\S]*?)<\/suggestion>/i)
  if (!match) return { displayText: text.trim(), suggestion: null }

  let suggestion = null
  try {
    suggestion = JSON.parse(match[1].trim())
  } catch {
    // malformed JSON — ignore suggestion
  }
  const displayText = text.replace(/<suggestion>[\s\S]*?<\/suggestion>/i, '').trim()
  return { displayText, suggestion }
}

function handleApply(selectedFields) {
  panelCtx.triggerApply(selectedFields)
}

function dismissSuggestion(msgIndex) {
  // Nullify the suggestion on that message so the card disappears
  const msg = panelCtx.currentMessages[msgIndex]
  if (msg) msg.suggestion = null
}

function renderMarkdown(text) {
  if (!text) return ''
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\[Source:(.*?)\]/g, '<span class="src">[Source:$1]</span>')
    .replace(/\n/g, '<br>')
}
</script>

<style scoped>
.ai-panel {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-left: 1px solid #e5e7eb;
  box-shadow: -2px 0 8px rgba(0,0,0,0.06);
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
  flex-shrink: 0;
}
.panel-title {
  display: flex;
  align-items: center;
  gap: 5px;
  font-weight: 700;
  font-size: 13px;
  min-width: 0;
}
.panel-icon { color: #3b82f6; flex-shrink: 0; }
.page-label {
  font-size: 11px;
  font-weight: 400;
  color: #6b7280;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.header-actions { display: flex; gap: 6px; align-items: center; }
.clear-btn, .collapse-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #9ca3af;
  font-size: 14px;
  padding: 0;
  line-height: 1;
}
.clear-btn:hover, .collapse-btn:hover { color: #374151; }

.panel-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.empty-hint {
  font-size: 12px;
  color: #9ca3af;
  text-align: center;
  padding: 24px 12px;
  line-height: 1.6;
}

.panel-message {
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.6;
}
.panel-message.user {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  align-self: flex-end;
  max-width: 88%;
}
.panel-message.assistant {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  align-self: flex-start;
  max-width: 98%;
}
.role-label {
  font-size: 10px;
  font-weight: 600;
  color: #9ca3af;
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  background: #374151;
  margin-left: 2px;
  animation: blink 1s step-end infinite;
}
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

.rag-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 4px 0;
}
.rag-pill {
  font-size: 10px;
  background: #eff6ff;
  color: #2563eb;
  padding: 2px 7px;
  border-radius: 8px;
  border: 1px solid #bfdbfe;
}

.panel-input {
  padding: 10px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}
textarea {
  flex: 1;
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 12px;
  resize: none;
  font-family: inherit;
  line-height: 1.5;
}
textarea:focus { outline: none; border-color: #3b82f6; }
.send-btn {
  width: 34px;
  height: 34px;
  background: #3b82f6;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  cursor: pointer;
  align-self: flex-end;
  flex-shrink: 0;
}
.send-btn:disabled { opacity: 0.45; cursor: not-allowed; }

.panel-slide-enter-active,
.panel-slide-leave-active { transition: transform 0.2s ease; }
.panel-slide-enter-from,
.panel-slide-leave-to { transform: translateX(100%); }

:deep(.src) { color: #2563eb; font-size: 11px; }
:deep(code) {
  background: #f3f4f6;
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 11px;
}
</style>
