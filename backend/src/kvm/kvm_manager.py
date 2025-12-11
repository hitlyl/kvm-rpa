"""KVM 连接池管理器

实现 KVM 实例的单例缓存，多流程共享同一个 KVM 连接。
根据 (ip, port, channel) 生成唯一 key，提供帧缓存和鼠标/键盘操作接口。

同步版本：
- 使用 sync_client.SyncKVMClient
- 无需事件循环管理
- 直接同步发送鼠标/键盘事件
"""

import threading
import time
import os
import sys
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, field
from loguru import logger

import numpy as np

# 添加 src 路径
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# 导入同步 KVM 客户端
from sync_client import SyncKVMClient


@dataclass
class KVMInstance:
    """KVM 实例数据"""
    key: str
    ip: str
    port: int
    channel: int
    username: str
    password: str
    client: SyncKVMClient = None
    connected: bool = False
    ref_count: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock)


class KVMManager:
    """KVM 连接池管理器
    
    单例模式，管理所有 KVM 连接实例。
    多个流程可以共享同一个 KVM 连接。
    
    同步版本：
    - 使用 SyncKVMClient，无需异步事件循环
    - 鼠标/键盘事件直接同步发送
    - 帧缓存由 SyncKVMClient 内部管理
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
        
        logger.info("KVM 连接池管理器初始化完成（同步版本）")
    
    @staticmethod
    def _generate_key(ip: str, port: int, channel: int) -> str:
        """生成唯一 key"""
        return f"{ip}:{port}:{channel}"
    
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
                client = instance.client
                # 检查实际客户端连接和认证状态
                if client and client.is_connected() and client.is_authenticated():
                    instance.ref_count += 1
                    instance.connected = True  # 同步状态
                    logger.info(f"复用 KVM 连接: {key}, 引用计数: {instance.ref_count}")
                    return instance
                else:
                    # 连接已断开或未认证，清理旧实例
                    reason = []
                    if not client:
                        reason.append("client=None")
                    elif not client.is_connected():
                        reason.append("disconnected")
                    elif not client.is_authenticated():
                        reason.append("unauthenticated")
                    logger.info(f"KVM 连接无效 ({', '.join(reason)})，重新创建: {key}")
                    if client:
                        try:
                            client.disconnect()
                        except:
                            pass
                    del self._instances[key]
            
            # 创建新实例
            logger.info(f"创建新 KVM 连接: {key}")
            
            # 创建同步 KVM 客户端
            client = SyncKVMClient()
            
            # 创建实例数据
            instance = KVMInstance(
                key=key,
                ip=ip,
                port=port,
                channel=channel,
                username=username,
                password=password,
                client=client
            )
            
            # 同步连接
            logger.info(f"正在连接 KVM: {key}")
            try:
                result = client.connect(
                    ip=ip,
                    port=port,
                    channel=channel,
                    username=username,
                    password=password,
                    timeout=timeout
                )
                
                if result:
                    # 设置鼠标为绝对坐标模式
                    logger.info("设置鼠标为绝对坐标模式...")
                    client.set_mouse_type(1)
                    time.sleep(0.3)
                    logger.info("鼠标模式设置完成")
                    
                    # 等待第一帧解码完成
                    logger.info("等待视频帧就绪...")
                    first_frame = None
                    for i in range(30):  # 最多等待 3 秒
                        first_frame = client.get_latest_frame(timeout=0.5)
                        if first_frame is not None:
                            logger.info(f"视频帧就绪: {first_frame.shape[1]}x{first_frame.shape[0]}")
                            break
                        time.sleep(0.1)
                    
                    if first_frame is None:
                        logger.warning("等待视频帧超时，但连接仍然有效")
                    
                    instance.connected = True
                    instance.ref_count = 1
                    self._instances[key] = instance
                    logger.info(f"KVM 连接成功: {key}")
                    return instance
                else:
                    logger.error(f"KVM 连接失败: {key}")
                    return None
                    
            except Exception as e:
                logger.error(f"连接 KVM 异常: {e}", exc_info=True)
                return None
    
    def send_mouse_click(
        self,
        ip: str,
        port: int,
        channel: int,
        x: int,
        y: int,
        button: str = "left",
        move_delay: float = 0.02,
        click_delay: float = 0.05,
        auto_reconnect: bool = True
    ) -> bool:
        """发送鼠标点击（同步）
        
        Args:
            ip: KVM IP
            port: 端口
            channel: 通道
            x: X 坐标（像素）
            y: Y 坐标（像素）
            button: 按钮 ("left", "right", "middle")
            move_delay: 移动后延时（秒），确保移动生效
            click_delay: 按下持续时间（秒）
            auto_reconnect: 连接断开时是否自动重连
            
        Returns:
            是否成功
        """
        key = self._generate_key(ip, port, channel)
        instance = self._instances.get(key)
        
        if not instance:
            logger.warning(f"KVM 实例不存在: {key}")
            return False
        
        client = instance.client
        if not client:
            logger.warning(f"KVM 客户端不存在: {key}")
            return False
        
        # 使用实际客户端状态而非缓存状态
        if not client.is_connected() or not client.is_authenticated():
            logger.warning(f"KVM 连接已断开或未认证: {key}")
            instance.connected = False
            
            # 尝试自动重连
            if auto_reconnect:
                logger.info(f"尝试自动重连 KVM: {key}")
                reconnected = self._try_reconnect(instance)
                if not reconnected:
                    logger.error(f"KVM 自动重连失败: {key}")
                    return False
                logger.info(f"KVM 自动重连成功: {key}")
                client = instance.client
            else:
                return False
        
        try:
            button_mask = {"left": 0x01, "middle": 0x02, "right": 0x04}.get(button, 0x01)
            x = int(x)
            y = int(y)
            
            logger.info(f"鼠标点击: ({x}, {y}), button={button}")
            
            # 1. 移动到位置
            if not client.send_mouse_event_raw(x, y, 0):
                logger.error(f"鼠标移动失败: ({x}, {y})")
                instance.connected = False
                return False
            time.sleep(move_delay)
            
            # 2. 按下按钮
            if not client.send_mouse_event_raw(x, y, button_mask):
                logger.error(f"鼠标按下失败: ({x}, {y})")
                instance.connected = False
                return False
            time.sleep(click_delay)
            
            # 3. 释放按钮
            if not client.send_mouse_event_raw(x, y, 0):
                logger.error(f"鼠标释放失败: ({x}, {y})")
                instance.connected = False
                return False
            
            logger.info(f"鼠标点击完成: ({x}, {y})")
            return True
            
        except Exception as e:
            logger.error(f"发送鼠标点击失败: {e}", exc_info=True)
            instance.connected = False
            return False
    
    def _try_reconnect(self, instance: KVMInstance) -> bool:
        """尝试重新连接 KVM
        
        Args:
            instance: KVM 实例
            
        Returns:
            是否重连成功
        """
        try:
            # 先断开旧连接
            if instance.client:
                try:
                    instance.client.disconnect()
                except:
                    pass
            
            # 创建新客户端
            client = SyncKVMClient()
            
            # 尝试连接
            result = client.connect(
                ip=instance.ip,
                port=instance.port,
                channel=instance.channel,
                username=instance.username,
                password=instance.password,
                timeout=10.0
            )
            
            if result:
                # 设置鼠标为绝对坐标模式
                client.set_mouse_type(1)
                time.sleep(0.2)
                
                # 等待视频帧就绪
                for i in range(10):
                    frame = client.get_latest_frame(timeout=0.5)
                    if frame is not None:
                        break
                    time.sleep(0.1)
                
                instance.client = client
                instance.connected = True
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"重连异常: {e}")
            return False
    
    def send_mouse_double_click(
        self,
        ip: str,
        port: int,
        channel: int,
        x: int,
        y: int,
        button: str = "left",
        click_delay: float = 0.05,
        double_click_interval: float = 0.1
    ) -> bool:
        """发送鼠标双击（同步）
        
        Args:
            ip: KVM IP
            port: 端口
            channel: 通道
            x: X 坐标（像素）
            y: Y 坐标（像素）
            button: 按钮 ("left", "right", "middle")
            click_delay: 每次按下持续时间（秒）
            double_click_interval: 两次点击间隔（秒）
            
        Returns:
            是否成功
        """
        key = self._generate_key(ip, port, channel)
        instance = self._instances.get(key)
        
        if not instance:
            logger.warning(f"KVM 实例不存在: {key}")
            return False
        
        client = instance.client
        if not client:
            logger.warning(f"KVM 客户端不存在: {key}")
            return False
        
        # 使用实际客户端状态
        if not client.is_connected():
            logger.warning(f"KVM 连接已断开: {key}")
            instance.connected = False
            return False
        
        if not client.is_authenticated():
            logger.warning(f"KVM 未认证: {key}")
            return False
        
        try:
            button_mask = {"left": 0x01, "middle": 0x02, "right": 0x04}.get(button, 0x01)
            x = int(x)
            y = int(y)
            
            logger.info(f"鼠标双击: ({x}, {y}), button={button}")
            
            # 移动到位置
            if not client.send_mouse_event_raw(x, y, 0):
                instance.connected = False
                return False
            time.sleep(0.02)
            
            # 第一次点击
            if not client.send_mouse_event_raw(x, y, button_mask):
                instance.connected = False
                return False
            time.sleep(click_delay)
            if not client.send_mouse_event_raw(x, y, 0):
                instance.connected = False
                return False
            
            # 两次点击间隔
            time.sleep(double_click_interval)
            
            # 第二次点击
            if not client.send_mouse_event_raw(x, y, button_mask):
                instance.connected = False
                return False
            time.sleep(click_delay)
            if not client.send_mouse_event_raw(x, y, 0):
                instance.connected = False
                return False
            
            logger.info(f"鼠标双击完成: ({x}, {y})")
            return True
            
        except Exception as e:
            logger.error(f"发送鼠标双击失败: {e}", exc_info=True)
            instance.connected = False
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
        
        Args:
            ip: KVM IP
            port: 端口
            channel: 通道
            x: X 坐标
            y: Y 坐标
            
        Returns:
            是否成功
        """
        key = self._generate_key(ip, port, channel)
        instance = self._instances.get(key)
        
        if not instance:
            return False
        
        client = instance.client
        if not client:
            return False
        
        # 使用实际客户端状态
        if not client.is_connected() or not client.is_authenticated():
            instance.connected = False
            return False
        
        try:
            x = int(x)
            y = int(y)
            
            if not client.send_mouse_event_raw(x, y, 0):
                instance.connected = False
                return False
            logger.debug(f"鼠标移动: ({x}, {y})")
            return True
            
        except Exception as e:
            logger.error(f"发送鼠标移动失败: {e}")
            instance.connected = False
            return False
    
    def send_mouse_drag(
        self,
        ip: str,
        port: int,
        channel: int,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        button: str = "left",
        steps: int = 10,
        step_delay: float = 0.02
    ) -> bool:
        """发送鼠标拖拽（同步）
        
        Args:
            ip: KVM IP
            port: 端口
            channel: 通道
            start_x: 起始 X 坐标
            start_y: 起始 Y 坐标
            end_x: 结束 X 坐标
            end_y: 结束 Y 坐标
            button: 按钮 ("left", "right", "middle")
            steps: 拖拽分几步完成
            step_delay: 每步之间的延时（秒）
            
        Returns:
            是否成功
        """
        key = self._generate_key(ip, port, channel)
        instance = self._instances.get(key)
        
        if not instance:
            logger.warning(f"KVM 实例不存在: {key}")
            return False
        
        client = instance.client
        if not client:
            logger.warning(f"KVM 客户端不存在: {key}")
            return False
        
        # 使用实际客户端状态
        if not client.is_connected():
            logger.warning(f"KVM 连接已断开: {key}")
            instance.connected = False
            return False
        
        if not client.is_authenticated():
            logger.warning(f"KVM 未认证: {key}")
            return False
        
        try:
            button_mask = {"left": 0x01, "middle": 0x02, "right": 0x04}.get(button, 0x01)
            start_x, start_y = int(start_x), int(start_y)
            end_x, end_y = int(end_x), int(end_y)
            
            logger.info(f"鼠标拖拽: ({start_x}, {start_y}) -> ({end_x}, {end_y})")
            
            # 1. 移动到起始位置
            if not client.send_mouse_event_raw(start_x, start_y, 0):
                instance.connected = False
                return False
            time.sleep(0.02)
            
            # 2. 按下按钮
            if not client.send_mouse_event_raw(start_x, start_y, button_mask):
                instance.connected = False
                return False
            time.sleep(0.02)
            
            # 3. 分步移动到目标位置（保持按钮按下）
            for i in range(1, steps + 1):
                ratio = i / steps
                current_x = int(start_x + (end_x - start_x) * ratio)
                current_y = int(start_y + (end_y - start_y) * ratio)
                if not client.send_mouse_event_raw(current_x, current_y, button_mask):
                    instance.connected = False
                    return False
                time.sleep(step_delay)
            
            # 4. 释放按钮
            if not client.send_mouse_event_raw(end_x, end_y, 0):
                instance.connected = False
                return False
            
            logger.info(f"鼠标拖拽完成: ({start_x}, {start_y}) -> ({end_x}, {end_y})")
            return True
            
        except Exception as e:
            logger.error(f"发送鼠标拖拽失败: {e}", exc_info=True)
            instance.connected = False
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
            for char in text:
                key_code = ord(char)
                instance.client.send_key_press(key_code)
                time.sleep(0.05)
                instance.client.send_key_release(key_code)
                time.sleep(0.05)
            
            return True
            
        except Exception as e:
            logger.error(f"发送键盘输入失败: {e}")
            return False
    
    def get_latest_frame(
        self,
        ip: str,
        port: int,
        channel: int = 0,
        timeout: float = 1.0
    ) -> Optional[np.ndarray]:
        """获取最新视频帧（从缓存）
        
        注意：此方法返回缓存中的最新帧，可能是几毫秒前的帧。
        如需确保获取操作后的最新帧，请使用 wait_for_new_frame。
        
        Args:
            ip: KVM IP
            port: 端口
            channel: 通道
            timeout: 超时时间（秒），帧太旧则返回 None
            
        Returns:
            视频帧（numpy 数组）或 None
        """
        key = self._generate_key(ip, port, channel)
        instance = self._instances.get(key)
        
        if not instance or not instance.client:
            return None
        
        return instance.client.get_latest_frame(timeout)
    
    def wait_for_new_frame(
        self,
        ip: str,
        port: int,
        channel: int = 0,
        timeout: float = 2.0
    ) -> Optional[np.ndarray]:
        """等待新帧到达
        
        与 get_latest_frame 不同，此方法会等待比当前帧更新的帧。
        适用于需要确保获取"操作后"的最新屏幕状态，例如：
        - 点击按钮后等待画面更新
        - 输入文字后等待显示
        
        Args:
            ip: KVM IP
            port: 端口
            channel: 通道
            timeout: 最长等待时间（秒）
            
        Returns:
            新的视频帧（numpy 数组）或 None（超时）
        """
        key = self._generate_key(ip, port, channel)
        instance = self._instances.get(key)
        
        if not instance or not instance.client:
            return None
        
        return instance.client.wait_for_new_frame(timeout)
    
    def release(self, ip: str, port: int, channel: int = 0) -> None:
        """释放 KVM 连接
        
        引用计数减 1，当引用计数为 0 时真正断开连接。
        
        Args:
            ip: KVM IP
            port: 端口
            channel: 通道
        """
        key = self._generate_key(ip, port, channel)
        
        with self._global_lock:
            instance = self._instances.get(key)
            if not instance:
                return
            
            instance.ref_count -= 1
            logger.info(f"释放 KVM 连接: {key}, 引用计数: {instance.ref_count}")
            
            if instance.ref_count <= 0:
                logger.info(f"断开 KVM 连接: {key}")
                
                if instance.client:
                    try:
                        instance.client.disconnect()
                    except Exception as e:
                        logger.warning(f"断开连接异常: {e}")
                
                del self._instances[key]
                logger.info(f"KVM 连接已释放: {key}")
    
    def send_key_press(
        self,
        ip: str,
        port: int,
        channel: int,
        key: str
    ) -> bool:
        """发送单个按键
        
        Args:
            ip: KVM IP
            port: 端口
            channel: 通道
            key: 按键名称（如 "ENTER", "ESC" 等）
            
        Returns:
            是否成功
        """
        key_name = self._generate_key(ip, port, channel)
        instance = self._instances.get(key_name)
        
        if not instance or not instance.connected or not instance.client:
            logger.warning(f"KVM 未连接: {key_name}")
            return False
        
        # 按键映射
        key_map = {
            "ENTER": 0xFF0D,
            "ESC": 0xFF1B,
            "TAB": 0xFF09,
            "BACKSPACE": 0xFF08,
            "DELETE": 0xFFFF,
            "SPACE": 0x0020,
            "UP": 0xFF52,
            "DOWN": 0xFF54,
            "LEFT": 0xFF51,
            "RIGHT": 0xFF53,
            "HOME": 0xFF50,
            "END": 0xFF57,
            "PAGEUP": 0xFF55,
            "PAGEDOWN": 0xFF56,
            "F1": 0xFFBE,
            "F2": 0xFFBF,
            "F3": 0xFFC0,
            "F4": 0xFFC1,
            "F5": 0xFFC2,
            "F6": 0xFFC3,
            "F7": 0xFFC4,
            "F8": 0xFFC5,
            "F9": 0xFFC6,
            "F10": 0xFFC7,
            "F11": 0xFFC8,
            "F12": 0xFFC9,
        }
        
        key_code = key_map.get(key.upper(), ord(key[0]) if len(key) == 1 else 0)
        if key_code == 0:
            logger.warning(f"未知按键: {key}")
            return False
        
        try:
            instance.client.send_key_press(key_code)
            time.sleep(0.05)
            instance.client.send_key_release(key_code)
            time.sleep(0.05)
            logger.debug(f"按键发送: {key} (0x{key_code:04X})")
            return True
            
        except Exception as e:
            logger.error(f"发送按键失败: {e}")
            return False
    
    def get_frame(
        self,
        ip: str,
        port: int,
        channel: int = 0,
        timeout: float = 1.0
    ) -> Optional[np.ndarray]:
        """获取视频帧（与 get_latest_frame 功能相同）"""
        return self.get_latest_frame(ip, port, channel, timeout)
    
    def get_frame_with_reconnect(
        self,
        ip: str,
        port: int,
        channel: int = 0,
        username: str = "admin",
        password: str = "admin",
        timeout: float = 1.0
    ) -> Optional[np.ndarray]:
        """获取视频帧（带自动重连）"""
        frame = self.get_latest_frame(ip, port, channel, timeout)
        if frame is not None:
            return frame
        
        key = self._generate_key(ip, port, channel)
        instance = self._instances.get(key)
        
        if not instance or not instance.connected:
            logger.info(f"尝试重新连接 KVM: {key}")
            new_instance = self.get_or_create(
                ip=ip,
                port=port,
                channel=channel,
                username=username,
                password=password,
                timeout=30.0
            )
            
            if new_instance and new_instance.connected:
                time.sleep(0.5)
                return self.get_latest_frame(ip, port, channel, timeout)
        
        return None
    
    def cleanup(self) -> None:
        """清理所有连接"""
        with self._global_lock:
            keys = list(self._instances.keys())
            for key in keys:
                instance = self._instances[key]
                logger.info(f"清理 KVM 连接: {key}")
                
                if instance.client:
                    try:
                        instance.client.disconnect()
                    except:
                        pass
            
            self._instances.clear()
        
        logger.info("所有 KVM 连接已清理")


# 全局单例访问函数
_kvm_manager: Optional[KVMManager] = None


def get_kvm_manager() -> KVMManager:
    """获取 KVM 管理器单例"""
    global _kvm_manager
    if _kvm_manager is None:
        _kvm_manager = KVMManager()
    return _kvm_manager
