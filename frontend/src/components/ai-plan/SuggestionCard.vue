<template>
  <div class="suggestion-card">
    <div class="suggestion-header">
      <span class="suggestion-icon">✦</span>
      <span class="suggestion-title">AI Suggestions</span>
      <button class="dismiss-btn" title="Dismiss" @click="$emit('dismiss')">✕</button>
    </div>

    <ul class="suggestion-list">
      <li v-for="item in items" :key="item.key" class="suggestion-item">
        <label class="suggestion-check">
          <input type="checkbox" v-model="item.checked" />
          <span class="field-label">{{ item.label }}</span>
          <span class="field-value">{{ item.value }}</span>
        </label>
      </li>
    </ul>

    <div class="suggestion-actions">
      <button class="btn-apply-all" @click="applyAll">Apply All</button>
      <button class="btn-apply-sel" @click="applySelected">Apply Selected</button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { getFieldLabel } from '@/services/aiPageContexts'

const props = defineProps({
  fields: { type: Object, required: true },
  pageType: { type: String, default: '' },
})

const emit = defineEmits(['apply', 'dismiss'])

const items = ref([])

watch(
  () => props.fields,
  (fields) => {
    items.value = Object.entries(fields).map(([key, value]) => ({
      key,
      label: getFieldLabel(props.pageType, key),
      value,
      checked: true,
    }))
  },
  { immediate: true },
)

function applyAll() {
  const result = {}
  items.value.forEach((item) => { result[item.key] = item.value })
  emit('apply', result)
}

function applySelected() {
  const result = {}
  items.value.filter((i) => i.checked).forEach((item) => { result[item.key] = item.value })
  if (Object.keys(result).length) emit('apply', result)
}
</script>

<style scoped>
.suggestion-card {
  margin-top: 10px;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  background: #eff6ff;
  font-size: 12px;
}
.suggestion-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-bottom: 1px solid #bfdbfe;
  font-weight: 700;
  color: #1d4ed8;
}
.suggestion-icon { color: #3b82f6; }
.suggestion-title { flex: 1; }
.dismiss-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #6b7280;
  font-size: 13px;
  padding: 0;
  line-height: 1;
}

.suggestion-list {
  list-style: none;
  margin: 0;
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.suggestion-item {}
.suggestion-check {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  cursor: pointer;
}
.suggestion-check input[type="checkbox"] {
  margin-top: 2px;
  flex-shrink: 0;
  accent-color: #3b82f6;
}
.field-label {
  color: #374151;
  font-weight: 600;
  flex-shrink: 0;
}
.field-label::after { content: ':'; }
.field-value {
  color: #1d4ed8;
  word-break: break-word;
}

.suggestion-actions {
  display: flex;
  gap: 8px;
  padding: 8px 12px;
  border-top: 1px solid #bfdbfe;
}
.btn-apply-all,
.btn-apply-sel {
  flex: 1;
  padding: 5px 0;
  border-radius: 5px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  border: none;
}
.btn-apply-all {
  background: #3b82f6;
  color: #fff;
}
.btn-apply-all:hover { background: #2563eb; }
.btn-apply-sel {
  background: #fff;
  color: #3b82f6;
  border: 1px solid #bfdbfe;
}
.btn-apply-sel:hover { background: #dbeafe; }
</style>
