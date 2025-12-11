"""
同步 KVM 客户端

提供简洁的同步 API，整合连接、协议和帧缓存
"""

import time
import logging
from typing import Optional, Callable

try:
    import numpy as np
except ImportError:
    np = None

from .sync_connection import SyncConnection
from .sync_protocol import SyncProtocolHandler
from .frame_buffer import FrameBuffer

logger = logging.getLogger(__name__)


class SyncKVMClient:
    """同步 KVM 客户端
    
    提供简单的同步 API：
    - connect() / disconnect()
    - send_mouse_event_raw() / send_key_event()
    - set_mouse_type()
    - get_latest_frame()
    
    使用示例：
        client = SyncKVMClient()
        if client.connect(ip, port, channel, username, password):
            client.set_mouse_type(1)  # 绝对坐标模式
            time.sleep(0.5)
            
            # 发送鼠标点击
            client.send_mouse_event_raw(100, 200, 0)  # 移动
            time.sleep(0.1)
            client.send_mouse_event_raw(100, 200, 1)  # 按下
            time.sleep(0.05)
            client.send_mouse_event_raw(100, 200, 0)  # 释放
            
            # 获取视频帧
            frame = client.get_latest_frame()
            
            client.disconnect()
    """
    
    def __init__(self):
        """初始化 KVM 客户端"""
        self._connection = SyncConnection()
        self._protocol = SyncProtocolHandler(self._connection)
        self._frame_buffer = FrameBuffer()
        
        self._connected = False
        self._authenticated = False
        
        # 设置回调
        self._setup_callbacks()
    
    def _setup_callbacks(self):
        """设置内部回调"""
        self._protocol.on_auth_success = self._on_auth_success
        self._protocol.on_auth_failed = self._on_auth_failed
        self._protocol.on_connection_ready = self._on_connection_ready
        self._protocol.on_video_frame = self._on_video_frame
        self._protocol.on_connection_error = self._on_connection_error
        
        self._connection.set_connection_closed_callback(self._on_connection_closed)
    
    def connect(self, ip: str, port: int, channel: int,
                username: str, password: str, timeout: float = 10.0) -> bool:
        """连接到 KVM 设备
        
        Args:
            ip: KVM IP 地址
            port: 端口号（通常为 5900）
            channel: 通道号（通常为 0）
            username: 用户名
            password: 密码
            timeout: 超时时间（秒）
            
        Returns:
            是否连接成功
        """
        logger.info(f"正在连接 KVM: {ip}:{port}, 通道 {channel}")
        
        try:
            # 重置状态
            self._connected = False
            self._authenticated = False
            self._frame_buffer.clear()
            
            # 启动连接和认证
            result = self._protocol.start_connection(
                ip, port, channel, username, password, timeout
            )
            
            if result:
                self._connected = True
                self._authenticated = True
                logger.info(f"KVM 连接成功: {ip}:{port}")
            else:
                logger.error(f"KVM 连接失败: {ip}:{port}")
            
            return result
            
        except Exception as e:
            logger.error(f"连接异常: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if not self._connected:
            return
        
        logger.info("正在断开 KVM 连接")
        
        self._protocol.disconnect()
        self._connected = False
        self._authenticated = False
        self._frame_buffer.cleanup()
        
        logger.info("KVM 连接已断开")
    
    def send_mouse_event(self, x: int, y: int, button_mask: int = 0, mouse_type: int = 1):
        """发送鼠标事件
        
        与 test_mouse_with_screenshot.py 一致，使用归一化坐标（0-65535）。
        
        Args:
            x: X 坐标（0-65535 归一化坐标）
            y: Y 坐标（0-65535 归一化坐标）
            button_mask: 按钮掩码 (0x01=左键, 0x02=中键, 0x04=右键)
            mouse_type: 鼠标类型（0=相对，1=绝对）
        """
        if not self._authenticated:
            logger.warning("无法发送鼠标事件: 未认证")
            return
        
        self._protocol.send_mouse_event(x, y, button_mask, mouse_type)
    
    def send_mouse_event_raw(self, x: int, y: int, button_mask: int = 0) -> bool:
        """发送原始鼠标事件
        
        与 test_click_button.py 中使用的方法完全一致。
        
        Args:
            x: X 坐标
            y: Y 坐标
            button_mask: 按钮掩码 (0x01=左键, 0x02=中键, 0x04=右键)
            
        Returns:
            是否发送成功
        """
        # 详细的状态检查日志
        logger.debug(f"send_mouse_event_raw: authenticated={self._authenticated}, "
                    f"connected={self._connected}, "
                    f"protocol_stage={self._protocol.stage}")
        
        if not self._authenticated:
            logger.warning("无法发送鼠标事件: 未认证 (_authenticated=False)")
            return False
        
        if not self._connected:
            logger.warning("无法发送鼠标事件: 未连接 (_connected=False)")
            return False
        
        return self._protocol.send_mouse_event_raw(x, y, button_mask)
    
    def send_key_event(self, key_code: int, down: int):
        """发送键盘事件
        
        Args:
            key_code: X11 keysym 值
            down: 1 表示按下，0 表示释放
        """
        if not self._authenticated:
            logger.warning("无法发送键盘事件: 未认证")
            return
        
        self._protocol.send_key_event(key_code, down)
    
    def send_key_press(self, key_code: int):
        """发送按键按下事件
        
        Args:
            key_code: X11 keysym 值
        """
        self.send_key_event(key_code, 1)
    
    def send_key_release(self, key_code: int):
        """发送按键释放事件
        
        Args:
            key_code: X11 keysym 值
        """
        self.send_key_event(key_code, 0)
    
    def request_mouse_type(self):
        """请求当前鼠标类型"""
        if not self._authenticated:
            logger.warning("无法请求鼠标类型: 未认证")
            return
        
        self._protocol.request_mouse_type()
    
    def set_mouse_type(self, mouse_type: int):
        """设置鼠标模式
        
        Args:
            mouse_type: 0=相对模式, 1=绝对模式
        """
        # 详细的状态检查日志
        logger.debug(f"set_mouse_type: authenticated={self._authenticated}, "
                    f"connected={self._connected}, "
                    f"protocol_stage={self._protocol.stage}")
        
        if not self._authenticated:
            logger.warning("无法设置鼠标类型: 未认证 (_authenticated=False)")
            return
        
        if not self._connected:
            logger.warning("无法设置鼠标类型: 未连接 (_connected=False)")
            return
        
        self._protocol.set_mouse_type(mouse_type)
    
    def get_latest_frame(self, timeout: float = 1.0) -> Optional['np.ndarray']:
        """获取最新视频帧
        
        Args:
            timeout: 超时时间（秒），帧太旧时返回 None
            
        Returns:
            视频帧（numpy 数组），或 None
        """
        return self._frame_buffer.get_latest_frame(timeout)
    
    def wait_for_new_frame(self, timeout: float = 2.0) -> Optional['np.ndarray']:
        """等待新帧到达
        
        与 get_latest_frame 不同，此方法会等待比当前帧更新的帧。
        适用于需要确保获取"操作后"的最新屏幕状态。
        
        Args:
            timeout: 最长等待时间（秒）
            
        Returns:
            新的视频帧，或 None（超时）
        """
        return self._frame_buffer.wait_for_new_frame(timeout)
    
    def get_frame_info(self) -> dict:
        """获取帧信息
        
        Returns:
            包含宽度、高度等信息的字典
        """
        return self._frame_buffer.get_frame_info()
    
    def get_resolution(self) -> tuple:
        """获取当前分辨率
        
        Returns:
            (width, height) 元组
        """
        return (self._protocol.image_width, self._protocol.image_height)
    
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._connected
    
    def is_authenticated(self) -> bool:
        """是否已认证"""
        return self._authenticated
    
    def set_video_callback(self, callback: Callable[[bytes, int, int, int], None]):
        """设置视频帧回调
        
        Args:
            callback: 回调函数 (frame_data, width, height, encoding_type)
        """
        # 保存用户回调
        self._user_video_callback = callback
    
    # 内部回调方法
    
    def _on_auth_success(self):
        """认证成功回调"""
        logger.info("认证成功")
        self._authenticated = True
    
    def _on_auth_failed(self, reason: str):
        """认证失败回调"""
        logger.error(f"认证失败: {reason}")
        self._authenticated = False
    
    def _on_connection_ready(self):
        """连接就绪回调"""
        logger.info("连接就绪")
    
    def _on_video_frame(self, frame_data: bytes, width: int, height: int, encoding_type: int):
        """视频帧回调"""
        # 传递给帧缓存处理
        self._frame_buffer.on_video_frame(frame_data, width, height, encoding_type)
        
        # 调用用户回调
        if hasattr(self, '_user_video_callback') and self._user_video_callback:
            self._user_video_callback(frame_data, width, height, encoding_type)
    
    def _on_connection_error(self, reason: str):
        """连接错误回调"""
        logger.error(f"连接错误: {reason}")
        self._connected = False
        self._authenticated = False
    
    def _on_connection_closed(self, reason: str):
        """连接关闭回调"""
        logger.info(f"连接关闭: {reason}")
        self._connected = False
        self._authenticated = False
        # 更新协议阶段，防止保活线程继续发送
        from .sync_protocol import ProtocolStage
        self._protocol._stage = ProtocolStage.INVALID

