<template>
  <el-container class="flow-editor">
    <!-- 顶部工具栏 -->
    <el-header class="editor-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="goBack">返回</el-button>
        <el-input
          v-model="flowName"
          placeholder="流程名称"
          style="width: 200px; margin-left: 10px"
          @blur="updateFlowName"
        />
        <!-- 流程状态标签 -->
        <el-tag 
          v-if="flowStatus" 
          :type="flowStatusType" 
          style="margin-left: 10px"
        >
          {{ flowStatusLabel }}
        </el-tag>
      </div>
      <div class="header-center">
        <el-button-group>
          <el-button :icon="RefreshLeft" @click="undo">撤销</el-button>
          <el-button :icon="RefreshRight" @click="redo">重做</el-button>
          <el-button :icon="ZoomIn" @click="zoomIn">放大</el-button>
          <el-button :icon="ZoomOut" @click="zoomOut">缩小</el-button>
          <el-button :icon="FullScreen" @click="fitView">适应画布</el-button>
        </el-button-group>
      </div>
      <div class="header-right">
        <el-button @click="validate">验证</el-button>
        <el-button 
          v-if="flowStatus !== 'running'" 
          type="success" 
          :icon="VideoPlay" 
          @click="startFlow"
          :loading="startingFlow"
        >
          启动
        </el-button>
        <el-button 
          v-else 
          type="danger" 
          :icon="VideoPause" 
          @click="stopFlow"
          :loading="stoppingFlow"
        >
          停止
        </el-button>
        <el-button type="primary" :icon="Check" @click="saveFlow" :loading="saving">
          保存
        </el-button>
      </div>
    </el-header>

    <el-container class="editor-body">
      <!-- 左侧节点面板 -->
      <el-aside width="250px" class="node-panel">
        <h3>节点库</h3>
        <el-collapse v-model="activeCategories">
          <el-collapse-item
            v-for="(nodes, category) in nodesByCategory"
            :key="category"
            :title="categoryLabels[category]"
            :name="category"
          >
            <div
              v-for="node in nodes"
              :key="node.type"
              class="node-item"
              draggable="true"
              @dragstart="onNodeDragStart($event, node)"
            >
              <el-icon><component :is="node.icon" /></el-icon>
              <span>{{ node.label }}</span>
            </div>
          </el-collapse-item>
        </el-collapse>
      </el-aside>

      <!-- 中间画布 -->
      <el-main class="canvas-container">
        <LogicFlowCanvas
          ref="canvasRef"
          @change="onFlowChange"
          @node-click="onNodeClick"
          @edge-click="onEdgeClick"
        />
      </el-main>

      <!-- 右侧面板（可调整宽度） -->
      <div 
        class="right-panel-container"
        :style="{ width: rightPanelWidth + 'px' }"
      >
        <!-- 拖动条 -->
        <div 
          class="resize-handle"
          @mousedown="startResize"
        ></div>
        
        <div class="right-panel">
          <!-- 节点属性配置面板 -->
          <div v-if="selectedNode && !selectedEdge && activePanel === 'property'" class="property-panel">
            <h3>节点属性</h3>
            <el-form label-position="top">
              <el-form-item label="节点名称">
                <el-input v-model="selectedNode.label" @blur="updateNodeLabel" />
              </el-form-item>

              <template v-for="prop in currentNodeConfig?.properties" :key="prop.key">
                <el-form-item
                  v-if="shouldShowProperty(prop)"
                  :label="prop.label"
                  :required="prop.required"
                >
                  <el-input
                    v-if="prop.type === 'text'"
                    v-model="selectedNode.properties[prop.key]"
                    :placeholder="prop.placeholder"
                  />
                  <el-input
                    v-else-if="prop.type === 'textarea'"
                    v-model="selectedNode.properties[prop.key]"
                    type="textarea"
                    :rows="3"
                    :placeholder="prop.placeholder"
                  />
                  <el-input-number
                    v-else-if="prop.type === 'number'"
                    v-model="selectedNode.properties[prop.key]"
                    style="width: 100%"
                  />
                  <el-select
                    v-else-if="prop.type === 'select'"
                    v-model="selectedNode.properties[prop.key]"
                    style="width: 100%"
                  >
                    <el-option
                      v-for="opt in prop.options"
                      :key="opt.value"
                      :label="opt.label"
                      :value="opt.value"
                    />
                  </el-select>
                  <el-switch
                    v-else-if="prop.type === 'boolean'"
                    v-model="selectedNode.properties[prop.key]"
                  />
                </el-form-item>
              </template>
            </el-form>
          </div>
          
          <!-- 连线属性配置面板 -->
          <div v-else-if="selectedEdge && activePanel === 'property'" class="property-panel">
            <h3>连线属性</h3>
            <el-alert
              v-if="isConditionEdge"
              type="info"
              :closable="false"
              style="margin-bottom: 15px"
            >
              此连线从条件判断节点发出，请配置分支条件
            </el-alert>
            <el-form label-position="top">
              <el-form-item label="分支条件" v-if="isConditionEdge">
                <el-select
                  v-model="edgeBranch"
                  style="width: 100%"
                  placeholder="选择分支条件"
                  @change="updateEdgeBranch"
                >
                  <el-option label="条件成立 (True)" value="true">
                    <span style="color: #67c23a">✓ 条件成立 (True)</span>
                  </el-option>
                  <el-option label="条件不成立 (False)" value="false">
                    <span style="color: #f56c6c">✗ 条件不成立 (False)</span>
                  </el-option>
                </el-select>
                <div class="branch-hint">
                  <span v-if="edgeBranch === 'true'" style="color: #67c23a">
                    当条件判断结果为 True 时，流程走此分支
                  </span>
                  <span v-else-if="edgeBranch === 'false'" style="color: #f56c6c">
                    当条件判断结果为 False 时，流程走此分支
                  </span>
                  <span v-else style="color: #909399">
                    未配置分支条件，默认按顺序执行
                  </span>
                </div>
              </el-form-item>
              <el-form-item label="连线说明">
                <el-input
                  v-model="edgeLabel"
                  placeholder="可选：添加说明文字"
                  @change="updateEdgeLabel"
                />
              </el-form-item>
            </el-form>
            <div style="margin-top: 20px">
              <el-button type="danger" size="small" @click="deleteSelectedEdge">
                删除连线
              </el-button>
            </div>
          </div>
          
          <!-- 运行时面板 -->
          <RuntimePanel
            v-else-if="activePanel === 'runtime' && flowId"
            :flow-id="flowId"
            :selected-node="selectedNode"
            @node-highlight="highlightNode"
          />
          
          <el-empty v-else description="请选择一个节点" />
          
          <!-- 面板切换按钮 -->
          <div class="panel-toggle" v-if="flowId">
            <el-button-group size="small">
              <el-button 
                :type="activePanel === 'property' ? 'primary' : 'default'"
                @click="activePanel = 'property'"
              >
                属性
              </el-button>
              <el-button 
                :type="activePanel === 'runtime' ? 'primary' : 'default'"
                @click="activePanel = 'runtime'"
              >
                运行时
              </el-button>
            </el-button-group>
          </div>
        </div>
      </div>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElLoading } from 'element-plus'
import {
  ArrowLeft,
  RefreshLeft,
  RefreshRight,
  ZoomIn,
  ZoomOut,
  FullScreen,
  VideoPlay,
  VideoPause,
  Check,
} from '@element-plus/icons-vue'
import LogicFlowCanvas from '@/components/flow/LogicFlowCanvas.vue'
import RuntimePanel from '@/components/flow/RuntimePanel.vue'
import { flowAPI } from '@/api/flow'
import { nodeConfigs, nodesByCategory, categoryLabels, loadNodeConfigs, shouldShowProperty as checkPropertyVisible } from '@/config/nodes'
import type { NodeProperty } from '@/config/nodes'

const route = useRoute()
const router = useRouter()

const canvasRef = ref<any>(null)
const flowName = ref('新建流程')
const flowId = ref<string | null>(null)
const selectedNode = ref<any>(null)
const selectedEdge = ref<any>(null)  // 选中的连线
const saving = ref(false)
const startingFlow = ref(false)
const stoppingFlow = ref(false)
const activeCategories = ref(['source', 'process', 'logic', 'action'])

// 流程运行状态
const flowStatus = ref<string>('')
const runningInfo = ref<any>({})
let statusPollingTimer: number | null = null

// 面板控制: 'property' | 'runtime'
const activePanel = ref<'property' | 'runtime'>('property')

// 右侧面板宽度（可拖动调整）
const rightPanelWidth = ref(320)
const isResizing = ref(false)
const minPanelWidth = 280
const maxPanelWidth = 600

const currentNodeConfig = computed(() => {
  if (!selectedNode.value) return null
  return nodeConfigs.value.find(n => n.type === selectedNode.value.type)
})

// 连线属性
const edgeBranch = ref('')
const edgeLabel = ref('')

// 判断选中的连线是否从条件节点发出
const isConditionEdge = computed(() => {
  if (!selectedEdge.value) return false
  const sourceNodeId = selectedEdge.value.sourceNodeId
  const graphData = canvasRef.value?.getGraphData()
  if (!graphData) return false
  
  const sourceNode = graphData.nodes?.find((n: any) => n.id === sourceNodeId)
  return sourceNode?.type === 'condition'
})

// 流程状态显示
const flowStatusLabel = computed(() => {
  switch (flowStatus.value) {
    case 'running': return '运行中'
    case 'paused': return '已暂停'
    case 'stopped': return '已停止'
    case 'error': return '错误'
    default: return ''
  }
})

const flowStatusType = computed(() => {
  switch (flowStatus.value) {
    case 'running': return 'success'
    case 'paused': return 'warning'
    case 'error': return 'danger'
    default: return 'info'
  }
})

// 监听属性变化，同步回 LogicFlow
import { watch } from 'vue'
watch(() => selectedNode.value?.properties, (newProps) => {
  if (selectedNode.value && canvasRef.value) {
    canvasRef.value.updateNodeProperties(selectedNode.value.id, newProps)
  }
}, { deep: true })

onMounted(async () => {
  // 先加载节点配置
  const loaded = await loadNodeConfigs()
  if (!loaded) {
    ElMessage.error('加载节点库失败，请检查后端服务是否正常')
  }
  
  // 然后加载流程
  const id = route.params.id as string
  if (id) {
    await loadFlow(id)
    // 开始轮询状态
    startStatusPolling()
  }
})

onUnmounted(() => {
  stopStatusPolling()
})

function startStatusPolling() {
  if (statusPollingTimer) return
  
  statusPollingTimer = window.setInterval(async () => {
    if (flowId.value) {
      await fetchFlowStatus()
    }
  }, 2000)
}

function stopStatusPolling() {
  if (statusPollingTimer) {
    clearInterval(statusPollingTimer)
    statusPollingTimer = null
  }
}

async function fetchFlowStatus() {
  try {
    const response = await flowAPI.getFlowStatus(flowId.value!)
    if (response.status === 'ok' && response.data) {
      flowStatus.value = response.data.status || 'stopped'
      runningInfo.value = response.data
    }
  } catch (error) {
    // 忽略轮询错误
  }
}

async function loadFlow(id: string) {
  const loading = ElLoading.service({ text: '加载中...' })
  try {
    const response = await flowAPI.getFlow(id)
    if (response.status === 'ok') {
      const flow = response.data
      flowId.value = flow.id
      flowName.value = flow.name
      
      // 转换边的字段名
      const transformedEdges = (flow.edges || []).map((edge: any) => ({
        id: edge.id,
        type: edge.type,
        sourceNodeId: edge.source,
        targetNodeId: edge.target,
        sourceAnchor: edge.sourceAnchor,
        targetAnchor: edge.targetAnchor,
        startPoint: edge.startPoint,
        endPoint: edge.endPoint,
        pointsList: edge.pointsList,
        properties: edge.properties || {}
      }))
      
      canvasRef.value?.setGraphData({ 
        nodes: flow.nodes, 
        edges: transformedEdges 
      })
    }
  } catch (error) {
    console.error('加载流程失败:', error)
    ElMessage.error('加载流程失败')
  } finally {
    loading.close()
  }
}

async function saveFlow() {
  saving.value = true
  try {
    const graphData = canvasRef.value?.getGraphData()
    
    // 转换边的字段名
    const transformedEdges = (graphData.edges || []).map((edge: any) => ({
      id: edge.id,
      type: edge.type,
      source: edge.sourceNodeId,
      target: edge.targetNodeId,
      sourceAnchor: edge.sourceAnchor,
      targetAnchor: edge.targetAnchor,
      properties: edge.properties || {}
    }))
    
    const flowData = {
      name: flowName.value,
      description: '',
      nodes: graphData.nodes || [],
      edges: transformedEdges,
      variables: {},
    }

    console.log('保存流程数据:', flowData)

    let response
    if (flowId.value) {
      response = await flowAPI.updateFlow(flowId.value, flowData)
    } else {
      response = await flowAPI.createFlow(flowData)
      flowId.value = response.data.id
    }

    ElMessage.success('保存成功')
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function validate() {
  if (!flowId.value) {
    ElMessage.warning('请先保存流程')
    return
  }

  try {
    const response = await flowAPI.validateFlow(flowId.value)
    if (response.data.is_valid) {
      ElMessage.success('流程验证通过')
    } else {
      ElMessage.error(`验证失败: ${response.data.errors.join(', ')}`)
    }
  } catch (error) {
    ElMessage.error('验证失败')
  }
}

async function startFlow() {
  if (!flowId.value) {
    ElMessage.warning('请先保存流程')
    return
  }

  startingFlow.value = true
  try {
    const response = await flowAPI.startFlow(flowId.value)
    if (response.status === 'ok') {
      ElMessage.success('流程已启动')
      flowStatus.value = 'running'
      // 自动切换到运行时面板
      activePanel.value = 'runtime'
    } else {
      ElMessage.error(response.message || '启动失败')
    }
  } catch (error) {
    ElMessage.error('启动失败')
  } finally {
    startingFlow.value = false
  }
}

async function stopFlow() {
  if (!flowId.value) return

  stoppingFlow.value = true
  try {
    const response = await flowAPI.stopFlow(flowId.value)
    if (response.status === 'ok') {
      ElMessage.success('流程已停止')
      flowStatus.value = 'stopped'
    } else {
      ElMessage.error(response.message || '停止失败')
    }
  } catch (error) {
    ElMessage.error('停止失败')
  } finally {
    stoppingFlow.value = false
  }
}

function goBack() {
  router.push('/flows')
}

function undo() {
  canvasRef.value?.undo()
}

function redo() {
  canvasRef.value?.redo()
}

function zoomIn() {
  canvasRef.value?.zoomIn()
}

function zoomOut() {
  canvasRef.value?.zoomOut()
}

function fitView() {
  canvasRef.value?.fitView()
}

function onNodeDragStart(event: DragEvent, node: any) {
  if (event.dataTransfer) {
    event.dataTransfer.setData('text/plain', node.type)
    event.dataTransfer.effectAllowed = 'copy'
  }
}

function onFlowChange(data: any) {
  // 流程变化时的处理
}

function onNodeClick(data: any) {
  selectedNode.value = data
  selectedEdge.value = null  // 清除选中的连线
}

function onEdgeClick(data: any) {
  selectedEdge.value = data
  selectedNode.value = null  // 清除选中的节点
  
  // 初始化连线属性
  if (data.properties) {
    edgeBranch.value = data.properties.branch || ''
    edgeLabel.value = data.text?.value || data.properties.label || ''
  } else {
    edgeBranch.value = ''
    edgeLabel.value = ''
  }
}

function updateFlowName() {
  // 更新流程名称
}

function updateNodeLabel() {
  // 更新节点标签
}

/**
 * 检查属性是否应该显示（根据依赖关系）
 */
function shouldShowProperty(prop: NodeProperty): boolean {
  if (!selectedNode.value) return false
  return checkPropertyVisible(prop, selectedNode.value.properties || {})
}

function highlightNode(nodeId: string) {
  // 高亮当前执行的节点
  canvasRef.value?.highlightNode(nodeId)
}

// 更新连线分支属性
function updateEdgeBranch() {
  if (!selectedEdge.value || !canvasRef.value) return
  
  const edgeId = selectedEdge.value.id
  const branch = edgeBranch.value
  
  // 更新连线属性
  canvasRef.value.updateEdgeProperties(edgeId, { branch })
  
  // 更新连线文本显示
  const labelText = branch === 'true' ? '✓ True' : branch === 'false' ? '✗ False' : ''
  canvasRef.value.updateEdgeText(edgeId, labelText)
}

// 更新连线标签
function updateEdgeLabel() {
  if (!selectedEdge.value || !canvasRef.value) return
  
  const edgeId = selectedEdge.value.id
  canvasRef.value.updateEdgeProperties(edgeId, { label: edgeLabel.value })
  
  // 如果有自定义标签，使用自定义标签；否则使用分支标签
  if (edgeLabel.value) {
    canvasRef.value.updateEdgeText(edgeId, edgeLabel.value)
  } else if (edgeBranch.value) {
    const labelText = edgeBranch.value === 'true' ? '✓ True' : '✗ False'
    canvasRef.value.updateEdgeText(edgeId, labelText)
  }
}

// 删除选中的连线
function deleteSelectedEdge() {
  if (!selectedEdge.value || !canvasRef.value) return
  
  canvasRef.value.deleteEdge(selectedEdge.value.id)
  selectedEdge.value = null
}

// 拖动调整面板宽度
function startResize(e: MouseEvent) {
  isResizing.value = true
  const startX = e.clientX
  const startWidth = rightPanelWidth.value
  
  const onMouseMove = (moveEvent: MouseEvent) => {
    if (!isResizing.value) return
    const delta = startX - moveEvent.clientX
    const newWidth = Math.min(maxPanelWidth, Math.max(minPanelWidth, startWidth + delta))
    rightPanelWidth.value = newWidth
  }
  
  const onMouseUp = () => {
    isResizing.value = false
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }
  
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}
</script>

<style scoped>
.flow-editor {
  height: 100vh;
  background: #fff;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
}

.editor-body {
  height: calc(100vh - 60px);
}

.node-panel {
  background: #f5f7fa;
  border-right: 1px solid #e4e7ed;
  overflow-y: auto;
  padding: 10px;
}

.node-item {
  display: flex;
  align-items: center;
  padding: 10px;
  margin: 5px 0;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  cursor: move;
}

.node-item:hover {
  border-color: #409eff;
}

.node-item .el-icon {
  margin-right: 8px;
}

.canvas-container {
  padding: 0;
  position: relative;
}

.right-panel-container {
  position: relative;
  flex-shrink: 0;
  display: flex;
}

.resize-handle {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 6px;
  cursor: col-resize;
  background: transparent;
  z-index: 20;
  transition: background 0.2s;
}

.resize-handle:hover,
.resize-handle:active {
  background: #409eff;
}

.right-panel {
  flex: 1;
  background: #f5f7fa;
  border-left: 1px solid #e4e7ed;
  overflow-y: auto;
  padding: 10px;
  display: flex;
  flex-direction: column;
  position: relative;
}

.property-panel {
  flex: 1;
  overflow-y: auto;
}

.panel-toggle {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
}

.branch-hint {
  margin-top: 8px;
  font-size: 12px;
  line-height: 1.5;
}
</style>
