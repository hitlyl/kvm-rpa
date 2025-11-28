"""
KVM Client - Main client class

High-level API for KVM connections
"""

import asyncio
import logging
from typing import Optional, Callable

from .network.connection import Connection
from .protocol.protocol_handler import ProtocolHandler
from .video.video_handler import VideoHandler


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KVMClient:
    """
    KVM Client for connecting to KVM devices
    
    Supports authentication, keyboard/mouse control, and video streaming.
    """
    
    def __init__(self):
        """Initialize KVM client"""
        self.connection = Connection()
        self.protocol = ProtocolHandler(self.connection)
        self.video = VideoHandler()
        
        self.connected = False
        self.authenticated = False
        
        # Set up protocol callbacks
        self._setup_callbacks()
    
    def _setup_callbacks(self):
        """Set up internal callbacks"""
        self.protocol.on_auth_success = self._on_auth_success
        self.protocol.on_auth_failed = self._on_auth_failed
        self.protocol.on_connection_ready = self._on_connection_ready
        self.protocol.on_video_frame = self._on_video_frame
        self.protocol.on_connection_error = self._on_connection_error
    
    async def connect(self, ip: str, port: int, channel: int, 
                     username: str, password: str, timeout: float = 10.0) -> bool:
        """
        Connect to KVM device
        
        Args:
            ip: IP address of KVM device
            port: Port number (typically 5900)
            channel: Channel number (typically 0)
            username: Authentication username
            password: Authentication password
            timeout: Connection timeout in seconds
            
        Returns:
            True if connection and authentication successful
            
        Raises:
            TimeoutError: If connection times out
            ConnectionError: If connection fails
        """
        logger.info(f"Connecting to KVM at {ip}:{port}, channel {channel}")
        
        try:
            # Start connection with timeout
            connected = await asyncio.wait_for(
                self.protocol.start_connection(ip, port, channel, username, password),
                timeout=timeout
            )
            
            if not connected:
                raise ConnectionError("Failed to establish connection")
            
            self.connected = True
            
            # Wait for authentication to complete
            start_time = asyncio.get_event_loop().time()
            while not self.authenticated:
                if asyncio.get_event_loop().time() - start_time > timeout:
                    raise TimeoutError("Authentication timeout")
                await asyncio.sleep(0.1)
            
            logger.info("Successfully connected and authenticated")
            return True
            
        except asyncio.TimeoutError:
            logger.error("Connection timeout")
            raise TimeoutError(f"Connection timeout after {timeout} seconds")
        except Exception as e:
            logger.error(f"Connection error: {e}")
            raise ConnectionError(f"Connection failed: {e}")
    
    async def disconnect(self):
        """Disconnect from KVM device"""
        if not self.connected:
            return
        
        logger.info("Disconnecting from KVM")
        await self.protocol.disconnect()
        self.connected = False
        self.authenticated = False
    
    def send_key_event(self, key_code: int, down: int):
        """
        Send keyboard event
        
        Args:
            key_code: X11 keysym value
            down: 1 for key press, 0 for key release
        """
        if not self.authenticated:
            logger.warning("Cannot send key event: not authenticated")
            return
        
        self.protocol.send_key_event(key_code, down)
    
    def send_key_press(self, key_code: int):
        """
        Send key press event
        
        Args:
            key_code: X11 keysym value
        """
        self.send_key_event(key_code, 1)
    
    def send_key_release(self, key_code: int):
        """
        Send key release event
        
        Args:
            key_code: X11 keysym value
        """
        self.send_key_event(key_code, 0)
    
    def send_key_combination(self, *key_codes: int):
        """
        Send key combination (press all, then release all in reverse)
        
        Args:
            key_codes: X11 keysym values
        """
        # Press all keys
        for key_code in key_codes:
            self.send_key_press(key_code)
        
        # Release all keys in reverse order
        for key_code in reversed(key_codes):
            self.send_key_release(key_code)
    
    def send_mouse_event(self, x: int, y: int, button_mask: int = 0, mouse_type: int = 1):
        """
        Send mouse event
        
        Args:
            x: X coordinate (0-65535 for absolute, offset for relative)
            y: Y coordinate (0-65535 for absolute, offset for relative)
            button_mask: Button state (0x01=left, 0x02=middle, 0x04=right)
            mouse_type: 0=relative, 1=absolute
        """
        if not self.authenticated:
            logger.warning("Cannot send mouse event: not authenticated")
            return
        
        self.protocol.send_mouse_event(x, y, button_mask, mouse_type)
    
    def send_mouse_move(self, x: int, y: int, mouse_type: int = 1):
        """
        Send mouse move (no buttons pressed)
        
        Args:
            x: X coordinate
            y: Y coordinate
            mouse_type: 0=relative, 1=absolute
        """
        self.send_mouse_event(x, y, 0, mouse_type)
    
    def send_mouse_click(self, x: int, y: int, button: int = 0x01, mouse_type: int = 1):
        """
        Send mouse click (move, press, release)
        
        Args:
            x: X coordinate
            y: Y coordinate
            button: Button to click (0x01=left, 0x02=middle, 0x04=right)
            mouse_type: 0=relative, 1=absolute
        """
        # Move to position
        self.send_mouse_event(x, y, 0, mouse_type)
        # Press button
        self.send_mouse_event(x, y, button, mouse_type)
        # Release button
        self.send_mouse_event(x, y, 0, mouse_type)
    
    def send_mouse_event_raw(self, x: int, y: int, button_mask: int = 0):
        """
        发送鼠标事件 - 与 Java ViewerSample 完全一致的编码方式
        
        这是一个简化版本，不区分相对/绝对模式，由设备根据当前鼠标模式解释坐标。
        
        Args:
            x: X 坐标（像素坐标）
            y: Y 坐标（像素坐标）
            button_mask: 按钮状态 (0x01=左键, 0x02=中键, 0x04=右键)
        """
        if not self.authenticated:
            logger.warning("Cannot send mouse event: not authenticated")
            return
        
        self.protocol.send_mouse_event_raw(x, y, button_mask)
    
    def set_mouse_type(self, mouse_type: int):
        """
        Set mouse type (absolute or relative)
        
        Args:
            mouse_type: 0=relative, 1=absolute
        """
        if not self.authenticated:
            logger.warning("Cannot set mouse type: not authenticated")
            return
        
        self.protocol.set_mouse_type(mouse_type)
    
    def set_video_callback(self, callback: Callable[[bytes, int, int, int], None]):
        """
        Set callback for video frames
        
        Args:
            callback: Function(frame_data: bytes, width: int, height: int, encoding_type: int)
                     Called when a video frame is received
        """
        self.video.set_frame_callback(callback)
    
    def set_connection_callback(self, callback: Callable[[str, dict], None]):
        """
        Set callback for connection events
        
        Args:
            callback: Function(event: str, data: dict)
                     Called on connection events (connected, disconnected, error)
        """
        # Store user callback
        self._user_connection_callback = callback
    
    def get_video_stats(self) -> dict:
        """
        Get video statistics
        
        Returns:
            Dictionary with video stats (frame_count, width, height, encoding_type)
        """
        return self.video.get_stats()
    
    def is_connected(self) -> bool:
        """Check if connected"""
        return self.connected
    
    def is_authenticated(self) -> bool:
        """Check if authenticated"""
        return self.authenticated
    
    # Internal callbacks
    
    def _on_auth_success(self):
        """Handle authentication success"""
        logger.info("Authentication successful")
        self.authenticated = True
    
    def _on_auth_failed(self, reason: str):
        """Handle authentication failure"""
        logger.error(f"Authentication failed: {reason}")
        self.authenticated = False
        
        if hasattr(self, '_user_connection_callback'):
            self._user_connection_callback('auth_failed', {'reason': reason})
    
    def _on_connection_ready(self):
        """Handle connection ready"""
        logger.info("Connection ready")
        
        if hasattr(self, '_user_connection_callback'):
            self._user_connection_callback('ready', {})
    
    def _on_video_frame(self, frame_data: bytes, width: int, height: int, encoding_type: int):
        """Handle video frame"""
        self.video.handle_frame(frame_data, width, height, encoding_type)
    
    def _on_connection_error(self, reason: str):
        """Handle connection error"""
        logger.error(f"Connection error: {reason}")
        self.connected = False
        self.authenticated = False
        
        if hasattr(self, '_user_connection_callback'):
            self._user_connection_callback('error', {'reason': reason})


# Example usage
async def example():
    """Example usage of KVMClient"""
    client = KVMClient()
    
    # Set video callback
    def on_video_frame(frame_data, width, height, encoding_type):
        print(f"Received frame: {width}x{height}, size: {len(frame_data)} bytes")
    
    client.set_video_callback(on_video_frame)
    
    # Connect
    try:
        await client.connect(
            ip="192.168.1.100",
            port=5900,
            channel=0,
            username="admin",
            password="123456"
        )
        
        # Send some keyboard events
        client.send_key_press(0x41)  # Press 'A'
        await asyncio.sleep(0.1)
        client.send_key_release(0x41)  # Release 'A'
        
        # Send mouse move
        client.send_mouse_move(32768, 32768)  # Center of screen
        
        # Keep connection alive
        await asyncio.sleep(30)
        
        # Disconnect
        await client.disconnect()
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(example())


