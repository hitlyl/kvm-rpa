/**
 * 节点类型配置
 * 
 * 节点配置完全从后端动态加载，前端不维护硬编码配置。
 */
import { ref } from 'vue'
import { nodeAPI } from '@/api/node'

export interface NodeConfig {
  type: string
  label: string
  category: string
  icon: string
  color: string
  description: string
  properties: NodeProperty[]
}

export interface NodeProperty {
  key: string
  label: string
  type: 'text' | 'number' | 'select' | 'boolean' | 'textarea' | 'array'
  default?: any
  options?: { label: string; value: any }[]
  placeholder?: string
  required?: boolean
  depends_on?: string        // 依赖的属性键名
  depends_value?: any        // 依赖属性需要的值(支持单值或数组)
  group?: string             // 属性分组名称
}

/**
 * 检查属性是否应该显示（根据依赖关系）
 */
export function shouldShowProperty(
  prop: NodeProperty, 
  currentProperties: Record<string, any>
): boolean {
  // 没有依赖关系，始终显示
  if (!prop.depends_on) {
    return true
  }
  
  const dependValue = currentProperties[prop.depends_on]
  const requiredValue = prop.depends_value
  
  // 如果依赖值是数组，检查当前值是否在数组中
  if (Array.isArray(requiredValue)) {
    return requiredValue.includes(dependValue)
  }
  
  // 单值比较
  return dependValue === requiredValue
}

// 从后端加载的节点配置
export const nodeConfigs = ref<NodeConfig[]>([])

// 按类别分组
export const nodesByCategory = ref<Record<string, NodeConfig[]>>({})

// 类别标签（从后端数据推断或使用默认值）
export const categoryLabels: Record<string, string> = {
  source: '数据源',
  process: '处理',
  logic: '逻辑',
  action: '动作'
}

// 加载状态
export const nodesLoading = ref(false)
export const nodesError = ref<string | null>(null)

/**
 * 从后端加载节点配置
 */
export async function loadNodeConfigs(): Promise<boolean> {
  nodesLoading.value = true
  nodesError.value = null
  
  try {
    const response = await nodeAPI.getNodes()
    
    if (response.status === 'ok' && response.data && response.data.nodes) {
      nodeConfigs.value = response.data.nodes
      
      // 按类别分组
      const grouped: Record<string, NodeConfig[]> = {}
      for (const node of nodeConfigs.value) {
        if (!grouped[node.category]) {
          grouped[node.category] = []
        }
        grouped[node.category].push(node)
      }
      nodesByCategory.value = grouped
      
      console.log(`成功加载 ${nodeConfigs.value.length} 个节点配置`)
      return true
    } else {
      nodesError.value = '后端返回的节点数据格式不正确'
      console.error(nodesError.value)
      return false
    }
  } catch (error) {
    nodesError.value = `加载节点配置失败: ${error}`
    console.error(nodesError.value)
    return false
  } finally {
    nodesLoading.value = false
  }
}

/**
 * 根据节点类型获取配置
 */
export function getNodeConfig(nodeType: string): NodeConfig | undefined {
  return nodeConfigs.value.find(n => n.type === nodeType)
}

/**
 * 获取节点的默认属性值
 */
export function getDefaultProperties(nodeType: string): Record<string, any> {
  const config = getNodeConfig(nodeType)
  if (!config) return {}
  
  const defaults: Record<string, any> = {}
  for (const prop of config.properties) {
    if (prop.default !== undefined) {
      defaults[prop.key] = prop.default
    }
  }
  return defaults
}
