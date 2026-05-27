import { defineStore } from 'pinia'
import { projects as projectsApi } from '@/services/api'

export const useProjectStore = defineStore('projects', {
  state: () => ({
    projects: [],
    currentProject: null,
    loading: false,
    error: null,
  }),

  getters: {
    activeProjects: (state) => state.projects.filter((p) => p.status === 'active'),
  },

  actions: {
    async fetchProjects() {
      this.loading = true
      this.error = null
      try {
        this.projects = await projectsApi.list()
      } catch (e) {
        this.error = e
      } finally {
        this.loading = false
      }
    },

    async fetchProject(id) {
      this.loading = true
      try {
        this.currentProject = await projectsApi.get(id)
      } catch (e) {
        this.error = e
      } finally {
        this.loading = false
      }
    },

    async createProject(data) {
      const project = await projectsApi.create(data)
      this.projects.unshift(project)
      return project
    },

    async updateProject(id, data) {
      const project = await projectsApi.update(id, data)
      const idx = this.projects.findIndex((p) => p.id === id)
      if (idx !== -1) this.projects[idx] = project
      if (this.currentProject?.id === id) this.currentProject = project
      return project
    },

    async deleteProject(id) {
      await projectsApi.delete(id)
      this.projects = this.projects.filter((p) => p.id !== id)
    },
  },
})
