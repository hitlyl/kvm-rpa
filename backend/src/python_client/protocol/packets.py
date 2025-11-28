"""
Protocol packet builders and parsers

Port of various packet classes from Java SDK
"""

from enum import Enum
from typing import Optional, List
from ..utils.hex_utils import HexUtils


class SecurityType(Enum):
    """Security types for authentication"""
    INVALID = 0
    NONE = 1
    VNC_AUTH = 2
    RSA = 9
    REMOTE_AUTH = 10
    CENTRALIZE_AUTH = 20
    U_KEY = 8
    
    @classmethod
    def parse(cls, code: int) -> 'SecurityType':
        """Parse security type from code"""
        for st in cls:
            if st.value == code:
                return st
        return cls.INVALID


class WriteNormalType(Enum):
    """Message types for client->server in NORMAL stage"""
    NONE = -1
    SET_PIXEL_FORMAT = 0
    FIX_COLOUR_MAP_ENTRIES = 1
    SET_ENCODINGS = 2
    FRAMEBUFFER_UPDATE_REQUEST = 3
    KEY_EVENT = 4
    POINTER_EVENT = 5
    CLIENT_CUT_TEXT = 6
    AUDIO_REQUEST = 7
    VM_LINK = 10
    VM_CLOSE = 11
    VM_DATA = 12
    CLIENT_HERE = 101
    VIDEO_PARAM_REQUEST = 102
    SET_CUSTOM_VIDEO_PARAM = 103
    KEY_STATUS_REQUEST = 104
    DEVICE_INFO_REQUEST = 105
    PORT_SWITCH = 106
    AUDIO_PARAM_REQUEST = 107
    SET_CUSTOM_AUDIO_PARAM = 108
    MOUSE_TYPE_REQUEST = 109
    SET_MOUSE_TYPE = 110
    VIDEO_LEVEL_REQUEST = 111
    SET_VIDEO_LEVEL = 112


class ReadNormalType(Enum):
    """Message types for server->client in NORMAL stage
    
    Based on Java ReadNormalType enum:
    - FrameBufferUpdate = 0
    - SetColourMapEntries = 1
    - Bell = 2
    - ServerCutText = 3
    - AudioBufferUpdate = 4
    - VMRead = 10
    - VMWrite = 11
    - VideoParam = 102
    - KeyStatus = 103
    - DeviceInfo = 104
    - AudioParam = 105
    - MouseType = 106
    - VideoLevel = 107
    - BroadcastStatus = -55 (201)
    - BroadcastSetStatus = -54 (202)
    """
    FRAME_BUFFER_UPDATE = 0
    SET_COLOUR_MAP_ENTRIES = 1
    BELL = 2
    SERVER_CUT_TEXT = 3
    AUDIO_BUFFER_UPDATE = 4      # 音频帧
    VM_READ = 10
    VM_WRITE = 11
    VIDEO_PARAM = 102
    KEY_STATUS = 103             # 按键状态
    DEVICE_INFO = 104            # 设备信息
    AUDIO_PARAM = 105            # 音频参数
    MOUSE_TYPE = 106             # 鼠标类型
    VIDEO_LEVEL = 107            # 视频级别
    BROADCAST_STATUS = 201
    BROADCAST_SET_STATUS = 202
    
    @classmethod
    def parse(cls, code: int) -> Optional['ReadNormalType']:
        """Parse read normal type from code"""
        for rt in cls:
            if rt.value == code:
                return rt
        return None


class VersionPacket:
    """RFB protocol version packet"""
    
    VERSION_3_8 = (3, 8)
    VERSION_LENGTH = 12
    
    def __init__(self, major: int = 3, minor: int = 8):
        """
        Initialize version packet
        
        Args:
            major: Major version number
            minor: Minor version number
        """
        self.major = major
        self.minor = minor
    
    def format_version(self) -> bytes:
        """
        Format version as RFB protocol string
        
        Returns:
            12-byte version string (e.g., "RFB 003.008\n")
        """
        version_str = f"RFB {self.major:03d}.{self.minor:03d}\n"
        return version_str.encode('ascii')
    
    @classmethod
    def parse(cls, data: bytes) -> 'VersionPacket':
        """
        Parse version from received data
        
        Args:
            data: 12-byte version string
            
        Returns:
            VersionPacket instance
        """
        version_str = data[:12].decode('ascii').strip()
        if not version_str.startswith("RFB "):
            raise ValueError("Invalid RFB version format")
        
        parts = version_str[4:].split('.')
        major = int(parts[0])
        minor = int(parts[1])
        
        return cls(major, minor)


class KeyEventPacket:
    """Keyboard event packet"""
    
    LENGTH = 8
    DOWN = 1
    UP = 0
    
    def __init__(self, key_code: int, down: int):
        """
        Initialize key event packet
        
        Args:
            key_code: X11 keysym value
            down: 1 for key press, 0 for key release
        """
        if down not in (0, 1):
            raise ValueError("down must be 0 (UP) or 1 (DOWN)")
        
        self.key_code = key_code
        self.down = down
    
    def build_rfb(self) -> bytes:
        """
        Build RFB packet bytes
        
        Returns:
            8-byte packet
        """
        packet = bytearray(self.LENGTH)
        packet[0] = WriteNormalType.KEY_EVENT.value
        packet[1] = self.down
        packet[2] = 0  # padding
        packet[3] = 0  # padding
        
        # Key code (4 bytes, big-endian)
        key_bytes = HexUtils.int_to_bytes_big_endian(self.key_code)
        packet[4:8] = key_bytes
        
        return bytes(packet)


class MouseEventPacket:
    """Mouse event packet"""
    
    LENGTH = 6
    TYPE_RELATIVE = 0
    TYPE_ABSOLUTE = 1
    
    def __init__(self, x: int, y: int, button_mask: int, mouse_type: int):
        """
        Initialize mouse event packet
        
        Args:
            x: X coordinate
            y: Y coordinate
            button_mask: Button mask (0x01=left, 0x02=middle, 0x04=right, 0x08=wheel up, 0x10=wheel down)
            mouse_type: 0=relative, 1=absolute
        """
        self.x = x
        self.y = y
        self.button_mask = button_mask
        self.mouse_type = mouse_type
    
    def build_rfb(self) -> bytes:
        """
        Build RFB packet bytes
        
        Returns:
            6-byte packet
        """
        packet = bytearray(self.LENGTH)
        packet[0] = WriteNormalType.POINTER_EVENT.value
        
        if self.mouse_type == self.TYPE_RELATIVE:
            # Relative mode: set 0x80 flag in mask byte
            packet[1] = (self.button_mask | 0x80) & 0xFF
            # Signed short coordinates
            x_bytes = HexUtils.signed_short_to_bytes(self.x)
            y_bytes = HexUtils.signed_short_to_bytes(self.y)
        else:
            # Absolute mode
            packet[1] = self.button_mask & 0xFF
            # Ensure non-negative
            x = max(0, self.x)
            y = max(0, self.y)
            # Unsigned short coordinates
            x_bytes = HexUtils.unsigned_short_to_bytes(x)
            y_bytes = HexUtils.unsigned_short_to_bytes(y)
        
        packet[2:4] = x_bytes
        packet[4:6] = y_bytes
        
        return bytes(packet)


class MouseTypePacket:
    """Mouse type configuration packet"""
    
    def __init__(self, mouse_type: int):
        """
        Initialize mouse type packet
        
        Args:
            mouse_type: 0=relative, 1=absolute
        """
        self.mouse_type = mouse_type
    
    def build_rfb(self) -> bytes:
        """
        Build RFB packet for setting mouse type
        
        Format (4 bytes total, per Java MouseTypePacket):
        - byte 0: WriteNormalType.SetMouseType (0x6E = 110)
        - byte 1: mouse_type (0=relative, 1=absolute)
        - byte 2-3: padding (0x00)
        """
        packet = bytearray(4)
        packet[0] = WriteNormalType.SET_MOUSE_TYPE.value  # 0x6E
        packet[1] = self.mouse_type
        packet[2] = 0
        packet[3] = 0
        return bytes(packet)
    
    @classmethod
    def parse(cls, data: bytes) -> 'MouseTypePacket':
        """Parse mouse type from received data"""
        mouse_type = data[4]
        return cls(mouse_type)


class VideoFramePacket:
    """Video frame packet parser"""
    
    HEAD_LENGTH = 4
    FRAME_MIN_LENGTH = 20
    
    def __init__(self):
        """Initialize video frame packet"""
        self.width = 0
        self.height = 0
        self.encoding_type = 0
        self.frame_data = b''
        self.resolution_changed = False
    
    def parse(self, data: bytes) -> bool:
        """
        Parse video frame data
        
        Args:
            data: Raw frame data from server
            
        Returns:
            True if frame was parsed successfully
        """
        if len(data) < self.FRAME_MIN_LENGTH:
            return False
        
        # Check message type (should be 0x00 for frame buffer update)
        if data[0] != ReadNormalType.FRAME_BUFFER_UPDATE.value:
            return False
        
        # Check frame type
        frame_type = data[3]
        
        if frame_type == 1:
            # Type 1: Normal frame or resolution change
            if self._is_resolution_change(data):
                # Resolution change message
                self._parse_resolution_change(data)
                return True
            else:
                # Normal frame with video data
                return self._parse_video_frame(data)
        elif frame_type == 2:
            # Type 2: Frame with resolution info
            return self._parse_video_frame(data)
        
        return False
    
    def _is_resolution_change(self, data: bytes) -> bool:
        """Check if this is a resolution change message"""
        if len(data) < 16:
            return False
        return (data[15] == 0x21 and 
                data[14] == 0xFF and 
                data[13] == 0xFF and 
                data[12] == 0xFF)
    
    def _parse_resolution_change(self, data: bytes):
        """Parse resolution change message"""
        if len(data) < 16:
            return
        
        # Resolution info starts at offset 4
        self.width = HexUtils.bytes_to_unsigned_short(data, 4)
        self.height = HexUtils.bytes_to_unsigned_short(data, 6)
        self.resolution_changed = True
    
    def _parse_video_frame(self, data: bytes) -> bool:
        """Parse actual video frame data"""
        if len(data) < self.FRAME_MIN_LENGTH:
            return False
        
        # Width and height at offset 8 (big-endian)
        self.width = HexUtils.bytes_to_unsigned_short(data, 8)
        self.height = HexUtils.bytes_to_unsigned_short(data, 10)
        
        # Encoding type at offset 15 (data[12+3] per Java code)
        # H264 = 7, H265 = 9
        self.encoding_type = data[15]
        
        # Frame size at offset 16 (4 bytes, big-endian)
        frame_size = HexUtils.bytes_to_int_big_endian(data, 16)
        
        # Frame data starts at offset 20
        if len(data) < 20 + frame_size:
            return False
        
        self.frame_data = data[20:20+frame_size]
        self.resolution_changed = False
        
        return True


class KeepAlivePacket:
    """Keep-alive packet"""
    
    @staticmethod
    def build_rfb() -> bytes:
        """Build keep-alive packet"""
        return bytes([0x65, 0x00, 0x00, 0x00])


class SharePacket:
    """Share desktop packet"""
    
    @staticmethod
    def build_rfb() -> bytes:
        """Build share packet"""
        return bytes([0x01])


class VideoParamRequestPacket:
    """Video parameter request packet"""
    
    @staticmethod
    def build_rfb() -> bytes:
        """Build video parameter request packet"""
        return bytes([0x66, 0x00, 0x00, 0x00])


class AudioParamRequestPacket:
    """Audio parameter request packet"""
    
    @staticmethod
    def build_rfb() -> bytes:
        """Build audio parameter request packet"""
        return bytes([0x6B, 0x00, 0x00, 0x00])


class MouseTypeRequestPacket:
    """Mouse type request packet"""
    
    @staticmethod
    def build_rfb() -> bytes:
        """Build mouse type request packet"""
        return bytes([0x6D, 0x00, 0x00, 0x00])


