<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useUIStore } from '@/stores/ui'

const store = useSettingsStore()
const ui = useUIStore()

// Local form state — edit without touching store until Save
const provider = ref('claude')
const model = ref('')
const anthropicApiKey = ref('')
const openaiApiKey = ref('')
const mistralApiKey = ref('')
const customEndpoint = ref('')
const customApiKey = ref('')

const dirty = ref(false)

const MODEL_SUGGESTIONS = {
  claude: ['claude-sonnet-4-6', 'claude-opus-4-7', 'claude-haiku-4-5-20251001'],
  openai: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'o3-mini'],
  mistral: ['mistral-large-latest', 'mistral-medium-latest', 'codestral-latest', 'open-mixtral-8x7b'],
  custom: [],
}

const suggestions = computed(() => MODEL_SUGGESTIONS[provider.value] || [])

function loadFromStore() {
  provider.value = store.provider
  model.value = store.model
  anthropicApiKey.value = store.anthropicApiKey
  openaiApiKey.value = store.openaiApiKey
  mistralApiKey.value = store.mistralApiKey
  customEndpoint.value = store.customEndpoint
  customApiKey.value = store.customApiKey
  dirty.value = false
}

watch(() => store.loaded, (v) => { if (v) loadFromStore() })

onMounted(async () => {
  if (!store.loaded) await store.fetch()
  else loadFromStore()
})

function setProvider(p) {
  provider.value = p
  const defaults = { claude: 'claude-sonnet-4-6', openai: 'gpt-4o', mistral: 'mistral-large-latest', custom: '' }
  model.value = defaults[p] || ''
  dirty.value = true
}

function markDirty() {
  dirty.value = true
}

async function save() {
  const payload = {
    provider: provider.value,
    model: model.value,
    custom_endpoint: customEndpoint.value,
  }
  // Only send key if it was actually changed (not the masked placeholder)
  if (anthropicApiKey.value && !anthropicApiKey.value.includes('•')) payload.anthropic_api_key = anthropicApiKey.value
  if (openaiApiKey.value && !openaiApiKey.value.includes('•')) payload.openai_api_key = openaiApiKey.value
  if (mistralApiKey.value && !mistralApiKey.value.includes('•')) payload.mistral_api_key = mistralApiKey.value
  if (customApiKey.value && !customApiKey.value.includes('•')) payload.custom_api_key = customApiKey.value

  await store.save(payload)
  await store.fetch()
  dirty.value = false
  ui.addToast('Settings saved', 'success')
}
</script>

<template>
  <div class="settings-page">
    <div class="settings-header">
      <h1 class="settings-title">Settings</h1>
      <p class="settings-subtitle">Configure the AI provider and model used across BioIntel.</p>
    </div>

    <div v-if="store.loading" class="settings-loading">Loading…</div>

    <template v-else>
      <section class="settings-section">
        <h2 class="section-title">LLM Provider</h2>
        <p class="section-hint">
          Claude supports full tool use (PubChem, ChEMBL, synthesis, etc.).
          OpenAI, Mistral, and Custom endpoints provide text-only responses.
        </p>

        <div class="provider-grid">
          <button
            v-for="p in ['claude', 'openai', 'mistral', 'custom']"
            :key="p"
            class="provider-card"
            :class="{ selected: provider === p }"
            @click="setProvider(p)"
          >
            <span class="provider-icon">
              <template v-if="p === 'claude'">✦</template>
              <template v-else-if="p === 'openai'">⬡</template>
              <template v-else-if="p === 'mistral'">◈</template>
              <template v-else>⚙</template>
            </span>
            <span class="provider-name">
              <template v-if="p === 'claude'">Claude (Anthropic)</template>
              <template v-else-if="p === 'openai'">OpenAI</template>
              <template v-else-if="p === 'mistral'">Mistral</template>
              <template v-else>Custom Endpoint</template>
            </span>
          </button>
        </div>
      </section>

      <section class="settings-section">
        <h2 class="section-title">Model</h2>
        <div class="field-row">
          <input
            v-model="model"
            class="settings-input"
            placeholder="e.g. claude-sonnet-4-6"
            @input="markDirty"
          />
          <div v-if="suggestions.length" class="model-chips">
            <button
              v-for="s in suggestions"
              :key="s"
              class="model-chip"
              :class="{ active: model === s }"
              @click="model = s; markDirty()"
            >{{ s }}</button>
          </div>
        </div>
      </section>

      <section class="settings-section">
        <h2 class="section-title">API Keys</h2>

        <template v-if="provider === 'claude' || provider === 'openai' || provider === 'mistral' || provider === 'custom'">
          <div v-if="provider === 'claude'" class="field-group">
            <label class="field-label">Anthropic API Key</label>
            <input
              v-model="anthropicApiKey"
              type="password"
              class="settings-input"
              placeholder="sk-ant-api03-…"
              @input="markDirty"
            />
          </div>

          <div v-if="provider === 'openai'" class="field-group">
            <label class="field-label">OpenAI API Key</label>
            <input
              v-model="openaiApiKey"
              type="password"
              class="settings-input"
              placeholder="sk-…"
              @input="markDirty"
            />
          </div>

          <div v-if="provider === 'mistral'" class="field-group">
            <label class="field-label">Mistral API Key</label>
            <input
              v-model="mistralApiKey"
              type="password"
              class="settings-input"
              placeholder="…"
              @input="markDirty"
            />
          </div>

          <template v-if="provider === 'custom'">
            <div class="field-group">
              <label class="field-label">Base URL</label>
              <input
                v-model="customEndpoint"
                class="settings-input"
                placeholder="https://your-llm-endpoint.com/v1"
                @input="markDirty"
              />
              <p class="field-hint">Must be an OpenAI-compatible endpoint.</p>
            </div>
            <div class="field-group">
              <label class="field-label">API Key</label>
              <input
                v-model="customApiKey"
                type="password"
                class="settings-input"
                placeholder="Bearer token or API key"
                @input="markDirty"
              />
            </div>
          </template>
        </template>
      </section>

      <div class="settings-footer">
        <button
          class="btn-save"
          :disabled="!dirty || store.saving"
          @click="save"
        >
          {{ store.saving ? 'Saving…' : 'Save Settings' }}
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.settings-page {
  max-width: 680px;
  margin: 0 auto;
  padding: 32px 24px;
}
.settings-header {
  margin-bottom: 32px;
}
.settings-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--text);
  margin: 0 0 6px;
}
.settings-subtitle {
  color: var(--text-muted);
  font-size: 14px;
  margin: 0;
}
.settings-loading {
  color: var(--text-muted);
  padding: 32px 0;
}
.settings-section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 20px 24px;
  margin-bottom: 16px;
}
.section-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 6px;
}
.section-hint {
  font-size: 12px;
  color: var(--text-muted);
  margin: 0 0 16px;
  line-height: 1.5;
}
.provider-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}
.provider-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 14px 8px;
  border: 1.5px solid var(--border);
  border-radius: 8px;
  background: var(--bg);
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}
.provider-card:hover {
  border-color: var(--primary);
}
.provider-card.selected {
  border-color: var(--primary);
  background: var(--primary-light);
}
.provider-icon {
  font-size: 20px;
  color: var(--primary);
}
.provider-name {
  font-size: 11px;
  font-weight: 600;
  color: var(--text);
  text-align: center;
}
.field-row {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.field-group {
  margin-bottom: 14px;
}
.field-group:last-child {
  margin-bottom: 0;
}
.field-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  margin-bottom: 6px;
}
.field-hint {
  font-size: 11px;
  color: var(--text-muted);
  margin: 4px 0 0;
}
.settings-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg);
  color: var(--text);
  font-size: 13px;
  font-family: monospace;
  box-sizing: border-box;
}
.settings-input:focus {
  outline: none;
  border-color: var(--primary);
}
.model-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.model-chip {
  padding: 4px 10px;
  border: 1px solid var(--border);
  border-radius: 20px;
  background: var(--bg);
  color: var(--text-muted);
  font-size: 11px;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}
.model-chip:hover {
  border-color: var(--primary);
  color: var(--primary);
}
.model-chip.active {
  border-color: var(--primary);
  background: var(--primary-light);
  color: var(--primary);
  font-weight: 600;
}
.settings-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}
.btn-save {
  padding: 9px 24px;
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: 7px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s;
}
.btn-save:disabled {
  opacity: 0.45;
  cursor: default;
}
.btn-save:not(:disabled):hover {
  opacity: 0.88;
}
</style>
