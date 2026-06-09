/**
 * Composable that wires a page component into the AI panel context system.
 *
 * Usage in a page component:
 *
 *   useAIPageContext({
 *     pageType: 'FormulationPlanning',
 *     projectIdRef: computed(() => parseInt(route.params.id)),
 *     getEntity: () => ({ dosage_form: form.dosage_form, ... }),
 *     applyFn: (s) => {
 *       if (s.dosage_form !== undefined) form.dosage_form = s.dosage_form
 *       // ...
 *     },
 *   })
 */
import { watchEffect, watch } from 'vue'
import { useAIPanelContextStore } from '@/stores/aiPanelContext'

export function useAIPageContext({ pageType, projectIdRef, getEntity, applyFn }) {
  const store = useAIPanelContextStore()

  // Keep context in sync whenever the project id or entity data changes.
  // watchEffect auto-tracks any reactive values accessed inside getEntity().
  watchEffect(() => {
    const id = typeof projectIdRef === 'function' ? projectIdRef() : projectIdRef?.value
    if (id) {
      store.setPageContext(pageType, id, getEntity ? getEntity() : {})
    }
  })

  // Apply suggestions when the user clicks "Apply" in the AI panel.
  watch(
    () => store.applyTrigger,
    () => {
      if (store.pendingSuggestions && applyFn) {
        applyFn(store.pendingSuggestions)
      }
    },
  )
}
