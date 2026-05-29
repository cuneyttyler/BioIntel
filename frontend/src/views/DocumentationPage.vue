<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { documents as docsApi, createSSEStream } from '@/services/api'
import { useUIStore } from '@/stores/ui'
import PageHeader from '@/components/layout/PageHeader.vue'
import MarkdownRenderer from '@/components/common/MarkdownRenderer.vue'
import StreamingIndicator from '@/components/common/StreamingIndicator.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const route = useRoute()
const ui = useUIStore()
const projectId = route.params.id

const docList = ref([])
const selectedDoc = ref(null)
const editContent = ref('')
const preview = ref(false)
const generating = ref(false)
const streamingText = ref('')
const docType = ref('process_summary')
const saving = ref(false)
const loading = ref(true)

onMounted(async () => {
  try {
    docList.value = await docsApi.list(projectId)
  } finally { loading.value = false }
})

const generateDoc = async () => {
  generating.value = true
  streamingText.value = ''
  editContent.value = ''
  selectedDoc.value = null
  try {
    const stream = createSSEStream(`/api/projects/${projectId}/documents/generate/`, {
      method: 'POST',
      body: { doc_type: docType.value },
    })
    for await (const event of stream) {
      if (event.type === 'text_delta') {
        streamingText.value += event.text
        editContent.value = streamingText.value
      }
    }
    ui.addToast('Document generated', 'success')
  } catch {
    ui.addToast('Generation failed', 'error')
  } finally { generating.value = false }
}

const saveDoc = async () => {
  saving.value = true
  try {
    if (selectedDoc.value?.id) {
      const updated = await docsApi.update(selectedDoc.value.id, { content: editContent.value, title: selectedDoc.value.title })
      const idx = docList.value.findIndex(d => d.id === updated.id)
      if (idx !== -1) docList.value[idx] = updated
    } else {
      const created = await docsApi.create(projectId, {
        doc_type: docType.value,
        title: `${docType.value.replace('_', ' ')} — ${new Date().toLocaleDateString()}`,
        content: editContent.value,
      })
      docList.value.unshift(created)
      selectedDoc.value = created
    }
    ui.addToast('Document saved', 'success')
  } catch {
    ui.addToast('Save failed', 'error')
  } finally { saving.value = false }
}

const openDoc = (doc) => {
  selectedDoc.value = doc
  editContent.value = doc.content
  streamingText.value = ''
}
</script>

<template>
  <div style="display:flex;gap:16px;height:calc(100vh - 56px - 48px);overflow:hidden">
    <!-- Document list -->
    <div style="width:260px;flex-shrink:0;display:flex;flex-direction:column;gap:8px;overflow-y:auto">
      <div class="card" style="padding:12px">
        <div class="card-title">Generate New Document</div>
        <div class="form-group">
          <select v-model="docType" class="form-control">
            <option value="process_summary">Process Summary</option>
            <option value="risk_report">Risk Report</option>
            <option value="handoff">Handoff Note</option>
            <option value="analog_report">Analog Development Report</option>
          </select>
        </div>
        <button class="btn btn-primary w-full" :disabled="generating" @click="generateDoc">
          {{ generating ? 'Generating...' : '🤖 Generate Draft' }}
        </button>
      </div>

      <div v-if="loading"><LoadingSpinner /></div>
      <div v-else-if="!docList.length" class="text-muted text-sm" style="padding:8px">No documents yet.</div>
      <div
        v-for="doc in docList"
        :key="doc.id"
        class="card"
        style="padding:10px;cursor:pointer"
        :style="selectedDoc?.id === doc.id ? 'border-color:var(--primary)' : ''"
        @click="openDoc(doc)"
      >
        <div class="font-bold text-sm">{{ doc.title }}</div>
        <div class="flex items-center justify-between mt-4" style="margin-top:4px">
          <span class="badge badge-completed">{{ doc.doc_type.replace('_', ' ') }}</span>
          <span class="text-muted text-sm">{{ new Date(doc.created_at).toLocaleDateString() }}</span>
        </div>
      </div>
    </div>

    <!-- Editor -->
    <div style="flex:1;display:flex;flex-direction:column;overflow:hidden">
      <div class="flex items-center gap-2 mb-4">
        <h2 style="font-size:16px">{{ selectedDoc?.title || 'New Document' }}</h2>
        <div class="ml-auto flex gap-2">
          <button :class="['btn btn-sm', preview ? 'btn-primary' : 'btn-secondary']" @click="preview = !preview">
            {{ preview ? 'Edit' : 'Preview' }}
          </button>
          <button class="btn btn-primary btn-sm" :disabled="saving || !editContent" @click="saveDoc">
            {{ saving ? 'Saving...' : 'Save' }}
          </button>
          <a v-if="selectedDoc?.id" :href="docsApi.exportUrl(selectedDoc.id)" class="btn btn-secondary btn-sm" download>⬇ Export MD</a>
        </div>
      </div>

      <div v-if="generating && !editContent" style="display:flex;align-items:center;gap:12px;padding:20px">
        <StreamingIndicator />
        <span class="text-muted">Generating document with Claude...</span>
      </div>

      <div style="flex:1;overflow:hidden">
        <div v-if="preview" style="height:100%;overflow-y:auto" class="card">
          <MarkdownRenderer :content="editContent" />
        </div>
        <textarea
          v-else
          v-model="editContent"
          class="form-control"
          style="height:100%;font-family:var(--mono);font-size:13px;resize:none;border-radius:8px"
          placeholder="Your document will appear here after generation, or start writing..."
        />
      </div>
    </div>
  </div>
</template>
