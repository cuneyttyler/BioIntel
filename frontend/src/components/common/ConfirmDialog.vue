<script setup>
import { useUIStore } from '@/stores/ui'
const ui = useUIStore()
</script>

<template>
  <div v-if="ui.dialog" class="modal-overlay" @click.self="ui.closeDialog(false)">
    <div class="modal">
      <h3 style="margin-bottom:12px">{{ ui.dialog.title || 'Confirm' }}</h3>
      <p style="margin-bottom:20px;color:var(--text-muted)">{{ ui.dialog.message }}</p>
      <div class="flex gap-2 justify-between">
        <button class="btn btn-secondary" @click="ui.closeDialog(false)">Cancel</button>
        <button class="btn btn-danger" @click="ui.closeDialog(true)">
          {{ ui.dialog.confirmLabel || 'Confirm' }}
        </button>
      </div>
    </div>
  </div>
</template>
