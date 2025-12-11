/**
 * 节点工具函数
 */

/**
 * 生成唯一节点ID
 */
export function generateNodeId(): string {
  return `node_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

/**
 * 生成唯一连线ID
 */
export function generateEdgeId(): string {
  return `edge_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

/**
 * 获取节点默认属性
 */
export function getDefaultProperties(nodeType: string, config: any): Record<string, any> {
  const properties: Record<string, any> = {}
  
  if (config && config.properties) {
    config.properties.forEach((prop: any) => {
      if (prop.default !== undefined) {
        properties[prop.key] = prop.default
      } else if (prop.type === 'boolean') {
        properties[prop.key] = false
      } else if (prop.type === 'number') {
        properties[prop.key] = 0
      } else if (prop.type === 'text' || prop.type === 'textarea') {
        properties[prop.key] = ''
      } else if (prop.type === 'select' && prop.options && prop.options.length > 0) {
        properties[prop.key] = prop.options[0].value
      }
    })
  }
  
  return properties
}


















