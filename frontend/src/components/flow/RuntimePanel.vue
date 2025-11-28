<template>
  <div class="runtime-panel">
    <div class="panel-header">
      <h4>运行时监控</h4>
      <el-tag :type="statusType" size="small">{{ statusLabel }}</el-tag>
    </div>

    <!-- 运行统计 -->
    <div class="stats-section" v-if="isRunning || hasExecuted">
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="循环次数">
          {{ loopCount }}
        </el-descriptions-item>
        <el-descriptions-item label="节点执行">
          {{ nodeExecutions }}
        </el-descriptions-item>
        <el-descriptions-item label="当前节点">
          <span class="current-node">{{ currentNodeLabel || '-' }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="耗时">
          {{ lastLoopDuration }}ms
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <!-- 执行日志 -->
    <div class="log-section">
      <div class="log-header">
        <span>执行日志</span>
        <el-button size="small" text @click="clearLogs">清空</el-button>
      </div>
      <div class="log-list" ref="logListRef">
        <div 
          v-for="(log, index) in logs" 
          :key="index" 
          :class="['log-item', `log-${log.type}`]"
        >
          <span class="log-time">{{ formatTime(log.timestamp) }}</span>
          <span class="log-type">{{ log.typeLabel }}</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
        <div v-if="logs.length === 0" class="log-empty">
          暂无日志
        </div>
      </div>
    </div>

    <!-- 预览图 -->
    <div class="preview-section" v-if="previewImage">
      <div class="preview-header">
        <span>画面预览</span>
        <div class="preview-actions">
          <el-button size="small" text @click="refreshPreview" :loading="loadingPreview">
            刷新
          </el-button>
          <el-button size="small" text type="danger" @click="closePreview">
            关闭
          </el-button>
        </div>
      </div>
      <div class="preview-container">
        <img :src="previewImage" alt="KVM 预览" />
      </div>
    </div>

    <!-- 节点交互 -->
    <div class="actions-section" v-if="selectedNodeActions.length > 0">
      <div class="actions-header">
        <span>节点操作</span>
      </div>
      <div class="actions-list">
        <el-button
          v-for="action in selectedNodeActions"
          :key="action.key"
          size="small"
          @click="executeAction(action)"
          :loading="executingAction === action.key"
        >
          {{ action.label }}
        </el-button>
      </div>
    </div>

    <!-- 错误信息 -->
    <div class="error-section" v-if="errorMessage">
      <el-alert
        :title="errorNode ? `节点 [${errorNode}] 执行失败` : '流程执行失败'"
        type="error"
        :description="errorMessage"
        show-icon
        :closable="false"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { FlowSSEClient, SSEMessage, SSEMessageTypes } from '@/api/sse'
import { nodeAPI } from '@/api/node'

interface LogEntry {
  type: 'info' | 'success' | 'warning' | 'error'
  typeLabel: string
  message: string
  timestamp: string
}

const props = defineProps<{
  flowId: string
  selectedNode?: any
}>()

const emit = defineEmits<{
  (e: 'node-highlight', nodeId: string): void
}>()

// 状态
const isRunning = ref(false)
const hasExecuted = ref(false)
const loopCount = ref(0)
const nodeExecutions = ref(0)
const currentNodeLabel = ref('')
const lastLoopDuration = ref(0)
const errorMessage = ref('')
const errorNode = ref('')
const logs = ref<LogEntry[]>([])
const logListRef = ref<HTMLElement | null>(null)

// 预览
const previewImage = ref('')
const loadingPreview = ref(false)

// 节点交互
const selectedNodeActions = ref<any[]>([])
const executingAction = ref('')

// SSE 客户端
let sseClient: FlowSSEClient | null = null

// 计算属性
const statusType = computed(() => {
  if (errorMessage.value) return 'danger'
  if (isRunning.value) return 'success'
  return 'info'
})

const statusLabel = computed(() => {
  if (errorMessage.value) return '错误'
  if (isRunning.value) return '运行中'
  if (hasExecuted.value) return '已停止'
  return '未运行'
})

// 方法
function formatTime(timestamp: string): string {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit' 
  })
}

function addLog(type: LogEntry['type'], typeLabel: string, message: string) {
  logs.value.unshift({
    type,
    typeLabel,
    message,
    timestamp: new Date().toISOString()
  })
  
  // 限制日志数量
  if (logs.value.length > 100) {
    logs.value.pop()
  }
}

function clearLogs() {
  logs.value = []
}

function handleSSEMessage(message: SSEMessage) {
  switch (message.type) {
    case SSEMessageTypes.FLOW_START:
      isRunning.value = true
      hasExecuted.value = true
      errorMessage.value = ''
      errorNode.value = ''
      addLog('info', '流程', `流程已启动: ${message.data.flow_name}`)
      break
      
    case SSEMessageTypes.FLOW_STOP:
      isRunning.value = false
      addLog('info', '流程', `流程已停止，共执行 ${message.data.loop_count} 轮`)
      break
      
    case SSEMessageTypes.FLOW_ERROR:
      isRunning.value = false
      errorMessage.value = message.data.error
      errorNode.value = message.data.error_node || ''
      addLog('error', '错误', message.data.error)
      break
      
    case SSEMessageTypes.LOOP_START:
      loopCount.value = message.data.loop_count
      addLog('info', '循环', `开始第 ${message.data.loop_count} 轮`)
      break
      
    case SSEMessageTypes.LOOP_COMPLETE:
      lastLoopDuration.value = Math.round(message.data.duration_ms)
      break
      
    case SSEMessageTypes.NODE_START:
      currentNodeLabel.value = message.data.node_label
      emit('node-highlight', message.data.node_id)
      addLog('info', '节点', `开始执行: ${message.data.node_label}`)
      break
      
    case SSEMessageTypes.NODE_COMPLETE:
      nodeExecutions.value++
      const duration = Math.round(message.data.duration_ms)
      addLog('success', '节点', `执行完成: ${message.data.node_label} (${duration}ms)`)
      break
      
    case SSEMessageTypes.NODE_ERROR:
      addLog('error', '节点', `执行失败: ${message.data.node_label} - ${message.data.error}`)
      break
      
    case SSEMessageTypes.DEBUG:
      addLog('info', '调试', message.data.message)
      break
  }
}

async function refreshPreview() {
  if (!props.selectedNode || props.selectedNode.type !== 'kvm_source') {
    return
  }
  
  loadingPreview.value = true
  try {
    const response = await nodeAPI.executeAction(
      'kvm_source',
      'get_preview',
      props.selectedNode.properties || {}
    )
    
    if (response.status === 'ok' && response.data?.success) {
      const { format, base64 } = response.data.data
      previewImage.value = `data:image/${format};base64,${base64}`
    }
  } catch (error) {
    console.error('获取预览图失败:', error)
  } finally {
    loadingPreview.value = false
  }
}

function closePreview() {
  previewImage.value = ''
}

async function executeAction(action: any) {
  if (!props.selectedNode) return
  
  executingAction.value = action.key
  try {
    const response = await nodeAPI.executeAction(
      props.selectedNode.type,
      action.key,
      props.selectedNode.properties || {}
    )
    
    if (response.status === 'ok' && response.data?.success) {
      if (action.returns === 'image' && response.data.data) {
        const { format, base64 } = response.data.data
        previewImage.value = `data:image/${format};base64,${base64}`
      } else if (action.returns === 'json') {
        addLog('success', '操作', `${action.label}: ${JSON.stringify(response.data.data)}`)
      } else {
        addLog('success', '操作', `${action.label} 执行成功`)
      }
    } else {
      addLog('error', '操作', `${action.label} 失败: ${response.data?.error || response.message}`)
    }
  } catch (error: any) {
    addLog('error', '操作', `${action.label} 异常: ${error.message}`)
  } finally {
    executingAction.value = ''
  }
}

// 监听选中节点变化
watch(() => props.selectedNode, async (node) => {
  selectedNodeActions.value = []
  
  if (node?.type) {
    try {
      const response = await nodeAPI.getNodeActions(node.type)
      if (response.status === 'ok' && response.data?.actions) {
        selectedNodeActions.value = response.data.actions
      }
    } catch (error) {
      console.error('获取节点交互方法失败:', error)
    }
  }
}, { immediate: true })

// 生命周期
onMounted(() => {
  if (props.flowId) {
    sseClient = new FlowSSEClient()
    sseClient.onAny(handleSSEMessage)
    sseClient.connect(props.flowId)
  }
})

onUnmounted(() => {
  if (sseClient) {
    sseClient.disconnect()
    sseClient = null
  }
})
</script>

<style scoped>
.runtime-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 8px;
  border-bottom: 1px solid #e4e7ed;
}

.panel-header h4 {
  margin: 0;
  font-size: 14px;
  color: #303133;
}

.stats-section {
  flex-shrink: 0;
}

.current-node {
  color: #409eff;
  font-weight: 500;
}

.log-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 150px;
  overflow: hidden;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 13px;
  color: #606266;
}

.log-list {
  flex: 1;
  overflow-y: auto;
  background: #fafafa;
  border-radius: 4px;
  padding: 8px;
  font-size: 12px;
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
}

.log-item {
  padding: 4px 0;
  display: flex;
  gap: 8px;
  border-bottom: 1px solid #eee;
}

.log-item:last-child {
  border-bottom: none;
}

.log-time {
  color: #909399;
  flex-shrink: 0;
}

.log-type {
  color: #409eff;
  flex-shrink: 0;
  width: 40px;
}

.log-message {
  color: #303133;
  word-break: break-all;
}

.log-info .log-type { color: #909399; }
.log-success .log-type { color: #67c23a; }
.log-warning .log-type { color: #e6a23c; }
.log-error .log-type { color: #f56c6c; }
.log-error .log-message { color: #f56c6c; }

.log-empty {
  color: #909399;
  text-align: center;
  padding: 20px;
}

.preview-section {
  flex-shrink: 0;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 13px;
  color: #606266;
}

.preview-actions {
  display: flex;
  gap: 4px;
}

.preview-container {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  overflow: hidden;
}

.preview-container img {
  width: 100%;
  display: block;
}

.actions-section {
  flex-shrink: 0;
}

.actions-header {
  margin-bottom: 8px;
  font-size: 13px;
  color: #606266;
}

.actions-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.error-section {
  flex-shrink: 0;
}
</style>

