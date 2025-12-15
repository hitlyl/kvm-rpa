# 鼠标测试修复日志

## 修复日期
2024-12-03

## 问题描述
鼠标测试代码可以正常截图，但鼠标光标不显示在正确位置。

## 根本原因
测试代码使用了归一化坐标（0-65535），但 Java SDK 直接使用像素坐标。

## 解决方案

### 1. 异步版本修复
**文件**: `backend/tests/test_mouse_with_screenshot.py`

**修改内容**:
- ❌ 删除了坐标归一化逻辑 (`to_normalized()` 函数)
- ✅ 改用 `send_mouse_event_raw()` 方法
- ✅ 直接使用像素坐标
- ✅ 添加十六进制坐标调试信息

**关键代码变更**:
```python
# 之前（错误）
norm_x = int(pixel_x / video_width * 65535)
norm_y = int(pixel_y / video_height * 65535)
client.send_mouse_event(norm_x, norm_y, 0, mouse_type=1)

# 现在（正确）
client.send_mouse_event_raw(pixel_x, pixel_y, 0)
```

### 2. 同步版本修复
**文件**: `backend/sync_tests/test_sync_mouse_screenshot.py`

**修改内容**:
- ✅ 与异步版本保持完全一致的逻辑
- ✅ 使用 `send_mouse_event_raw()` 方法
- ✅ 添加相同的调试信息
- ✅ 更新注释说明

## 修改文件列表

### 测试文件
1. `backend/tests/test_mouse_with_screenshot.py` - 异步版本测试
2. `backend/sync_tests/test_sync_mouse_screenshot.py` - 同步版本测试

### 文档文件（新增）
1. `backend/tests/README_鼠标测试修复.md` - 详细修复说明
2. `backend/tests/README_同步异步对比.md` - 两个版本对比说明
3. `backend/tests/CHANGELOG_鼠标测试修复.md` - 本文件

## 验证方法

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

### 预期结果
- ✅ 鼠标光标准确显示在指定位置
- ✅ 截图中可以清晰看到鼠标指针
- ✅ 11 个测试点全部通过
- ✅ 日志显示正确的坐标信息

## 技术细节

### 坐标编码
- **格式**: Big-endian unsigned short (2 字节)
- **范围**: 0 到 65535 (但使用实际像素值，不是归一化)
- **示例**: 像素 (960, 540) 编码为 `03 C0 02 1C`

### 数据包格式
```
Byte 0: 0x05 (WriteNormalType.PointerEvent)
Byte 1: button_mask
Byte 2-3: X 坐标 (big-endian)
Byte 4-5: Y 坐标 (big-endian)
```

## 参考资料
- Java SDK: `refs/com/hiklife/svc/viewer/ViewerSample.java` (encodeMouseEvent 方法)
- Python 异步: `backend/src/python_client/protocol/protocol_handler.py` (send_mouse_event_raw 方法)
- Python 同步: `backend/src/sync_client/sync_protocol.py` (send_mouse_event_raw 方法)

## 未来改进
- [ ] 添加自动化测试来验证坐标准确性
- [ ] 支持更多分辨率的测试
- [ ] 添加鼠标点击和拖拽测试
- [ ] 性能优化：减少截图间的等待时间

## 备注
- 修改只涉及测试代码，没有改动核心客户端代码
- 异步和同步版本的底层实现已经是正确的
- 此次修复确保了与 Java SDK 的完全兼容性













