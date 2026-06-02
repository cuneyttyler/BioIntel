<script setup>
defineProps({
  components: { type: Array, default: () => [] },
  editable: { type: Boolean, default: false },
})

const emit = defineEmits(['remove'])
</script>

<template>
  <table class="data-table">
    <thead>
      <tr>
        <th>Component</th>
        <th>Type</th>
        <th>Function</th>
        <th>Concentration</th>
        <th>Grade</th>
        <th v-if="editable"></th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="c in components" :key="c.id">
        <td><strong>{{ c.name }}</strong></td>
        <td>{{ c.component_type }}</td>
        <td class="text-muted">{{ c.function || '-' }}</td>
        <td>{{ c.concentration != null ? `${c.concentration} ${c.unit}` : '-' }}</td>
        <td>{{ c.grade || '-' }}</td>
        <td v-if="editable">
          <button class="btn btn-sm btn-danger" @click="emit('remove', c.id)">Remove</button>
        </td>
      </tr>
      <tr v-if="!components.length">
        <td :colspan="editable ? 6 : 5" class="text-muted" style="text-align:center;padding:16px">No components</td>
      </tr>
    </tbody>
  </table>
</template>
