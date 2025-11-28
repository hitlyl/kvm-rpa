/**
 * SSE 事件流客户端
 * 
 * 提供流程执行状态的实时订阅功能。
 */

export interface SSEMessage {
  type: string
  flow_id: string
  data: Record<string, any>
  timestamp: string
}

export type SSEMessageHandler = (message: SSEMessage) => void

/**
 * 流程 SSE 客户端
 */
export class FlowSSEClient {
  private eventSource: EventSource | null = null
  private flowId: string | null = null
  private handlers: Map<string, Set<SSEMessageHandler>> = new Map()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private isConnected = false

  /**
   * 连接到流程事件流
   * @param flowId 流程 ID，为空则订阅所有流程
   */
  connect(flowId?: string): void {
    if (this.eventSource) {
      this.disconnect()
    }

    this.flowId = flowId || null
    const url = flowId 
      ? `/api/sse/flows/${flowId}/events`
      : '/api/sse/flows/events'

    console.log(`[SSE] 连接到: ${url}`)

    this.eventSource = new EventSource(url)

    this.eventSource.onopen = () => {
      console.log('[SSE] 连接已建立')
      this.isConnected = true
      this.reconnectAttempts = 0
    }

    this.eventSource.onmessage = (event) => {
      try {
        // 忽略心跳
        if (event.data.startsWith(':')) {
          return
        }

        const message: SSEMessage = JSON.parse(event.data)
        this.dispatchMessage(message)
      } catch (error) {
        console.error('[SSE] 解析消息失败:', error, event.data)
      }
    }

    this.eventSource.onerror = (error) => {
      console.error('[SSE] 连接错误:', error)
      this.isConnected = false
      
      // 尝试重连
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++
        console.log(`[SSE] ${this.reconnectDelay}ms 后尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
        setTimeout(() => {
          if (this.flowId !== null || flowId === undefined) {
            this.connect(this.flowId || undefined)
          }
        }, this.reconnectDelay * this.reconnectAttempts)
      }
    }
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    if (this.eventSource) {
      console.log('[SSE] 断开连接')
      this.eventSource.close()
      this.eventSource = null
      this.isConnected = false
    }
  }

  /**
   * 订阅特定类型的消息
   * @param type 消息类型
   * @param handler 处理函数
   */
  on(type: string, handler: SSEMessageHandler): void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set())
    }
    this.handlers.get(type)!.add(handler)
  }

  /**
   * 取消订阅
   * @param type 消息类型
   * @param handler 处理函数
   */
  off(type: string, handler: SSEMessageHandler): void {
    const handlers = this.handlers.get(type)
    if (handlers) {
      handlers.delete(handler)
    }
  }

  /**
   * 订阅所有消息
   * @param handler 处理函数
   */
  onAny(handler: SSEMessageHandler): void {
    this.on('*', handler)
  }

  /**
   * 分发消息到处理函数
   */
  private dispatchMessage(message: SSEMessage): void {
    // 调用特定类型的处理函数
    const typeHandlers = this.handlers.get(message.type)
    if (typeHandlers) {
      typeHandlers.forEach(handler => {
        try {
          handler(message)
        } catch (error) {
          console.error(`[SSE] 处理 ${message.type} 消息时出错:`, error)
        }
      })
    }

    // 调用通配符处理函数
    const anyHandlers = this.handlers.get('*')
    if (anyHandlers) {
      anyHandlers.forEach(handler => {
        try {
          handler(message)
        } catch (error) {
          console.error('[SSE] 处理消息时出错:', error)
        }
      })
    }
  }

  /**
   * 获取连接状态
   */
  get connected(): boolean {
    return this.isConnected
  }
}

// 导出单例
export const flowSSE = new FlowSSEClient()

// 便捷的消息类型常量
export const SSEMessageTypes = {
  NODE_START: 'node_start',
  NODE_COMPLETE: 'node_complete',
  NODE_ERROR: 'node_error',
  LOOP_START: 'loop_start',
  LOOP_COMPLETE: 'loop_complete',
  FLOW_START: 'flow_start',
  FLOW_STOP: 'flow_stop',
  FLOW_ERROR: 'flow_error',
  FLOW_STATUS: 'flow_status',
  DEBUG: 'debug',
  CONNECTED: 'connected'
} as const

