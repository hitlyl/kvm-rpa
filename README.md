# KVM RPA 系统

基于 KVM 视频画面抓取的 RPA（代操作）系统。通过 RTSP 视频流获取画面，结合 YOLO 检测和 OCR 识别，实现对被控机器的自动化操作。

## 项目概述

本系统实现了一个完整的 KVM RPA 解决方案，核心功能包括：

- **视频采集**：从 RTSP 源稳定拉取视频流，支持自动重连
- **目标检测**：基于 YOLOv8 的 UI 元素检测
- **文字识别**：基于 PaddleOCR 的中英文混合识别
- **流程编排**：支持 YAML 脚本的规则引擎和高级流程控制
- **键鼠控制**：通过 REST API 发送键盘鼠标指令
- **监控告警**：Prometheus 指标和日志系统

## 技术栈

### 后端
- **Python 3.9+**
- **OpenCV**：视频采集和图像处理
- **Ultralytics YOLOv8**：目标检测
- **PaddleOCR**：OCR 识别
- **FastAPI + Uvicorn**：HTTP/WebSocket API
- **Loguru**：日志管理
- **Prometheus Client**：监控指标

### 前端（后续）
- Vue3 + Vite
- Element Plus / Naive UI
- Pinia + Vue Router
- WebSocket + Axios

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

**注意**：
- 如需 GPU 加速，请安装对应的 CUDA 版本的 PyTorch
- PaddleOCR 首次运行会自动下载模型文件

### 2. 配置系统

编辑配置文件 `backend/config/default.yaml`：

```yaml
# RTSP 视频流配置
rtsp:
  url: "rtsp://your-rtsp-server:554/stream"  # 修改为实际 RTSP 地址
  fps: 8
  resolution: [1280, 720]

# YOLO 模型配置
yolo:
  path: "models/yolov8n.pt"  # 模型会自动下载
  conf_threshold: 0.25
  device: "cpu"  # 或 "cuda" 用于 GPU

# OCR 配置
ocr:
  lang: ["ch", "en"]
  conf_threshold: 0.5
  use_gpu: false

# 键鼠 API 配置
keystroke_api:
  url: "http://localhost:8080/v1/exec"
  token: ""
```

### 3. 运行系统

```bash
cd backend
python main.py
```

可选：指定自定义配置文件

```bash
python main.py path/to/custom-config.yaml
```

### 4. 查看日志

日志文件位于 `backend/logs/kvm_rpa.log`，可以实时查看：

```bash
tail -f backend/logs/kvm_rpa.log
```

### 5. 访问 API

系统启动后，可以通过以下端点访问：

- **Swagger 文档**：`http://localhost:8000/docs`
- **Prometheus 指标**：`http://localhost:9090/metrics`
- **WebSocket 画面流**：`ws://localhost:8000/ws/frame`
- **WebSocket 推理结果**：`ws://localhost:8000/ws/inference`
- **WebSocket 系统指标**：`ws://localhost:8000/ws/metrics`

## 项目结构

```
kvm-rpa/
├── backend/                    # Python 后端服务
│   ├── src/
│   │   ├── capture/           # 视频采集模块
│   │   ├── preprocessing/     # 图像预处理
│   │   ├── detection/         # YOLO 检测
│   │   ├── ocr/              # OCR 识别
│   │   ├── engine/           # 流程编排引擎
│   │   ├── kvm_api/          # 键鼠 API 适配
│   │   ├── api/              # HTTP/WebSocket API
│   │   ├── monitoring/       # 日志与监控
│   │   └── utils/            # 工具函数
│   ├── config/               # 配置文件
│   ├── models/               # 模型存储目录
│   ├── logs/                 # 日志目录
│   ├── tests/                # 测试代码
│   ├── requirements.txt      # Python 依赖
│   └── main.py              # 主程序入口
├── docs/                      # 文档
└── README.md                 # 本文件
```

## 核心模块说明

### 1. 视频采集模块 (`src/capture/rtsp_stream.py`)

- 从 RTSP 源拉取视频流
- 维护帧缓存队列
- 自动重连机制（指数回退）
- 监控指标：帧率、丢帧数、重连次数

### 2. YOLO 检测模块 (`src/detection/yolo_detector.py`)

- 基于 Ultralytics YOLOv8
- 支持模型热更新
- 可配置置信度和 IOU 阈值
- 返回检测框、类别、置信度、中心点

### 3. OCR 识别模块 (`src/ocr/ocr_engine.py`)

- 基于 PaddleOCR
- 支持中英文混合识别
- 可配置最小置信度
- 支持文本查找和匹配

### 4. 规则引擎 (`src/engine/rule_engine.py`)

- 基于规则的触发-动作模型
- 支持 OCR 和检测触发条件
- 提供常用动作：点击、移动、输入、按键、等待

### 5. 高级流程引擎 (`src/engine/`)

- **脚本解析器** (`script_parser.py`)：解析 YAML 脚本
- **执行器** (`executor.py`)：执行脚本动作，支持条件分支、循环
- **执行上下文** (`context.py`)：管理变量、计数器、历史记录

### 6. 键鼠适配层 (`src/kvm_api/keystroke_adapter.py`)

- 封装键鼠操作的统一接口
- 当前为模拟模式，可替换为真实 KVM 控制器 API
- 支持重试机制

### 7. HTTP API 服务 (`src/api/http_server.py`)

- 基于 FastAPI
- 提供脚本管理、模型管理、配置管理接口
- 标准化 JSON 响应格式
- Swagger 自动文档

### 8. WebSocket 服务 (`src/api/websocket_server.py`)

- 实时画面流（JPEG 编码）
- 实时推理结果（JSON）
- 实时系统指标（JSON）

## 流程脚本示例

创建 YAML 脚本 `scripts/example.yaml`：

```yaml
name: "安装向导流程"
description: "自动完成软件安装向导"
version: "1.0"

variables:
  install_path: "C:\\Program Files\\MyApp"
  step_count: 0

actions:
  # 等待"欢迎"页面
  - type: ocr_check
    text: "欢迎"
    timeout: 10
    on_success:
      - type: log
        message: "检测到欢迎页面"
      - type: click
        target: [640, 500]  # 下一步按钮坐标
      - type: wait
        duration: 1.0
  
  # 输入安装路径
  - type: ocr_check
    text: "安装路径"
    timeout: 10
    on_success:
      - type: click
        target: [640, 400]  # 路径输入框
      - type: input
        text: "${install_path}"
      - type: click
        target: [640, 500]  # 下一步
  
  # 条件判断
  - type: conditional
    condition:
      variable: step_count
      operator: "<"
      value: 5
    then:
      - type: set_variable
        name: step_count
        value: 6
      - type: log
        message: "安装步骤完成"
```

## 配置热加载

系统支持配置热加载，通过 API 更新配置：

```bash
curl -X PUT http://localhost:8000/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "updates": {
      "yolo": {
        "conf_threshold": 0.3
      },
      "rtsp": {
        "fps": 10
      }
    }
  }'
```

## 监控与指标

系统提供 Prometheus 指标，可集成到监控平台：

```bash
# 查看所有指标
curl http://localhost:9090/metrics

# 关键指标
# - rtsp_fps: 当前帧率
# - yolo_inference_duration_seconds: YOLO 推理耗时
# - ocr_inference_duration_seconds: OCR 识别耗时
# - kvm_api_calls_total: 键鼠 API 调用总数
# - pipeline_duration_seconds: 端到端处理耗时
```

## 开发指南

### 添加自定义规则

在 `main.py` 中注册自定义规则：

```python
def _register_example_rules(self) -> None:
    my_rule = {
        "name": "我的规则",
        "enabled": True,
        "trigger": {
            "type": "ocr",
            "text_contains": "目标文本",
            "min_confidence": 0.7
        },
        "actions": [
            {"type": "click", "target": "trigger_bbox"},
            {"type": "wait", "duration": 0.5}
        ]
    }
    self.rule_engine.register_rule(my_rule)
```

### 自定义键鼠 API 适配器

修改 `src/kvm_api/keystroke_adapter.py`，实现真实的 HTTP 调用：

```python
def __init__(self, ..., mock_mode=False):  # 关闭模拟模式
    self.mock_mode = mock_mode
    # 其他初始化...
```

### 训练自定义 YOLO 模型

1. 标注 UI 元素数据集
2. 使用 Ultralytics 训练脚本
3. 将训练好的模型放到 `backend/models/` 目录
4. 更新配置文件中的模型路径

## 常见问题

### 1. RTSP 连接失败

- 检查 RTSP URL 是否正确
- 确认网络连通性
- 检查 RTSP 服务器是否需要认证

### 2. YOLO 模型下载慢

- 首次运行会自动下载 YOLOv8n 模型
- 可以手动下载并放到 `models/` 目录

### 3. OCR 识别准确率低

- 尝试启用图像预处理（去噪、锐化、二值化）
- 调整 `conf_threshold` 阈值
- 确保图像清晰度足够

### 4. GPU 不可用

- 检查 CUDA 和 PyTorch 是否正确安装
- 配置文件中设置 `device: "cuda"`

## 性能优化建议

1. **降低帧率**：如果不需要实时性，可以降低 FPS 到 5-8
2. **使用 GPU**：YOLO 和 OCR 都可以使用 GPU 加速
3. **调整模型大小**：使用 YOLOv8n（nano）而不是 YOLOv8x
4. **预处理优化**：根据实际场景选择性启用预处理
5. **ROI 裁剪**：如果目标区域固定，可以裁剪 ROI 减少计算量

## 后续计划（M4+）

- [ ] Vue3 前端管理界面
- [ ] Docker 容器化部署
- [ ] 多路 RTSP 并行处理
- [ ] 脚本可视化编辑器
- [ ] 更完善的错误处理和恢复机制
- [ ] 性能优化和稳定性测试

## 许可证

本项目仅供学习和研究使用。

## 联系方式

如有问题或建议，请提交 Issue。

# kvm-rpa
