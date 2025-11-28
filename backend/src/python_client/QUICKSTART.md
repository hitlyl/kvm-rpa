# KVM Python SDK - 快速入门指南

## 安装

1. 进入 python_client 目录：

```bash
cd python_client
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

## 基本用法

### 1. 简单连接

```python
import asyncio
from kvm_client import KVMClient

async def main():
    client = KVMClient()

    # Set video callback
    client.set_video_callback(
        lambda data, w, h, enc: print(f"Frame: {w}x{h}")
    )

    # Connect
    await client.connect(
        ip="192.168.1.100",
        port=5900,
        channel=0,
        username="admin",
        password="123456"
    )

    # Keep connection alive
    await asyncio.sleep(30)

    # Disconnect
    await client.disconnect()

asyncio.run(main())
```

### 2. 发送键盘事件

```python
# 按下和释放按键
client.send_key_event(0x41, 1)  # 按下 'A'（键符 0x41）
await asyncio.sleep(0.1)
client.send_key_event(0x41, 0)  # 释放 'A'

# 或者使用键盘控制器
from input.keyboard import KeyboardController

key_code = KeyboardController.get_keysym('a')
client.send_key_press(key_code)
await asyncio.sleep(0.1)
client.send_key_release(key_code)
```

### 3. 发送鼠标事件

```python
# 绝对位置（0-65535 范围）
client.send_mouse_move(32768, 32768)  # 屏幕中心

# 在位置点击
client.send_mouse_click(32768, 32768, button=0x01)  # 左键点击

# 按钮掩码
BUTTON_LEFT = 0x01      # 左键
BUTTON_MIDDLE = 0x02    # 中键
BUTTON_RIGHT = 0x04     # 右键
```

### 4. 保存视频到文件

```python
video_file = open("output.h264", "wb")

def save_frame(data, w, h, enc):
    video_file.write(data)

client.set_video_callback(save_frame)
# ... 连接并运行 ...
video_file.close()
```

## 运行示例

```bash
# 简单客户端示例
python examples/simple_client.py

# 保存视频到文件
python examples/save_video.py

# RTSP 中继（占位符）
python examples/rtsp_relay.py
```

## 常用 X11 键符

```python
# 字母
'a' = 0x0061, 'A' = 0x0041

# 数字
'0' = 0x0030, '1' = 0x0031, 等等

# 特殊键
'Enter' = 0xff0d      # 回车
'Escape' = 0xff1b     # 退出
'BackSpace' = 0xff08  # 退格
'Tab' = 0xff09        # 制表符
'Delete' = 0xffff     # 删除

# 方向键
'Left' = 0xff51       # 左
'Up' = 0xff52         # 上
'Right' = 0xff53      # 右
'Down' = 0xff54       # 下

# 修饰键
'Shift_L' = 0xffe1    # 左Shift
'Control_L' = 0xffe3  # 左Ctrl
'Alt_L' = 0xffe9      # 左Alt

# 功能键
'F1' = 0xffbe, 'F2' = 0xffbf, 等等
```

## 故障排查

### "连接超时"

- 检查 IP 和端口
- 验证 KVM 设备是否可访问
- 检查防火墙设置

### "身份验证失败"

- 验证用户名和密码
- 检查通道号
- 确保设备支持 VNC 或集中式认证

### "未收到视频帧"

- 在连接前设置视频回调
- 检查设备是否正在发送视频
- 验证 H.264 编码支持

## 配置

在示例或您的代码中编辑这些值：

```python
KVM_IP = "192.168.1.100"  # 您的 KVM 设备 IP
KVM_PORT = 5900            # 通常为 5900
KVM_CHANNEL = 0            # 通常为 0
USERNAME = "admin"         # 您的用户名
PASSWORD = "123456"        # 您的密码
```

## 下一步

1. 阅读完整的 [README.md](README.md) 获取详细文档
2. 查看 [examples/](examples/) 获取更多使用示例
3. 参见 [IMPLEMENTATION.md](IMPLEMENTATION.md) 了解技术细节

## 支持

如有问题：

1. 查看 README.md 文档
2. 审阅示例脚本
3. 查看 IMPLEMENTATION.md 中的实现细节
