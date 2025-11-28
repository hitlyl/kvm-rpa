<template>
  <el-container class="flow-list-container">
    <el-header>
      <div class="header-content">
        <h2>流程列表</h2>
        <el-button type="primary" @click="createNewFlow" :icon="Plus">
          新建流程
        </el-button>
      </div>
    </el-header>

    <el-main>
      <el-row :gutter="20">
        <el-col :span="6" v-for="flow in flows" :key="flow.id">
          <el-card class="flow-card" shadow="hover" :class="getFlowCardClass(flow)">
            <template #header>
              <div class="card-header">
                <span>{{ flow.name }}</span>
                <div class="header-actions">
                  <!-- 运行状态标签 -->
                  <el-tag 
                    v-if="flowStatusMap[flow.id]?.status === 'running'" 
                    type="success" 
                    size="small"
                    effect="dark"
                  >
                    运行中
                  </el-tag>
                  <el-tag 
                    v-else-if="flowStatusMap[flow.id]?.status === 'paused'" 
                    type="warning" 
                    size="small"
                    effect="dark"
                  >
                    已暂停
                  </el-tag>
                  <el-tag 
                    v-else-if="flowStatusMap[flow.id]?.status === 'error'" 
                    type="danger" 
                    size="small"
                    effect="dark"
                  >
                    错误
                  </el-tag>
                  <el-tag 
                    v-else-if="flowStatusMap[flow.id]?.status === 'stopped'" 
                    type="info" 
                    size="small"
                  >
                    已停止
                  </el-tag>
                  <el-dropdown @command="handleCommand($event, flow)">
                    <el-icon><More /></el-icon>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item command="edit">编辑</el-dropdown-item>
                        <el-dropdown-item 
                          v-if="flowStatusMap[flow.id]?.status !== 'running'" 
                          command="start"
                        >
                          启动
                        </el-dropdown-item>
                        <el-dropdown-item 
                          v-if="flowStatusMap[flow.id]?.status === 'running'" 
                          command="stop"
                        >
                          停止
                        </el-dropdown-item>
                        <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>
            </template>

            <div class="flow-info">
              <p class="description">{{ flow.description || '暂无描述' }}</p>
              <div class="meta">
                <el-tag size="small">{{ flow.node_count !== undefined ? flow.node_count : (flow.nodes ? flow.nodes.length : 0) }} 个节点</el-tag>
                <span class="time">{{ formatTime(flow.updated_at) }}</span>
              </div>
              
              <!-- 运行信息 -->
              <div v-if="flowStatusMap[flow.id]?.status === 'running'" class="running-info">
                <div class="current-node">
                  <el-icon class="spin"><Loading /></el-icon>
                  <span>{{ flowStatusMap[flow.id]?.current_node?.label || '准备中...' }}</span>
                </div>
                <span class="loop-count">
                  已执行 {{ flowStatusMap[flow.id]?.loop_count || 0 }} 轮
                </span>
              </div>
              
              <!-- 错误信息 -->
              <div v-else-if="flowStatusMap[flow.id]?.status === 'error'" class="error-info">
                <el-alert
                  :title="flowStatusMap[flow.id]?.error || '未知错误'"
                  type="error"
                  :closable="false"
                  show-icon
                >
                  <template v-if="flowStatusMap[flow.id]?.error_node">
                    <div class="error-detail">
                      失败节点: {{ flowStatusMap[flow.id]?.error_node }}
                    </div>
                  </template>
                </el-alert>
              </div>
            </div>

            <template #footer>
              <el-button text type="primary" @click="openFlow(flow)">
                打开编辑器
              </el-button>
              <el-button 
                v-if="flowStatusMap[flow.id]?.status !== 'running'"
                text 
                type="success" 
                @click="startFlow(flow)"
              >
                启动
              </el-button>
              <el-button 
                v-else
                text 
                type="danger" 
                @click="stopFlow(flow)"
              >
                停止
              </el-button>
            </template>
          </el-card>
        </el-col>
      </el-row>

      <el-empty v-if="flows.length === 0" description="暂无流程，点击新建流程开始" />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, More, Loading } from '@element-plus/icons-vue'
import { flowAPI } from '@/api/flow'

const router = useRouter()
const flows = ref<any[]>([])
const flowStatusMap = ref<Record<string, any>>({})

let statusPollingTimer: number | null = null

onMounted(async () => {
  await loadFlows()
  startStatusPolling()
})

onUnmounted(() => {
  stopStatusPolling()
})

function startStatusPolling() {
  fetchAllFlowsStatus()
  statusPollingTimer = window.setInterval(() => {
    fetchAllFlowsStatus()
  }, 2000)
}

function stopStatusPolling() {
  if (statusPollingTimer) {
    clearInterval(statusPollingTimer)
    statusPollingTimer = null
  }
}

async function fetchAllFlowsStatus() {
  try {
    const response = await flowAPI.getAllFlowsStatus()
    if (response.status === 'ok' && response.data?.flows) {
      const statusMap: Record<string, any> = {}
      for (const status of response.data.flows) {
        statusMap[status.flow_id] = status
      }
      flowStatusMap.value = statusMap
    }
  } catch (error) {
    // 忽略轮询错误
  }
}

async function loadFlows() {
  try {
    const response = await flowAPI.listFlows()
    if (response.status === 'ok') {
      flows.value = response.data.flows || []
    }
  } catch (error) {
    ElMessage.error('加载流程列表失败')
    console.error(error)
  }
}

function createNewFlow() {
  router.push('/flows/editor')
}

function openFlow(flow: any) {
  router.push(`/flows/editor/${flow.id}`)
}

function getFlowCardClass(flow: any) {
  const status = flowStatusMap.value[flow.id]?.status
  return {
    'flow-card--running': status === 'running',
    'flow-card--error': status === 'error',
    'flow-card--stopped': status === 'stopped'
  }
}

async function startFlow(flow: any) {
  try {
    const response = await flowAPI.startFlow(flow.id)
    if (response.status === 'ok') {
      ElMessage.success(`流程"${flow.name}"已启动`)
      await fetchAllFlowsStatus()
    } else {
      ElMessage.error(response.message || '启动失败')
    }
  } catch (error) {
    ElMessage.error('启动失败')
  }
}

async function stopFlow(flow: any) {
  try {
    const response = await flowAPI.stopFlow(flow.id)
    if (response.status === 'ok') {
      ElMessage.success(`流程"${flow.name}"已停止`)
      await fetchAllFlowsStatus()
    } else {
      ElMessage.error(response.message || '停止失败')
    }
  } catch (error) {
    ElMessage.error('停止失败')
  }
}

async function handleCommand(command: string, flow: any) {
  if (command === 'edit') {
    openFlow(flow)
  } else if (command === 'start') {
    await startFlow(flow)
  } else if (command === 'stop') {
    await stopFlow(flow)
  } else if (command === 'delete') {
    if (flowStatusMap.value[flow.id]?.status === 'running') {
      ElMessage.warning('请先停止运行中的流程')
      return
    }
    
    try {
      await ElMessageBox.confirm(`确定要删除流程"${flow.name}"吗？`, '确认删除', {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      })

      await flowAPI.deleteFlow(flow.id)
      ElMessage.success('删除成功')
      await loadFlows()
    } catch (error) {
      if (error !== 'cancel') {
        ElMessage.error('删除失败')
      }
    }
  }
}

function formatTime(time: string) {
  if (!time) return ''
  return new Date(time).toLocaleString('zh-CN')
}
</script>

<style scoped>
.flow-list-container {
  height: 100vh;
  background: #f5f7fa;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  padding: 0 20px;
}

.el-main {
  padding: 20px;
}

.flow-card {
  margin-bottom: 20px;
  cursor: pointer;
  transition: transform 0.2s, border-color 0.2s;
}

.flow-card:hover {
  transform: translateY(-2px);
}

.flow-card--running {
  border-color: #67c23a;
  box-shadow: 0 0 8px rgba(103, 194, 58, 0.3);
}

.flow-card--error {
  border-color: #f56c6c;
  box-shadow: 0 0 8px rgba(245, 108, 108, 0.3);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.flow-info {
  min-height: 100px;
}

.description {
  color: #909399;
  font-size: 14px;
  margin-bottom: 12px;
}

.meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}

.time {
  color: #909399;
}

.running-info {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e4e7ed;
}

.current-node {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #67c23a;
  margin-bottom: 4px;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.loop-count {
  display: block;
  font-size: 12px;
  color: #909399;
}

.error-info {
  margin-top: 12px;
}

.error-detail {
  margin-top: 4px;
  font-size: 12px;
  color: #f56c6c;
}
</style>
