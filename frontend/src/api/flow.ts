import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

export interface Flow {
  id: string
  name: string
  description: string
  version: string
  nodes: any[]
  edges: any[]
  variables: Record<string, any>
  created_at: string
  updated_at: string
}

export interface FlowStatus {
  flow_id: string
  flow_name: string
  status: 'stopped' | 'running' | 'paused' | 'error'
  loop_count: number
  total_node_executions: number
  start_time: string | null
  last_loop_time: string | null
  error: string | null
}

export const flowAPI = {
  // 获取流程列表
  async listFlows() {
    const response = await api.get('/flows')
    return response.data
  },

  // 获取流程详情
  async getFlow(flowId: string) {
    const response = await api.get(`/flows/${flowId}`)
    return response.data
  },

  // 创建流程
  async createFlow(flowData: Partial<Flow>) {
    const response = await api.post('/flows', flowData)
    return response.data
  },

  // 更新流程
  async updateFlow(flowId: string, flowData: Partial<Flow>) {
    const response = await api.put(`/flows/${flowId}`, flowData)
    return response.data
  },

  // 删除流程
  async deleteFlow(flowId: string) {
    const response = await api.delete(`/flows/${flowId}`)
    return response.data
  },

  // 验证流程
  async validateFlow(flowId: string) {
    const response = await api.get(`/flows/${flowId}/validate`)
    return response.data
  },

  // 执行流程（旧接口，等同于 start）
  async executeFlow(flowId: string) {
    const response = await api.post(`/flows/${flowId}/execute`)
    return response.data
  },

  // 启动流程循环执行
  async startFlow(flowId: string) {
    const response = await api.post(`/flows/${flowId}/start`)
    return response.data
  },

  // 停止流程
  async stopFlow(flowId: string) {
    const response = await api.post(`/flows/${flowId}/stop`)
    return response.data
  },

  // 暂停流程
  async pauseFlow(flowId: string) {
    const response = await api.post(`/flows/${flowId}/pause`)
    return response.data
  },

  // 恢复流程
  async resumeFlow(flowId: string) {
    const response = await api.post(`/flows/${flowId}/resume`)
    return response.data
  },

  // 获取流程运行状态
  async getFlowStatus(flowId: string): Promise<{ status: string; data: FlowStatus }> {
    const response = await api.get(`/flows/${flowId}/status`)
    return response.data
  },

  // 获取所有运行中的流程
  async getRunningFlows() {
    const response = await api.get('/flows/running')
    return response.data
  },

  // 获取所有流程状态
  async getAllFlowsStatus() {
    const response = await api.get('/flows/status/all')
    return response.data
  },

  // 获取模板
  async getTemplates() {
    const response = await api.get('/flows/templates/list')
    return response.data
  }
}
