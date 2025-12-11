<template>
  <div 
    ref="containerRef"
    class="logic-flow-container"
    @drop="onDrop"
    @dragover="onDragOver"
  ></div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import LogicFlow, { RectNode, RectNodeModel } from '@logicflow/core'
import '@logicflow/core/dist/style/index.css'
import { Menu, Snapshot, SelectionSelect } from '@logicflow/extension'
import '@logicflow/extension/lib/style/index.css'
import { nodeConfigs } from '@/config/nodes'
import { generateNodeId, getDefaultProperties } from '@/utils/node'

const props = defineProps<{
  graphData?: any
}>()

const emit = defineEmits<{
  (e: 'change', data: any): void
  (e: 'node-click', data: any): void
  (e: 'edge-click', data: any): void
}>()

const lf = ref<LogicFlow | null>(null)
const containerRef = ref<HTMLElement | null>(null)

onMounted(() => {
  // 如果节点配置已加载，直接初始化
  if (nodeConfigs.value && nodeConfigs.value.length > 0) {
    initLogicFlow()
  } else {
    // 否则等待节点配置加载完成
    const unwatch = watch(
      () => nodeConfigs.value.length,
      (newLength) => {
        if (newLength > 0) {
          console.log('节点配置已加载，初始化 LogicFlow')
          initLogicFlow()
          unwatch() // 取消监听
        }
      },
      { immediate: true }
    )
  }
})

onUnmounted(() => {
  if (lf.value && typeof (lf.value as any).destroy === 'function') {
    // 低版本 LogicFlow 未导出 destroy 类型，这里做能力探测后再调用
    (lf.value as any).destroy()
  }
  lf.value = null
})

function initLogicFlow() {
  if (!containerRef.value) return

  lf.value = new LogicFlow({
    container: containerRef.value,
    grid: {
      size: 20,
      visible: true,
      type: 'dot',
      config: {
        color: '#ababab',
        thickness: 1,
      },
    },
    background: {
      backgroundImage: 'none',
      backgroundColor: '#f7f9ff',
    },
    keyboard: {
      enabled: true,
    },
    snapline: true,
    history: true,
    partial: false,
    pluginOptions: {
      exportTool: {},
    },
    edgeType: 'polyline',
    edgeTextDraggable: true,
  })

  // 注册插件
  lf.value.extension.menu = Menu
  lf.value.extension.snapshot = Snapshot
  lf.value.extension.selectionSelect = SelectionSelect

  // 注册自定义节点
  registerCustomNodes()

  // 初始渲染（参考 logicflow_vue_demo，空图也需先 render 一次）
  const initialData = props.graphData ?? { nodes: [], edges: [] }
  lf.value.render(initialData)

  // 监听事件
  lf.value.on('node:click', ({ data }) => {
    emit('node-click', data)
  })

  lf.value.on('edge:click', ({ data }) => {
    emit('edge-click', data)
  })

  lf.value.on('history:change', () => {
    const data = lf.value!.getGraphData()
    emit('change', data)
  })
}

// 监听 graphData 变化
watch(() => props.graphData, (val) => {
  if (lf.value && val) {
    lf.value.render(val)
  }
})

// 拖拽处理
function onDragOver(event: DragEvent) {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'copy'
  }
}

function onDrop(event: DragEvent) {
  event.preventDefault()
  
  if (!lf.value || !event.dataTransfer) return
  
  // 获取拖拽的节点类型
  const nodeType = event.dataTransfer.getData('text/plain')
  if (!nodeType) {
    console.warn('No node type found in drag data')
    return
  }
  
  // 查找节点配置
  const nodeConfig = nodeConfigs.value.find(n => n.type === nodeType)
  if (!nodeConfig) {
    console.warn('Node config not found for type:', nodeType)
    return
  }
  
  try {
    // 转换为 LogicFlow 画布坐标
    const { canvasOverlayPosition } = lf.value.graphModel.getPointByClient({
      x: event.clientX,
      y: event.clientY
    })
    const { x, y } = canvasOverlayPosition

    if (typeof x !== 'number' || typeof y !== 'number') {
      console.warn('Invalid drop position:', canvasOverlayPosition)
      return
    }

    // 创建节点
    const nodeId = generateNodeId()
    const properties = getDefaultProperties(nodeType, nodeConfig)
    
    lf.value.addNode({
      id: nodeId,
      type: nodeType,
      x,
      y,
      text: nodeConfig.label,
      properties: properties
    })
    console.log('Node added:', nodeType, canvasOverlayPosition)
  } catch (error) {
    console.error('Failed to add node:', error)
  }
}

function registerCustomNodes() {
  if (!lf.value) return

  // 使用 .value 访问 ref 对象的值
  nodeConfigs.value.forEach(config => {
    // 使用立即执行函数创建闭包，确保每个节点都有独立的 config 引用
    const nodeColor = config.color
    const nodeType = config.type
    
    class CustomNodeModel extends RectNodeModel {
      getNodeStyle() {
        const style = super.getNodeStyle()
        const properties = this.getProperties()
        return {
          ...style,
          fill: nodeColor,
          stroke: nodeColor,
          radius: 4,
        }
      }
    }

    lf.value!.register({
      type: nodeType,
      view: RectNode,
      model: CustomNodeModel,
    })
    
    console.log(`已注册节点类型: ${nodeType}`)
  })
  
  console.log(`共注册 ${nodeConfigs.value.length} 个节点类型`)
}

// 更新节点属性
function updateNodeProperties(id: string, properties: any) {
  if (lf.value) {
    lf.value.setProperties(id, properties)
  }
}

// 更新节点文本（显示名称）
function updateNodeText(id: string, text: string) {
  if (lf.value) {
    const nodeModel = lf.value.getNodeModelById(id)
    if (nodeModel) {
      nodeModel.updateText(text)
    }
  }
}

// 更新连线属性
function updateEdgeProperties(id: string, properties: any) {
  if (lf.value) {
    const edge = lf.value.getEdgeModelById(id)
    if (edge) {
      edge.setProperties({
        ...edge.properties,
        ...properties
      })
    }
  }
}

// 更新连线文本
function updateEdgeText(id: string, text: string) {
  if (lf.value) {
    const edge = lf.value.getEdgeModelById(id)
    if (edge) {
      edge.updateText(text)
    }
  }
}

// 删除连线
function deleteEdge(id: string) {
  if (lf.value) {
    lf.value.deleteEdge(id)
  }
}

// 高亮节点
function highlightNode(nodeId: string) {
  if (lf.value) {
    // 先清除所有高亮
    const graphData = lf.value.getGraphData()
    graphData.nodes?.forEach((node: any) => {
      const model = lf.value!.getNodeModelById(node.id)
      if (model) {
        model.setProperties({ _highlighted: false })
      }
    })
    
    // 高亮指定节点
    const model = lf.value.getNodeModelById(nodeId)
    if (model) {
      model.setProperties({ _highlighted: true })
    }
  }
}

// 暴露方法给父组件
defineExpose({
  getGraphData: () => lf.value?.getGraphData(),
  setGraphData: (data: any) => lf.value?.render(data),
  clearGraph: () => lf.value?.clearData(),
  undo: () => lf.value?.undo(),
  redo: () => lf.value?.redo(),
  zoomIn: () => lf.value?.zoom(true),
  zoomOut: () => lf.value?.zoom(false),
  fitView: () => lf.value?.fitView(),
  updateNodeProperties,
  updateNodeText,
  updateEdgeProperties,
  updateEdgeText,
  deleteEdge,
  highlightNode
})
</script>

<style scoped>
.logic-flow-container {
  width: 100%;
  height: 100%;
  position: relative;
}
</style>

