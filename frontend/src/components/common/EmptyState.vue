<script setup>
defineProps({ title: String, message: String, actionLabel: String })
defineEmits(['action'])
</script>

<template>
  <div class="empty-state">
    <div style="font-size:48px;margin-bottom:16px">📭</div>
    <h3>{{ title }}</h3>
    <p>{{ message }}</p>
    <button v-if="actionLabel" class="btn btn-primary mt-4" @click="$emit('action')">
      {{ actionLabel }}
    </button>
  </div>
</template>
