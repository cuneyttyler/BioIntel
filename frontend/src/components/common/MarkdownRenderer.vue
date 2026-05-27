<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const props = defineProps({ content: { type: String, default: '' } })
const html = computed(() => DOMPurify.sanitize(marked.parse(props.content || '')))
</script>

<template>
  <div class="markdown-content" v-html="html" />
</template>
