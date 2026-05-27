<script setup>
defineProps({ title: String })
</script>

<template>
  <div class="page-header">
    <h1>{{ title }}</h1>
    <div class="actions">
      <slot name="actions" />
    </div>
  </div>
</template>
