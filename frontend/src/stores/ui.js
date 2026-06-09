import { defineStore } from 'pinia'

let toastId = 0

export const useUIStore = defineStore('ui', {
  state: () => ({
    toasts: [],
    dialog: null,
    sidenavOpen: false,
    navCollapsed: false,
  }),

  actions: {
    addToast(message, type = 'info') {
      const id = ++toastId
      this.toasts.push({ id, message, type })
      setTimeout(() => this.removeToast(id), 4000)
    },

    removeToast(id) {
      this.toasts = this.toasts.filter((t) => t.id !== id)
    },

    showConfirm(options) {
      return new Promise((resolve) => {
        this.dialog = { ...options, resolve }
      })
    },

    closeDialog(result) {
      if (this.dialog?.resolve) this.dialog.resolve(result)
      this.dialog = null
    },

    toggleSidenav() {
      this.sidenavOpen = !this.sidenavOpen
    },

    closeSidenav() {
      this.sidenavOpen = false
    },

    toggleNavCollapsed() {
      this.navCollapsed = !this.navCollapsed
    },
  },
})
