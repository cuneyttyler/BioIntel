<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useProjectStore } from '@/stores/projects'
import { useUIStore } from '@/stores/ui'
import PageHeader from '@/components/layout/PageHeader.vue'
import MarkdownRenderer from '@/components/common/MarkdownRenderer.vue'
import StreamingIndicator from '@/components/common/StreamingIndicator.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const chatStore = useChatStore()
const projectStore = useProjectStore()
const ui = useUIStore()

const messageInput = ref('')
const messagesEl = ref(null)
const selectedProject = ref(null)

const suggestedQueries = [
  'What are the key ADMET risks for my compound?',
  'Summarize recent clinical trials for type 2 diabetes',
  'What FDA guidance documents apply to process validation?',
  'Suggest a synthesis route for aspirin',
  'What are common excipients for oral solid dosage forms?',
  'Explain the ICH Q8 pharmaceutical development guidelines',
]

onMounted(async () => {
  await projectStore.fetchProjects()
  await chatStore.fetchSessions()
})

watch(() => chatStore.streamingText, async () => {
  await nextTick()
  if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
})

const createSession = async () => {
  await chatStore.createSession({
    title: 'New Chat',
    project: selectedProject.value || null,
  })
}

const sendMessage = async () => {
  const content = messageInput.value.trim()
  if (!content || chatStore.isStreaming) return
  messageInput.value = ''
  if (!chatStore.currentSession) {
    await createSession()
  }
  await chatStore.sendMessage(chatStore.currentSession.id, content)
  await nextTick()
  if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
}

const deleteSession = async (id) => {
  const ok = await ui.showConfirm({ title: 'Delete session?', message: 'This will permanently delete this chat session.', confirmLabel: 'Delete' })
  if (ok) await chatStore.deleteSession(id)
}
</script>

<template>
  <div style="display:flex;height:calc(100vh - 56px);overflow:hidden">
    <!-- Session sidebar -->
    <div style="width:260px;flex-shrink:0;border-right:1px solid var(--border);background:var(--surface);display:flex;flex-direction:column;overflow:hidden">
      <div style="padding:12px;border-bottom:1px solid var(--border)">
        <div class="form-group" style="margin-bottom:8px">
          <select v-model="selectedProject" class="form-control">
            <option :value="null">No project</option>
            <option v-for="p in projectStore.projects" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
        </div>
        <button class="btn btn-primary w-full" @click="createSession">+ New Session</button>
      </div>
      <div style="flex:1;overflow-y:auto">
        <div
          v-for="s in chatStore.sessions"
          :key="s.id"
          :style="`padding:10px 12px;cursor:pointer;border-bottom:1px solid var(--border);background:${chatStore.currentSession?.id === s.id ? 'var(--primary-light)' : ''}`"
          @click="chatStore.loadSession(s.id)"
        >
          <div class="font-bold text-sm" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ s.title }}</div>
          <div class="flex items-center justify-between mt-4" style="margin-top:2px">
            <span class="text-muted text-sm">{{ s.message_count }} messages</span>
            <button class="btn btn-sm" style="padding:2px 6px;font-size:11px;background:none;color:var(--text-muted)" @click.stop="deleteSession(s.id)">✕</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Chat area -->
    <div style="flex:1;display:flex;flex-direction:column;overflow:hidden">
      <div ref="messagesEl" style="flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:16px">
        <!-- Empty state -->
        <div v-if="!chatStore.currentSession" style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;gap:24px">
          <div style="text-align:center">
            <div style="font-size:48px;margin-bottom:12px">🧬</div>
            <h2 style="font-size:20px;margin-bottom:8px">BioIntel AI Assistant</h2>
            <p class="text-muted">Ask me anything about drug development, compounds, synthesis, or regulatory topics.</p>
          </div>
          <div style="display:flex;flex-wrap:wrap;gap:8px;max-width:600px;justify-content:center">
            <button
              v-for="q in suggestedQueries"
              :key="q"
              class="btn btn-secondary"
              style="font-size:13px"
              @click="messageInput = q"
            >{{ q }}</button>
          </div>
        </div>

        <!-- Messages -->
        <template v-else>
          <div
            v-for="msg in chatStore.messages"
            :key="msg.id || msg.created_at"
            :class="[msg.role === 'user' ? 'message-user' : 'message-assistant']"
          >
            <div v-if="msg.role === 'user'" class="text-sm">{{ msg.content }}</div>
            <div v-else>
              <MarkdownRenderer :content="msg.content" />
              <div v-if="msg.sources?.length" style="margin-top:8px;border-top:1px solid var(--border);padding-top:8px">
                <details>
                  <summary class="text-muted text-sm" style="cursor:pointer">Sources ({{ msg.sources.length }})</summary>
                  <div style="margin-top:8px;display:flex;flex-direction:column;gap:6px">
                    <div v-if="msg.sources.filter(s => s.type === 'rag').length" style="display:flex;flex-wrap:wrap;gap:6px;align-items:center">
                      <span class="text-muted text-sm" style="white-space:nowrap">📚 Knowledge base:</span>
                      <span v-for="s in msg.sources.filter(s => s.type === 'rag')" :key="s.api" class="badge" style="background:#ede9fe;color:#6d28d9">{{ s.api }}</span>
                    </div>
                    <div v-if="msg.sources.filter(s => s.type !== 'rag').length" style="display:flex;flex-wrap:wrap;gap:6px;align-items:center">
                      <span class="text-muted text-sm" style="white-space:nowrap">🔧 Tools:</span>
                      <span v-for="s in msg.sources.filter(s => s.type !== 'rag')" :key="s.api" class="badge badge-completed">{{ s.api }}</span>
                    </div>
                  </div>
                </details>
              </div>
            </div>
          </div>

          <!-- RAG retrieval indicator (fires before text starts) -->
          <div v-if="chatStore.ragChunks.length && chatStore.isStreaming" class="rag-live-indicator">
            <span class="rag-live-icon">📚</span>
            <span class="rag-live-label">Retrieved from knowledge base:</span>
            <span
              v-for="name in [...new Set(chatStore.ragChunks.map(c => c.document))]"
              :key="name"
              class="rag-live-doc"
            >{{ name }}</span>
          </div>

          <!-- Streaming message -->
          <div v-if="chatStore.streamingText || chatStore.isStreaming" class="message-assistant">
            <MarkdownRenderer v-if="chatStore.streamingText" :content="chatStore.streamingText" />
            <StreamingIndicator v-else />
          </div>

          <!-- Tool calls -->
          <div v-if="chatStore.toolCalls.length && chatStore.isStreaming" style="display:flex;flex-wrap:wrap;gap:6px;margin-top:4px">
            <span v-for="(t, i) in chatStore.toolCalls.filter(tc => tc.type === 'use')" :key="i" class="badge badge-phase1" style="font-size:12px">
              🔧 {{ t.name }}
            </span>
          </div>
        </template>
      </div>

      <!-- Input bar -->
      <div style="border-top:1px solid var(--border);padding:12px 20px;background:var(--surface);display:flex;gap:10px;align-items:flex-end">
        <textarea
          v-model="messageInput"
          class="form-control"
          style="resize:none;min-height:44px;max-height:120px"
          placeholder="Ask about your compound, experiment results, regulatory requirements..."
          @keydown.enter.exact.prevent="sendMessage"
        />
        <button
          class="btn btn-primary"
          :disabled="chatStore.isStreaming || !messageInput.trim()"
          @click="sendMessage"
          style="flex-shrink:0"
        >
          {{ chatStore.isStreaming ? '...' : 'Send' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.rag-live-indicator {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  padding: 8px 12px;
  background: #ede9fe;
  border: 1px solid #c4b5fd;
  border-radius: 8px;
  font-size: 12px;
  animation: fade-in 0.2s ease;
}
.rag-live-icon { font-size: 14px; }
.rag-live-label { color: #6d28d9; font-weight: 600; white-space: nowrap; }
.rag-live-doc {
  background: #fff;
  color: #6d28d9;
  border: 1px solid #c4b5fd;
  border-radius: 6px;
  padding: 2px 8px;
  font-weight: 600;
}
@keyframes fade-in { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
</style>
