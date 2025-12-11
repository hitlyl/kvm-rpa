# KVM 视频帧颜色异常问题修复

## 问题描述

KVM 数据源节点获取到的图片颜色异常（灰色或粉色），但测试脚本 `save_video_screenshots.py` 执行截图却是正常的彩色图像。

## 根本原因（第二次修复）

经过深入对比分析发现，真正的问题在于 **H.264 数据缓冲方式不同**：

### save_video_screenshots.py (正常)

```python
# 累积完整的帧数据（包含起始码）
self.h264_buffer.extend(frame_data)

# 解码时直接使用缓冲区
h264_data = bytes(self.h264_buffer)

cmd = [
    'ffmpeg',
    '-f', 'h264',
    '-i', 'pipe:0',           # 从管道读取完整数据
    '-vframes', '1',
    '-f', 'image2',
    '-y',
    output_file
]
```

### kvm_manager.py (粉色图 - 第一次修复后)

```python
# 问题1：只保存 NAL 数据，丢失起始码
nal_units = self._parse_h264_nals(frame_data)
for nal_data, nal_type in nal_units:
    instance.h264_buffer.extend(nal_data)  # 只有 NAL 数据，没有起始码

# 问题2：尝试手动组装 SPS + PPS + 帧数据
h264_data = instance.sps + instance.pps + bytes(instance.h264_buffer)  # 不完整
```

**问题分析：**

1. **第一个问题（灰色图）**：使用 `-pix_fmt bgr24 -f rawvideo` 输出原始数据，缺少颜色空间转换
2. **第二个问题（粉色图）**：
   - `_parse_h264_nals()` 解析后只保存 NAL 单元本身，**丢失了起始码**
   - 手动组装 `SPS + PPS + 帧数据` 的方式不完整，缺少必要的起始码
   - FFmpeg 无法正确识别 NAL 单元边界，导致解码出粉色图像

**正确做法：**

- 直接累积**完整的帧数据**（包含起始码和 NAL 数据）
- 通过管道传给 FFmpeg，让 FFmpeg 自己解析 NAL 单元
- 输出为 JPG 格式，确保颜色空间转换正确

## 修复方案（第二次 - 完整修复）

将 `kvm_manager.py` 的 H.264 处理逻辑完全改为与 `save_video_screenshots.py` 一致：

### 1. 修改帧处理函数

```python
def _handle_h264_frame(
    self,
    instance: KVMInstance,
    frame_data: bytes,
    width: int,
    height: int
) -> None:
    """处理 H.264 视频帧（与 save_video_screenshots.py 保持一致）"""
    if not CV2_AVAILABLE or not self._ffmpeg_available:
        return

    with instance.lock:
        # 更新分辨率
        if instance.frame_width != width or instance.frame_height != height:
            instance.frame_width = width
            instance.frame_height = height
            logger.info(f"视频分辨率: {width}x{height}")

        # 检查是否是关键帧（与 save_video_screenshots.py 一致）
        if len(frame_data) > 4:
            nal_offset = 0
            if frame_data[:4] == b'\x00\x00\x00\x01':
                nal_offset = 4
            elif frame_data[:3] == b'\x00\x00\x01':
                nal_offset = 3

            if nal_offset > 0 and len(frame_data) > nal_offset:
                nal_type = frame_data[nal_offset] & 0x1F

                # SPS (7), PPS (8), IDR (5) 都表示新的 GOP
                if nal_type in (5, 7, 8):
                    instance.has_keyframe = True
                    # SPS 表示新序列，重置缓冲区
                    if nal_type == 7:
                        instance.h264_buffer = bytearray()

        # 累积整个帧数据（包含起始码，与 save_video_screenshots.py 一致）
        instance.h264_buffer.extend(frame_data)

        # 只有在有关键帧后才尝试解码
        if not instance.has_keyframe:
            return

        # 尝试解码累积的数据
        self._decode_h264_buffer(instance)
```

### 2. 修改解码函数

```python
def _decode_h264_buffer(self, instance: KVMInstance) -> None:
    """解码 H.264 缓冲区（与 save_video_screenshots.py 完全一致）"""
    try:
        # 直接使用缓冲区数据（已包含 SPS/PPS 和起始码）
        h264_data = bytes(instance.h264_buffer)

        # 使用 FFmpeg 通过管道解码（与 save_video_screenshots.py 一致）
        instance.frame_index += 1
        output_file = os.path.join(instance.temp_dir, f'frame_{instance.frame_index}.jpg')

        # FFmpeg 命令：从 stdin 读取 H.264，输出一帧 JPEG
        cmd = [
            'ffmpeg',
            '-f', 'h264',           # 输入格式
            '-i', 'pipe:0',          # 从 stdin 读取
            '-vframes', '1',         # 只输出一帧
            '-f', 'image2',          # 输出图像
            '-y',                    # 覆盖输出文件
            output_file
        ]

        result = subprocess.run(
            cmd,
            input=h264_data,
            capture_output=True,
            timeout=2.0
        )

        if result.returncode == 0 and os.path.exists(output_file):
            # 读取解码后的图像
            frame = cv2.imread(output_file)

            if frame is not None:
                instance.last_frame = frame
                instance.last_frame_time = time.time()
                logger.debug(f"解码帧成功: {frame.shape[1]}x{frame.shape[0]}")

            # 删除临时文件
            try:
                os.remove(output_file)
            except:
                pass

    except subprocess.TimeoutExpired:
        logger.debug("FFmpeg 解码超时")
    except Exception as e:
        logger.debug(f"解码失败: {e}")
```

### 3. 删除不需要的函数和字段

- 删除 `_parse_h264_nals()` 函数（不再需要手动解析 NAL）
- 从 `KVMInstance` 删除 `sps` 和 `pps` 字段（不再单独存储）

## 关键改动

### 第一次修复（解决灰色图）

1. 输出格式从 `.yuv` 改为 `.jpg`
2. FFmpeg 命令改为使用 `-f image2` 输出图像格式
3. 读取方式改为 `cv2.imread()` 读取 JPG

### 第二次修复（解决粉色图）

1. **缓冲方式**：从"解析后只保存 NAL 数据"改为"直接累积完整帧数据（含起始码）"
2. **解码方式**：从"手动组装 SPS+PPS+帧"改为"通过管道传递完整缓冲区给 FFmpeg"
3. **代码简化**：删除 `_parse_h264_nals()` 函数和 `sps`/`pps` 字段
4. **完全对齐**：与 `save_video_screenshots.py` 的实现完全一致

## 测试验证

运行测试脚本验证修复效果：

```bash
cd kvm-rpa/backend
python tests/test_kvm_source_frame.py
```

测试脚本会：

1. 连接到 KVM 设备
2. 获取视频帧
3. 分析图像颜色（检查 BGR 三通道是否有差异）
4. 保存截图到 `test_kvm_source_frame.jpg`

预期输出：

```
✅ 获取到帧: shape=(1080, 1920, 3), dtype=uint8
   通道标准差: B=XX.XX, G=XX.XX, R=XX.XX
   通道均值: B=XX.XX, G=XX.XX, R=XX.XX
   ✅ 图像正常（有色彩）
   📸 已保存截图: test_kvm_source_frame.jpg
```

## 性能影响

- **编码开销**: JPG 编码比原始数据稍慢，但差异不大（毫秒级）
- **磁盘 I/O**: JPG 文件更小，减少磁盘写入
- **解码质量**: JPG 编码可能有轻微的压缩损失，但对于 KVM 显示足够

## 后续优化方向

如果需要更高性能，可以考虑：

1. 使用 PNG 格式（无损，但文件更大）
2. 研究为什么原始 BGR24 格式解码出灰色图，找到正确的颜色空间转换方法
3. 使用 Python 的 H.264 解码库（如 PyAV）替代 FFmpeg 进程调用

## 修改文件

- `kvm-rpa/backend/src/kvm/kvm_manager.py` - `_decode_h264_buffer()` 函数

## 相关问题

- 如果其他地方也使用了类似的原始视频解码方式，可能也需要修复
