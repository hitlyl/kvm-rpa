"""
Protocol handler implementing the KVM protocol state machine

Port of ProtocolHandlerImpl.java to Python
"""

import asyncio
import logging
from enum import Enum
from typing import Optional, Callable, Dict, Any
from ..network.connection import Connection
from ..auth.vnc_auth import VncAuth, CentralizeAuth
from ..utils.hex_utils import HexUtils
from .packets import (
    VersionPacket,
    SecurityType,
    KeyEventPacket,
    MouseEventPacket,
    VideoFramePacket,
    KeepAlivePacket,
    SharePacket,
    ReadNormalType,
    MouseTypeRequestPacket
)


logger = logging.getLogger(__name__)


class ProtocolStage(Enum):
    """Protocol connection stages"""
    UNINITIALISED = 0
    PROTOCOL_VERSION = 1
    SECURITY_TYPES = 2
    CENTRALIZE_TYPES = 3
    SECURITY = 4
    SECURITY_RESULT = 5
    INITIALISATION = 6
    NORMAL = 7
    INVALID = 8


class ProtocolHandler:
    """Protocol handler for KVM connection"""
    
    KEEP_ALIVE_INTERVAL = 3.0  # seconds
    
    def __init__(self, connection: Connection):
        """
        Initialize protocol handler
        
        Args:
            connection: Network connection instance
        """
        self.connection = connection
        self.stage = ProtocolStage.PROTOCOL_VERSION
        
        # Connection parameters
        self.ip = ""
        self.port = 0
        self.channel = 0
        self.username = ""
        self.password = ""
        
        # Protocol state
        self.security_type: Optional[SecurityType] = None
        self.device_info: Dict[str, Any] = {}
        self.image_width = 0
        self.image_height = 0
        
        # Callbacks
        self.on_auth_required: Optional[Callable[[SecurityType], None]] = None
        self.on_auth_success: Optional[Callable[[], None]] = None
        self.on_auth_failed: Optional[Callable[[str], None]] = None
        self.on_connection_ready: Optional[Callable[[], None]] = None
        self.on_video_frame: Optional[Callable[[bytes, int, int, int], None]] = None
        self.on_connection_error: Optional[Callable[[str], None]] = None
        
        # Keep-alive task
        self._keep_alive_task: Optional[asyncio.Task] = None
        
        # Message buffer
        self._buffer = bytearray()
        
        # Video frame parser
        self._video_parser = VideoFramePacket()
    
    async def start_connection(self, ip: str, port: int, channel: int, 
                               username: str, password: str) -> bool:
        """
        Start connection and authentication
        
        Args:
            ip: Server IP
            port: Server port
            channel: Channel number
            username: Username
            password: Password
            
        Returns:
            True if connection started successfully
        """
        self.ip = ip
        self.port = port
        self.channel = channel
        self.username = username
        self.password = password
        
        # Set up connection callbacks
        self.connection.set_data_received_callback(self._on_data_received)
        self.connection.set_connection_closed_callback(self._on_connection_closed)
        
        # Connect
        if not await self.connection.connect(ip, port):
            return False
        
        # Send protocol version
        await self._send_protocol_version()
        
        return True
    
    async def disconnect(self):
        """Disconnect and cleanup"""
        # Stop keep-alive
        if self._keep_alive_task and not self._keep_alive_task.done():
            self._keep_alive_task.cancel()
            try:
                await self._keep_alive_task
            except asyncio.CancelledError:
                pass
        
        # Disconnect connection
        await self.connection.disconnect()
        
        self.stage = ProtocolStage.UNINITIALISED
    
    def send_key_event(self, key_code: int, down: int):
        """Send keyboard event"""
        if self.stage != ProtocolStage.NORMAL:
            logger.warning("Cannot send key event: not in NORMAL stage")
            return
        
        packet = KeyEventPacket(key_code, down)
        self.connection.write(packet.build_rfb())
    
    def send_mouse_event(self, x: int, y: int, button_mask: int, mouse_type: int):
        """Send mouse event"""
        if self.stage != ProtocolStage.NORMAL:
            logger.warning("Cannot send mouse event: not in NORMAL stage")
            return
        
        packet = MouseEventPacket(x, y, button_mask, mouse_type)
        data = packet.build_rfb()
        logger.info(f"Sending mouse event: x={x}, y={y}, mask={button_mask}, type={mouse_type}")
        logger.info(f"Mouse packet bytes: {HexUtils.bytes_to_hex_string(data)}")
        self.connection.write(data)
    
    def send_mouse_event_raw(self, x: int, y: int, button_mask: int):
        """发送鼠标事件 - 与 Java ViewerSample.encodeMouseEvent 完全一致
        
        Java ViewerSample 使用这种简化的编码方式，不区分相对/绝对模式，
        由设备端根据当前鼠标模式设置来解释坐标。
        
        Args:
            x: X 坐标（像素坐标）
            y: Y 坐标（像素坐标）
            button_mask: 按钮状态
        """
        if self.stage != ProtocolStage.NORMAL:
            logger.warning("Cannot send mouse event: not in NORMAL stage")
            return
        
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
        
        logger.info(f"Sending raw mouse event: x={x}, y={y}, mask={button_mask}")
        logger.info(f"Raw mouse packet bytes: {HexUtils.bytes_to_hex_string(bytes(data))}")
        self.connection.write(bytes(data))
    
    def send_keep_alive(self):
        """Send keep-alive packet"""
        if self.stage == ProtocolStage.NORMAL:
            self.connection.write(KeepAlivePacket.build_rfb())
            logger.debug("Sent keep-alive")
    
    def set_mouse_type(self, mouse_type: int):
        """
        Set mouse type (absolute or relative)
        
        Args:
            mouse_type: 0=relative, 1=absolute
        """
        if self.stage != ProtocolStage.NORMAL:
            logger.warning("Cannot set mouse type: not in NORMAL stage")
            return
        
        from .packets import MouseTypePacket
        packet = MouseTypePacket(mouse_type)
        data = packet.build_rfb()
        logger.info(f"Set mouse type to: {'absolute' if mouse_type == 1 else 'relative'}")
        logger.info(f"MouseType packet bytes: {HexUtils.bytes_to_hex_string(data)}")
        self.connection.write(data)
    
    async def _send_protocol_version(self):
        """Send protocol version"""
        version = VersionPacket(3, 8)
        data = version.format_version()
        await self.connection.write_and_drain(data)
        logger.info("Sent protocol version: RFB 003.008")
    
    def _on_data_received(self, data: bytes):
        """Handle received data"""
        # 减少日志输出，只在非 NORMAL 阶段打印详细信息
        if self.stage != ProtocolStage.NORMAL:
            logger.debug(f"Received {len(data)} bytes")
        
        # Add to buffer
        self._buffer.extend(data)
        
        # Process messages
        self._process_buffer()
    
    def _process_buffer(self):
        """Process buffered data"""
        try:
            while len(self._buffer) > 0:
                consumed = self._handle_message()
                if consumed == 0:
                    # Need more data
                    break
                elif consumed > 0:
                    # Remove consumed bytes
                    self._buffer = self._buffer[consumed:]
                else:
                    # Error
                    logger.error("Error processing message")
                    break
        except Exception as e:
            logger.error(f"Error processing buffer: {e}", exc_info=True)
    
    def _handle_message(self) -> int:
        """
        Handle message based on current stage
        
        Returns:
            Number of bytes consumed, 0 if need more data, -1 on error
        """
        if self.stage == ProtocolStage.PROTOCOL_VERSION:
            return self._handle_protocol_version()
        elif self.stage == ProtocolStage.SECURITY_TYPES:
            return self._handle_security_types()
        elif self.stage == ProtocolStage.CENTRALIZE_TYPES:
            return self._handle_centralize_types()
        elif self.stage == ProtocolStage.SECURITY:
            return self._handle_security()
        elif self.stage == ProtocolStage.SECURITY_RESULT:
            return self._handle_security_result()
        elif self.stage == ProtocolStage.INITIALISATION:
            return self._handle_initialisation()
        elif self.stage == ProtocolStage.NORMAL:
            return self._handle_normal()
        
        return -1
    
    def _handle_protocol_version(self) -> int:
        """Handle protocol version response"""
        # Need at least 12 bytes for version
        if len(self._buffer) < 12:
            return 0
        
        try:
            # 打印原始数据用于调试
            logger.debug(f"Protocol version buffer ({len(self._buffer)} bytes): {HexUtils.bytes_to_hex_string(bytes(self._buffer[:min(100, len(self._buffer))]))}")
            
            # Parse version (first 12 bytes)
            version = VersionPacket.parse(bytes(self._buffer[:12]))
            logger.info(f"Server version: RFB {version.major:03d}.{version.minor:03d}")
            
            # 检查是否有设备信息（Java实现会在版本后附加设备信息）
            # DevicePacket需要至少53字节: VERSION(12) + HEADER(41) = 53
            consumed = 12
            if len(self._buffer) >= 53:
                # 可能包含设备信息，尝试计算设备信息长度
                device_info_length = HexUtils.bytes_to_int_little_endian(bytes(self._buffer), 12)
                total_device_length = 53 + device_info_length
                logger.debug(f"Device info detected, length: {device_info_length}, total: {total_device_length}")
                
                if len(self._buffer) >= total_device_length:
                    # 跳过设备信息
                    consumed = total_device_length
                    logger.info(f"Skipped device info ({device_info_length} bytes)")
            
            # Move to security types stage
            self.stage = ProtocolStage.SECURITY_TYPES
            
            return consumed
        except Exception as e:
            logger.error(f"Failed to parse version: {e}", exc_info=True)
            return -1
    
    def _handle_security_types(self) -> int:
        """Handle security types"""
        if len(self._buffer) < 1:
            return 0
        
        # 打印原始数据用于调试
        logger.debug(f"Security types buffer ({len(self._buffer)} bytes): {HexUtils.bytes_to_hex_string(bytes(self._buffer[:min(50, len(self._buffer))]))}")
        
        num_types = self._buffer[0]
        logger.debug(f"Number of security types: {num_types}")
        
        if num_types == 0:
            logger.error("No security types available")
            return -1
        
        if len(self._buffer) < 1 + num_types:
            logger.debug(f"Need more data: have {len(self._buffer)}, need {1 + num_types}")
            return 0
        
        # Parse security types
        types = []
        for i in range(num_types):
            type_code = self._buffer[1 + i]
            sec_type = SecurityType.parse(type_code)
            types.append(sec_type)
            logger.info(f"Security type available: {sec_type} (code={type_code})")
        
        # Select security type and send authentication
        self._select_and_authenticate(types)
        
        return 1 + num_types
    
    def _select_and_authenticate(self, types: list):
        """Select security type and start authentication"""
        # Prefer VNC_AUTH, then CENTRALIZE_AUTH, then NONE
        if SecurityType.VNC_AUTH in types:
            self._start_vnc_auth()
        elif SecurityType.CENTRALIZE_AUTH in types:
            self._start_centralize_auth()
        elif SecurityType.NONE in types:
            self._start_none_auth()
        else:
            logger.error("No supported security type available")
            if self.on_auth_failed:
                self.on_auth_failed("No supported security type")
    
    def _start_vnc_auth(self):
        """Start VNC authentication"""
        logger.info("Starting VNC authentication")
        self.security_type = SecurityType.VNC_AUTH
        
        # Send security type
        self.connection.write(bytes([SecurityType.VNC_AUTH.value]))
        
        # Send channel path
        path = bytes([self.channel])
        msg = bytearray([len(path)])
        msg.extend(path)
        self.connection.write(bytes(msg))
        
        # Move to security stage (wait for challenge)
        self.stage = ProtocolStage.SECURITY
    
    def _start_centralize_auth(self):
        """Start centralize authentication"""
        logger.info("Starting centralize authentication")
        self.security_type = SecurityType.CENTRALIZE_AUTH
        
        # Send security type
        self.connection.write(bytes([SecurityType.CENTRALIZE_AUTH.value]))
        
        # Send user account
        auth = CentralizeAuth(self.username, self.password)
        self.connection.write(auth.build_user_account_packet())
        
        # Send channel path
        path = bytes([self.channel])
        msg = bytearray([len(path)])
        msg.extend(path)
        self.connection.write(bytes(msg))
        
        # Move to centralize types stage
        self.stage = ProtocolStage.CENTRALIZE_TYPES
    
    def _start_none_auth(self):
        """Start NONE authentication (no auth)"""
        logger.info("Starting NONE authentication")
        self.security_type = SecurityType.NONE
        
        # Send security type
        self.connection.write(bytes([SecurityType.NONE.value]))
        
        # Send channel path
        path = bytes([self.channel])
        msg = bytearray([len(path)])
        msg.extend(path)
        self.connection.write(bytes(msg))
        
        # Move to security result stage
        self.stage = ProtocolStage.SECURITY_RESULT
    
    def _handle_centralize_types(self) -> int:
        """Handle centralize auth sub-type"""
        if len(self._buffer) < 1:
            return 0
        
        sub_type = self._buffer[0]
        logger.debug(f"Centralize sub-type: {sub_type}")
        
        if sub_type == SecurityType.NONE.value:
            self.stage = ProtocolStage.SECURITY_RESULT
        elif sub_type == SecurityType.VNC_AUTH.value:
            self.stage = ProtocolStage.SECURITY
        else:
            logger.error(f"Unsupported centralize sub-type: {sub_type}")
            return -1
        
        return 1
    
    def _handle_security(self) -> int:
        """Handle security challenge"""
        # Need 16 bytes for challenge
        if len(self._buffer) < 16:
            return 0
        
        challenge = bytes(self._buffer[:16])
        logger.debug(f"Received challenge: {HexUtils.bytes_to_hex_string(challenge)}")
        
        # Encrypt with VNC auth
        try:
            auth = VncAuth(challenge, self.username, self.password)
            response = auth.encrypt()
            self.connection.write(response)
            logger.info("Sent authentication response")
            
            # Move to security result stage
            self.stage = ProtocolStage.SECURITY_RESULT
            
            return 16
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            if self.on_auth_failed:
                self.on_auth_failed(str(e))
            return -1
    
    def _handle_security_result(self) -> int:
        """Handle security result"""
        # 打印原始数据用于调试
        logger.debug(f"Security result buffer ({len(self._buffer)} bytes): {HexUtils.bytes_to_hex_string(bytes(self._buffer[:min(20, len(self._buffer))]))}")
        
        if len(self._buffer) < 4:
            return 0
        
        result = HexUtils.bytes_to_int_big_endian(bytes(self._buffer[:4]))
        logger.debug(f"Security result value: {result}")
        
        if result == 0:
            logger.info("Authentication successful")
            if self.on_auth_success:
                self.on_auth_success()
            
            # Send share flag
            share_data = SharePacket.build_rfb()
            logger.debug(f"Sending share flag: {HexUtils.bytes_to_hex_string(share_data)}")
            self.connection.write(share_data)
            
            # Move to initialisation stage
            self.stage = ProtocolStage.INITIALISATION
            logger.debug("Moved to INITIALISATION stage, waiting for init message...")
            
            return 4
        else:
            logger.error(f"Authentication failed: result={result}")
            if self.on_auth_failed:
                self.on_auth_failed(f"Auth result: {result}")
            return -1
    
    def _handle_initialisation(self) -> int:
        """Handle initialisation message"""
        # 打印原始数据用于调试
        logger.debug(f"Initialisation buffer ({len(self._buffer)} bytes): {HexUtils.bytes_to_hex_string(bytes(self._buffer[:min(50, len(self._buffer))]))}")
        
        # Minimum size for init message
        if len(self._buffer) < 24:
            logger.debug(f"Need more data for init: have {len(self._buffer)}, need 24")
            return 0
        
        # Parse image info
        self.image_width = HexUtils.bytes_to_unsigned_short(bytes(self._buffer), 0)
        self.image_height = HexUtils.bytes_to_unsigned_short(bytes(self._buffer), 2)
        
        logger.info(f"Initialisation: {self.image_width}x{self.image_height}")
        
        # Parse name length (at offset 20, 4 bytes)
        name_length = HexUtils.bytes_to_int_big_endian(bytes(self._buffer), 20)
        logger.debug(f"Device name length: {name_length}")
        
        total_length = 24 + name_length
        if len(self._buffer) < total_length:
            logger.debug(f"Need more data for init: have {len(self._buffer)}, need {total_length}")
            return 0
        
        # 解析设备名称
        if name_length > 0:
            device_name = bytes(self._buffer[24:24+name_length]).decode('ascii', errors='ignore')
            logger.info(f"Device name: {device_name}")
        
        # Move to normal stage
        self.stage = ProtocolStage.NORMAL
        
        # Start keep-alive task
        self._keep_alive_task = asyncio.create_task(self._keep_alive_loop())
        
        # Notify connection ready
        if self.on_connection_ready:
            self.on_connection_ready()
        
        logger.info("Entered NORMAL stage - connection ready")
        
        return total_length
    
    def _handle_normal(self) -> int:
        """Handle normal stage messages"""
        if len(self._buffer) < 1:
            return 0
        
        msg_type_code = self._buffer[0]
        msg_type = ReadNormalType.parse(msg_type_code)
        
        # 只对非视频帧和非音频消息打印日志（这些太频繁）
        if msg_type not in (ReadNormalType.FRAME_BUFFER_UPDATE, 
                            ReadNormalType.AUDIO_BUFFER_UPDATE,
                            ReadNormalType.KEY_STATUS):
            logger.debug(f"Normal message type: {msg_type} (code={msg_type_code})")
        
        if msg_type == ReadNormalType.FRAME_BUFFER_UPDATE:
            return self._handle_video_frame()
        elif msg_type == ReadNormalType.VIDEO_PARAM:
            return self._handle_video_param()
        elif msg_type == ReadNormalType.MOUSE_TYPE:
            return self._handle_mouse_type()
        elif msg_type == ReadNormalType.AUDIO_BUFFER_UPDATE:
            return self._handle_audio_frame()
        elif msg_type == ReadNormalType.KEY_STATUS:
            return self._handle_key_status()
        elif msg_type == ReadNormalType.DEVICE_INFO:
            return self._handle_device_info()
        elif msg_type == ReadNormalType.AUDIO_PARAM:
            return self._handle_audio_param()
        elif msg_type == ReadNormalType.BROADCAST_STATUS:
            return self._handle_broadcast_status()
        elif msg_type == ReadNormalType.BROADCAST_SET_STATUS:
            return self._handle_broadcast_set_status()
        else:
            # Unknown or unhandled message type - 尝试跳过
            logger.warning(f"Unhandled message type in NORMAL stage: code={msg_type_code}")
            # 对于未知消息，尝试消费4字节（大多数消息的最小长度）
            if len(self._buffer) >= 4:
                return 4
            return 1
    
    def _handle_video_frame(self) -> int:
        """Handle video frame message (type 0x00)"""
        # 检查消息头
        if len(self._buffer) < 4:
            return 0
        
        # 获取帧类型 (offset 3)
        frame_type = self._buffer[3]
        
        # 类型 0: 空帧或心跳
        if frame_type == 0:
            return 4
        
        # 类型 1: 普通视频帧或分辨率变更
        if frame_type == 1:
            if len(self._buffer) < 20:
                return 0
            
            # 检查是否是分辨率变更消息
            if (len(self._buffer) >= 16 and
                self._buffer[12] == 0xFF and 
                self._buffer[13] == 0xFF and 
                self._buffer[14] == 0xFF and 
                self._buffer[15] == 0x21):
                # 分辨率变更 (16 bytes total)
                width = HexUtils.bytes_to_unsigned_short(bytes(self._buffer), 4)
                height = HexUtils.bytes_to_unsigned_short(bytes(self._buffer), 6)
                logger.info(f"Resolution changed: {width}x{height}")
                self.image_width = width
                self.image_height = height
                return 16
            
            # 普通视频帧
            # 帧大小在 offset 16-19 (4 bytes, big-endian)
            frame_size = HexUtils.bytes_to_int_big_endian(bytes(self._buffer), 16)
            
            # 检查帧大小是否合理 (不超过 10MB)
            if frame_size > 10000000:
                logger.warning(f"Video frame size too large ({frame_size}), may be corrupted data, skipping 4 bytes")
                return 4
            
            total_size = 20 + frame_size
            
            if len(self._buffer) < total_size:
                return 0
            
            # 解析帧数据
            frame_data = bytes(self._buffer[:total_size])
            if self._video_parser.parse(frame_data):
                if self.on_video_frame and self._video_parser.frame_data:
                    try:
                        self.on_video_frame(
                            self._video_parser.frame_data,
                            self._video_parser.width,
                            self._video_parser.height,
                            self._video_parser.encoding_type
                        )
                    except Exception as e:
                        logger.error(f"Error in video frame callback: {e}")
            
            return total_size
        
        # 类型 2: 另一种视频帧格式
        if frame_type == 2:
            if len(self._buffer) < 20:
                return 0
            
            frame_size = HexUtils.bytes_to_int_big_endian(bytes(self._buffer), 16)
            
            # 检查帧大小是否合理
            if frame_size > 10000000:
                logger.warning(f"Video frame type 2 size too large ({frame_size}), skipping 4 bytes")
                return 4
            
            total_size = 20 + frame_size
            
            if len(self._buffer) < total_size:
                return 0
            
            # 解析帧数据
            frame_data = bytes(self._buffer[:total_size])
            if self._video_parser.parse(frame_data):
                if self.on_video_frame and self._video_parser.frame_data:
                    try:
                        self.on_video_frame(
                            self._video_parser.frame_data,
                            self._video_parser.width,
                            self._video_parser.height,
                            self._video_parser.encoding_type
                        )
                    except Exception as e:
                        logger.error(f"Error in video frame callback: {e}")
            
            return total_size
        
        # 未知帧类型，跳过4字节
        logger.warning(f"Unknown video frame type: {frame_type}")
        return 4
    
    def _handle_video_param(self) -> int:
        """Handle video parameter message (type 102)"""
        # Video param message is 36 bytes
        if len(self._buffer) < 36:
            return 0
        
        logger.debug("Received video parameters")
        return 36
    
    def _handle_mouse_type(self) -> int:
        """Handle mouse type message (type 106)
        
        格式 (4 bytes):
        - byte 0: 消息类型 (106)
        - byte 1: 鼠标类型 (0=relative, 1=absolute)
        - byte 2-3: 填充
        """
        if len(self._buffer) < 4:
            return 0
        
        # 解析鼠标类型
        mouse_type = self._buffer[1]
        type_str = 'absolute' if mouse_type == 1 else 'relative'
        logger.info(f"Received mouse type from server: {mouse_type} ({type_str})")
        
        return 4
    
    def _handle_audio_frame(self) -> int:
        """Handle audio frame message (type 4)
        
        格式 (基于 Java AudioFramePacket):
        - 4 bytes: 消息类型 + 填充 (04 00 00 00)
        - 4 bytes: 音频数据长度 (big-endian)
        - N bytes: 音频数据
        总长度: 8 + audioSize
        """
        if len(self._buffer) < 8:
            return 0
        
        # Audio frame size at offset 4 (4 bytes, big-endian)
        audio_size = HexUtils.bytes_to_int_big_endian(bytes(self._buffer), 4)
        
        # 检查长度是否合理
        if audio_size > 1000000:  # 超过 1MB 认为是错误的
            logger.warning(f"Audio frame size too large: {audio_size}")
            return 4
        
        total_size = 8 + audio_size
        
        if len(self._buffer) < total_size:
            # 不打印日志，音频帧太频繁
            return 0
        
        # 不打印日志，音频帧太频繁
        return total_size
    
    def _handle_key_status(self) -> int:
        """Handle key status message (type 103)"""
        # Key status is 5 bytes
        if len(self._buffer) < 5:
            return 0
        
        # 不打印日志，按键状态太频繁
        return 5
    
    def _handle_device_info(self) -> int:
        """Handle device info message (type 104)"""
        # Minimum size: 8 bytes header
        if len(self._buffer) < 8:
            return 0
        
        # Device info length at offset 4 (4 bytes, little-endian)
        info_length = HexUtils.bytes_to_int_little_endian(bytes(self._buffer), 4)
        total_size = 8 + info_length
        
        if len(self._buffer) < total_size:
            return 0
        
        logger.debug(f"Received device info, size: {info_length}")
        return total_size
    
    def _handle_audio_param(self) -> int:
        """Handle audio parameter message (type 105)"""
        # Audio param is 8 bytes
        if len(self._buffer) < 8:
            return 0
        
        logger.debug("Received audio parameters")
        return 8
    
    def _handle_broadcast_status(self) -> int:
        """Handle broadcast status message (type 201)"""
        # Broadcast status is 68 bytes
        if len(self._buffer) < 68:
            return 0
        
        logger.debug("Received broadcast status")
        return 68
    
    def _handle_broadcast_set_status(self) -> int:
        """Handle broadcast set status message (type 202)"""
        # Broadcast set status is 68 bytes
        if len(self._buffer) < 68:
            return 0
        
        logger.debug("Received broadcast set status")
        return 68
    
    async def _keep_alive_loop(self):
        """Background task to send keep-alive packets"""
        try:
            while self.stage == ProtocolStage.NORMAL:
                await asyncio.sleep(self.KEEP_ALIVE_INTERVAL)
                self.send_keep_alive()
        except asyncio.CancelledError:
            logger.debug("Keep-alive loop cancelled")
        except Exception as e:
            logger.error(f"Keep-alive loop error: {e}")
    
    def _on_connection_closed(self, reason: str):
        """Handle connection closed"""
        logger.info(f"Connection closed: {reason}")
        
        if self.on_connection_error:
            self.on_connection_error(reason)
        
        self.stage = ProtocolStage.UNINITIALISED


