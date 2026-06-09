<template>
  <div class="discussion-panel">
    <div class="messages" ref="messagesEl">
      <div
        v-for="(msg, i) in allMessages"
        :key="i"
        class="message"
        :class="msg.role"
      >
        <div class="role-label">{{ msg.role === 'ai' ? 'BioIntel AI' : 'You' }}</div>
        <div class="content" v-html="renderMarkdown(msg.content)" />
        <div v-if="msg.sources?.length" class="sources">
          <span v-for="src in msg.sources" :key="src" class="source-tag">{{ src }}</span>
        </div>
      </div>

      <div v-if="isStreaming && streamingText" class="message ai streaming">
        <div class="role-label">BioIntel AI</div>
        <div class="content" v-html="renderMarkdown(streamingText)" />
        <span class="cursor" />
      </div>

      <div v-if="ragCitations.length" class="rag-citations">
        <div class="citations-header">References retrieved</div>
        <div v-for="(c, i) in ragCitations" :key="i" class="citation">
          <span class="citation-num">[{{ i + 1 }}]</span>
          <span class="citation-doc">{{ c.document }}</span>
          <span class="citation-score">{{ (c.score * 100).toFixed(0) }}%</span>
        </div>
      </div>
    </div>

    <div class="input-row">
      <textarea
        v-model="input"
        :placeholder="placeholder"
        :disabled="isStreaming"
        rows="3"
        @keydown.ctrl.enter="send"
        @keydown.meta.enter="send"
      />
      <button class="btn-send" :disabled="isStreaming || !input.trim()" @click="send">
        {{ isStreaming ? '…' : 'Send' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, computed } from 'vue'
import { useAIPlanStore } from '@/stores/aiPlan'

const props = defineProps({
  stepId: { type: Number, required: true },
  placeholder: { type: String, default: 'Ask a question or provide feedback… (Ctrl+Enter to send)' },
})

const planStore = useAIPlanStore()
const messagesEl = ref(null)
const input = ref('')

const allMessages = computed(() => planStore.discussions[props.stepId] || [])
const isStreaming = computed(() => planStore.isStreaming)
const streamingText = computed(() => planStore.streamingText)
const ragCitations = computed(() => planStore.ragCitations)

watch(
  () => [allMessages.value.length, isStreaming.value],
  () => nextTick(() => {
    if (messagesEl.value) {
      messagesEl.value.scrollTop = messagesEl.value.scrollHeight
    }
  }),
)

async function send() {
  const msg = input.value.trim()
  if (!msg || isStreaming.value) return
  input.value = ''
  await planStore.streamDiscuss(props.stepId, msg)
}

function renderMarkdown(text) {
  if (!text) return ''
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\[Source:(.*?)\]/g, '<span class="source-inline">[Source:$1]</span>')
    .replace(/\n/g, '<br>')
}
</script>

<style scoped>
.discussion-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 12px;
}
.messages {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 4px;
}
.message {
  padding: 10px 14px;
  border-radius: 8px;
  max-width: 90%;
}
.message.scientist {
  background: #eff6ff;
  align-self: flex-end;
  border: 1px solid #bfdbfe;
}
.message.ai {
  background: #f9fafb;
  align-self: flex-start;
  border: 1px solid #e5e7eb;
}
.message.streaming { opacity: 0.9; }
.role-label {
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 4px;
  text-transform: uppercase;
}
.content { font-size: 14px; line-height: 1.6; }
.cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  background: #374151;
  margin-left: 2px;
  animation: blink 1s step-end infinite;
}
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
.sources { margin-top: 6px; display: flex; flex-wrap: wrap; gap: 4px; }
.source-tag {
  font-size: 10px;
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  color: #6b7280;
}
.rag-citations {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 8px 12px;
  background: #fafafa;
  font-size: 12px;
}
.citations-header { font-weight: 600; color: #374151; margin-bottom: 6px; }
.citation { display: flex; gap: 8px; margin-bottom: 2px; color: #6b7280; }
.citation-num { font-weight: 600; color: #374151; }
.citation-score { margin-left: auto; color: #9ca3af; }
.input-row { display: flex; gap: 8px; }
textarea {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  resize: none;
  font-family: inherit;
}
textarea:focus { outline: none; border-color: #3b82f6; }
.btn-send {
  padding: 8px 18px;
  background: #3b82f6;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  align-self: flex-end;
}
.btn-send:disabled { opacity: 0.5; cursor: not-allowed; }
:deep(.source-inline) { color: #2563eb; font-size: 12px; }
</style>
