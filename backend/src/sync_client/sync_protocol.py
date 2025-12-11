"""
同步协议处理器

实现 KVM 协议状态机，参考 Java ProtocolHandlerImpl.java
复用 python_client/protocol/packets.py 中的数据包定义
"""

import logging
import threading
import time
from enum import Enum
from typing import Optional, Callable, Dict, Any

# 复用现有的包定义和工具
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_client.protocol.packets import (
    VersionPacket,
    SecurityType,
    KeyEventPacket,
    MouseEventPacket,
    VideoFramePacket,
    KeepAlivePacket,
    SharePacket,
    ReadNormalType,
    MouseTypePacket,
    WriteNormalType
)
from python_client.auth.vnc_auth import VncAuth
from python_client.utils.hex_utils import HexUtils

from .sync_connection import SyncConnection

logger = logging.getLogger(__name__)


class ProtocolStage(Enum):
    """协议连接阶段"""
    UNINITIALISED = 0
    PROTOCOL_VERSION = 1
    SECURITY_TYPES = 2
    CENTRALIZE_TYPES = 3
    SECURITY = 4
    SECURITY_RESULT = 5
    INITIALISATION = 6
    NORMAL = 7
    INVALID = 8


class SyncProtocolHandler:
    """同步协议处理器
    
    实现 KVM 协议状态机，处理连接、认证、视频帧等
    """
    
    KEEP_ALIVE_INTERVAL = 3.0  # 保活间隔（秒）
    
    def __init__(self, connection: SyncConnection):
        """初始化协议处理器
        
        Args:
            connection: 同步连接实例
        """
        self.connection = connection
        self._stage = ProtocolStage.PROTOCOL_VERSION
        
        # 连接参数
        self.ip = ""
        self.port = 0
        self.channel = 0
        self.username = ""
        self.password = ""
        
        # 协议状态
        self.security_type: Optional[SecurityType] = None
        self.image_width = 0
        self.image_height = 0
        
        # 回调函数
        self.on_auth_success: Optional[Callable[[], None]] = None
        self.on_auth_failed: Optional[Callable[[str], None]] = None
        self.on_connection_ready: Optional[Callable[[], None]] = None
        self.on_video_frame: Optional[Callable[[bytes, int, int, int], None]] = None
        self.on_connection_error: Optional[Callable[[str], None]] = None
        
        # 消息缓冲区
        self._buffer = bytearray()
        self._buffer_lock = threading.Lock()
        
        # 视频帧解析器
        self._video_parser = VideoFramePacket()
        
        # 认证完成事件
        self._auth_event = threading.Event()
        self._auth_success = False
        
        # 连接就绪事件
        self._ready_event = threading.Event()
        
        # 保活线程
        self._keep_alive_thread: Optional[threading.Thread] = None
        self._keep_alive_stop_event = threading.Event()
        
        # 设置数据接收回调
        connection.set_data_received_callback(self._on_data_received)
    
    @property
    def stage(self) -> ProtocolStage:
        """当前协议阶段"""
        return self._stage
    
    @property
    def is_normal(self) -> bool:
        """是否处于正常阶段"""
        return self._stage == ProtocolStage.NORMAL
    
    def start_connection(self, ip: str, port: int, channel: int,
                        username: str, password: str, timeout: float = 10.0) -> bool:
        """启动连接和认证
        
        Args:
            ip: 服务器 IP
            port: 服务器端口
            channel: 通道号
            username: 用户名
            password: 密码
            timeout: 超时时间（秒）
            
        Returns:
            是否连接成功
        """
        self.ip = ip
        self.port = port
        self.channel = channel
        self.username = username
        self.password = password
        
        # 重置状态
        self._stage = ProtocolStage.PROTOCOL_VERSION
        self._auth_event.clear()
        self._ready_event.clear()
        self._auth_success = False
        self._buffer.clear()
        
        # 连接服务器
        if not self.connection.connect(ip, port):
            return False
        
        # 发送协议版本
        self._send_protocol_version()
        
        # 等待认证完成
        if not self._auth_event.wait(timeout=timeout):
            logger.error("认证超时")
            return False
        
        if not self._auth_success:
            logger.error("认证失败")
            return False
        
        # 等待连接就绪
        if not self._ready_event.wait(timeout=timeout):
            logger.error("连接就绪超时")
            return False
        
        return True
    
    def disconnect(self):
        """断开连接"""
        # 停止保活线程
        self._stop_keep_alive()
        
        self.connection.disconnect()
        self._stage = ProtocolStage.UNINITIALISED
    
    def _start_keep_alive(self):
        """启动保活线程"""
        self._keep_alive_stop_event.clear()
        self._keep_alive_thread = threading.Thread(
            target=self._keep_alive_loop,
            name="SyncProtocol-KeepAlive",
            daemon=True
        )
        self._keep_alive_thread.start()
        logger.debug("保活线程已启动")
    
    def _stop_keep_alive(self):
        """停止保活线程"""
        self._keep_alive_stop_event.set()
        if self._keep_alive_thread and self._keep_alive_thread.is_alive():
            self._keep_alive_thread.join(timeout=2.0)
        self._keep_alive_thread = None
        logger.debug("保活线程已停止")
    
    def _keep_alive_loop(self):
        """保活循环（在后台线程中运行）"""
        logger.debug("保活循环开始")
        while not self._keep_alive_stop_event.is_set():
            # 等待指定时间或直到收到停止信号
            if self._keep_alive_stop_event.wait(timeout=self.KEEP_ALIVE_INTERVAL):
                break
            
            # 检查连接状态，如果已断开则退出循环
            if not self.connection.connected:
                logger.debug("连接已断开，退出保活循环")
                break
            
            # 发送保活包
            if self._stage == ProtocolStage.NORMAL:
                self.send_keep_alive()
                # 如果阶段变为 INVALID，说明发送失败
                if self._stage == ProtocolStage.INVALID:
                    logger.debug("保活发送失败，退出保活循环")
                    break
        
        logger.debug("保活循环结束")
    
    def send_mouse_event(self, x: int, y: int, button_mask: int, mouse_type: int = 1):
        """发送鼠标事件（支持相对/绝对模式）
        
        Args:
            x: X 坐标（当 mouse_type=1 时为绝对坐标，0-65535；mouse_type=0 时为偏移量）
            y: Y 坐标
            button_mask: 按钮掩码
            mouse_type: 鼠标类型（0=相对，1=绝对）
        """
        if self._stage != ProtocolStage.NORMAL:
            logger.warning("无法发送鼠标事件: 未进入 NORMAL 阶段")
            return
        
        packet = MouseEventPacket(x, y, button_mask, mouse_type)
        data = packet.build_rfb()
        logger.debug(
            "发送鼠标事件: x=%s, y=%s, mask=%s, type=%s (%s)",
            x, y, button_mask, mouse_type,
            "绝对" if mouse_type == 1 else "相对"
        )
        self.connection.send(data)
    
    def send_mouse_event_raw(self, x: int, y: int, button_mask: int) -> bool:
        """发送原始鼠标事件（与 Java ViewerSample.encodeMouseEvent 一致）
        
        与异步版本 ProtocolHandler.send_mouse_event_raw 完全一致的实现。
        
        Args:
            x: 像素坐标 X
            y: 像素坐标 Y
            button_mask: 按钮掩码
            
        Returns:
            是否发送成功
        """
        # 详细的状态检查日志
        logger.debug(f"send_mouse_event_raw: 当前阶段={self._stage}, 连接状态={self.connection.connected}")
        
        if self._stage != ProtocolStage.NORMAL:
            logger.warning(f"无法发送鼠标事件: 未进入 NORMAL 阶段, 当前阶段={self._stage}")
            return False
        
        # 确保坐标非负（与异步版本一致）
        if x < 0:
            x = 0
        if y < 0:
            y = 0
        
        # 构建数据包 - 与异步版本 protocol_handler.py 完全一致
        data = bytearray(6)
        data[0] = 5  # WriteNormalType.POINTER_EVENT = 5
        data[1] = button_mask & 0xFF
        
        # X 坐标 (big-endian unsigned short)
        data[2] = (x >> 8) & 0xFF
        data[3] = x & 0xFF
        
        # Y 坐标 (big-endian unsigned short)
        data[4] = (y >> 8) & 0xFF
        data[5] = y & 0xFF
        
        logger.info(
            "发送原始鼠标事件: x=%s, y=%s, mask=%s, bytes=%s",
            x, y, button_mask, HexUtils.bytes_to_hex_string(bytes(data))
        )
        result = self.connection.send(bytes(data))
        if not result:
            logger.error("鼠标事件发送失败 - 连接可能已断开")
        return result
    
    def send_key_event(self, key_code: int, down: int):
        """发送键盘事件
        
        Args:
            key_code: X11 keysym 值
            down: 1 表示按下，0 表示释放
        """
        if self._stage != ProtocolStage.NORMAL:
            logger.warning("无法发送键盘事件: 未进入 NORMAL 阶段")
            return
        
        packet = KeyEventPacket(key_code, down)
        self.connection.send(packet.build_rfb())
    
    def request_mouse_type(self):
        """请求当前鼠标类型
        
        发送 MouseTypeRequest (0x6D 00 00 00) 查询当前鼠标模式
        """
        if self._stage != ProtocolStage.NORMAL:
            logger.warning("无法请求鼠标类型: 未进入 NORMAL 阶段")
            return
        
        # MouseTypeRequest: 109 (0x6D), 0, 0, 0
        data = bytes([0x6D, 0x00, 0x00, 0x00])
        logger.info(f"请求鼠标类型: {data.hex().upper()}")
        self.connection.send(data)
    
    def set_mouse_type(self, mouse_type: int):
        """设置鼠标类型
        
        Args:
            mouse_type: 0=相对模式, 1=绝对模式
        """
        # 详细的状态检查日志
        logger.debug(f"set_mouse_type: 当前阶段={self._stage}, 连接状态={self.connection.connected}")
        
        if self._stage != ProtocolStage.NORMAL:
            logger.warning(f"无法设置鼠标类型: 未进入 NORMAL 阶段, 当前阶段={self._stage}")
            return
        
        packet = MouseTypePacket(mouse_type)
        data = packet.build_rfb()
        logger.info(f"设置鼠标类型: {'绝对' if mouse_type else '相对'}, 数据: {data.hex().upper()}")
        result = self.connection.send(data)
        if not result:
            logger.error("设置鼠标类型发送失败 - 连接可能已断开")
    
    def send_keep_alive(self):
        """发送保活包"""
        # 双重检查：协议阶段和连接状态
        if self._stage == ProtocolStage.NORMAL and self.connection.connected:
            result = self.connection.send(KeepAlivePacket.build_rfb())
            if result:
                logger.debug("保活包已发送")
            else:
                # 发送失败，连接可能已断开
                logger.warning("保活包发送失败，停止保活循环")
                self._stage = ProtocolStage.INVALID
        elif self._stage == ProtocolStage.NORMAL:
            # 协议阶段是 NORMAL 但连接已断开
            logger.warning("连接已断开，更新协议阶段")
            self._stage = ProtocolStage.INVALID
    
    def _send_protocol_version(self):
        """发送协议版本"""
        version = VersionPacket(3, 8)
        data = version.format_version()
        logger.info(f"发送协议版本: RFB 003.008")
        self.connection.send(data)
    
    def _on_data_received(self, data: bytes):
        """处理接收到的数据"""
        with self._buffer_lock:
            self._buffer.extend(data)
            self._process_buffer()
    
    def _process_buffer(self):
        """处理缓冲区数据"""
        while len(self._buffer) > 0:
            consumed = self._handle_protocol_message()
            if consumed == 0:
                break
            self._buffer = self._buffer[consumed:]
    
    def _handle_protocol_message(self) -> int:
        """处理协议消息
        
        Returns:
            消费的字节数
        """
        if len(self._buffer) == 0:
            return 0
        
        try:
            if self._stage == ProtocolStage.PROTOCOL_VERSION:
                return self._handle_version()
            elif self._stage == ProtocolStage.SECURITY_TYPES:
                return self._handle_security_types()
            elif self._stage == ProtocolStage.SECURITY:
                return self._handle_security()
            elif self._stage == ProtocolStage.SECURITY_RESULT:
                return self._handle_security_result()
            elif self._stage == ProtocolStage.INITIALISATION:
                return self._handle_initialisation()
            elif self._stage == ProtocolStage.NORMAL:
                return self._handle_normal()
            else:
                return 0
        except Exception as e:
            logger.error(f"处理协议消息异常: {e}")
            return 0
    
    def _handle_version(self) -> int:
        """处理版本消息"""
        # 服务器版本至少 12 字节，但可能包含设备信息
        if len(self._buffer) < 12:
            return 0
        
        logger.debug(f"版本缓冲区 ({len(self._buffer)} 字节): "
                    f"{self._buffer[:min(100, len(self._buffer))].hex().upper()}")
        
        # 解析版本
        try:
            version = VersionPacket.parse(bytes(self._buffer[:12]))
            logger.info(f"服务器版本: RFB {version.major:03d}.{version.minor:03d}")
        except Exception as e:
            logger.error(f"解析版本失败: {e}")
        
        # 检查是否有设备信息（与异步版本一致）
        # DevicePacket 需要至少 53 字节: VERSION(12) + HEADER(41) = 53
        consumed = 12
        if len(self._buffer) >= 53:
            # 可能包含设备信息，使用小端序读取长度
            device_info_length = HexUtils.bytes_to_int_little_endian(bytes(self._buffer), 12)
            total_device_length = 53 + device_info_length
            logger.debug(f"检测到设备信息, 长度: {device_info_length}, 总长度: {total_device_length}")
            
            if len(self._buffer) >= total_device_length:
                # 跳过设备信息
                consumed = total_device_length
                logger.info(f"跳过设备信息 ({device_info_length} 字节)")
        
        self._stage = ProtocolStage.SECURITY_TYPES
        return consumed
    
    def _handle_security_types(self) -> int:
        """处理安全类型消息"""
        if len(self._buffer) < 1:
            return 0
        
        num_types = self._buffer[0]
        logger.debug(f"安全类型数量: {num_types}, 缓冲区大小: {len(self._buffer)}")
        
        if num_types == 0:
            logger.error("没有可用的安全类型")
            return -1
        
        if len(self._buffer) < 1 + num_types:
            return 0
        
        # 解析安全类型
        types = []
        for i in range(num_types):
            type_code = self._buffer[1 + i]
            st = SecurityType.parse(type_code)
            types.append(st)
            logger.info(f"可用安全类型: {st.name} (code={type_code})")
        
        # 选择 VNC_AUTH 或 NONE
        if SecurityType.VNC_AUTH in types:
            self.security_type = SecurityType.VNC_AUTH
            self._send_security_response(SecurityType.VNC_AUTH)
            self._stage = ProtocolStage.SECURITY
        elif SecurityType.NONE in types:
            self.security_type = SecurityType.NONE
            self._send_security_response(SecurityType.NONE)
            # 对于 NONE 类型，仍需等待 security_result（服务器会返回 0 表示成功）
            self._stage = ProtocolStage.SECURITY_RESULT
        else:
            logger.error("不支持的安全类型")
            self._auth_failed("不支持的安全类型")
        
        return 1 + num_types
    
    def _send_security_response(self, security_type: SecurityType):
        """发送安全类型选择响应"""
        # 1. 发送选择的安全类型
        self.connection.send(bytes([security_type.value]))
        
        # 2. 发送通道路径
        path = bytes([self.channel])
        msg = bytearray(1 + len(path))
        msg[0] = len(path)
        msg[1:] = path
        self.connection.send(bytes(msg))
        
        logger.info(f"选择安全类型: {security_type.name}, 通道: {self.channel}")
    
    def _handle_security(self) -> int:
        """处理安全认证"""
        if self.security_type == SecurityType.VNC_AUTH:
            # VNC 认证需要 16 字节挑战
            if len(self._buffer) < 16:
                return 0
            
            challenge = bytes(self._buffer[:16])
            logger.debug(f"收到挑战: {challenge.hex().upper()}")
            
            # 加密并发送响应
            vnc_auth = VncAuth(challenge, self.username, self.password)
            response = vnc_auth.encrypt()
            self.connection.send(response)
            
            logger.info("已发送认证响应")
            self._stage = ProtocolStage.SECURITY_RESULT
            return 16
        
        return 0
    
    def _handle_security_result(self) -> int:
        """处理安全结果"""
        logger.debug(f"处理安全结果, 缓冲区大小: {len(self._buffer)}, "
                    f"数据: {self._buffer[:min(20, len(self._buffer))].hex().upper()}")
        
        if len(self._buffer) < 4:
            return 0
        
        result = (self._buffer[0] << 24 | self._buffer[1] << 16 | 
                 self._buffer[2] << 8 | self._buffer[3])
        
        logger.debug(f"安全结果值: {result}")
        
        if result == 0:
            logger.info("认证成功")
            self._auth_success = True
            if self.on_auth_success:
                self.on_auth_success()
            
            # 发送共享标志
            share_data = SharePacket.build_rfb()
            logger.debug(f"发送共享标志: {share_data.hex().upper()}")
            self.connection.send(share_data)
            self._stage = ProtocolStage.INITIALISATION
        else:
            logger.error(f"认证失败: result={result}")
            self._auth_failed("认证失败")
        
        self._auth_event.set()
        return 4
    
    def _handle_initialisation(self) -> int:
        """处理初始化消息"""
        logger.debug(f"处理初始化消息, 缓冲区大小: {len(self._buffer)}, "
                    f"数据: {self._buffer[:min(50, len(self._buffer))].hex().upper()}")
        
        # 初始化消息至少 24 字节
        if len(self._buffer) < 24:
            logger.debug(f"需要更多数据: 有 {len(self._buffer)}, 需要 24")
            return 0
        
        # 解析分辨率
        self.image_width = (self._buffer[0] << 8) | self._buffer[1]
        self.image_height = (self._buffer[2] << 8) | self._buffer[3]
        
        logger.info(f"初始化: {self.image_width}x{self.image_height}")
        
        # 获取名称长度
        name_length = (self._buffer[20] << 24 | self._buffer[21] << 16 |
                      self._buffer[22] << 8 | self._buffer[23])
        
        logger.debug(f"名称长度: {name_length}")
        
        total_length = 24 + name_length
        if len(self._buffer) < total_length:
            logger.debug(f"需要更多数据: 有 {len(self._buffer)}, 需要 {total_length}")
            return 0
        
        # 进入 NORMAL 阶段
        self._stage = ProtocolStage.NORMAL
        logger.info("进入 NORMAL 阶段 - 连接就绪")
        
        # 启动保活线程
        self._start_keep_alive()
        
        self._ready_event.set()
        
        if self.on_connection_ready:
            self.on_connection_ready()
        
        return total_length
    
    def _handle_normal(self) -> int:
        """处理 NORMAL 阶段消息"""
        if len(self._buffer) < 1:
            return 0
        
        msg_type = self._buffer[0]
        
        # 调试：打印前几个字节
        if msg_type not in (0, 4, 106):  # 不打印常见消息
            debug_bytes = self._buffer[:min(20, len(self._buffer))].hex().upper()
            logger.debug(f"消息类型 {msg_type}, 前 20 字节: {debug_bytes}")
        
        # 视频帧更新（类型 0）
        if msg_type == ReadNormalType.FRAME_BUFFER_UPDATE.value:
            return self._handle_video_frame()
        
        # SetColourMapEntries（类型 1）- VNC 标准消息
        if msg_type == 1:
            # 格式: type(1) + padding(1) + first_color(2) + num_colors(2) + colors(n*6)
            if len(self._buffer) < 6:
                return 0
            num_colors = (self._buffer[4] << 8) | self._buffer[5]
            total_len = 6 + num_colors * 6
            if len(self._buffer) < total_len:
                return 0
            return total_len
        
        # Bell（类型 2）- 只有 1 字节
        if msg_type == 2:
            return 1
        
        # ServerCutText（类型 3）- 剪贴板文本
        if msg_type == 3:
            if len(self._buffer) < 8:
                return 0
            text_len = HexUtils.bytes_to_int_big_endian(bytes(self._buffer), 4)
            total_len = 8 + text_len
            if len(self._buffer) < total_len:
                return 0
            return total_len
        
        # 音频帧更新（类型 4）
        # 格式: type(1) + padding(3) + audio_size(4) + data(N)
        if msg_type == 4:
            if len(self._buffer) < 8:
                return 0
            debug_bytes = self._buffer[:min(16, len(self._buffer))].hex().upper()
            logger.debug(f"音频帧头: {debug_bytes}")
            audio_size = HexUtils.bytes_to_int_big_endian(bytes(self._buffer), 4)
            # 检查长度是否合理
            if audio_size > 1000000:  # 超过 1MB 认为错误
                logger.warning(f"音频帧大小异常: {audio_size}, 跳过 4 字节")
                return 4
            total_len = 8 + audio_size
            if len(self._buffer) < total_len:
                logger.debug(f"等待音频帧: 需要 {total_len}, 有 {len(self._buffer)}")
                return 0
            logger.debug(f"跳过音频帧: {audio_size} 字节, 总长度 {total_len}")
            return total_len
        
        # 视频参数（类型 102）
        if msg_type == 102:
            if len(self._buffer) < 36:
                return 0
            logger.debug("收到视频参数")
            return 36
        
        # 按键状态（类型 103）
        if msg_type == 103:
            if len(self._buffer) < 5:
                return 0
            return 5
        
        # 设备信息（类型 104）
        if msg_type == 104:
            if len(self._buffer) < 8:
                return 0
            # 长度在偏移 4 (Little Endian)
            info_len = HexUtils.bytes_to_int_little_endian(bytes(self._buffer), 4)
            total_len = 8 + info_len
            if len(self._buffer) < total_len:
                return 0
            logger.debug(f"收到设备信息: {info_len} 字节")
            return total_len
        
        # 音频参数（类型 105）
        if msg_type == 105:
            if len(self._buffer) < 8:
                return 0
            logger.debug("收到音频参数")
            return 8
        
        # 鼠标类型响应（类型 106）
        if msg_type == 106:
            if len(self._buffer) < 4:
                return 0
            # 格式: type(1) + mouse_type(1) + padding(2)
            mouse_type = self._buffer[1]
            logger.debug(f"收到鼠标类型响应: {mouse_type}")
            return 4
        
        # 视频等级（类型 107）
        if msg_type == 107:
            if len(self._buffer) < 4:
                return 0
            return 4
            
        # 广播状态 (类型 201) - 补全缺失的处理
        if msg_type == 201:
            if len(self._buffer) < 68:
                return 0
            return 68
            
        # 广播设置状态 (类型 202) - 补全缺失的处理
        if msg_type == 202:
            if len(self._buffer) < 68:
                return 0
            return 68
        
        # 未知消息类型，尝试使用通用方式跳过（4字节头）
        logger.debug(f"未处理的消息类型: {msg_type}")
        if len(self._buffer) >= 4:
            return 4
        return 1
    
    def _handle_video_frame(self) -> int:
        """处理视频帧"""
        # 视频帧最小长度检查（头部 4 字节）
        if len(self._buffer) < 4:
            return 0
        
        # 检查帧类型（偏移 3）
        frame_type = self._buffer[3]
        
        logger.debug(f"视频帧类型: {frame_type}, 缓冲区: {len(self._buffer)} 字节")
        
        # 类型 0: 空帧或心跳
        if frame_type == 0:
            return 4
        
        # 类型 1 或 2: 视频帧
        if frame_type == 1 or frame_type == 2:
            # 需要完整帧头（20 字节）
            if len(self._buffer) < 20:
                return 0
            
            # 帧大小在偏移 16-19
            frame_size = HexUtils.bytes_to_int_big_endian(bytes(self._buffer), 16)
            total_size = 20 + frame_size
            
            if len(self._buffer) < total_size:
                logger.debug(f"等待视频帧数据: 有 {len(self._buffer)}, 需要 {total_size}")
                return 0
            
            # 解析分辨率（偏移 8-9 和 10-11）
            width = HexUtils.bytes_to_unsigned_short(bytes(self._buffer), 8)
            height = HexUtils.bytes_to_unsigned_short(bytes(self._buffer), 10)
            encoding_type = self._buffer[15]
            
            logger.debug(f"视频帧: {width}x{height}, encoding={encoding_type}, size={frame_size}")
            
            # 提取帧数据
            frame_data = bytes(self._buffer[20:total_size])
            
            # 更新分辨率
            if width > 0 and height > 0:
                self.image_width = width
                self.image_height = height
            
            # 调用回调
            if self.on_video_frame and len(frame_data) > 0:
                self.on_video_frame(frame_data, width, height, encoding_type)
            
            return total_size
        
        # 其他帧类型，跳过 4 字节
        logger.debug(f"未知视频帧类型: {frame_type}")
        return 4
    
    def _auth_failed(self, reason: str):
        """认证失败处理"""
        self._auth_success = False
        self._auth_event.set()
        if self.on_auth_failed:
            self.on_auth_failed(reason)

