<template>
  <div class="ai-lab-page">
    <div class="sidebar">
      <div class="sidebar-header">
        <h2>AI Lab</h2>
        <button class="btn-new" @click="startNewSession">+ New Session</button>
      </div>
      <div class="sessions-list">
        <div
          v-for="s in labStore.sessions"
          :key="s.id"
          class="session-item"
          :class="{ active: labStore.currentSession?.id === s.id }"
          @click="loadSession(s.id)"
        >
          <div class="session-title">{{ s.title }}</div>
          <div class="session-meta">{{ formatDate(s.created_at) }}</div>
        </div>
      </div>
    </div>

    <div class="main-panel">
      <div v-if="!labStore.currentSession" class="welcome-screen">
        <div class="welcome-icon">✦</div>
        <h2>AI Lab — Chat-First Project Creation</h2>
        <p>
          Describe what you want to develop and AI will conduct a structured intake interview,
          then propose a complete project and development plan grounded in pharmaceutical methodology.
        </p>
        <button class="btn-start" @click="startNewSession">Start New Session</button>
      </div>

      <template v-else>
        <div class="chat-area" ref="chatEl">
          <div
            v-for="(msg, i) in labStore.messages"
            :key="i"
            class="chat-message"
            :class="msg.role"
          >
            <div class="role-label">{{ msg.role === 'assistant' ? 'BioIntel AI' : 'You' }}</div>
            <div class="message-content" v-html="renderMarkdown(msg.content)" />
          </div>

          <div v-if="labStore.isStreaming" class="chat-message assistant streaming">
            <div class="role-label">BioIntel AI</div>
            <div class="message-content" v-html="renderMarkdown(labStore.streamingText)" />
            <span class="cursor" />
          </div>
        </div>

        <!-- Proposal card -->
        <div v-if="labStore.proposal" class="proposal-card">
          <div class="proposal-header">
            <span class="proposal-icon">📋</span>
            Project Proposal
          </div>
          <div class="proposal-fields">
            <div class="field"><span class="label">Project Name</span><span class="value">{{ labStore.proposal.project_name }}</span></div>
            <div class="field"><span class="label">Molecule Type</span><span class="value">{{ labStore.proposal.molecule_type }}</span></div>
            <div class="field"><span class="label">Pathway</span><span class="value">{{ labStore.proposal.pathway }}</span></div>
            <div class="field"><span class="label">Phase</span><span class="value">{{ labStore.proposal.phase }}</span></div>
            <div class="field full"><span class="label">Disease/Target</span><span class="value">{{ labStore.proposal.disease_description }}</span></div>
            <div v-if="labStore.proposal.first_steps?.length" class="field full">
              <span class="label">First Steps</span>
              <ol class="steps-preview">
                <li v-for="step in labStore.proposal.first_steps" :key="step">{{ step }}</li>
              </ol>
            </div>
          </div>
          <div class="proposal-actions">
            <button class="btn-create" :disabled="isCreating" @click="createProject">
              {{ isCreating ? 'Creating…' : 'Create Project & Plan' }}
            </button>
            <button class="btn-continue" @click="continueIntake">Continue Intake</button>
          </div>
        </div>

        <!-- Input -->
        <div class="input-row">
          <textarea
            v-model="input"
            :disabled="labStore.isStreaming"
            placeholder="Describe your drug development goal… (Enter to send)"
            rows="3"
            @keydown.enter.exact.prevent="send()"
          />
          <button class="btn-send" :disabled="labStore.isStreaming || !input.trim()" @click="send()">
            {{ labStore.isStreaming ? '…' : '→' }}
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAILabStore } from '@/stores/aiLab'

const router = useRouter()
const labStore = useAILabStore()
const chatEl = ref(null)
const input = ref('')
const isCreating = ref(false)

onMounted(async () => {
  await labStore.fetchSessions()
})

watch(
  () => [labStore.messages.length, labStore.isStreaming],
  () => nextTick(() => {
    if (chatEl.value) chatEl.value.scrollTop = chatEl.value.scrollHeight
  }),
)

async function startNewSession() {
  labStore.reset()
  const session = await labStore.createSession()
  await send('Hello! I would like to start a new drug development project.')
}

async function loadSession(id) {
  await labStore.loadSession(id)
}

async function send(messageOverride) {
  const msg = (messageOverride || input.value).trim()
  if (!msg || labStore.isStreaming) return
  if (!messageOverride) input.value = ''
  await labStore.sendMessage(labStore.currentSession.id, msg)
}

async function createProject() {
  isCreating.value = true
  try {
    const result = await labStore.createProject(labStore.currentSession.id)
    router.push(`/projects/${result.project_id}`)
  } finally {
    isCreating.value = false
  }
}

function continueIntake() {
  input.value = 'Can we refine the proposal?'
}

function formatDate(dt) {
  return new Date(dt).toLocaleDateString()
}

function renderMarkdown(text) {
  if (!text) return ''
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/<proposal>[\s\S]*?<\/proposal>/g, '')
    .replace(/\n/g, '<br>')
}
</script>

<style scoped>
.ai-lab-page {
  display: flex;
  height: 100%;
  overflow: hidden;
}
.sidebar {
  width: 220px;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  background: #f9fafb;
}
.sidebar-header {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  border-bottom: 1px solid #e5e7eb;
}
.sidebar-header h2 { margin: 0; font-size: 15px; }
.btn-new {
  padding: 6px 12px;
  background: #3b82f6;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}
.sessions-list { flex: 1; overflow-y: auto; }
.session-item {
  padding: 10px 16px;
  cursor: pointer;
  border-bottom: 1px solid #f3f4f6;
}
.session-item:hover { background: #eff6ff; }
.session-item.active { background: #eff6ff; border-left: 3px solid #3b82f6; }
.session-title { font-size: 13px; font-weight: 500; }
.session-meta { font-size: 11px; color: #9ca3af; margin-top: 2px; }

.main-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 16px;
  gap: 16px;
}
.welcome-screen {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: 16px;
  color: #374151;
}
.welcome-icon { font-size: 48px; }
.welcome-screen h2 { margin: 0; font-size: 22px; }
.welcome-screen p { max-width: 480px; color: #6b7280; line-height: 1.6; }
.btn-start {
  padding: 10px 24px;
  background: #3b82f6;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
}

.chat-area {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.chat-message {
  padding: 12px 16px;
  border-radius: 10px;
  max-width: 80%;
}
.chat-message.user { background: #eff6ff; border: 1px solid #bfdbfe; align-self: flex-end; }
.chat-message.assistant { background: #f9fafb; border: 1px solid #e5e7eb; align-self: flex-start; }
.role-label { font-size: 11px; font-weight: 600; color: #6b7280; margin-bottom: 4px; text-transform: uppercase; }
.message-content { font-size: 14px; line-height: 1.7; }
.cursor {
  display: inline-block; width: 2px; height: 1em;
  background: #374151; margin-left: 2px;
  animation: blink 1s step-end infinite;
}
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

.proposal-card {
  border: 2px solid #3b82f6;
  border-radius: 10px;
  padding: 16px;
  background: #eff6ff;
}
.proposal-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 12px;
}
.proposal-fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 14px;
}
.field { display: flex; flex-direction: column; gap: 2px; }
.field.full { grid-column: 1 / -1; }
.label { font-size: 10px; font-weight: 600; color: #6b7280; text-transform: uppercase; }
.value { font-size: 13px; color: #111827; }
.steps-preview { margin: 0; padding-left: 16px; }
.steps-preview li { font-size: 13px; color: #374151; }
.proposal-actions { display: flex; gap: 10px; }
.btn-create {
  padding: 8px 20px;
  background: #3b82f6;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}
.btn-continue {
  padding: 8px 20px;
  background: #fff;
  color: #374151;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}
.btn-create:disabled { opacity: 0.5; }

.input-row { display: flex; gap: 8px; }
textarea {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  resize: none;
  font-family: inherit;
}
textarea:focus { outline: none; border-color: #3b82f6; }
.btn-send {
  width: 44px;
  height: 44px;
  background: #3b82f6;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 20px;
  cursor: pointer;
  align-self: flex-end;
}
.btn-send:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
