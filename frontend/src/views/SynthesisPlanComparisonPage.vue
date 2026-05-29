<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { synthesisPlan as synthesisPlanApi } from '@/services/api'
import PageHeader from '@/components/layout/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const route = useRoute()
const router = useRouter()

const plans = ref([])
const loading = ref(false)
const error = ref(null)

const SynthesisTreeNode = {
  name: 'SynthesisTreeNode',
  props: { node: Object, depth: { type: Number, default: 0 } },
  template: `
    <div :style="{ paddingLeft: depth * 16 + 'px', borderLeft: depth ? '2px solid var(--border)' : 'none', marginLeft: depth ? '8px' : '0', paddingTop: '4px' }">
      <div class="flex items-center gap-2" style="flex-wrap:wrap;margin-bottom:4px">
        <code style="font-size:11px;background:var(--surface-2,#f3f4f6);padding:2px 8px;border-radius:4px;word-break:break-all">{{ node.smiles }}</code>
        <span v-if="node.terminal" class="badge badge-completed" style="font-size:10px">starting material</span>
      </div>
      <div v-for="(child, i) in node.children" :key="i" style="margin-top:4px">
        <div class="text-muted text-sm" style="font-size:11px;margin-bottom:2px">↓ {{ child.transform }}</div>
        <SynthesisTreeNode v-for="(p, j) in child.precursors" :key="j" :node="p" :depth="depth + 1" />
      </div>
    </div>
  `,
}
SynthesisTreeNode.components = { SynthesisTreeNode }

onMounted(async () => {
  const ids = (route.query.plans || '').split(',').map(Number).filter(Boolean)
  if (ids.length < 2) {
    error.value = 'Select at least 2 synthesis plans to compare.'
    return
  }
  loading.value = true
  try {
    plans.value = await Promise.all(ids.map(id => synthesisPlanApi.get(id)))
  } catch {
    error.value = 'Failed to load one or more plans.'
  } finally {
    loading.value = false
  }
})

const smilesTrunc = (s) => s ? (s.length > 40 ? s.slice(0, 40) + '…' : s) : '—'
const planTypeBadge = (t) => t === 'retro' ? 'Single-Step' : 'Multi-Step'
const stepCount = (plan) => {
  const data = plan.route_data
  if (!data) return 0
  if (data.results?.length) return data.results.length
  if (data.tree) return '(tree)'
  return 0
}
</script>

<template>
  <div>
    <PageHeader title="Synthesis Plan Comparison">
      <template #actions>
        <button class="btn btn-secondary btn-sm" @click="router.back()">← Back</button>
      </template>
    </PageHeader>

    <div v-if="loading" style="text-align:center;padding:64px"><LoadingSpinner /></div>

    <div v-else-if="error" class="card" style="padding:32px;text-align:center;color:#dc2626">
      {{ error }}
      <br />
      <button class="btn btn-secondary" style="margin-top:16px" @click="router.back()">Go back</button>
    </div>

    <div v-else-if="plans.length">
      <!-- Header row: one card per plan -->
      <div :style="`display:grid;grid-template-columns:repeat(${plans.length},1fr);gap:16px;margin-bottom:16px`">
        <div v-for="plan in plans" :key="plan.id" class="card">
          <div class="flex items-center gap-2 mb-2">
            <span class="badge">{{ planTypeBadge(plan.plan_type) }}</span>
            <span class="badge" :class="plan.status === 'active' ? 'badge-active' : plan.status === 'draft' ? '' : 'badge-completed'">{{ plan.status }}</span>
          </div>
          <div class="text-muted text-sm" style="margin-bottom:6px;font-size:11px;text-transform:uppercase;letter-spacing:0.04em;font-weight:600">Target SMILES</div>
          <code style="font-size:11px;background:var(--surface-2,#f3f4f6);padding:4px 8px;border-radius:4px;word-break:break-all;display:block">{{ plan.target_smiles }}</code>
          <img
            v-if="plan.target_smiles"
            :src="`https://depict.chembl.io/svg/?smi=${encodeURIComponent(plan.target_smiles)}&molSize=200x120`"
            style="width:100%;margin-top:8px;border-radius:4px;background:#fff"
            @error="$event.target.style.display='none'"
          />
          <div class="flex items-center gap-4 text-muted text-sm" style="margin-top:10px;font-size:12px">
            <span>Steps: <strong>{{ stepCount(plan) }}</strong></span>
            <span>Experiments: <strong>{{ plan.experiment_count || 0 }}</strong></span>
            <span>Created: <strong>{{ plan.created_at ? new Date(plan.created_at).toLocaleDateString() : '—' }}</strong></span>
          </div>
        </div>
      </div>

      <!-- Route detail: one column per plan -->
      <div :style="`display:grid;grid-template-columns:repeat(${plans.length},1fr);gap:16px`">
        <div v-for="plan in plans" :key="plan.id + '-route'">

          <!-- Single-step retro route -->
          <template v-if="plan.plan_type === 'retro' && plan.route_data?.results?.length">
            <div v-for="(step, i) in plan.route_data.results" :key="i" class="card mb-3" style="padding:14px">
              <div class="flex items-center gap-2 mb-1">
                <span class="badge badge-active" style="font-size:11px">Step {{ i + 1 }}</span>
                <span class="font-bold text-sm">{{ step.transform }}</span>
              </div>
              <div class="text-muted text-sm mb-2" style="font-size:12px">{{ step.forward_reaction }}</div>
              <div class="text-muted text-sm" style="font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:0.04em;margin-bottom:6px">Starting Materials</div>
              <div class="flex items-center gap-2" style="flex-wrap:wrap">
                <template v-for="(p, j) in step.precursors" :key="j">
                  <code style="font-size:11px;background:var(--surface-2,#f3f4f6);padding:3px 8px;border-radius:4px;word-break:break-all;max-width:200px">{{ p }}</code>
                  <span v-if="j < step.precursors.length - 1" class="text-muted font-bold">+</span>
                </template>
                <span class="text-muted">→ target</span>
              </div>
            </div>
          </template>

          <!-- Multi-step tree -->
          <div v-else-if="plan.plan_type === 'tree' && plan.route_data?.tree" class="card mb-3" style="padding:14px">
            <div class="card-title mb-2" style="font-size:13px">Synthesis Tree</div>
            <SynthesisTreeNode :node="plan.route_data.tree" />
          </div>

          <div v-else class="card mb-3 text-muted text-sm" style="padding:14px">
            No route data available for this plan.
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
