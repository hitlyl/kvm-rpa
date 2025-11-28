"""RTSP 视频采集模块

负责从 RTSP 源拉取视频流，提供帧抓取功能，包括重连策略和监控指标。
支持模拟模式用于开发环境。
"""
import time
import threading
from queue import Queue, Full
from typing import Optional, Dict, Any, Tuple
import numpy as np
from loguru import logger

# 可选导入 OpenCV
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("opencv-python 未安装，RTSP 采集将使用模拟模式")


class RTSPCapture:
    """RTSP 视频采集器
    
    支持从 RTSP 源拉取视频流，维护帧缓存队列，提供自动重连机制。
    
    Attributes:
        rtsp_url: RTSP 流地址
        resolution: 目标分辨率 (宽, 高)
        fps: 目标帧率
        reconnect_attempts: 重连尝试次数
        reconnect_delay: 重连延迟（秒）
        frame_buffer_size: 帧缓存队列大小
    """
    
    def __init__(
        self,
        rtsp_url: str,
        resolution: Tuple[int, int] = (1280, 720),
        fps: int = 8,
        reconnect_attempts: int = 3,
        reconnect_delay: float = 1.0,
        frame_buffer_size: int = 3,
        mock_mode: bool = None
    ):
        """初始化 RTSP 采集器
        
        Args:
            rtsp_url: RTSP 流地址
            resolution: 目标分辨率 (宽, 高)
            fps: 目标帧率
            reconnect_attempts: 重连尝试次数
            reconnect_delay: 重连延迟（秒）
            frame_buffer_size: 帧缓存队列大小
            mock_mode: 是否使用模拟模式（None 表示自动检测）
        """
        self.rtsp_url = rtsp_url
        self.resolution = resolution
        self.fps = fps
        self.reconnect_attempts = reconnect_attempts
        self.reconnect_delay = reconnect_delay
        self.frame_buffer_size = frame_buffer_size
        
        # 确定是否使用模拟模式
        if mock_mode is None:
            self.mock_mode = not CV2_AVAILABLE
        else:
            self.mock_mode = mock_mode
        
        if self.mock_mode:
            logger.warning("RTSP 采集器运行在模拟模式")
        
        # 视频捕获对象
        self.cap = None
        
        # 帧缓存队列
        self.frame_queue: Queue = Queue(maxsize=frame_buffer_size)
        
        # 采集线程
        self.capture_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.is_connected = False
        
        # 监控指标
        self.metrics = {
            'total_frames': 0,        # 总帧数
            'dropped_frames': 0,      # 丢帧数
            'reconnect_count': 0,     # 重连次数
            'current_fps': 0.0,       # 当前帧率
            'last_frame_time': 0.0,   # 最后一帧时间
            'stream_latency': 0.0     # 拉流延迟
        }
        
        # FPS 计算
        self._fps_counter = 0
        self._fps_start_time = time.time()
    
    def start_stream(self) -> bool:
        """启动视频流采集
        
        Returns:
            bool: 是否成功启动
        """
        if self.is_running:
            logger.warning("视频流已在运行中")
            return True
        
        # 连接 RTSP 流
        if not self._connect():
            return False
        
        # 启动采集线程
        self.is_running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        
        logger.info(f"RTSP 视频流已启动: {self.rtsp_url}")
        return True
    
    def stop_stream(self) -> None:
        """停止视频流采集"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # 等待采集线程结束
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=5.0)
        
        # 释放资源
        self._disconnect()
        
        logger.info("RTSP 视频流已停止")
    
    def get_frame(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """获取最新帧
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            字典包含 'frame' (numpy 数组) 和 'timestamp' (时间戳)，
            如果超时或队列为空返回 None
        """
        if not self.is_running:
            logger.warning("视频流未运行")
            return None
        
        try:
            # 从队列获取帧（阻塞等待）
            frame_data = self.frame_queue.get(timeout=timeout)
            return frame_data
        except Exception as e:
            logger.debug(f"获取帧超时: {e}")
            return None
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取监控指标
        
        Returns:
            监控指标字典
        """
        return self.metrics.copy()
    
    def _connect(self) -> bool:
        """连接到 RTSP 流
        
        Returns:
            bool: 是否连接成功
        """
        # 模拟模式：直接返回成功
        if self.mock_mode:
            logger.info("RTSP 流连接成功（模拟模式）")
            self.is_connected = True
            self.cap = "mock_capture"
            return True
        
        if not CV2_AVAILABLE:
            logger.error("OpenCV 未安装，无法连接 RTSP 流")
            return False
        
        logger.info(f"正在连接 RTSP 流: {self.rtsp_url}")
        
        for attempt in range(1, self.reconnect_attempts + 1):
            try:
                # 创建 VideoCapture 对象
                self.cap = cv2.VideoCapture(self.rtsp_url)
                
                # 设置缓冲区大小
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                # 尝试读取一帧验证连接
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    self.is_connected = True
                    logger.success(f"RTSP 流连接成功（尝试 {attempt}/{self.reconnect_attempts}）")
                    return True
                else:
                    raise Exception("无法读取帧")
                    
            except Exception as e:
                logger.warning(f"连接失败（尝试 {attempt}/{self.reconnect_attempts}）: {e}")
                if self.cap:
                    self.cap.release()
                    self.cap = None
                
                if attempt < self.reconnect_attempts:
                    # 指数回退延迟
                    delay = self.reconnect_delay * (2 ** (attempt - 1))
                    logger.info(f"等待 {delay:.1f} 秒后重试...")
                    time.sleep(delay)
        
        logger.error("RTSP 流连接失败，已达最大重试次数")
        return False
    
    def _disconnect(self) -> None:
        """断开 RTSP 流连接"""
        self.is_connected = False
        if self.cap:
            if not self.mock_mode and CV2_AVAILABLE:
                self.cap.release()
            self.cap = None
    
    def _reconnect(self) -> bool:
        """重新连接 RTSP 流
        
        Returns:
            bool: 是否重连成功
        """
        logger.warning("RTSP 流连接丢失，尝试重连...")
        self.metrics['reconnect_count'] += 1
        
        self._disconnect()
        time.sleep(self.reconnect_delay)
        
        return self._connect()
    
    def _capture_loop(self) -> None:
        """采集循环（在独立线程中运行）"""
        frame_interval = 1.0 / self.fps
        last_capture_time = 0.0
        
        logger.info("视频采集线程已启动")
        
        while self.is_running:
            try:
                # 控制帧率
                current_time = time.time()
                elapsed = current_time - last_capture_time
                if elapsed < frame_interval:
                    time.sleep(frame_interval - elapsed)
                    continue
                
                last_capture_time = current_time
                
                # 检查连接状态
                if not self.is_connected or self.cap is None:
                    if not self._reconnect():
                        time.sleep(1.0)
                        continue
                
                # 模拟模式：生成模拟帧
                if self.mock_mode:
                    # 生成随机灰度图像
                    frame = np.random.randint(0, 256, 
                                             (self.resolution[1], self.resolution[0], 3), 
                                             dtype=np.uint8)
                else:
                    # 真实模式：从 RTSP 读取帧
                    ret, frame = self.cap.read()
                    
                    if not ret or frame is None:
                        logger.warning("读取帧失败，尝试重连...")
                        self.is_connected = False
                        continue
                    
                    # 调整分辨率（如果需要）
                    if frame.shape[1] != self.resolution[0] or frame.shape[0] != self.resolution[1]:
                        if CV2_AVAILABLE:
                            frame = cv2.resize(frame, self.resolution)
                
                # 创建帧数据
                frame_data = {
                    'frame': frame,
                    'timestamp': current_time
                }
                
                # 放入队列（如果队列满则丢弃最旧的帧）
                try:
                    self.frame_queue.put_nowait(frame_data)
                except Full:
                    # 队列满，丢弃旧帧并放入新帧
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait(frame_data)
                        self.metrics['dropped_frames'] += 1
                    except:
                        pass
                
                # 更新指标
                self.metrics['total_frames'] += 1
                self.metrics['last_frame_time'] = current_time
                
                # 计算 FPS
                self._fps_counter += 1
                if current_time - self._fps_start_time >= 1.0:
                    self.metrics['current_fps'] = self._fps_counter / (current_time - self._fps_start_time)
                    self._fps_counter = 0
                    self._fps_start_time = current_time
                
            except Exception as e:
                logger.error(f"采集循环异常: {e}")
                time.sleep(1.0)
        
        logger.info("视频采集线程已停止")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start_stream()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.stop_stream()

