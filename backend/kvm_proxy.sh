#!/bin/bash
#
# KVM HTTP 代理启动脚本
#
# 使用测试 KVM 配置启动代理服务
#

# KVM 连接配置（与测试脚本一致）
KVM_IP="192.168.0.100"
KVM_PORT=5900
KVM_CHANNEL=0
USERNAME="admin"
PASSWORD="123456"

# HTTP 服务配置
HTTP_PORT=9990
HTTP_HOST="0.0.0.0"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 切换到脚本目录
cd "$SCRIPT_DIR"

echo "=========================================="
echo "KVM HTTP 代理服务"
echo "=========================================="
echo "KVM 地址: ${KVM_IP}:${KVM_PORT}"
echo "KVM 通道: ${KVM_CHANNEL}"
echo "用户名:   ${USERNAME}"
echo "HTTP 服务: http://${HTTP_HOST}:${HTTP_PORT}"
echo "API 文档:  http://localhost:${HTTP_PORT}/docs"
echo "=========================================="
echo ""

# 启动服务
python kvm_proxy.py \
    --ip "${KVM_IP}" \
    --port "${KVM_PORT}" \
    --channel "${KVM_CHANNEL}" \
    --username "${USERNAME}" \
    --password "${PASSWORD}" \
    --http-port "${HTTP_PORT}" \
    --http-host "${HTTP_HOST}"

