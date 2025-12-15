#!/bin/bash
#
# KVM HTTP 代理 API 调用示例
#
# 服务地址: http://localhost:9990
#

BASE_URL="http://localhost:9990"

echo "=========================================="
echo "KVM HTTP 代理 API 调用示例"
echo "=========================================="
echo ""

# 1. 获取状态
echo ">>> 1. 获取状态"
curl -s "${BASE_URL}/status" | python3 -m json.tool
echo ""

# 2. 鼠标移动示例
echo ">>> 2. 鼠标移动到左上角 (50, 50)"
curl -s -X POST "${BASE_URL}/mouse/move" \
  -H "Content-Type: application/json" \
  -d '{"x": 50, "y": 50}'
echo ""
echo ""

echo ">>> 3. 鼠标移动到屏幕中心 (960, 540)"
curl -s -X POST "${BASE_URL}/mouse/move" \
  -H "Content-Type: application/json" \
  -d '{"x": 960, "y": 540}'
echo ""
echo ""

echo ">>> 4. 鼠标移动到右下角 (1870, 1030)"
curl -s -X POST "${BASE_URL}/mouse/move" \
  -H "Content-Type: application/json" \
  -d '{"x": 1870, "y": 1030}'
echo ""
echo ""

# 3. 鼠标点击示例
echo ">>> 5. 左键点击 (500, 300)"
curl -s -X POST "${BASE_URL}/mouse/click" \
  -H "Content-Type: application/json" \
  -d '{"x": 500, "y": 300, "button": "left"}'
echo ""
echo ""

echo ">>> 6. 右键点击 (500, 300)"
curl -s -X POST "${BASE_URL}/mouse/click" \
  -H "Content-Type: application/json" \
  -d '{"x": 500, "y": 300, "button": "right"}'
echo ""
echo ""

# 4. 键盘事件示例
echo ">>> 7. 发送键盘事件 - 按下 A 键 (key_code=65)"
curl -s -X POST "${BASE_URL}/key/send" \
  -H "Content-Type: application/json" \
  -d '{"key_code": 65, "action": "click"}'
echo ""
echo ""

echo ">>> 8. 发送键盘事件 - 按下 Enter 键 (key_code=65293)"
curl -s -X POST "${BASE_URL}/key/send" \
  -H "Content-Type: application/json" \
  -d '{"key_code": 65293, "action": "click"}'
echo ""
echo ""

# 5. 截图示例
echo ">>> 9. 截取当前屏幕"
curl -s "${BASE_URL}/capture" -o capture_sample.jpg
if [ -f capture_sample.jpg ]; then
    echo "截图已保存: capture_sample.jpg"
    ls -lh capture_sample.jpg
else
    echo "截图失败"
fi
echo ""

echo "=========================================="
echo "示例完成"
echo "=========================================="
echo ""
echo "常用 curl 命令："
echo ""
echo "# 获取状态"
echo "curl ${BASE_URL}/status"
echo ""
echo "# 移动鼠标"
echo "curl -X POST ${BASE_URL}/mouse/move -H 'Content-Type: application/json' -d '{\"x\": 500, \"y\": 300}'"
echo ""
echo "# 鼠标点击"
echo "curl -X POST ${BASE_URL}/mouse/click -H 'Content-Type: application/json' -d '{\"x\": 500, \"y\": 300, \"button\": \"left\"}'"
echo ""
echo "# 发送键盘"
echo "curl -X POST ${BASE_URL}/key/send -H 'Content-Type: application/json' -d '{\"key_code\": 65, \"action\": \"click\"}'"
echo ""
echo "# 截图"
echo "curl ${BASE_URL}/capture -o screenshot.jpg"
echo ""













