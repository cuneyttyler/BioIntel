<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: String,
  placeholder: { type: String, default: 'Search...' },
  debounce: { type: Number, default: 400 },
  loading: Boolean,
})
const emit = defineEmits(['update:modelValue'])

const local = ref(props.modelValue || '')
let timer = null

watch(local, (val) => {
  clearTimeout(timer)
  timer = setTimeout(() => emit('update:modelValue', val), props.debounce)
})

watch(() => props.modelValue, (val) => { if (val !== local.value) local.value = val })
</script>

<template>
  <div style="position:relative">
    <input
      v-model="local"
      class="form-control"
      :placeholder="placeholder"
    />
    <LoadingSpinner
      v-if="loading"
      size="sm"
      style="position:absolute;right:10px;top:50%;transform:translateY(-50%)"
    />
  </div>
</template>

<script>
import LoadingSpinner from './LoadingSpinner.vue'
export default { components: { LoadingSpinner } }
</script>
