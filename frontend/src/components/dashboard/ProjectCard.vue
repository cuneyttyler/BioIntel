<script setup>
import { RouterLink } from 'vue-router'
defineProps({ project: Object })
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
    <div class="flex gap-2 mt-4">
      <RouterLink :to="`/projects/${project.id}/edit`" class="btn btn-secondary btn-sm">Edit</RouterLink>
      <RouterLink :to="`/projects/${project.id}/risk`" class="btn btn-secondary btn-sm">Risk</RouterLink>
      <RouterLink :to="`/projects/${project.id}/documents`" class="btn btn-secondary btn-sm">Docs</RouterLink>
    </div>
  </div>
</template>
