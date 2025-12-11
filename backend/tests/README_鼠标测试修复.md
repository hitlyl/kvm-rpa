# KVM 鼠标测试代码修复说明

## 问题描述

`test_mouse_with_screenshot.py` 测试代码可以正常截图，但是**鼠标光标不显示在正确位置**。

## 问题原因

之前的代码使用了归一化坐标（将像素坐标转换为 0-65535 范围），但这与 Java SDK 的实现不一致。

### Java SDK 的实现方式

查看 Java 参考代码 `ViewerSample.encodeMouseEvent()`：

```java
private synchronized byte[] encodeMouseEvent(int x, int y, int mask) {
    if (x < 0) x = 0; 
    if (y < 0) y = 0;
    
    byte[] mouseMsg = new byte[6];
    mouseMsg[0] = WriteNormalType.PointerEvent.getCode();
    mouseMsg[1] = (byte)mask;
    byte[] xbyte = HexUtils.unsignedShortToRegister(x);  // 直接使用像素坐标
    System.arraycopy(xbyte, 0, mouseMsg, 2, 2);
    byte[] ybyte = HexUtils.unsignedShortToRegister(y);  // 直接使用像素坐标
    System.arraycopy(ybyte, 0, mouseMsg, 4, 2);
    return mouseMsg;
}
```

**关键发现**：Java SDK 直接使用像素坐标（unsignedShort，0-width, 0-height），**不进行归一化**。

## 解决方案

### 1. 修改坐标计算方式

**之前（错误）**:
```python
# 将像素坐标转换为 0-65535 归一化坐标
def to_normalized(pixel_x: int, pixel_y: int) -> tuple:
    norm_x = int(pixel_x / video_width * 65535)
    norm_y = int(pixel_y / video_height * 65535)
    return (norm_x, norm_y)

# 使用归一化坐标
client.send_mouse_event(norm_x, norm_y, 0, mouse_type=1)
```

**现在（正确）**:
```python
# 直接使用像素坐标，与 Java SDK 一致
test_positions = [
    ("左上角", 50, 50),
    ("中心", video_width // 2, video_height // 2),
    ("右下角", video_width - 50, video_height - 50),
]

# 使用 send_mouse_event_raw 方法，直接发送像素坐标
client.send_mouse_event_raw(pixel_x, pixel_y, 0)
```

### 2. 使用正确的方法

使用 `send_mouse_event_raw()` 方法，该方法与 Java SDK 的 `encodeMouseEvent()` 完全一致：

```python
def send_mouse_event_raw(self, x: int, y: int, button_mask: int):
    """发送鼠标事件 - 与 Java ViewerSample.encodeMouseEvent 完全一致
    
    Java ViewerSample 使用这种简化的编码方式，不区分相对/绝对模式，
    由设备端根据当前鼠标模式设置来解释坐标。
    
    Args:
        x: X 坐标（像素坐标）
        y: Y 坐标（像素坐标）
        button_mask: 按钮状态
    """
    # 确保坐标非负
    if x < 0:
        x = 0
    if y < 0:
        y = 0
    
    # 构建数据包 - 与 Java ViewerSample.encodeMouseEvent 完全一致
    data = bytearray(6)
    data[0] = 5  # WriteNormalType.PointerEvent
    data[1] = button_mask & 0xFF  # 不设置 0x80 标志
    
    # X 坐标 (big-endian unsigned short)
    data[2] = (x >> 8) & 0xFF
    data[3] = x & 0xFF
    
    # Y 坐标 (big-endian unsigned short)
    data[4] = (y >> 8) & 0xFF
    data[5] = y & 0xFF
    
    self.connection.write(bytes(data))
```

## 测试结果

修改后，鼠标光标应该正确显示在指定位置：

- 原点 (0, 0)
- 左上角 (50, 50)
- 中心 (width/2, height/2)
- 右下角 (width-50, height-50)
- 等等...

## 关键要点

1. **不要进行坐标归一化** - 直接使用像素坐标（0 到 width-1, 0 到 height-1）
2. **使用 `send_mouse_event_raw()` 方法** - 与 Java SDK 完全一致
3. **设备端负责解释坐标** - 根据当前鼠标模式（绝对/相对）来处理坐标
4. **坐标编码为 unsigned short (big-endian)** - 2 字节，高字节在前

## 文件修改

- `/Users/liu/Work/sophon/sophon-demo/kvm-rpa/backend/tests/test_mouse_with_screenshot.py`
  - 移除了坐标归一化逻辑
  - 改用 `send_mouse_event_raw()` 方法
  - 直接使用像素坐标

## 参考

- Java SDK: `refs/com/hiklife/svc/viewer/ViewerSample.java:660` (encodeMouseEvent 方法)
- Python Client: `backend/src/python_client/protocol/protocol_handler.py:158` (send_mouse_event_raw 方法)










