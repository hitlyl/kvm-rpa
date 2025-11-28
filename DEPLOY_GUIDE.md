# KVM-RPA 部署指南

## 快速部署

```bash
# 1. 执行部署脚本
cd /Users/liu/Work/sophon/sophon-demo/kvm-rpa
./deploy.sh

# 2. 进入部署目录
cd deploy

# 3. 安装依赖
pip3 install -r requirements.txt

# 4. 启动系统
./start.sh
```

## 访问系统

- **前端界面**: http://localhost:8000/
- **API 文档**: http://localhost:8000/docs

## 部署目录结构

```
deploy/
├── main.py              # 主程序（支持静态文件服务）
├── start.sh             # 启动脚本
├── requirements.txt     # Python 依赖
├── src/                 # 后端源代码
├── static/              # 前端静态文件
├── config/              # 配置文件
├── flows/               # 流程定义文件
├── logs/                # 日志目录
└── models/              # 模型文件目录
```

## 配置说明

编辑 `config/default.yaml`：

```yaml
# 日志配置
logging:
  level: "INFO"
  file_path: "logs/rpa.log"

# API 服务配置
api:
  host: "0.0.0.0"
  port: 8000

# 流程配置
flows:
  directory: "flows"
  auto_load: false
  auto_execute: false
```

**注意**: YOLO、OCR、KVM 等参数在流程节点中配置，不在配置文件中。

## 故障排查

```bash
# 查看日志
tail -f logs/rpa.log
```

## 更新部署

```bash
cd /path/to/kvm-rpa
./deploy.sh
```
