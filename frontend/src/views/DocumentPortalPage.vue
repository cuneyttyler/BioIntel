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

    <!-- Filter bar -->
    <div class="filter-bar">
      <input
        v-model="filters.name"
        class="filter-input"
        placeholder="Filter by name…"
        @input="onNameInput"
      />
      <select v-model="filters.document_type" class="filter-select" @change="applyFilters">
        <option value="">All Types</option>
        <option value="ich_guideline">ICH Guideline</option>
        <option value="academic_paper">Academic Paper</option>
        <option value="lab_report">Lab Report</option>
        <option value="regulatory">Regulatory Submission</option>
        <option value="internal">Internal Study</option>
        <option value="competitor_analysis">Competitor Analysis</option>
        <option value="clinical_data">Clinical Data</option>
        <option value="other">Other</option>
      </select>
      <select v-model="filters.project_id" class="filter-select" @change="applyFilters">
        <option value="">All Projects</option>
        <option v-for="p in projectStore.projects" :key="p.id" :value="String(p.id)">{{ p.name }}</option>
      </select>
      <button v-if="hasActiveFilters" class="btn btn-clear" @click="clearFilters">Clear Filters</button>
    </div>

    <!-- Error banner -->
    <div v-if="store.error" class="error-banner">{{ store.error }}</div>

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
        <div class="form-group">
          <label>Project <span class="label-hint">(optional — leave blank for global)</span></label>
          <select v-model="uploadForm.project_id">
            <option value="">Global (all projects)</option>
            <option v-for="p in projectStore.projects" :key="p.id" :value="String(p.id)">{{ p.name }}</option>
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

    <!-- Edit modal -->
    <div v-if="editingDoc" class="upload-modal-overlay" @click.self="editingDoc = null">
      <div class="upload-modal">
        <h3>Edit Document</h3>
        <div class="form-group">
          <label>Document Name</label>
          <input v-model="editForm.name" />
        </div>
        <div class="form-group">
          <label>Document Type</label>
          <select v-model="editForm.document_type">
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
          <select v-model="editForm.molecule_type">
            <option value="both">Both</option>
            <option value="small_molecule">Small Molecule</option>
            <option value="biologic">Biologic</option>
          </select>
        </div>
        <div class="form-group">
          <label>Project <span class="label-hint">(optional — leave blank for global)</span></label>
          <select v-model="editForm.project_id">
            <option value="">Global (all projects)</option>
            <option v-for="p in projectStore.projects" :key="p.id" :value="String(p.id)">{{ p.name }}</option>
          </select>
        </div>
        <div class="form-group reingest-row">
          <label class="reingest-label">
            <input type="checkbox" v-model="reIngestAfterSave" />
            Re-ingest after saving
          </label>
          <span class="label-hint">Re-processes the file and rebuilds RAG chunks</span>
        </div>
        <div class="modal-actions">
          <button class="btn btn-primary" :disabled="isSaving" @click="submitEdit">
            {{ isSaving ? 'Saving…' : 'Save Changes' }}
          </button>
          <button class="btn btn-cancel" @click="editingDoc = null">Cancel</button>
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
        No documents found. Upload ICH guidelines, academic papers, or lab reports to enhance AI recommendations.
      </div>
      <div v-else>
        <div v-for="doc in store.documents" :key="doc.id" class="doc-card">
          <div class="doc-info">
            <div class="doc-name">{{ doc.name }}</div>
            <div class="doc-meta">
              <span class="badge type">{{ doc.document_type }}</span>
              <span class="badge mol">{{ doc.molecule_type }}</span>
              <span class="badge" :class="`status-${doc.ingestion_status}`">{{ doc.ingestion_status }}</span>
              <span v-if="projectNameForDoc(doc)" class="badge project">{{ projectNameForDoc(doc) }}</span>
              <span v-if="doc.chunk_count" class="meta-item">{{ doc.chunk_count }} chunks</span>
              <span v-if="doc.page_count" class="meta-item">{{ doc.page_count }} pages</span>
            </div>
          </div>
          <div class="doc-actions">
            <button class="btn btn-sm btn-edit" @click="openEdit(doc)">Edit</button>
            <button class="btn btn-sm btn-reingest" @click="reIngest(doc.id)">Re-ingest</button>
            <button class="btn btn-sm btn-delete" @click="deleteDoc(doc.id)">Delete</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useDocumentsStore } from '@/stores/documents'
import { useProjectStore } from '@/stores/projects'

const store = useDocumentsStore()
const projectStore = useProjectStore()
const route = useRoute()

const searchQuery = ref('')
const pendingFile = ref(null)
const isUploading = ref(false)
const uploadForm = ref({ name: '', document_type: 'other', molecule_type: 'both', project_id: '' })

const editingDoc = ref(null)
const editForm = ref({ name: '', document_type: 'other', molecule_type: 'both', project_id: '' })
const reIngestAfterSave = ref(false)
const isSaving = ref(false)

function openEdit(doc) {
  editingDoc.value = doc
  editForm.value = {
    name: doc.name,
    document_type: doc.document_type,
    molecule_type: doc.molecule_type,
    project_id: doc.project ? String(doc.project) : '',
  }
  reIngestAfterSave.value = false
}

async function submitEdit() {
  if (!editingDoc.value) return
  isSaving.value = true
  try {
    const data = {
      name: editForm.value.name,
      document_type: editForm.value.document_type,
      molecule_type: editForm.value.molecule_type,
      project: editForm.value.project_id ? Number(editForm.value.project_id) : null,
    }
    await store.updateDocument(editingDoc.value.id, data, reIngestAfterSave.value)
    editingDoc.value = null
  } catch {
    // store.error shown in banner
  } finally {
    isSaving.value = false
  }
}

const filters = reactive({ name: '', document_type: '', project_id: '' })

const hasActiveFilters = computed(() => filters.name || filters.document_type || filters.project_id)

let nameDebounceTimer = null

function activeFilters() {
  const params = {}
  if (filters.name) params.name = filters.name
  if (filters.document_type) params.document_type = filters.document_type
  if (filters.project_id) params.project_id = filters.project_id
  return params
}

function applyFilters() {
  store.fetchDocuments(activeFilters())
}

function onNameInput() {
  clearTimeout(nameDebounceTimer)
  nameDebounceTimer = setTimeout(applyFilters, 300)
}

function clearFilters() {
  filters.name = ''
  filters.document_type = ''
  filters.project_id = ''
  applyFilters()
}

function projectNameForDoc(doc) {
  if (!doc.project) return null
  const p = projectStore.projects.find((p) => String(p.id) === String(doc.project))
  return p ? p.name : `Project ${doc.project}`
}

onMounted(async () => {
  await projectStore.fetchProjects()
  const initialProjectId = route.query.project || ''
  if (initialProjectId) {
    filters.project_id = String(initialProjectId)
    uploadForm.value.project_id = String(initialProjectId)
  }
  await store.fetchDocuments(activeFilters())
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
    if (uploadForm.value.project_id) fd.append('project_id', uploadForm.value.project_id)
    await store.uploadDocument(fd)
    pendingFile.value = null
    uploadForm.value = { name: '', document_type: 'other', molecule_type: 'both', project_id: filters.project_id }
  } catch {
    // store.error is already set; banner will show it
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

.filter-bar {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  padding: 10px 14px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}
.filter-input {
  flex: 1;
  min-width: 160px;
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 13px;
}
.filter-input:focus { outline: none; border-color: #3b82f6; }
.filter-select {
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 13px;
  background: #fff;
  cursor: pointer;
}

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
.label-hint { font-weight: 400; color: #9ca3af; }
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
.badge.project { background: #ede9fe; color: #6d28d9; }
.status-ready { background: #d1fae5; color: #065f46; }
.status-processing { background: #fef3c7; color: #92400e; }
.status-pending { background: #f3f4f6; color: #6b7280; }
.status-failed { background: #fee2e2; color: #991b1b; }
.meta-item { font-size: 11px; color: #6b7280; }
.doc-actions { display: flex; gap: 6px; }
.btn-sm { padding: 4px 10px; font-size: 12px; }
.btn-edit { background: #fff; color: #3b82f6; border-color: #bfdbfe; }
.btn-reingest { background: #fff; color: #374151; border-color: #d1d5db; }
.btn-delete { background: #fff; color: #ef4444; border-color: #fee2e2; }
.reingest-row { flex-direction: row; align-items: center; gap: 8px; padding: 8px; background: #f9fafb; border-radius: 6px; border: 1px solid #e5e7eb; }
.reingest-label { display: flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 600; color: #374151; cursor: pointer; margin: 0; }
.loading, .empty-state { text-align: center; color: #6b7280; padding: 32px; font-size: 14px; }
.error-banner {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fca5a5;
  border-radius: 8px;
  padding: 10px 16px;
  font-size: 13px;
  font-weight: 600;
}
</style>
