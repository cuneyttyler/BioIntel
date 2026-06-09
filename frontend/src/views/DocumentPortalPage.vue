<template>
  <div class="doc-portal">
    <div class="page-header">
      <h1>Document Portal</h1>
      <p class="subtitle">Upload scientific documents to enhance AI recommendations with your project-specific knowledge.</p>
    </div>

    <div class="toolbar">
      <div class="search-row">
        <input v-model="searchQuery" placeholder="Search documents by content…" @keydown.enter="search" />
        <button class="btn btn-search" @click="search" :disabled="store.isSearching">
          {{ store.isSearching ? 'Searching…' : 'Search' }}
        </button>
        <button v-if="searchQuery" class="btn btn-clear" @click="clearSearch">Clear</button>
      </div>
      <label class="btn btn-upload">
        Upload Document
        <input type="file" accept=".pdf,.docx,.doc,.txt" @change="handleFileSelect" hidden />
      </label>
    </div>

    <!-- Upload modal -->
    <div v-if="pendingFile" class="upload-modal-overlay" @click.self="pendingFile = null">
      <div class="upload-modal">
        <h3>Upload Document</h3>
        <div class="form-group">
          <label>Document Name</label>
          <input v-model="uploadForm.name" :placeholder="pendingFile.name" />
        </div>
        <div class="form-group">
          <label>Document Type</label>
          <select v-model="uploadForm.document_type">
            <option value="ich_guideline">ICH Guideline</option>
            <option value="academic_paper">Academic Paper</option>
            <option value="lab_report">Lab Report</option>
            <option value="regulatory">Regulatory Submission</option>
            <option value="internal">Internal Study</option>
            <option value="competitor_analysis">Competitor Analysis</option>
            <option value="clinical_data">Clinical Data</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div class="form-group">
          <label>Molecule Type</label>
          <select v-model="uploadForm.molecule_type">
            <option value="both">Both</option>
            <option value="small_molecule">Small Molecule</option>
            <option value="biologic">Biologic</option>
          </select>
        </div>
        <div class="modal-actions">
          <button class="btn btn-primary" :disabled="isUploading" @click="submitUpload">
            {{ isUploading ? 'Uploading…' : 'Upload & Ingest' }}
          </button>
          <button class="btn btn-cancel" @click="pendingFile = null">Cancel</button>
        </div>
      </div>
    </div>

    <!-- Search results -->
    <div v-if="store.searchResults.length" class="search-results">
      <h3>Search Results</h3>
      <div v-for="(result, i) in store.searchResults" :key="i" class="search-result">
        <div class="result-header">
          <span class="result-num">[{{ i + 1 }}]</span>
          <span class="result-doc">{{ result.document }}</span>
          <span class="result-score">{{ (result.score * 100).toFixed(0) }}% match</span>
        </div>
        <div class="result-text">{{ result.text }}</div>
      </div>
    </div>

    <!-- Document list -->
    <div class="doc-list">
      <div v-if="store.isLoading" class="loading">Loading documents…</div>
      <div v-else-if="!store.documents.length" class="empty-state">
        No documents uploaded yet. Upload ICH guidelines, academic papers, or lab reports to enhance AI recommendations.
      </div>
      <div v-else>
        <div v-for="doc in store.documents" :key="doc.id" class="doc-card">
          <div class="doc-info">
            <div class="doc-name">{{ doc.name }}</div>
            <div class="doc-meta">
              <span class="badge type">{{ doc.document_type }}</span>
              <span class="badge mol">{{ doc.molecule_type }}</span>
              <span class="badge" :class="`status-${doc.ingestion_status}`">{{ doc.ingestion_status }}</span>
              <span v-if="doc.chunk_count" class="meta-item">{{ doc.chunk_count }} chunks</span>
              <span v-if="doc.page_count" class="meta-item">{{ doc.page_count }} pages</span>
            </div>
          </div>
          <div class="doc-actions">
            <button class="btn btn-sm btn-reingest" @click="reIngest(doc.id)">Re-ingest</button>
            <button class="btn btn-sm btn-delete" @click="deleteDoc(doc.id)">Delete</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useDocumentsStore } from '@/stores/documents'

const store = useDocumentsStore()
const searchQuery = ref('')
const pendingFile = ref(null)
const isUploading = ref(false)
const uploadForm = ref({ name: '', document_type: 'other', molecule_type: 'both' })

onMounted(async () => {
  await store.fetchDocuments()
})

function handleFileSelect(e) {
  const file = e.target.files[0]
  if (!file) return
  pendingFile.value = file
  uploadForm.value.name = file.name.replace(/\.[^.]+$/, '')
  e.target.value = ''
}

async function submitUpload() {
  if (!pendingFile.value) return
  isUploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', pendingFile.value)
    fd.append('name', uploadForm.value.name || pendingFile.value.name)
    fd.append('document_type', uploadForm.value.document_type)
    fd.append('molecule_type', uploadForm.value.molecule_type)
    await store.uploadDocument(fd)
    pendingFile.value = null
  } finally {
    isUploading.value = false
  }
}

async function deleteDoc(id) {
  if (!confirm('Delete this document and its RAG chunks?')) return
  await store.deleteDocument(id)
}

async function reIngest(id) {
  await store.reIngest(id)
}

async function search() {
  if (!searchQuery.value.trim()) return
  await store.search(searchQuery.value)
}

function clearSearch() {
  searchQuery.value = ''
  store.clearSearch()
}
</script>

<style scoped>
.doc-portal { padding: 24px; display: flex; flex-direction: column; gap: 24px; max-width: 900px; }
.page-header h1 { margin: 0 0 4px; font-size: 22px; }
.subtitle { margin: 0; color: #6b7280; font-size: 14px; }

.toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}
.search-row { display: flex; gap: 8px; flex: 1; }
.search-row input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}
.search-row input:focus { outline: none; border-color: #3b82f6; }

.btn {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
}
.btn-search { background: #3b82f6; color: #fff; }
.btn-upload { background: #10b981; color: #fff; cursor: pointer; }
.btn-clear { background: #fff; color: #6b7280; border-color: #d1d5db; }
.btn-primary { background: #3b82f6; color: #fff; }
.btn-cancel { background: #fff; color: #374151; border-color: #d1d5db; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.upload-modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center;
  z-index: 200;
}
.upload-modal {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  width: 420px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.2);
}
.upload-modal h3 { margin: 0; font-size: 16px; }
.form-group { display: flex; flex-direction: column; gap: 4px; }
.form-group label { font-size: 12px; font-weight: 600; color: #374151; }
.form-group input, .form-group select {
  padding: 7px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 13px;
}
.modal-actions { display: flex; gap: 10px; justify-content: flex-end; }

.search-results {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 16px;
  background: #f9fafb;
}
.search-results h3 { margin: 0 0 12px; font-size: 14px; font-weight: 700; }
.search-result {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 10px 12px;
  background: #fff;
  margin-bottom: 8px;
}
.result-header { display: flex; gap: 8px; align-items: center; margin-bottom: 6px; }
.result-num { font-weight: 700; color: #374151; }
.result-doc { font-weight: 600; font-size: 13px; }
.result-score { margin-left: auto; font-size: 11px; color: #3b82f6; font-weight: 600; }
.result-text { font-size: 12px; color: #6b7280; line-height: 1.5; }

.doc-list { display: flex; flex-direction: column; gap: 8px; }
.doc-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px 16px;
  background: #fff;
}
.doc-name { font-weight: 600; font-size: 14px; margin-bottom: 4px; }
.doc-meta { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
.badge {
  font-size: 10px;
  padding: 2px 7px;
  border-radius: 8px;
  font-weight: 600;
  background: #f3f4f6;
  color: #374151;
}
.badge.type { background: #dbeafe; color: #1d4ed8; }
.badge.mol { background: #d1fae5; color: #065f46; }
.status-ready { background: #d1fae5; color: #065f46; }
.status-processing { background: #fef3c7; color: #92400e; }
.status-pending { background: #f3f4f6; color: #6b7280; }
.status-failed { background: #fee2e2; color: #991b1b; }
.meta-item { font-size: 11px; color: #6b7280; }
.doc-actions { display: flex; gap: 6px; }
.btn-sm { padding: 4px 10px; font-size: 12px; }
.btn-reingest { background: #fff; color: #374151; border-color: #d1d5db; }
.btn-delete { background: #fff; color: #ef4444; border-color: #fee2e2; }
.loading, .empty-state { text-align: center; color: #6b7280; padding: 32px; font-size: 14px; }
</style>
