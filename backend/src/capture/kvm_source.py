"""KVM视频源模块

从KVM设备获取视频流并解码为OpenCV格式的图像帧
支持H.264解码和原始帧两种模式
"""
import time
import threading
from queue import Queue, Full
from typing import Optional, Dict, Any, Tuple
import numpy as np
from loguru import logger

# 可选导入OpenCV
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("opencv-python 未安装,KVM视频源将无法解码H.264")

# 导入KVM客户端包装器
from kvm.kvm_client_wrapper import KVMClientWrapper


class KVMSource:
    """KVM视频源
    
    从KVM设备获取视频流,支持帧解码和跳帧处理
    
    Attributes:
        ip: KVM设备IP地址
        port: KVM设备端口
        channel: KVM通道号
        username: 认证用户名
        password: 认证密码
        frame_skip: 跳帧数(0=不跳帧)
        resolution: 目标分辨率(宽,高)
    """
    
    def __init__(
        self,
        ip: str,
        port: int = 5900,
        channel: int = 0,
        username: str = "admin",
        password: str = "admin",
        frame_skip: int = 0,
        resolution: Tuple[int, int] = None,
        connection_timeout: float = 10.0
    ):
        """初始化KVM视频源
        
        Args:
            ip: KVM设备IP地址
            port: KVM设备端口
            channel: KVM通道号
            username: 认证用户名
            password: 认证密码
            frame_skip: 跳帧数(0=不跳帧,1=跳过1帧,2=跳过2帧...)
            resolution: 目标分辨率(宽,高),None=使用原始分辨率
            connection_timeout: 连接超时(秒)
        """
        self.ip = ip
        self.port = port
        self.channel = channel
        self.username = username
        self.password = password
        self.frame_skip = frame_skip
        self.resolution = resolution
        self.connection_timeout = connection_timeout
        
        # KVM客户端包装器
        self.kvm_client: Optional[KVMClientWrapper] = None
        
        # 解码后的帧缓存队列
        self.decoded_frame_queue: Queue = Queue(maxsize=3)
        
        # 解码线程
        self.decode_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.is_connected = False
        
        # 跳帧计数器
        self._frame_counter = 0
        
        # H.264 解码器
        self.h264_decoder = None
        
        # 监控指标
        self.metrics = {
            'total_frames': 0,
            'decoded_frames': 0,
            'skipped_frames': 0,
            'dropped_frames': 0,
            'decode_errors': 0,
            'current_fps': 0.0,
            'last_frame_time': 0.0
        }
        
        # FPS 计算
        self._fps_counter = 0
        self._fps_start_time = time.time()
    
    def start_stream(self) -> bool:
        """启动KVM视频流
        
        Returns:
            bool: 是否成功启动
        """
        if self.is_running:
            logger.warning("KVM视频流已在运行中")
            return True
        
        logger.info(f"正在启动KVM视频源: {self.ip}:{self.port} 通道{self.channel}")
        
        # 创建KVM客户端
        self.kvm_client = KVMClientWrapper()
        
        # 连接到KVM设备
        if not self.kvm_client.connect(
            ip=self.ip,
            port=self.port,
            channel=self.channel,
            username=self.username,
            password=self.password,
            timeout=self.connection_timeout
        ):
            logger.error("连接KVM设备失败")
            return False
        
        self.is_connected = True
        
        # 设置视频帧回调
        self.kvm_client.set_frame_callback(self._on_kvm_frame)
        
        # 启动解码线程
        self.is_running = True
        self.decode_thread = threading.Thread(target=self._decode_loop, daemon=True)
        self.decode_thread.start()
        
        logger.success(f"KVM视频源已启动: {self.ip}:{self.port}")
        return True
    
    def stop_stream(self) -> None:
        """停止KVM视频流"""
        if not self.is_running:
            return
        
        logger.info("正在停止KVM视频源...")
        self.is_running = False
        
        # 等待解码线程结束
        if self.decode_thread and self.decode_thread.is_alive():
            self.decode_thread.join(timeout=5.0)
        
        # 断开KVM连接
        if self.kvm_client:
            self.kvm_client.disconnect()
            self.kvm_client = None
        
        self.is_connected = False
        logger.info("KVM视频源已停止")
    
    def get_frame(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """获取解码后的视频帧
        
        Args:
            timeout: 超时时间(秒)
            
        Returns:
            字典包含'frame'(numpy数组BGR格式)和'timestamp',
            如果超时或队列为空返回None
        """
        if not self.is_running:
            logger.warning("KVM视频流未运行")
            return None
        
        try:
            frame_data = self.decoded_frame_queue.get(timeout=timeout)
            return frame_data
        except Exception as e:
            logger.debug(f"获取帧超时: {e}")
            return None
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取监控指标
        
        Returns:
            监控指标字典
        """
        metrics = self.metrics.copy()
        
        # 添加KVM客户端统计
        if self.kvm_client:
            kvm_stats = self.kvm_client.get_stats()
            metrics.update({
                'kvm_total_frames': kvm_stats.get('total_frames', 0),
                'kvm_dropped_frames': kvm_stats.get('dropped_frames', 0),
                'kvm_queue_size': kvm_stats.get('queue_size', 0)
            })
        
        return metrics
    
    def _on_kvm_frame(self, frame_data: bytes, width: int, height: int, encoding_type: int) -> None:
        """KVM视频帧回调(在KVM客户端事件循环线程中调用)
        
        Args:
            frame_data: 帧数据
            width: 宽度
            height: 高度
            encoding_type: 编码类型
        """
        # 此回调不做处理,实际解码在decode_loop中进行
        pass
    
    def _decode_loop(self) -> None:
        """解码循环(在独立线程中运行)"""
        logger.info("KVM视频解码线程已启动")
        
        while self.is_running:
            try:
                # 从KVM客户端获取原始帧
                raw_frame = self.kvm_client.get_frame(timeout=1.0)
                if not raw_frame:
                    continue
                
                self.metrics['total_frames'] += 1
                
                # 跳帧处理
                if self.frame_skip > 0:
                    self._frame_counter += 1
                    if self._frame_counter % (self.frame_skip + 1) != 0:
                        self.metrics['skipped_frames'] += 1
                        continue
                
                # 解码帧
                frame_bgr = self._decode_frame(
                    raw_frame['data'],
                    raw_frame['width'],
                    raw_frame['height'],
                    raw_frame['encoding_type']
                )
                
                if frame_bgr is None:
                    self.metrics['decode_errors'] += 1
                    continue
                
                self.metrics['decoded_frames'] += 1
                
                # 调整分辨率(如果需要)
                if self.resolution and CV2_AVAILABLE:
                    if frame_bgr.shape[1] != self.resolution[0] or frame_bgr.shape[0] != self.resolution[1]:
                        frame_bgr = cv2.resize(frame_bgr, self.resolution)
                
                # 创建帧数据
                frame_data = {
                    'frame': frame_bgr,
                    'timestamp': raw_frame['timestamp']
                }
                
                # 放入解码队列
                try:
                    self.decoded_frame_queue.put_nowait(frame_data)
                except Full:
                    # 队列满,丢弃最旧的帧
                    try:
                        self.decoded_frame_queue.get_nowait()
                        self.decoded_frame_queue.put_nowait(frame_data)
                        self.metrics['dropped_frames'] += 1
                    except:
                        pass
                
                # 更新FPS
                current_time = time.time()
                self.metrics['last_frame_time'] = current_time
                self._fps_counter += 1
                if current_time - self._fps_start_time >= 1.0:
                    self.metrics['current_fps'] = self._fps_counter / (current_time - self._fps_start_time)
                    self._fps_counter = 0
                    self._fps_start_time = current_time
                
            except Exception as e:
                logger.error(f"解码循环异常: {e}")
                time.sleep(0.1)
        
        logger.info("KVM视频解码线程已停止")
    
    def _decode_frame(self, frame_data: bytes, width: int, height: int, encoding_type: int) -> Optional[np.ndarray]:
        """解码视频帧
        
        Args:
            frame_data: 原始帧数据
            width: 宽度
            height: 高度
            encoding_type: 编码类型
            
        Returns:
            解码后的BGR格式numpy数组,失败返回None
        """
        try:
            # 根据编码类型选择解码方式
            if encoding_type == 0:
                # Raw RGB/BGR格式
                return self._decode_raw_frame(frame_data, width, height)
            elif encoding_type == 1:
                # H.264格式
                return self._decode_h264_frame(frame_data, width, height)
            else:
                logger.warning(f"不支持的编码类型: {encoding_type}")
                return None
                
        except Exception as e:
            logger.error(f"解码帧失败: {e}")
            return None
    
    def _decode_raw_frame(self, frame_data: bytes, width: int, height: int) -> Optional[np.ndarray]:
        """解码原始RGB/BGR帧
        
        Args:
            frame_data: 原始帧数据
            width: 宽度
            height: 高度
            
        Returns:
            BGR格式numpy数组
        """
        try:
            # 假设数据是RGB24格式
            expected_size = width * height * 3
            if len(frame_data) != expected_size:
                logger.warning(f"帧大小不匹配: 预期{expected_size}, 实际{len(frame_data)}")
                return None
            
            # 转换为numpy数组
            frame_rgb = np.frombuffer(frame_data, dtype=np.uint8).reshape((height, width, 3))
            
            # RGB转BGR(OpenCV格式)
            if CV2_AVAILABLE:
                frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            else:
                # 手动转换
                frame_bgr = frame_rgb[:, :, ::-1].copy()
            
            return frame_bgr
            
        except Exception as e:
            logger.error(f"解码原始帧失败: {e}")
            return None
    
    def _decode_h264_frame(self, frame_data: bytes, width: int, height: int) -> Optional[np.ndarray]:
        """解码H.264帧
        
        Args:
            frame_data: H.264编码数据
            width: 宽度
            height: 高度
            
        Returns:
            BGR格式numpy数组
        """
        if not CV2_AVAILABLE:
            logger.error("OpenCV未安装,无法解码H.264")
            return None
        
        try:
            # 使用OpenCV的VideoCapture解码H.264
            # 注: 这是一个简化的实现,实际可能需要更复杂的解码器
            # 这里假设frame_data是完整的NAL单元
            
            # 临时方案: 如果KVM提供的是完整的编码流,可以使用cv2.imdecode
            # 但H.264通常需要专门的解码器
            
            # TODO: 实现完整的H.264解码
            # 可以使用ffmpeg-python或其他H.264解码库
            
            logger.warning("H.264解码暂未完全实现,返回None")
            return None
            
        except Exception as e:
            logger.error(f"解码H.264帧失败: {e}")
            return None
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start_stream()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.stop_stream()




