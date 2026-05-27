<script setup>
defineProps({ message: String, retry: Function })
</script>

<template>
  <div style="background:#fee2e2;border:1px solid #fca5a5;border-radius:8px;padding:12px 16px;color:#991b1b;display:flex;align-items:center;gap:12px;">
    <span style="flex:1">⚠️ {{ message }}</span>
    <button v-if="retry" class="btn btn-sm btn-secondary" @click="retry">Retry</button>
  </div>
</template>
