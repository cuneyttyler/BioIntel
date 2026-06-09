<template>
  <span class="status-badge" :class="`status-${status}`">{{ label }}</span>
</template>

<script setup>
const props = defineProps({
  status: { type: String, required: true },
})

const LABELS = {
  pending: 'Pending',
  in_progress: 'In Progress',
  awaiting_approval: 'Awaiting Approval',
  approved: 'Approved',
  revision_needed: 'Revision Needed',
  completed: 'Completed',
  skipped: 'Skipped',
  abandoned: 'Abandoned',
}

const label = computed(() => LABELS[props.status] || props.status)
</script>

<script>
import { computed } from 'vue'
</script>

<style scoped>
.status-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.3px;
  text-transform: uppercase;
}
.status-pending { background: var(--step-pending, #e5e7eb); color: #374151; }
.status-in_progress { background: var(--step-in-progress, #dbeafe); color: #1d4ed8; }
.status-awaiting_approval { background: var(--step-awaiting, #fef3c7); color: #92400e; }
.status-approved { background: var(--step-approved, #d1fae5); color: #065f46; }
.status-revision_needed { background: var(--step-revision, #fee2e2); color: #991b1b; }
.status-completed { background: var(--step-completed, #a7f3d0); color: #065f46; }
.status-skipped { background: #f3f4f6; color: #6b7280; }
.status-abandoned { background: #f3f4f6; color: #9ca3af; text-decoration: line-through; }
</style>
