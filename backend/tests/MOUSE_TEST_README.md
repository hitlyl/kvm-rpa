# KVM 鼠标测试脚本说明

## 概述

本目录包含多个鼠标测试脚本，用于测试和调试 KVM 鼠标坐标发送功能。

## 测试脚本

### 1. test_mouse_with_screenshot.py（增强版综合测试）

**功能**：
- 测试 11 个不同位置的鼠标移动
- 包括边界测试（原点、最大坐标）
- 自动截图保存
- 详细的调试信息输出

**测试位置**：
1. 原点 (0, 0)
2. 左上角 (50, 50)
3. 上边中点
4. 右上角
5. 右边中点
6. 右下角
7. 下边中点
8. 左下角
9. 左边中点
10. 中心
11. 最大坐标 (width-1, height-1)

**使用方法**：
```bash
cd /Users/liu/Work/sophon/sophon-demo/kvm-rpa/backend/tests
python3 test_mouse_with_screenshot.py
```

**输出**：
- 截图保存在 `mouse_test_screenshots/` 目录
- 文件名格式：`时间戳_序号_位置标签.jpg`

### 2. test_mouse_coordinates_debug.py（交互式调试）

**功能**：
- 逐个测试位置
- 每个位置重复发送 3 次鼠标命令
- 等待足够长的时间
- 用户可以手动检查屏幕
- 交互式控制（按 Enter 继续，输入 'q' 退出）

**使用方法**：
```bash
cd /Users/liu/Work/sophon/sophon-demo/kvm-rpa/backend/tests
python3 test_mouse_coordinates_debug.py
```

**适用场景**：
- 需要手动观察鼠标移动效果
- 调试单个位置的鼠标坐标
- 确认鼠标移动是否生效

### 3. test_mouse_coordinate_comparison.py（方法对比）

**功能**：
- 对比两种鼠标事件发送方法：
  - `send_mouse_event_raw(x, y, 0)` - 简化版本
  - `send_mouse_event(x, y, 0, 1)` - 完整版本
- 为每种方法分别截图
- 方便对比哪种方法更准确

**使用方法**：
```bash
cd /Users/liu/Work/sophon/sophon-demo/kvm-rpa/backend/tests
python3 test_mouse_coordinate_comparison.py
```

**输出**：
- 截图保存在 `mouse_comparison_screenshots/` 目录
- 文件名前缀：
  - `raw_` - 使用 send_mouse_event_raw 方法
  - `normal_` - 使用 send_mouse_event 方法

## 问题诊断

### 问题1：鼠标位置不准确

**可能原因**：
1. **坐标系统问题**：
   - KVM 设备可能使用不同的坐标系统
   - 可能需要坐标转换或缩放

2. **等待时间不足**：
   - 鼠标移动需要时间
   - 视频编码和传输有延迟
   - 建议增加等待时间（当前为 0.8 秒）

3. **鼠标模式设置**：
   - 确认鼠标模式已正确设置为绝对坐标模式
   - 检查设备是否支持绝对坐标模式

4. **坐标范围问题**：
   - 某些设备可能使用 0-65535 的归一化坐标
   - 某些设备使用实际像素坐标
   - 需要根据实际设备调整

### 问题2：截图中看不到鼠标

**可能原因**：
1. **视频流不包含鼠标光标**：
   - 某些 KVM 设备的视频流不包含鼠标光标
   - 鼠标光标可能在客户端渲染

2. **H.264 解码延迟**：
   - 视频解码需要时间
   - 可能需要等待更多帧

### 问题3：左上角图中鼠标在右上角

**可能原因**：
1. **X 坐标反转**：
   - 可能需要使用 `width - x` 来反转 X 坐标

2. **坐标字节序问题**：
   - 检查大端/小端字节序
   - 当前实现使用大端序（与 Java 一致）

3. **坐标解释错误**：
   - 设备可能以不同方式解释坐标
   - 可能需要查看设备文档

## 调试技巧

### 1. 查看详细日志

修改脚本开头的日志级别：
```python
logging.basicConfig(
    level=logging.DEBUG,  # 改为 DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 2. 增加等待时间

在脚本中找到 `await asyncio.sleep(0.8)` 并增加时间：
```python
await asyncio.sleep(2.0)  # 增加到 2 秒
```

### 3. 检查坐标编码

脚本会输出坐标的十六进制表示，例如：
```
坐标十六进制: X=0x0032, Y=0x0032
```

对比 Java 参考实现中的编码方式。

### 4. 使用交互式测试

使用 `test_mouse_coordinates_debug.py`，可以：
- 逐个测试位置
- 手动观察屏幕
- 确认鼠标是否移动到正确位置

## 下一步

如果问题仍然存在，建议：

1. **查看 Java 参考实现**：
   - 检查 `ViewerSample.java` 中的 `encodeMouseEvent` 方法
   - 确认坐标编码方式完全一致

2. **抓包分析**：
   - 使用 Wireshark 抓包
   - 对比 Java 客户端和 Python 客户端发送的数据包
   - 确认字节序和数据格式

3. **咨询设备文档**：
   - 查看 KVM 设备的协议文档
   - 确认鼠标坐标的格式和范围

4. **测试不同分辨率**：
   - 尝试不同的视频分辨率
   - 确认坐标是否与分辨率相关

## 配置

所有测试脚本的 KVM 配置都在脚本开头：

```python
KVM_IP = "192.168.0.100"
KVM_PORT = 5900
KVM_CHANNEL = 0
USERNAME = "admin"
PASSWORD = "123456"
```

根据实际情况修改这些参数。

## 依赖

确保已安装所需的 Python 包：

```bash
pip install opencv-python numpy
```

FFmpeg 也需要安装（用于 H.264 解码）：

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

## 联系

如有问题，请联系开发团队。


















