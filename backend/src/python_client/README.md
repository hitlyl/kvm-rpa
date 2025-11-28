# KVM Python SDK

用于连接 KVM（键盘、视频、鼠标）设备的 Python SDK，支持身份验证、键盘/鼠标控制和 H.264 视频流。

## 功能特性

- **身份验证**：支持 VNC 身份验证和集中式身份验证
- **键盘控制**：向远程 KVM 设备发送键盘事件
- **鼠标控制**：发送鼠标事件（绝对和相对模式）
- **视频流**：接收 H.264 视频帧，具有灵活的基于回调的处理
- **可选 RTSP 服务器**：将 H.264 视频重新流式传输为 RTSP 供媒体播放器使用
- **异步 I/O**：基于 Python 的 asyncio 构建，实现高效的网络操作

## 安装

```bash
pip install -r requirements.txt
```

## 快速开始

### 基本连接和视频接收

```python
import asyncio
from kvm_client import KVMClient

async def on_video_frame(frame_data, width, height, encoding_type):
    """接收视频帧的回调函数"""
    print(f"接收到帧: {width}x{height}, 大小: {len(frame_data)} 字节")
    # 在此处理 H.264 帧数据

async def main():
    client = KVMClient()

    # 设置视频回调
    client.set_video_callback(on_video_frame)

    # 连接到 KVM 设备
    await client.connect(
        ip="192.168.1.100",
        port=5900,
        channel=0,
        username="admin",
        password="123456"
    )

    # 保持连接
    await asyncio.sleep(30)

    # 断开连接
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

### 发送键盘事件

```python
# 发送按键
client.send_key_event(key_code=0x41, down=1)  # 按下 'A'
await asyncio.sleep(0.1)
client.send_key_event(key_code=0x41, down=0)  # 释放 'A'
```

### 发送鼠标事件

```python
# 绝对鼠标模式（坐标 0-65535）
client.send_mouse_event(x=32768, y=32768, button_mask=0x01, mouse_type=1)

# 相对鼠标模式
client.send_mouse_event(x=10, y=10, button_mask=0x00, mouse_type=0)
```

## API 参考

### KVMClient

KVM 连接的主客户端类。

#### 方法

- `async connect(ip: str, port: int, channel: int, username: str, password: str) -> bool`

  连接到 KVM 设备并进行身份验证。

  - **ip**: KVM 设备的 IP 地址
  - **port**: 端口号（通常为 5900）
  - **channel**: 通道号（通常为 0）
  - **username**: 身份验证用户名
  - **password**: 身份验证密码
  - **返回**: 连接成功返回 True

- `async disconnect()`

  断开与 KVM 设备的连接。

- `send_key_event(key_code: int, down: int)`

  发送键盘事件。

  - **key_code**: 键码（X11 键符值）
  - **down**: 1 表示按下，0 表示释放

- `send_mouse_event(x: int, y: int, button_mask: int, mouse_type: int)`

  发送鼠标事件。

  - **x**: X 坐标
  - **y**: Y 坐标
  - **button_mask**: 按钮状态（0x01=左键，0x02=中键，0x04=右键）
  - **mouse_type**: 0=相对，1=绝对

- `set_video_callback(callback: Callable)`

  设置视频帧接收回调。

  回调签名: `callback(frame_data: bytes, width: int, height: int, encoding_type: int)`

- `set_connection_callback(callback: Callable)`

  设置连接事件回调。

  回调签名: `callback(event: str, data: dict)`

## 协议详情

本 SDK 实现了自定义的基于 RFB 的协议，包含以下阶段：

1. **VERSION**: 交换协议版本（RFB 003.008）
2. **SECURITY_TYPES**: 协商安全类型
3. **SECURITY**: 执行身份验证（VNC 或集中式）
4. **SECURITY_RESULT**: 接收身份验证结果
5. **INITIALISATION**: 接收屏幕/设备初始化数据
6. **NORMAL**: 正常操作（发送/接收视频、键盘、鼠标）

### 支持的安全类型

- **NONE** (0x01): 无身份验证
- **VNC_AUTH** (0x02): 使用 DES 加密的 VNC 身份验证
- **CENTRALIZE_AUTH** (0x14): 集中式身份验证

## 示例

查看 `examples/` 目录获取完整的工作示例：

- `simple_client.py`: 基本连接和视频接收
- `rtsp_relay.py`: RTSP 服务器视频中继设置

## 要求

- Python 3.7+
- pydes（用于 VNC 身份验证）

## 许可证

本 SDK 按原样提供，用于 KVM 设备集成。

## 故障排查

### 连接问题

- 验证 IP 地址和端口正确
- 检查防火墙设置
- 确保 KVM 设备已开机且网络可访问

### 身份验证失败

- 验证用户名和密码
- 检查设备支持哪种身份验证类型
- 确保通道号正确

### 视频问题

- 连接前必须设置视频回调
- H.264 解码需要额外的库（例如 OpenCV、FFmpeg）
- RTSP 服务器需要 `aiortsp` 包

## 高级用法

### 自定义视频处理

```python
async def process_video(frame_data, width, height, encoding_type):
    # 保存到文件
    with open("frame.h264", "ab") as f:
        f.write(frame_data)

    # 或使用 OpenCV/FFmpeg 解码
    # decoded = decode_h264(frame_data)
    # cv2.imshow("KVM", decoded)
```

### 错误处理

```python
try:
    await client.connect(ip, port, channel, username, password)
except ConnectionError as e:
    print(f"连接失败: {e}")
except AuthenticationError as e:
    print(f"身份验证失败: {e}")
```
