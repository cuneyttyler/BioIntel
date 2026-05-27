<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/projects'
import { compounds as compoundsApi } from '@/services/api'
import { useUIStore } from '@/stores/ui'
import PageHeader from '@/components/layout/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ProjectForm from '@/components/projects/ProjectForm.vue'
import CompoundSearch from '@/components/projects/CompoundSearch.vue'
import CompoundPreviewCard from '@/components/projects/CompoundPreviewCard.vue'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const ui = useUIStore()

const isEdit = !!route.params.id
const existingProject = ref(null)
const selectedCompound = ref(null)
const saving = ref(false)

onMounted(async () => {
  if (isEdit) {
    await projectStore.fetchProject(route.params.id)
    existingProject.value = projectStore.currentProject
  }
})

const handleSubmit = async (formData) => {
  saving.value = true
  try {
    let project
    if (isEdit) {
      project = await projectStore.updateProject(route.params.id, formData)
    } else {
      project = await projectStore.createProject(formData)
    }

    if (selectedCompound.value && !isEdit) {
      await compoundsApi.create({ ...selectedCompound.value, project: project.id })
    }

    ui.addToast(`Project ${isEdit ? 'updated' : 'created'} successfully`, 'success')
    router.push('/')
  } catch (e) {
    ui.addToast('Failed to save project', 'error')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div style="max-width:700px">
    <PageHeader :title="isEdit ? 'Edit Project' : 'New Project'" />

    <div v-if="!isEdit || existingProject" class="card mb-4">
      <ProjectForm :initial="existingProject || {}" @submit="handleSubmit" />
    </div>
    <div v-else class="card mb-4" style="padding:32px;text-align:center">
      <LoadingSpinner />
    </div>

    <div v-if="!isEdit" class="card mb-4">
      <div class="card-title">Attach Compound</div>
      <CompoundSearch @select="selectedCompound = $event" />
      <CompoundPreviewCard :compound="selectedCompound" />
    </div>
  </div>
</template>
