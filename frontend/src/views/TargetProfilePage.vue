<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageHeader from '@/components/layout/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { targets } from '@/services/api'

const route = useRoute()
const router = useRouter()
const profileId = route.params.id

const profile = ref(null)
const pdbStructures = ref([])
const bindingSites = ref([])
const loadingProfile = ref(false)
const loadingPDB = ref(false)
const loadingSites = ref(false)
const error = ref(null)

const bindingSiteForm = ref({ pdb_id: '', center_x: 0, center_y: 0, center_z: 0, size_x: 20, size_y: 20, size_z: 20 })
const saving = ref(false)

async function loadProfile() {
  loadingProfile.value = true
  try {
    profile.value = await targets.getProfile(profileId)
    if (profile.value.selected_pdb_id) {
      bindingSiteForm.value.pdb_id = profile.value.selected_pdb_id
    }
  } catch (e) {
    error.value = e.detail || 'Failed to load target profile'
  } finally {
    loadingProfile.value = false
  }
}

async function fetchPDB() {
  loadingPDB.value = true
  try {
    const result = await targets.pdb(profileId)
    pdbStructures.value = result.structures || []
  } catch (e) {
    error.value = 'Failed to fetch PDB structures'
  } finally {
    loadingPDB.value = false
  }
}

async function fetchBindingSites() {
  if (!bindingSiteForm.value.pdb_id) return
  loadingSites.value = true
  try {
    const result = await targets.bindingSites(profileId, bindingSiteForm.value.pdb_id)
    bindingSites.value = result.sites || []
  } catch (e) {
    error.value = 'Failed to fetch binding sites'
  } finally {
    loadingSites.value = false
  }
}

async function saveBindingSite() {
  saving.value = true
  try {
    const { pdb_id, center_x, center_y, center_z, size_x, size_y, size_z } = bindingSiteForm.value
    await targets.saveBindingSite(profileId, {
      pdb_id,
      binding_site: { center: [center_x, center_y, center_z], size: [size_x, size_y, size_z] },
    })
    await loadProfile()
  } catch (e) {
    error.value = 'Failed to save binding site'
  } finally {
    saving.value = false
  }
}

function goToScreening() {
  router.push({ name: 'VirtualScreening', query: { target: profileId } })
}

onMounted(loadProfile)
</script>

<template>
  <div>
    <PageHeader :title="profile ? (profile.gene_symbol || profile.uniprot_id) : 'Target Profile'">
      <template #actions>
        <button class="btn btn-primary" :disabled="!profile?.selected_pdb_id || !profile?.binding_site_definition?.center" @click="goToScreening">
          Run Virtual Screening
        </button>
      </template>
    </PageHeader>

    <LoadingSpinner v-if="loadingProfile" />

    <div v-else-if="profile" class="grid-2" style="align-items:start">
      <div>
        <div class="card mb-3">
          <h3 class="card-title">Target Information</h3>
          <table class="data-table">
            <tr><td>UniProt ID</td><td>{{ profile.uniprot_id }}</td></tr>
            <tr><td>Gene Symbol</td><td>{{ profile.gene_symbol }}</td></tr>
            <tr><td>Protein Name</td><td>{{ profile.protein_name }}</td></tr>
            <tr><td>Organism</td><td>{{ profile.organism }}</td></tr>
          </table>
        </div>

        <div class="card mb-3">
          <div class="card-header">
            <h3 class="card-title">PDB Structures</h3>
            <button class="btn btn-sm btn-secondary" :disabled="loadingPDB" @click="fetchPDB">
              {{ loadingPDB ? 'Loading...' : 'Fetch from PDB' }}
            </button>
          </div>
          <LoadingSpinner v-if="loadingPDB" />
          <div v-else-if="pdbStructures.length" style="max-height:200px;overflow-y:auto">
            <div
              v-for="s in pdbStructures" :key="s.pdb_id"
              class="list-item"
              :class="{ selected: bindingSiteForm.pdb_id === s.pdb_id }"
              style="cursor:pointer"
              @click="bindingSiteForm.pdb_id = s.pdb_id; fetchBindingSites()"
            >
              <strong>{{ s.pdb_id }}</strong>
              <span class="text-muted" style="margin-left:8px">score: {{ s.score?.toFixed(2) }}</span>
            </div>
          </div>
          <EmptyState v-else title="No structures loaded" message="Click 'Fetch from PDB' to search RCSB." />
        </div>
      </div>

      <div>
        <div class="card mb-3">
          <h3 class="card-title">Binding Site Definition</h3>
          <div class="form-group">
            <label>PDB ID</label>
            <input v-model="bindingSiteForm.pdb_id" class="form-input" placeholder="e.g. 3ERT" @blur="fetchBindingSites" />
          </div>
          <div class="grid-3" style="gap:8px">
            <div class="form-group">
              <label>Center X</label>
              <input v-model.number="bindingSiteForm.center_x" type="number" class="form-input" />
            </div>
            <div class="form-group">
              <label>Center Y</label>
              <input v-model.number="bindingSiteForm.center_y" type="number" class="form-input" />
            </div>
            <div class="form-group">
              <label>Center Z</label>
              <input v-model.number="bindingSiteForm.center_z" type="number" class="form-input" />
            </div>
            <div class="form-group">
              <label>Size X (Å)</label>
              <input v-model.number="bindingSiteForm.size_x" type="number" class="form-input" />
            </div>
            <div class="form-group">
              <label>Size Y (Å)</label>
              <input v-model.number="bindingSiteForm.size_y" type="number" class="form-input" />
            </div>
            <div class="form-group">
              <label>Size Z (Å)</label>
              <input v-model.number="bindingSiteForm.size_z" type="number" class="form-input" />
            </div>
          </div>
          <button class="btn btn-primary" :disabled="saving" @click="saveBindingSite">
            {{ saving ? 'Saving...' : 'Save Binding Site' }}
          </button>
        </div>

        <div v-if="bindingSites.length" class="card">
          <h3 class="card-title">Detected Sites ({{ bindingSiteForm.pdb_id }})</h3>
          <div v-for="site in bindingSites" :key="site.site_id" class="list-item">
            <strong>{{ site.site_id }}</strong>
            <p class="text-muted" style="margin:4px 0 0">{{ site.details }}</p>
          </div>
        </div>
      </div>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>
  </div>
</template>
