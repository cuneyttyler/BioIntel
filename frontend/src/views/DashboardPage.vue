<script setup>
import { onMounted } from 'vue'
import { useProjectStore } from '@/stores/projects'
import { useExperimentStore } from '@/stores/experiments'
import PageHeader from '@/components/layout/PageHeader.vue'
import ProjectCard from '@/components/dashboard/ProjectCard.vue'
import RecentActivityFeed from '@/components/dashboard/RecentActivityFeed.vue'
import QuickActionPanel from '@/components/dashboard/QuickActionPanel.vue'
import StatsBadge from '@/components/common/StatsBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const projectStore = useProjectStore()
const expStore = useExperimentStore()

onMounted(async () => {
  await Promise.all([projectStore.fetchProjects(), expStore.fetchRecent()])
})
</script>

<template>
  <div>
    <PageHeader title="Dashboard">
      <template #actions>
        <RouterLink to="/projects/new" class="btn btn-primary">New Project</RouterLink>
      </template>
    </PageHeader>

    <div class="grid-4 mb-4">
      <StatsBadge :value="projectStore.projects.length" label="Total Projects" />
      <StatsBadge :value="projectStore.activeProjects.length" label="Active" />
      <StatsBadge :value="expStore.recentExperiments.length" label="Recent Experiments" />
      <StatsBadge :value="projectStore.projects.filter(p => p.status === 'completed').length" label="Completed" />
    </div>

    <QuickActionPanel class="mb-4" />

    <div class="grid-2" style="align-items:start">
      <div>
        <h2 style="font-size:16px;margin-bottom:16px">Projects</h2>
        <div v-if="projectStore.loading">
          <LoadingSpinner />
        </div>
        <EmptyState
          v-else-if="!projectStore.projects.length"
          title="No projects yet"
          message="Create your first project to get started."
          action-label="New Project"
          @action="$router.push('/projects/new')"
        />
        <div v-else style="display:flex;flex-direction:column;gap:12px">
          <ProjectCard v-for="p in projectStore.projects" :key="p.id" :project="p" />
        </div>
      </div>

      <RecentActivityFeed :activities="expStore.recentExperiments" />
    </div>
  </div>
</template>

<script>
import { RouterLink } from 'vue-router'
export default { components: { RouterLink } }
</script>
