# 项目改进建议

## 1. 当前实现分析

### Backend (后端)
- **Flow Engine**: `AsyncGraphExecutor` (`backend/src/engine/graph_executor.py`) 已经实现了基于条件的分支逻辑。
- **Condition Node**: `ConditionNode` (`backend/src/nodes/logic.py`) 执行后返回 `True` 或 `False`。
- **Branching Logic**: 执行器会检查从条件节点发出的连线（Edge）的 `properties.branch` 属性。
    - 如果 `branch` 为 "true" 且节点返回 `True`，则执行该分支。
    - 如果 `branch` 为 "false" 且节点返回 `False`，则执行该分支。
    - 也支持直接匹配字符串结果。

### Frontend (前端)
- **LogicFlow**: 使用了 `@logicflow/core`，支持自定义节点和边。
- **FlowEditor**: `FlowEditor.vue` 目前只处理了 **节点点击** (`node-click`) 事件，用于显示和编辑节点属性。
- **缺失功能**: **目前没有处理 `edge-click` 事件**，也没有提供编辑连线属性（如 `branch`）的界面。这意味着用户无法在前端界面上配置条件分支的走向。

## 2. 完善建议

### 针对判断节点（Decision Node）的改进

**问题**: 用户无法直观地配置“成功走这条路，失败走那条路”。

**建议方案**:

1.  **前端增加连线属性编辑功能**:
    - 在 `FlowEditor.vue` 中监听 `edge-click` 事件。
    - 在右侧属性面板中增加“连线属性”配置区。
    - 当选中连线时，允许用户输入或选择 `branch` 属性（例如下拉框选择 "True" / "False"）。

2.  **连线可视化优化**:
    - 开启 LogicFlow 的连线文本功能，将 `branch` 属性的值直接显示在连线上，让流程图更直观。
    - 可以在 `LogicFlowCanvas.vue` 中配置边的默认样式，或者在设置属性时自动更新边的 `text`。

3.  **交互优化 (可选)**:
    - 当从“条件判断”节点连线时，自动弹出对话框询问是 "True" 分支还是 "False" 分支。
    - 或者使用 LogicFlow 的自定义 Anchor（锚点），在条件节点上预设两个输出点（绿色代表 True，红色代表 False），从不同锚点连出的线自动带有对应的 `branch` 属性。

### LogicFlow 组件支持情况

- **支持情况**: LogicFlow 完全支持上述功能。
    - **多出口**: 支持一个节点连接多条输出边。
    - **边属性**: 支持给边附加自定义数据 (`properties`)。
    - **边文本**: 支持在边上显示文本标签。
    - **自定义锚点**: 支持自定义节点的锚点位置和样式。

### 实施步骤

1.  **修改 `frontend/src/views/FlowEditor.vue`**:
    - 添加 `onEdgeClick` 处理函数。
    - 在右侧面板增加 `EdgeProperty` 编辑组件。
2.  **修改 `frontend/src/components/flow/LogicFlowCanvas.vue`**:
    - 确保 `edge:click` 事件正确 emit 到父组件。
    - 配置边的 `text` 显示逻辑。

## 3. 其他建议

- **节点状态反馈**: 目前运行时面板 (`RuntimePanel`) 似乎主要显示日志，建议在画布上通过节点颜色变化实时反馈执行状态（如 运行中-蓝色，成功-绿色，失败-红色）。
- **验证机制**: 在保存或验证流程时，检查条件节点是否至少有一条 `branch="true"` 和一条 `branch="false"` 的连线（或覆盖了所有可能情况），避免流程死端。
