import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

export interface NodeProperty {
  key: string
  label: string
  type: string
  default?: any
  options?: Array<{ label: string; value: any }>
  placeholder?: string
  required?: boolean
}

export interface NodeAction {
  key: string
  label: string
  description: string
  returns: 'image' | 'text' | 'json' | 'none'
}

export interface NodeConfig {
  type: string
  label: string
  category: string
  icon: string
  color: string
  description: string
  properties: NodeProperty[]
  actions?: NodeAction[]
}

export const nodeAPI = {
  /**
   * 获取所有节点配置
   */
  async getNodes() {
    const response = await api.get('/nodes')
    return response.data
  },

  /**
   * 获取所有节点类型
   */
  async getNodeTypes() {
    const response = await api.get('/nodes/types')
    return response.data
  },

  /**
   * 获取节点按类别分组
   */
  async getNodeCategories() {
    const response = await api.get('/nodes/categories')
    return response.data
  },

  /**
   * 获取节点支持的交互方法
   */
  async getNodeActions(nodeType: string) {
    const response = await api.get(`/nodes/${nodeType}/actions`)
    return response.data
  },

  /**
   * 执行节点交互方法
   */
  async executeAction(nodeType: string, action: string, properties: Record<string, any>) {
    const response = await api.post('/nodes/action', {
      node_type: nodeType,
      action,
      properties
    })
    return response.data
  }
}





