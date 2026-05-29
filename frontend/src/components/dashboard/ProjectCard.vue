<script setup>
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useProjectStore } from '@/stores/projects'

const props = defineProps({ project: Object })
const store = useProjectStore()
const confirming = ref(false)
const deleting = ref(false)

const deleteProject = async () => {
  deleting.value = true
  try {
    await store.deleteProject(props.project.id)
  } finally {
    deleting.value = false
    confirming.value = false
  }
}
</script>

<template>
  <div class="card" style="display:flex;flex-direction:column;gap:12px">
    <div class="flex items-center gap-2 justify-between">
      <span class="font-bold" style="font-size:15px">{{ project.name }}</span>
      <span :class="['badge', `badge-${project.phase}`]">{{ project.phase }}</span>
    </div>
    <p v-if="project.description" class="text-muted text-sm" style="margin:0">
      {{ project.description.slice(0, 100) }}{{ project.description.length > 100 ? '...' : '' }}
    </p>
    <div class="flex gap-3 text-sm text-muted">
      <span>{{ project.compound_count }} compounds</span>
      <span>{{ project.experiment_count }} experiments</span>
    </div>
    <div class="flex gap-2">
      <span :class="['badge', `badge-${project.status}`]">{{ project.status.replace('_', ' ') }}</span>
    </div>
    <div class="flex items-center gap-2 mt-4" style="flex-wrap:wrap">
      <RouterLink :to="`/projects/${project.id}/edit`" class="btn btn-secondary btn-sm">Edit</RouterLink>
      <RouterLink :to="`/projects/${project.id}/risk`" class="btn btn-secondary btn-sm">Risk</RouterLink>
      <RouterLink :to="`/projects/${project.id}/documents`" class="btn btn-secondary btn-sm">Docs</RouterLink>
      <div style="margin-left:auto">
        <div v-if="!confirming">
          <button class="btn btn-sm" style="color:#dc2626;border-color:#dc2626" @click="confirming = true">Delete</button>
        </div>
        <div v-else class="flex items-center gap-1">
          <span class="text-sm text-muted">Sure?</span>
          <button class="btn btn-sm" style="background:#dc2626;color:#fff;border-color:#dc2626" :disabled="deleting" @click="deleteProject">
            {{ deleting ? '...' : 'Yes' }}
          </button>
          <button class="btn btn-secondary btn-sm" @click="confirming = false">No</button>
        </div>
      </div>
    </div>
  </div>
</template>
