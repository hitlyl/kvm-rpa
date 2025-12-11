"""
线程安全的视频帧缓存

负责接收和解码 H.264 视频帧，提供最新帧访问
"""

import os
import time
import logging
import tempfile
import subprocess
import threading
from typing import Optional

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

logger = logging.getLogger(__name__)

# H.264 编码类型
ENCODING_H264 = 7


class FrameBuffer:
    """线程安全的视频帧缓存
    
    功能：
    - 接收 H.264 帧数据
    - 使用 FFmpeg 解码
    - 提供线程安全的帧访问
    
    H.264 解码策略：
    - 单独保存 SPS/PPS 参数集，解码时始终添加
    - GOP 缓冲区只保存 IDR 和 P 帧
    - 解码成功后清空 GOP 缓冲区，等待下一个完整 GOP
    """
    
    def __init__(self):
        """初始化帧缓存"""
        self._lock = threading.Lock()
        
        # 帧数据
        self._latest_frame: Optional[np.ndarray] = None
        self._frame_time: float = 0.0
        self._frame_width: int = 0
        self._frame_height: int = 0
        
        # H.264 解码状态
        self._sps_nal: Optional[bytes] = None  # SPS 参数集 (完整 NAL 单元，含起始码)
        self._pps_nal: Optional[bytes] = None  # PPS 参数集 (完整 NAL 单元，含起始码)
        self._gop_buffer = bytearray()  # 当前 GOP 的帧数据 (IDR + P 帧)
        self._has_sps = False
        self._has_pps = False
        self._has_idr = False  # 当前 GOP 是否有 IDR 帧
        self._frame_index = 0
        self._decode_count = 0  # 解码计数
        self._last_decode_time = 0.0  # 上次解码时间
        
        # 临时目录
        self._temp_dir = tempfile.mkdtemp(prefix='sync_kvm_')
        
        # FFmpeg 可用性
        self._ffmpeg_available = self._check_ffmpeg()
        
        if not CV2_AVAILABLE:
            logger.warning("OpenCV 不可用，无法解码视频帧")
        if not self._ffmpeg_available:
            logger.warning("FFmpeg 不可用，无法解码 H.264")
    
    @staticmethod
    def _check_ffmpeg() -> bool:
        """检查 FFmpeg 是否可用"""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def on_video_frame(self, frame_data: bytes, width: int, height: int, encoding_type: int):
        """处理视频帧回调
        
        Args:
            frame_data: 帧数据
            width: 宽度
            height: 高度
            encoding_type: 编码类型
        """
        if encoding_type == ENCODING_H264:
            self._handle_h264_frame(frame_data, width, height)
        else:
            logger.debug(f"不支持的编码类型: {encoding_type}")
    
    def _handle_h264_frame(self, frame_data: bytes, width: int, height: int):
        """处理 H.264 帧
        
        策略：
        1. 解析收到的帧数据，提取各类 NAL 单元
        2. SPS/PPS 单独保存，不放入 GOP 缓冲区
        3. IDR/P 帧放入 GOP 缓冲区
        4. 收到 IDR 时，重置 GOP 缓冲区（新的 GOP 开始）
        5. 当有完整参数集 (SPS+PPS) 且有 IDR 时，尝试解码
        6. 解码成功后，清空 GOP 缓冲区等待下一帧
        """
        if not CV2_AVAILABLE or not self._ffmpeg_available:
            return
        
        with self._lock:
            # 更新分辨率
            if width > 0 and height > 0:
                if self._frame_width != width or self._frame_height != height:
                    logger.info(f"视频分辨率: {width}x{height}")
                    self._frame_width = width
                    self._frame_height = height
            
            # 解析帧数据中的所有 NAL 单元
            nals = self._parse_nal_units(frame_data)
            
            for nal_type, nal_data in nals:
                if nal_type == 7:  # SPS
                    self._sps_nal = nal_data
                    self._has_sps = True
                    logger.debug(f"保存 SPS: {len(nal_data)} 字节")
                    
                elif nal_type == 8:  # PPS
                    self._pps_nal = nal_data
                    self._has_pps = True
                    logger.debug(f"保存 PPS: {len(nal_data)} 字节")
                    
                elif nal_type == 5:  # IDR (关键帧)
                    # 新的 GOP 开始，清空缓冲区
                    self._gop_buffer = bytearray(nal_data)
                    self._has_idr = True
                    logger.debug(f"新 GOP: IDR {len(nal_data)} 字节")
                    
                elif nal_type == 1:  # P 帧
                    # 只有在有 IDR 后才累积 P 帧
                    if self._has_idr:
                        self._gop_buffer.extend(nal_data)
            
            # 限制 GOP 缓冲区大小（最大 100KB）
            max_gop_size = 100 * 1024
            if len(self._gop_buffer) > max_gop_size:
                # 缓冲区过大，可能是 P 帧累积太多，清空等待下一个 IDR
                logger.warning(f"GOP 缓冲区过大 ({len(self._gop_buffer)} 字节)，清空等待新 IDR")
                self._gop_buffer = bytearray()
                self._has_idr = False
                return
            
            # 检查是否可以解码
            # 需要：SPS + PPS + IDR（至少）
            if not (self._has_sps and self._has_pps and self._has_idr):
                return
            
            # 限制解码频率：每 100ms 最多解码一次
            current_time = time.time()
            if current_time - self._last_decode_time < 0.1:
                return
            
            # 尝试解码
            self._decode_current_gop()
    
    def _parse_nal_units(self, frame_data: bytes) -> list:
        """解析帧数据中的所有 NAL 单元
        
        Args:
            frame_data: 帧数据
            
        Returns:
            [(nal_type, nal_data_with_start_code), ...]
        """
        nals = []
        data = bytes(frame_data)
        
        # 查找所有起始码位置
        start_positions = []
        i = 0
        while i < len(data) - 3:
            if data[i:i+4] == b'\x00\x00\x00\x01':
                start_positions.append((i, 4))
                i += 4
            elif data[i:i+3] == b'\x00\x00\x01':
                start_positions.append((i, 3))
                i += 3
            else:
                i += 1
        
        # 如果没有起始码，返回空列表
        if not start_positions:
            return nals
        
        # 提取每个 NAL 单元
        for idx, (pos, start_len) in enumerate(start_positions):
            # NAL 类型在起始码之后的第一个字节
            nal_type_pos = pos + start_len
            if nal_type_pos >= len(data):
                continue
            
            nal_type = data[nal_type_pos] & 0x1F
            
            # 计算 NAL 单元结束位置
            if idx + 1 < len(start_positions):
                end_pos = start_positions[idx + 1][0]
            else:
                end_pos = len(data)
            
            # 提取完整的 NAL 单元（包含起始码）
            nal_data = data[pos:end_pos]
            nals.append((nal_type, nal_data))
        
        return nals
    
    
    def _decode_current_gop(self):
        """解码当前 GOP
        
        策略：
        1. 构造完整的 H.264 流：SPS + PPS + GOP数据
        2. 使用 FFmpeg 解码输出最后一帧
        3. 解码成功后清空 GOP 缓冲区
        """
        try:
            # 检查必要数据
            if not self._sps_nal or not self._pps_nal:
                logger.debug("缺少 SPS 或 PPS，无法解码")
                return
            
            if len(self._gop_buffer) < 50:
                return  # GOP 数据太少，跳过
            
            # 构造完整的 H.264 流：SPS + PPS + GOP
            h264_stream = bytearray()
            h264_stream.extend(self._sps_nal)
            h264_stream.extend(self._pps_nal)
            h264_stream.extend(self._gop_buffer)
            
            # 使用 FFmpeg 解码
            self._frame_index += 1
            output_file = os.path.join(self._temp_dir, f'frame_{self._frame_index}.jpg')
            
            # FFmpeg 命令：解码并输出最后一帧
            cmd = [
                'ffmpeg',
                '-loglevel', 'error',
                '-f', 'h264',
                '-i', 'pipe:0',
                '-vframes', '1',
                '-update', '1',
                '-f', 'image2',
                '-y',
                output_file
            ]
            
            result = subprocess.run(
                cmd,
                input=bytes(h264_stream),
                capture_output=True,
                timeout=2.0
            )
            
            if result.returncode == 0 and os.path.exists(output_file):
                # 读取解码后的图像
                frame = cv2.imread(output_file)
                
                if frame is not None:
                    self._latest_frame = frame
                    self._frame_time = time.time()
                    self._last_decode_time = time.time()
                    self._decode_count += 1
                    
                    # 解码成功后，清空 GOP 缓冲区，等待下一个完整 GOP
                    # 注意：保留 SPS/PPS，它们不会变化
                    self._gop_buffer = bytearray()
                    self._has_idr = False
                    
                    # 每 50 次解码打印一次详细日志
                    if self._decode_count % 50 == 0:
                        logger.info(f"解码帧 #{self._decode_count}: {frame.shape[1]}x{frame.shape[0]}")
                    else:
                        logger.debug(f"解码帧成功: {frame.shape[1]}x{frame.shape[0]}")
                
                # 删除临时文件
                try:
                    os.remove(output_file)
                except:
                    pass
            else:
                # 解码失败，记录原因
                stderr = result.stderr.decode('utf-8', errors='ignore') if result.stderr else ''
                if stderr:
                    logger.debug(f"FFmpeg 错误: {stderr[:200]}")
                else:
                    logger.debug(f"解码失败，流大小: {len(h264_stream)} 字节")
                    
        except subprocess.TimeoutExpired:
            logger.debug("解码超时")
        except Exception as e:
            logger.debug(f"解码异常: {e}")
    
    def get_latest_frame(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """获取最新帧
        
        Args:
            timeout: 超时时间（秒），如果帧太旧则返回 None
            
        Returns:
            最新的视频帧，或 None
        """
        with self._lock:
            if self._latest_frame is None:
                return None
            
            # 检查帧是否过期
            if timeout > 0 and time.time() - self._frame_time > timeout:
                return None
            
            return self._latest_frame.copy()
    
    def wait_for_new_frame(self, timeout: float = 2.0) -> Optional[np.ndarray]:
        """等待新帧到达
        
        与 get_latest_frame 不同，此方法会等待比当前帧更新的帧。
        适用于需要确保获取"操作后"的最新屏幕状态。
        
        Args:
            timeout: 最长等待时间（秒）
            
        Returns:
            新的视频帧，或 None（超时）
        """
        with self._lock:
            current_frame_time = self._frame_time
        
        start_time = time.time()
        poll_interval = 0.05  # 50ms 轮询间隔
        
        while time.time() - start_time < timeout:
            time.sleep(poll_interval)
            
            with self._lock:
                if self._latest_frame is not None and self._frame_time > current_frame_time:
                    logger.debug(f"获取到新帧，等待时间: {time.time() - start_time:.3f}s")
                    return self._latest_frame.copy()
        
        logger.debug(f"等待新帧超时: {timeout}s")
        return None
    
    def get_frame_info(self) -> dict:
        """获取帧信息
        
        Returns:
            包含宽度、高度、时间戳的字典
        """
        with self._lock:
            return {
                'width': self._frame_width,
                'height': self._frame_height,
                'frame_time': self._frame_time,
                'has_frame': self._latest_frame is not None
            }
    
    def clear(self):
        """清除缓存"""
        with self._lock:
            self._latest_frame = None
            self._frame_time = 0.0
            self._gop_buffer = bytearray()
            self._sps_nal = None
            self._pps_nal = None
            self._has_sps = False
            self._has_pps = False
            self._has_idr = False
            self._decode_count = 0
            self._last_decode_time = 0.0
    
    def cleanup(self):
        """清理资源"""
        self.clear()
        
        # 清理临时目录
        if self._temp_dir and os.path.exists(self._temp_dir):
            try:
                import shutil
                shutil.rmtree(self._temp_dir, ignore_errors=True)
            except:
                pass

