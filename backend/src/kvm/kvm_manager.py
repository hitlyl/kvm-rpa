"""KVM 连接池管理器

实现 KVM 实例的单例缓存，多流程共享同一个 KVM 连接。
根据 (ip, port, channel) 生成唯一 key，提供帧缓存和鼠标/键盘操作接口。
"""
import asyncio
import threading
import time
import subprocess
import tempfile
import os
from queue import Queue, Empty
from typing import Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from loguru import logger

import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


# H.264 编码类型
ENCODING_H264 = 7


@dataclass
class KVMInstance:
    """KVM 实例数据"""
    key: str
    ip: str
    port: int
    channel: int
    username: str
    password: str
    client: Any = None
    connected: bool = False
    last_frame: Optional[np.ndarray] = None
    last_frame_time: float = 0.0
    frame_width: int = 0
    frame_height: int = 0
    ref_count: int = 0  # 引用计数
    lock: threading.Lock = field(default_factory=threading.Lock)
    
    # H.264 解码相关
    h264_buffer: bytearray = field(default_factory=bytearray)
    has_keyframe: bool = False
    sps: Optional[bytes] = None
    pps: Optional[bytes] = None
    temp_dir: Optional[str] = None
    frame_index: int = 0


class KVMManager:
    """KVM 连接池管理器
    
    单例模式，管理所有 KVM 连接实例。
    多个流程可以共享同一个 KVM 连接。
    """
    
    _instance: Optional['KVMManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化管理器"""
        if self._initialized:
            return
        
        self._initialized = True
        self._instances: Dict[str, KVMInstance] = {}
        self._global_lock = threading.Lock()
        
        # 异步事件循环
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
        self._running = False
        
        # 检查 FFmpeg
        self._ffmpeg_available = self._check_ffmpeg()
        
        logger.info("KVM 连接池管理器初始化完成")
    
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
    
    @staticmethod
    def _generate_key(ip: str, port: int, channel: int) -> str:
        """生成唯一 key"""
        return f"{ip}:{port}:{channel}"
    
    def _ensure_event_loop(self) -> None:
        """确保事件循环运行中"""
        if self._running and self._loop:
            return
        
        self._running = True
        self._loop_thread = threading.Thread(
            target=self._run_event_loop,
            daemon=True,
            name="KVMManager-EventLoop"
        )
        self._loop_thread.start()
        
        # 等待事件循环就绪
        time.sleep(0.2)
        logger.debug("KVM 管理器事件循环已启动")
    
    def _run_event_loop(self) -> None:
        """事件循环线程"""
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()
        except Exception as e:
            logger.error(f"事件循环异常: {e}")
        finally:
            if self._loop:
                self._loop.close()
            logger.debug("KVM 管理器事件循环已退出")
    
    def _run_coroutine(self, coro) -> Any:
        """在事件循环中运行协程"""
        if not self._loop:
            raise RuntimeError("事件循环未运行")
        
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future
    
    def get_or_create(
        self,
        ip: str,
        port: int = 5900,
        channel: int = 0,
        username: str = "admin",
        password: str = "admin",
        timeout: float = 30.0
    ) -> Optional[KVMInstance]:
        """获取或创建 KVM 实例
        
        如果已存在相同配置的实例，则复用；否则创建新实例。
        
        Args:
            ip: KVM IP 地址
            port: 端口
            channel: 通道
            username: 用户名
            password: 密码
            timeout: 连接超时
            
        Returns:
            KVMInstance 或 None
        """
        key = self._generate_key(ip, port, channel)
        
        with self._global_lock:
            if key in self._instances:
                instance = self._instances[key]
                if instance.connected:
                    instance.ref_count += 1
                    logger.info(f"复用 KVM 连接: {key}, 引用计数: {instance.ref_count}")
                    return instance
                else:
                    # 连接已断开，尝试重连
                    logger.info(f"KVM 连接已断开，尝试重连: {key}")
            
            # 创建新实例
            instance = KVMInstance(
                key=key,
                ip=ip,
                port=port,
                channel=channel,
                username=username,
                password=password,
                temp_dir=tempfile.mkdtemp(prefix='kvm_h264_')
            )
            self._instances[key] = instance
        
        # 连接
        if self._connect_instance(instance, timeout):
            instance.ref_count = 1
            logger.info(f"KVM 连接成功: {key}")
            return instance
        else:
            logger.error(f"KVM 连接失败: {key}")
            with self._global_lock:
                del self._instances[key]
            return None
    
    def _connect_instance(self, instance: KVMInstance, timeout: float) -> bool:
        """连接 KVM 实例"""
        from kvm.kvm_client_wrapper import KVMClientWrapper
        
        try:
            self._ensure_event_loop()
            
            # 创建客户端
            client = KVMClientWrapper()
            
            # 设置视频回调
            def on_frame(frame_data: bytes, width: int, height: int, encoding_type: int):
                self._on_video_frame(instance, frame_data, width, height, encoding_type)
            
            client.set_frame_callback(on_frame)
            
            # 连接
            result = client.connect(
                ip=instance.ip,
                port=instance.port,
                channel=instance.channel,
                username=instance.username,
                password=instance.password,
                timeout=timeout
            )
            
            if result:
                instance.client = client
                instance.connected = True
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"连接 KVM 异常: {e}")
            return False
    
    def _on_video_frame(
        self,
        instance: KVMInstance,
        frame_data: bytes,
        width: int,
        height: int,
        encoding_type: int
    ) -> None:
        """视频帧回调"""
        try:
            instance.frame_width = width
            instance.frame_height = height
            
            frame = None
            
            if encoding_type == ENCODING_H264:
                frame = self._decode_h264_frame(instance, frame_data)
            elif len(frame_data) >= width * height * 3:
                frame = self._decode_raw_frame(frame_data, width, height)
            
            if frame is not None:
                with instance.lock:
                    instance.last_frame = frame
                    instance.last_frame_time = time.time()
                    
        except Exception as e:
            logger.debug(f"处理视频帧异常: {e}")
    
    def _decode_raw_frame(
        self,
        frame_data: bytes,
        width: int,
        height: int
    ) -> Optional[np.ndarray]:
        """解码原始帧"""
        if not CV2_AVAILABLE:
            return None
        
        try:
            expected_size = width * height * 3
            if len(frame_data) < expected_size:
                return None
            
            frame_rgb = np.frombuffer(frame_data[:expected_size], dtype=np.uint8)
            frame_rgb = frame_rgb.reshape((height, width, 3))
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            return frame_bgr
        except Exception as e:
            logger.debug(f"解码原始帧失败: {e}")
            return None
    
    def _decode_h264_frame(
        self,
        instance: KVMInstance,
        frame_data: bytes
    ) -> Optional[np.ndarray]:
        """解码 H.264 帧"""
        if not self._ffmpeg_available or not CV2_AVAILABLE:
            return None
        
        try:
            # 检查关键帧
            if len(frame_data) > 4:
                nal_offset = 0
                if frame_data[:4] == b'\x00\x00\x00\x01':
                    nal_offset = 4
                elif frame_data[:3] == b'\x00\x00\x01':
                    nal_offset = 3
                
                if nal_offset > 0 and len(frame_data) > nal_offset:
                    nal_type = frame_data[nal_offset] & 0x1F
                    
                    if nal_type in (5, 7, 8):
                        instance.has_keyframe = True
                        if nal_type == 7:
                            instance.h264_buffer = bytearray()
                    
                    # 提取 SPS/PPS
                    if nal_type == 7:
                        instance.sps = self._extract_nal_unit(frame_data, nal_offset - (4 if nal_offset == 4 else 3))
                    elif nal_type == 8:
                        instance.pps = self._extract_nal_unit(frame_data, nal_offset - (4 if nal_offset == 4 else 3))
            
            instance.h264_buffer.extend(frame_data)
            
            if not instance.has_keyframe:
                return None
            
            # 构建完整的 H.264 数据
            h264_data = bytearray()
            if instance.sps:
                h264_data.extend(instance.sps)
            if instance.pps:
                h264_data.extend(instance.pps)
            
            if not frame_data.startswith(b'\x00\x00\x00\x01') and not frame_data.startswith(b'\x00\x00\x01'):
                h264_data.extend(b'\x00\x00\x00\x01')
            h264_data.extend(instance.h264_buffer)
            
            # 使用 FFmpeg 解码
            instance.frame_index += 1
            output_file = os.path.join(instance.temp_dir, f'frame_{instance.frame_index}.jpg')
            
            cmd = [
                'ffmpeg', '-loglevel', 'error',
                '-f', 'h264', '-i', 'pipe:0',
                '-vframes', '1', '-f', 'image2', '-y', output_file
            ]
            
            result = subprocess.run(
                cmd,
                input=bytes(h264_data),
                capture_output=True,
                timeout=2
            )
            
            if result.returncode == 0 and os.path.exists(output_file):
                img = cv2.imread(output_file)
                os.remove(output_file)
                return img
            
            return None
            
        except subprocess.TimeoutExpired:
            return None
        except Exception as e:
            logger.debug(f"H.264 解码失败: {e}")
            return None
    
    def _extract_nal_unit(self, data: bytes, start_pos: int) -> bytes:
        """提取 NAL 单元"""
        # 查找下一个起始码
        i = start_pos + 4
        while i < len(data) - 3:
            if data[i:i+4] == b'\x00\x00\x00\x01' or data[i:i+3] == b'\x00\x00\x01':
                return data[start_pos:i]
            i += 1
        return data[start_pos:]
    
    def get_frame(
        self,
        ip: str,
        port: int = 5900,
        channel: int = 0,
        timeout: float = 2.0
    ) -> Optional[np.ndarray]:
        """获取最新帧
        
        Args:
            ip: KVM IP
            port: 端口
            channel: 通道
            timeout: 超时时间
            
        Returns:
            BGR 格式的 numpy 数组，或 None
        """
        key = self._generate_key(ip, port, channel)
        
        instance = self._instances.get(key)
        if not instance or not instance.connected:
            logger.warning(f"KVM 未连接: {key}")
            return None
        
        # 等待新帧
        start_time = time.time()
        while time.time() - start_time < timeout:
            with instance.lock:
                if instance.last_frame is not None:
                    return instance.last_frame.copy()
            time.sleep(0.05)
        
        logger.warning(f"获取帧超时: {key}")
        return None
    
    def get_frame_with_reconnect(
        self,
        ip: str,
        port: int = 5900,
        channel: int = 0,
        username: str = "admin",
        password: str = "admin",
        timeout: float = 2.0
    ) -> Optional[np.ndarray]:
        """获取最新帧，连接断开时自动重连
        
        Args:
            ip: KVM IP
            port: 端口
            channel: 通道
            username: 用户名（重连时使用）
            password: 密码（重连时使用）
            timeout: 超时时间
            
        Returns:
            BGR 格式的 numpy 数组，或 None
        """
        key = self._generate_key(ip, port, channel)
        
        instance = self._instances.get(key)
        
        # 检查连接状态，断开则尝试重连
        if instance and not instance.connected:
            logger.info(f"KVM 连接已断开，尝试重连: {key}")
            if self._reconnect_instance(instance, username, password):
                logger.info(f"KVM 重连成功: {key}")
            else:
                logger.error(f"KVM 重连失败: {key}")
                return None
        
        if not instance:
            logger.warning(f"KVM 实例不存在: {key}")
            return None
        
        # 获取最新帧
        with instance.lock:
            if instance.last_frame is not None:
                frame_age = time.time() - instance.last_frame_time
                logger.debug(f"获取帧: {key}, 帧龄={frame_age:.3f}s")
                # 检查帧是否过期（超过 5 秒认为可能断连）
                if frame_age < 5.0:
                    return instance.last_frame.copy()
                else:
                    logger.warning(f"帧过期: {key}, 帧龄={frame_age:.1f}s")
        
        # 如果没有帧或帧过期，等待新帧
        start_time = time.time()
        while time.time() - start_time < timeout:
            # 再次检查连接状态
            if not instance.connected:
                logger.warning(f"KVM 连接在获取帧时断开: {key}")
                return None
            
            with instance.lock:
                if instance.last_frame is not None:
                    frame_age = time.time() - instance.last_frame_time
                    if frame_age < 5.0:
                        logger.debug(f"等待后获取帧: {key}, 帧龄={frame_age:.3f}s")
                        return instance.last_frame.copy()
            time.sleep(0.05)
        
        logger.warning(f"获取帧超时: {key}")
        return None
    
    def _reconnect_instance(
        self,
        instance: KVMInstance,
        username: str,
        password: str,
        timeout: float = 30.0
    ) -> bool:
        """重连 KVM 实例
        
        Args:
            instance: KVM 实例
            username: 用户名
            password: 密码
            timeout: 连接超时
            
        Returns:
            是否成功
        """
        try:
            # 先断开旧连接
            if instance.client:
                try:
                    instance.client.disconnect()
                except Exception:
                    pass
                instance.client = None
            
            instance.connected = False
            instance.username = username
            instance.password = password
            
            # 清理 H.264 状态
            instance.h264_buffer = bytearray()
            instance.has_keyframe = False
            instance.sps = None
            instance.pps = None
            instance.last_frame = None
            instance.last_frame_time = 0.0
            
            # 重新连接
            return self._connect_instance(instance, timeout)
            
        except Exception as e:
            logger.error(f"重连 KVM 异常: {e}")
            return False
    
    def send_mouse_click(
        self,
        ip: str,
        port: int,
        channel: int,
        x: int,
        y: int,
        button: str = "left"
    ) -> bool:
        """发送鼠标点击
        
        使用与测试脚本 test_click_button.py 完全一致的实现：
        1. 移动到位置（button_mask=0）
        2. 等待 0.1 秒
        3. 按下按钮（button_mask=按钮值）
        4. 等待 0.05 秒
        5. 释放按钮（button_mask=0）
        
        使用 send_mouse_event_raw 而不是 send_mouse_click，确保与 Java ViewerSample 一致。
        
        Args:
            ip: KVM IP
            port: 端口
            channel: 通道
            x: X 坐标（像素）
            y: Y 坐标（像素）
            button: 按钮 ("left", "right", "middle")
            
        Returns:
            是否成功
        """
        key = self._generate_key(ip, port, channel)
        instance = self._instances.get(key)
        
        if not instance or not instance.connected or not instance.client:
            logger.warning(f"KVM 未连接: {key}")
            return False
        
        try:
            button_mask = {"left": 0x01, "middle": 0x02, "right": 0x04}.get(button, 0x01)
            x = int(x)
            y = int(y)
            
            # 使用异步方式在事件循环中发送鼠标事件
            future = self._run_coroutine(
                self._async_mouse_click(instance, x, y, button_mask)
            )
            # 等待完成，超时 2 秒
            result = future.result(timeout=2.0)
            
            logger.info(f"发送鼠标点击完成: ({x}, {y}), button={button}")
            return result
        except Exception as e:
            logger.error(f"发送鼠标点击失败: {e}")
            return False
    
    async def _async_mouse_click(
        self,
        instance: KVMInstance,
        x: int,
        y: int,
        button_mask: int
    ) -> bool:
        """异步执行鼠标点击
        
        与测试脚本 test_click_button.py 完全一致的实现。
        """
        try:
            if not instance.client or not instance.client.client:
                logger.warning("KVM 客户端不可用")
                return False
            
            # 获取底层的 KVMClient
            kvm_client = instance.client.client
            
            # 1. 移动到位置
            logger.debug(f"鼠标移动到: ({x}, {y})")
            kvm_client.send_mouse_event_raw(x, y, 0)
            await asyncio.sleep(0.1)  # 等待移动生效
            
            # 2. 按下按钮
            logger.debug(f"鼠标按下: ({x}, {y}), mask={button_mask}")
            kvm_client.send_mouse_event_raw(x, y, button_mask)
            await asyncio.sleep(0.05)  # 等待按下生效
            
            # 3. 释放按钮
            logger.debug(f"鼠标释放: ({x}, {y})")
            kvm_client.send_mouse_event_raw(x, y, 0)
            
            return True
        except Exception as e:
            logger.error(f"异步鼠标点击失败: {e}")
            return False
    
    def send_mouse_move(
        self,
        ip: str,
        port: int,
        channel: int,
        x: int,
        y: int
    ) -> bool:
        """发送鼠标移动
        
        使用 send_mouse_event_raw，与 Java ViewerSample 一致。
        """
        key = self._generate_key(ip, port, channel)
        instance = self._instances.get(key)
        
        if not instance or not instance.connected or not instance.client:
            return False
        
        try:
            # 使用异步方式在事件循环中发送
            future = self._run_coroutine(
                self._async_mouse_move(instance, int(x), int(y))
            )
            future.result(timeout=1.0)
            logger.debug(f"发送鼠标移动: ({x}, {y})")
            return True
        except Exception as e:
            logger.error(f"发送鼠标移动失败: {e}")
            return False
    
    async def _async_mouse_move(
        self,
        instance: KVMInstance,
        x: int,
        y: int
    ) -> bool:
        """异步执行鼠标移动"""
        try:
            if not instance.client or not instance.client.client:
                return False
            
            kvm_client = instance.client.client
            kvm_client.send_mouse_event_raw(x, y, 0)
            return True
        except Exception as e:
            logger.error(f"异步鼠标移动失败: {e}")
            return False
    
    def send_key_input(
        self,
        ip: str,
        port: int,
        channel: int,
        text: str
    ) -> bool:
        """发送键盘文本输入
        
        Args:
            ip: KVM IP
            port: 端口
            channel: 通道
            text: 要输入的文本
            
        Returns:
            是否成功
        """
        key = self._generate_key(ip, port, channel)
        instance = self._instances.get(key)
        
        if not instance or not instance.connected or not instance.client:
            logger.warning(f"KVM 未连接: {key}")
            return False
        
        try:
            # 逐字符发送
            for char in text:
                key_code = ord(char)
                instance.client.send_key_event(key_code, 1)  # 按下
                time.sleep(0.02)
                instance.client.send_key_event(key_code, 0)  # 释放
                time.sleep(0.02)
            
            logger.debug(f"发送键盘输入: {text}")
            return True
        except Exception as e:
            logger.error(f"发送键盘输入失败: {e}")
            return False
    
    def send_key_press(
        self,
        ip: str,
        port: int,
        channel: int,
        key_name: str
    ) -> bool:
        """发送特殊按键
        
        Args:
            ip: KVM IP
            port: 端口
            channel: 通道
            key_name: 按键名称 (ENTER, ESC, TAB, etc.)
            
        Returns:
            是否成功
        """
        key = self._generate_key(ip, port, channel)
        instance = self._instances.get(key)
        
        if not instance or not instance.connected or not instance.client:
            return False
        
        # X11 keysym 映射
        key_map = {
            'ENTER': 0xFF0D,
            'RETURN': 0xFF0D,
            'ESC': 0xFF1B,
            'ESCAPE': 0xFF1B,
            'TAB': 0xFF09,
            'BACKSPACE': 0xFF08,
            'DELETE': 0xFFFF,
            'UP': 0xFF52,
            'DOWN': 0xFF54,
            'LEFT': 0xFF51,
            'RIGHT': 0xFF53,
            'HOME': 0xFF50,
            'END': 0xFF57,
            'PAGEUP': 0xFF55,
            'PAGEDOWN': 0xFF56,
            'F1': 0xFFBE,
            'F2': 0xFFBF,
            'F3': 0xFFC0,
            'F4': 0xFFC1,
            'F5': 0xFFC2,
            'F6': 0xFFC3,
            'F7': 0xFFC4,
            'F8': 0xFFC5,
            'F9': 0xFFC6,
            'F10': 0xFFC7,
            'F11': 0xFFC8,
            'F12': 0xFFC9,
        }
        
        try:
            key_code = key_map.get(key_name.upper())
            if key_code is None:
                logger.warning(f"未知按键: {key_name}")
                return False
            
            instance.client.send_key_event(key_code, 1)
            time.sleep(0.05)
            instance.client.send_key_event(key_code, 0)
            
            logger.debug(f"发送按键: {key_name}")
            return True
        except Exception as e:
            logger.error(f"发送按键失败: {e}")
            return False
    
    def release(self, ip: str, port: int = 5900, channel: int = 0) -> None:
        """释放 KVM 实例引用
        
        当引用计数归零时断开连接。
        """
        key = self._generate_key(ip, port, channel)
        
        with self._global_lock:
            instance = self._instances.get(key)
            if not instance:
                return
            
            instance.ref_count -= 1
            logger.info(f"释放 KVM 连接: {key}, 引用计数: {instance.ref_count}")
            
            if instance.ref_count <= 0:
                self._disconnect_instance(instance)
                del self._instances[key]
                logger.info(f"断开 KVM 连接: {key}")
    
    def _disconnect_instance(self, instance: KVMInstance) -> None:
        """断开 KVM 实例"""
        try:
            if instance.client:
                instance.client.disconnect()
            
            # 清理临时目录
            if instance.temp_dir:
                import shutil
                shutil.rmtree(instance.temp_dir, ignore_errors=True)
            
            instance.connected = False
            instance.client = None
        except Exception as e:
            logger.error(f"断开 KVM 异常: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取所有连接状态"""
        status = {}
        for key, instance in self._instances.items():
            status[key] = {
                'connected': instance.connected,
                'ref_count': instance.ref_count,
                'frame_width': instance.frame_width,
                'frame_height': instance.frame_height,
                'last_frame_time': instance.last_frame_time
            }
        return status
    
    def shutdown(self) -> None:
        """关闭管理器，断开所有连接"""
        logger.info("正在关闭 KVM 连接池管理器...")
        
        with self._global_lock:
            for key, instance in list(self._instances.items()):
                self._disconnect_instance(instance)
            self._instances.clear()
        
        # 停止事件循环
        self._running = False
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        
        if self._loop_thread and self._loop_thread.is_alive():
            self._loop_thread.join(timeout=3.0)
        
        logger.info("KVM 连接池管理器已关闭")


# 全局单例获取函数
def get_kvm_manager() -> KVMManager:
    """获取 KVM 管理器单例"""
    return KVMManager()
