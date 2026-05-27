<script setup>
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="card">
    <div class="card-title">Quick Actions</div>
    <div class="flex gap-2" style="flex-wrap:wrap">
      <RouterLink to="/projects/new" class="btn btn-primary">➕ New Project</RouterLink>
      <RouterLink to="/experiments/new" class="btn btn-secondary">🧪 New Experiment</RouterLink>
      <RouterLink to="/chat" class="btn btn-secondary">💬 Open Chat</RouterLink>
      <RouterLink to="/diseases" class="btn btn-secondary">🔬 Explore Diseases</RouterLink>
    </div>
  </div>
</template>
