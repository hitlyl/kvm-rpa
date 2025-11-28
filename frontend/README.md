# KVM RPA Frontend - 可视化流程编排系统

基于 Vue 3 + TypeScript + LogicFlow + Element Plus 的可视化流程编排前端。

## 快速开始

### 安装依赖

```bash
cd frontend
npm install
```

### 启动开发服务器

```bash
npm run dev
```

访问 `http://localhost:3000`

### 构建生产版本

```bash
npm run build
```

## 技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **TypeScript** - 类型安全
- **Vite** - 下一代前端构建工具
- **LogicFlow** - 流程编排画布（蚂蚁金服）
- **Element Plus** - Vue 3 UI 组件库
- **Pinia** - 状态管理
- **Vue Router** - 路由管理
- **Axios** - HTTP 客户端

## 项目结构

```
frontend/
├── src/
│   ├── api/                # API 接口封装
│   │   └── flow.ts         # 流程 API
│   ├── components/         # 组件
│   │   ├── flow/           # 流程相关组件
│   │   │   ├── LogicFlowCanvas.vue  # 画布组件
│   │   │   ├── NodePanel.vue        # 节点面板
│   │   │   └── PropertyPanel.vue    # 属性面板
│   │   └── common/         # 通用组件
│   ├── views/              # 页面
│   │   ├── FlowList.vue    # 流程列表
│   │   └── FlowEditor.vue  # 流程编辑器
│   ├── stores/             # Pinia 状态管理
│   │   └── flow.ts         # 流程状态
│   ├── config/             # 配置
│   │   └── nodes.ts        # 节点配置
│   ├── types/              # TypeScript 类型
│   ├── router/             # 路由配置
│   ├── assets/             # 静态资源
│   ├── App.vue             # 根组件
│   └── main.ts             # 入口文件
├── index.html              # HTML 模板
├── package.json            # 依赖配置
├── vite.config.ts          # Vite 配置
└── tsconfig.json           # TypeScript 配置
```

## 核心功能

### 1. 流程列表页 (`/flows`)
- 展示所有流程
- 创建新流程
- 编辑/删除流程
- 流程搜索和筛选

### 2. 流程编辑器 (`/flows/editor/:id?`)
- 拖拽式节点编排
- 节点属性配置
- 流程验证
- 流程保存和执行
- 撤销/重做
- 画布缩放和适应

## 节点类型

### 数据源节点
- **RTSP 视频源** - 从 RTSP 流获取视频帧
- **图像输入** - 输入单张图像

### 处理节点
- **图像预处理** - 缩放、去噪、锐化
- **YOLO 检测** - 目标检测
- **OCR 识别** - 文字识别

### 逻辑节点
- **条件判断** - if-else 分支
- **循环** - 重复执行
- **变量操作** - 设置/获取变量

### 动作节点
- **鼠标操作** - 点击、移动、拖拽
- **键盘操作** - 输入文本、按键
- **等待** - 延时

### 工具节点
- **日志输出** - 记录日志

## 开发指南

### 添加新节点类型

1. 在 `src/config/nodes.ts` 中添加节点配置：

```typescript
{
  type: 'my_node',
  label: '我的节点',
  category: 'action',
  icon: 'IconName',
  color: '#5470C6',
  description: '节点描述',
  properties: [
    { key: 'param1', label: '参数1', type: 'text', required: true }
  ]
}
```

2. 在 `LogicFlowCanvas.vue` 的 `registerCustomNodes()` 中注册节点

3. 后端实现对应的节点执行逻辑

### API 代理配置

开发环境下，`/api` 和 `/ws` 请求会自动代理到后端服务器（`http://localhost:8000`）。

配置文件：`vite.config.ts`

## 注意事项

1. 确保后端服务已启动（`python backend/main.py`）
2. 节点拖拽功能需要 LogicFlow 正确初始化
3. 流程保存前会自动验证
4. 使用 Element Plus 的暗色模式需要额外配置

## 待实现功能

- [ ] 流程模板应用
- [ ] 实时执行状态显示
- [ ] 节点错误高亮
- [ ] 快捷键支持
- [ ] 流程导入/导出
- [ ] 批量操作
- [ ] 搜索和替换

