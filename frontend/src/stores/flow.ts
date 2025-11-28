import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Flow } from '@/api/flow'

export const useFlowStore = defineStore('flow', () => {
  const currentFlow = ref<Flow | null>(null)
  const flows = ref<Flow[]>([])
  const isModified = ref(false)

  function setCurrentFlow(flow: Flow | null) {
    currentFlow.value = flow
    isModified.value = false
  }

  function setFlows(flowList: Flow[]) {
    flows.value = flowList
  }

  function markAsModified() {
    isModified.value = true
  }

  function updateCurrentFlow(updates: Partial<Flow>) {
    if (currentFlow.value) {
      currentFlow.value = { ...currentFlow.value, ...updates }
      markAsModified()
    }
  }

  return {
    currentFlow,
    flows,
    isModified,
    setCurrentFlow,
    setFlows,
    markAsModified,
    updateCurrentFlow
  }
})

