#!/bin/bash
#
# KVM-RPA 系统部署脚本
# 用途: 编译前端、整合前后端代码到 deploy 目录
#

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
DEPLOY_DIR="$PROJECT_ROOT/deploy"

log_info "========================================"
log_info "KVM-RPA 系统部署脚本"
log_info "========================================"
log_info "项目根目录: $PROJECT_ROOT"
log_info "部署目标目录: $DEPLOY_DIR"
log_info ""

# 检查必要的命令
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 命令未找到，请先安装"
        exit 1
    fi
}

log_info "检查依赖工具..."
check_command pnpm
check_command python3
check_command rsync
log_info "依赖检查完成"
log_info ""

# 清理旧的 deploy 目录
if [ -d "$DEPLOY_DIR" ]; then
    log_warn "清理旧的部署目录..."
    rm -rf "$DEPLOY_DIR"
fi

# 创建 deploy 目录结构
log_info "创建部署目录结构..."
mkdir -p "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR/src"
mkdir -p "$DEPLOY_DIR/static"
mkdir -p "$DEPLOY_DIR/config"
mkdir -p "$DEPLOY_DIR/flows"
mkdir -p "$DEPLOY_DIR/logs"
mkdir -p "$DEPLOY_DIR/models"

log_info "部署目录创建完成"
log_info ""

# 编译前端
log_info "========================================"
log_info "步骤 1: 编译前端代码"
log_info "========================================"
cd "$PROJECT_ROOT/frontend"

if [ ! -d "node_modules" ]; then
    log_info "安装前端依赖..."
    pnpm install
fi

log_info "开始构建前端..."
pnpm run build

if [ ! -d "dist" ]; then
    log_error "前端构建失败，dist 目录未生成"
    exit 1
fi

log_info "前端构建完成"
log_info ""

# 复制前端静态文件
log_info "========================================"
log_info "步骤 2: 复制前端静态文件"
log_info "========================================"
cp -r "$PROJECT_ROOT/frontend/dist"/* "$DEPLOY_DIR/static/"
log_info "前端静态文件复制完成"
log_info ""

# 复制后端代码
log_info "========================================"
log_info "步骤 3: 复制后端代码"
log_info "========================================"
cd "$PROJECT_ROOT/backend"

# 复制 src 目录，排除 __pycache__ 和 .pyc 文件
log_info "复制 src 目录（排除 pyc 文件）..."
rsync -av --exclude='__pycache__' --exclude='*.pyc' src/ "$DEPLOY_DIR/src/"

# 复制主程序
log_info "复制主程序..."
cp main.py "$DEPLOY_DIR/"

# 复制配置文件
log_info "复制配置文件..."
cp config/default.yaml "$DEPLOY_DIR/config/"

# 复制依赖文件
log_info "复制依赖文件..."
cp requirements.txt "$DEPLOY_DIR/"
cp requirements-production.txt "$DEPLOY_DIR/"

# 复制示例流程
if [ -f "flows/example_simple.json" ]; then
    log_info "复制示例流程..."
    cp flows/example_simple.json "$DEPLOY_DIR/flows/"
fi

log_info "后端代码复制完成"
log_info ""

# 创建启动脚本
log_info "========================================"
log_info "步骤 4: 创建启动脚本"
log_info "========================================"

cat > "$DEPLOY_DIR/start.sh" << 'EOF'
#!/bin/bash
#
# KVM-RPA 系统启动脚本
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PID_FILE="$SCRIPT_DIR/kvm-rpa.pid"
LOG_FILE="$SCRIPT_DIR/logs/kvm-rpa.log"

# 检查是否已经在运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "KVM-RPA 系统已在运行中 (PID: $PID)"
        exit 1
    else
        echo "清理过期的 PID 文件..."
        rm -f "$PID_FILE"
    fi
fi

echo "========================================"
echo "启动 KVM-RPA 系统"
echo "========================================"

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "错误: python3 未安装"
    exit 1
fi

# 检查 Python 版本 (要求 3.8+)
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "错误: Python 版本过低 (当前: $PYTHON_VERSION, 要求: $REQUIRED_VERSION+)"
    exit 1
fi

echo "Python 版本: $PYTHON_VERSION"

# 确保日志目录存在
mkdir -p logs

# 启动系统（后台运行）
echo "启动系统（后台模式）..."
nohup python3 -u main.py config/default.yaml > "$LOG_FILE" 2>&1 &
PID=$!

# 保存 PID
echo $PID > "$PID_FILE"

# 等待一下确保启动成功
sleep 2

if ps -p "$PID" > /dev/null 2>&1; then
    echo "系统启动成功 (PID: $PID)"
    echo "日志文件: $LOG_FILE"
    echo ""
    echo "访问地址："
    echo "- 前端界面: http://localhost:8000/"
    echo "- API 文档: http://localhost:8000/docs"
    echo ""
    echo "停止系统: ./stop.sh"
    echo "查看日志: tail -f $LOG_FILE"
else
    echo "系统启动失败，请查看日志: $LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi
EOF

chmod +x "$DEPLOY_DIR/start.sh"

# 创建停止脚本
cat > "$DEPLOY_DIR/stop.sh" << 'EOF'
#!/bin/bash
#
# KVM-RPA 系统停止脚本
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PID_FILE="$SCRIPT_DIR/kvm-rpa.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "系统未运行（PID 文件不存在）"
    exit 0
fi

PID=$(cat "$PID_FILE")

if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "系统未运行（进程不存在）"
    rm -f "$PID_FILE"
    exit 0
fi

echo "正在停止 KVM-RPA 系统 (PID: $PID)..."
kill "$PID"

# 等待进程退出
for i in {1..10}; do
    if ! ps -p "$PID" > /dev/null 2>&1; then
        echo "系统已停止"
        rm -f "$PID_FILE"
        exit 0
    fi
    sleep 1
done

# 如果还未退出，强制终止
echo "强制终止系统..."
kill -9 "$PID" 2>/dev/null
rm -f "$PID_FILE"
echo "系统已强制停止"
EOF

chmod +x "$DEPLOY_DIR/stop.sh"

log_info "启动/停止脚本创建完成"
log_info ""

# 创建 README
log_info "========================================"
log_info "步骤 5: 创建部署说明"
log_info "========================================"

cat > "$DEPLOY_DIR/README.md" << 'EOF'
# KVM-RPA 系统部署说明

## 目录结构

```
deploy/
├── main.py              # 主程序（支持静态文件服务）
├── start.sh             # 启动脚本（后台运行）
├── stop.sh              # 停止脚本
├── requirements.txt     # Python 依赖
├── src/                 # 后端源代码（已排除 pyc 文件）
├── static/              # 前端静态文件
├── config/              # 配置文件
├── flows/               # 流程定义文件
├── logs/                # 日志目录
└── models/              # 模型文件目录
```

## 部署步骤

### 1. 安装依赖

```bash
pip3 install -r requirements.txt
```

### 2. 启动系统

后台启动：

```bash
./start.sh
```

前台运行（调试用）：

```bash
python3 main.py config/default.yaml
```

### 3. 停止系统

```bash
./stop.sh
```

### 4. 访问系统

- 前端界面: http://localhost:8000/
- API 文档: http://localhost:8000/docs

## 配置说明

编辑 `config/default.yaml` 修改配置：

- `api.port`: API 服务端口
- `logging.level`: 日志级别
- `flows.auto_load`: 是否自动加载流程

YOLO、OCR 等参数在流程节点中配置。

## 日志管理

### 查看实时日志

```bash
tail -f logs/kvm-rpa.log
```

### 查看系统状态

检查进程是否运行：

```bash
ps aux | grep "main.py"
```

查看 PID 文件：

```bash
cat kvm-rpa.pid
```

## 注意事项

1. **跨架构部署**：本部署包已排除 .pyc 文件，可在不同架构间（如 x86 到 ARM）部署
2. **后台运行**：系统默认以后台方式运行，PID 保存在 `kvm-rpa.pid`
3. **日志轮转**：建议配置日志轮转避免日志文件过大

## 故障排查

### 启动失败

1. 查看日志文件：`cat logs/kvm-rpa.log`
2. 检查端口占用：`lsof -i :8000`
3. 检查 Python 版本：`python3 --version`（要求 3.8+）

### 系统无响应

1. 检查进程状态：`ps aux | grep main.py`
2. 查看系统资源：`top` 或 `htop`
3. 重启系统：`./stop.sh && ./start.sh`
EOF

log_info "部署说明创建完成"
log_info ""

# 统计信息
log_info "========================================"
log_info "部署完成！"
log_info "========================================"

DEPLOY_SIZE=$(du -sh "$DEPLOY_DIR" | cut -f1)
log_info "部署目录大小: $DEPLOY_SIZE"

FILE_COUNT=$(find "$DEPLOY_DIR" -type f | wc -l)
log_info "文件总数: $FILE_COUNT"

log_info ""
log_info "部署目录: $DEPLOY_DIR"
log_info ""
log_info "下一步操作："
log_info "1. cd deploy"
log_info "2. pip3 install -r requirements.txt"
log_info "3. ./start.sh（后台启动）"
log_info "4. ./stop.sh（停止系统）"
log_info ""
log_info "访问地址："
log_info "- 前端界面: http://localhost:8000/"
log_info "- API 文档: http://localhost:8000/docs"
log_info ""
log_info "注意事项："
log_info "- 已排除 .pyc 文件，支持跨架构部署（如 x86 到 ARM）"
log_info "- 系统默认后台运行，日志文件: logs/kvm-rpa.log"
log_info "========================================"
