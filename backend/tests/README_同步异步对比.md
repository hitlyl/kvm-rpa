# 同步与异步鼠标测试代码对比

## 概述

现在同步版本 (`test_sync_mouse_screenshot.py`) 和异步版本 (`test_mouse_with_screenshot.py`) 的鼠标测试代码已经**完全一致**。

## 核心修改

### 1. 坐标处理方式

**统一使用像素坐标，不进行归一化**

```python
# 定义测试位置（像素坐标）
# 注意：Java SDK 的 ViewerSample.encodeMouseEvent 直接使用像素坐标（unsignedShort）
# 不进行归一化，直接发送原始像素坐标值
test_positions = [
    ("原点_0_0", 0, 0),
    ("左上角", 50, 50),
    ("中心", video_width // 2, video_height // 2),
    ("右下角", video_width - 50, video_height - 50),
    # ...
]
```

### 2. 发送方法

**统一使用 `send_mouse_event_raw()` 方法**

```python
# 使用 send_mouse_event_raw 发送鼠标移动命令（与 Java SDK 一致）
print(f"  🖱️  发送鼠标移动命令 (send_mouse_event_raw，像素坐标)...")
client.send_mouse_event_raw(pixel_x, pixel_y, 0)
```

### 3. 调试信息

**统一添加十六进制坐标显示**

```python
# 计算坐标的十六进制表示（用于调试）
x_hex = f"0x{(pixel_x >> 8) & 0xFF:02X}{pixel_x & 0xFF:02X}"
y_hex = f"0x{(pixel_y >> 8) & 0xFF:02X}{pixel_y & 0xFF:02X}"
print(f"  🔢 坐标十六进制: X={x_hex}, Y={y_hex}")
```

## 文件对比

### 异步版本
- 文件: `backend/tests/test_mouse_with_screenshot.py`
- 使用: `python_client.KVMClient` (异步)
- 方法: `await client.connect()`, `await asyncio.sleep()`
- 特点: 使用异步 I/O，线程池解码 H.264

### 同步版本
- 文件: `backend/sync_tests/test_sync_mouse_screenshot.py`
- 使用: `sync_client.SyncKVMClient` (同步)
- 方法: `client.connect()`, `time.sleep()`
- 特点: 使用同步 I/O，简化的 API

## 共同点

1. **坐标系统**: 都使用像素坐标（0 到 width-1, 0 到 height-1）
2. **发送方法**: 都使用 `send_mouse_event_raw(pixel_x, pixel_y, button_mask)`
3. **测试位置**: 完全相同的测试点列表
4. **输出格式**: 相似的进度显示和调试信息

## 底层实现

### 异步版本实现

```python
# python_client/protocol/protocol_handler.py
def send_mouse_event_raw(self, x: int, y: int, button_mask: int):
    """发送鼠标事件 - 与 Java ViewerSample.encodeMouseEvent 完全一致"""
    if x < 0:
        x = 0
    if y < 0:
        y = 0
    
    data = bytearray(6)
    data[0] = 5  # WriteNormalType.PointerEvent
    data[1] = button_mask & 0xFF
    data[2] = (x >> 8) & 0xFF
    data[3] = x & 0xFF
    data[4] = (y >> 8) & 0xFF
    data[5] = y & 0xFF
    
    self.connection.write(bytes(data))
```

### 同步版本实现

```python
# sync_client/sync_protocol.py
def send_mouse_event_raw(self, x: int, y: int, button_mask: int):
    """发送原始鼠标事件（与 Java ViewerSample.encodeMouseEvent 一致）"""
    x = max(0, x)
    y = max(0, y)
    
    data = bytearray(6)
    data[0] = WriteNormalType.POINTER_EVENT.value
    data[1] = button_mask & 0xFF
    data[2:4] = HexUtils.unsigned_short_to_bytes(x)
    data[4:6] = HexUtils.unsigned_short_to_bytes(y)
    
    self.connection.send(bytes(data))
```

**关键点**: 两个实现完全一致，都直接使用像素坐标编码为 big-endian unsigned short。

## 使用示例

### 运行异步测试

```bash
cd /Users/liu/Work/sophon/sophon-demo/kvm-rpa/backend
python tests/test_mouse_with_screenshot.py
```

### 运行同步测试

```bash
cd /Users/liu/Work/sophon/sophon-demo/kvm-rpa/backend
python sync_tests/test_sync_mouse_screenshot.py
```

### 自定义参数

```bash
# 异步版本
python tests/test_mouse_with_screenshot.py

# 同步版本
python sync_tests/test_sync_mouse_screenshot.py \
    --ip 192.168.0.100 \
    --port 5900 \
    --channel 0 \
    --username admin \
    --password 123456 \
    --debug
```

## 预期结果

两个版本应该产生完全相同的结果：

1. **鼠标光标位置准确** - 截图中可以看到鼠标在正确位置
2. **测试点覆盖全面** - 11 个测试点覆盖屏幕各个区域
3. **截图保存成功** - 每个测试点都有对应的截图文件

## 故障排除

如果鼠标位置不正确：

1. **检查鼠标模式** - 确保设置为绝对坐标模式（`set_mouse_type(1)`）
2. **检查视频分辨率** - 确保获取到正确的视频分辨率
3. **检查等待时间** - 可能需要增加等待时间让设备响应
4. **查看日志** - 使用 `--debug` 参数启用详细日志

## 总结

现在同步和异步版本的鼠标测试代码已经完全一致，都正确使用像素坐标与 Java SDK 保持兼容。这确保了：

- ✅ 代码行为一致性
- ✅ 与 Java SDK 完全兼容
- ✅ 测试结果可重现
- ✅ 易于维护和理解













