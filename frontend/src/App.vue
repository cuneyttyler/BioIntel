<script setup>
import SideNav from '@/components/layout/SideNav.vue'
import TopBar from '@/components/layout/TopBar.vue'
import ToastNotification from '@/components/common/ToastNotification.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
</script>

<template>
  <div class="app-shell">
    <SideNav />
    <div class="main-area">
      <TopBar />
      <main class="page-content">
        <router-view />
      </main>
    </div>
    <ToastNotification />
    <ConfirmDialog />
  </div>
</template>
