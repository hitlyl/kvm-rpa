"""
Async TCP connection manager

Handles socket connection, reading, writing for KVM protocol
"""

import asyncio
import logging
from typing import Optional, Callable


logger = logging.getLogger(__name__)


class Connection:
    """Async TCP connection manager"""
    
    CONNECT_TIMEOUT = 3.0  # seconds
    READ_BUFFER_SIZE = 65536  # 64KB
    
    def __init__(self):
        """Initialize connection"""
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.connected = False
        self.ip = ""
        self.port = 0
        
        # Callbacks
        self.on_data_received: Optional[Callable[[bytes], None]] = None
        self.on_connection_closed: Optional[Callable[[str], None]] = None
        
        # Background tasks
        self._read_task: Optional[asyncio.Task] = None
        self._pending_drains: set = set()  # 用于保存 drain task 引用，防止被垃圾回收
    
    async def connect(self, ip: str, port: int) -> bool:
        """
        Connect to server
        
        Args:
            ip: Server IP address
            port: Server port
            
        Returns:
            True if connection successful
        """
        try:
            logger.info(f"Connecting to {ip}:{port}")
            
            # Create connection with timeout
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=self.CONNECT_TIMEOUT
            )
            
            self.ip = ip
            self.port = port
            self.connected = True
            
            # Start reading task
            self._read_task = asyncio.create_task(self._read_loop())
            
            logger.info(f"Connected to {ip}:{port}")
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Connection timeout to {ip}:{port}")
            return False
        except Exception as e:
            logger.error(f"Connection failed to {ip}:{port}: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from server"""
        if not self.connected:
            return
        
        logger.info(f"Disconnecting from {self.ip}:{self.port}")
        
        self.connected = False
        
        # Cancel read task
        if self._read_task and not self._read_task.done():
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
        
        # Close writer
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
        
        self.reader = None
        self.writer = None
        
        logger.info("Disconnected")
    
    def write(self, data: bytes):
        """
        Write data to server
        
        注意: asyncio StreamWriter.write() 会将数据写入内部缓冲区，
        并在下次 await 时（或内部 buffer 满时）自动发送。
        为了确保数据及时发送，我们创建一个 drain task。
        
        重要: 此方法必须在事件循环线程中调用！
        
        Args:
            data: Data to send
        """
        if not self.connected or not self.writer:
            logger.warning("Cannot write: not connected")
            return
        
        try:
            self.writer.write(data)
            logger.debug(f"Written {len(data)} bytes to buffer: {data.hex().upper()}")
            # 创建 drain task 确保数据被发送
            # 保存 task 引用防止被垃圾回收
            task = asyncio.create_task(self._safe_drain())
            self._pending_drains.add(task)
            task.add_done_callback(self._pending_drains.discard)
        except Exception as e:
            logger.error(f"Write error: {e}")
            self._handle_connection_error("Write error")
    
    async def _safe_drain(self):
        """安全地执行 drain 操作"""
        try:
            if self.connected and self.writer:
                await self.writer.drain()
                logger.debug("Drain completed")
        except Exception as e:
            logger.debug(f"Drain error (may be normal during disconnect): {e}")
    
    async def write_and_drain(self, data: bytes):
        """
        Write data and wait for it to be sent
        
        Args:
            data: Data to send
        """
        if not self.connected or not self.writer:
            logger.warning("Cannot write: not connected")
            return
        
        try:
            self.writer.write(data)
            await self.writer.drain()
            logger.debug(f"Sent {len(data)} bytes")
        except Exception as e:
            logger.error(f"Write error: {e}")
            self._handle_connection_error("Write error")
    
    async def read_exact(self, num_bytes: int) -> Optional[bytes]:
        """
        Read exact number of bytes
        
        Args:
            num_bytes: Number of bytes to read
            
        Returns:
            Bytes read, or None on error
        """
        if not self.connected or not self.reader:
            return None
        
        try:
            data = await self.reader.readexactly(num_bytes)
            return data
        except asyncio.IncompleteReadError:
            logger.warning("Connection closed while reading")
            self._handle_connection_error("Incomplete read")
            return None
        except Exception as e:
            logger.error(f"Read error: {e}")
            self._handle_connection_error(f"Read error: {e}")
            return None
    
    async def read_available(self) -> Optional[bytes]:
        """
        Read available data (non-blocking)
        
        Returns:
            Bytes read, or None on error
        """
        if not self.connected or not self.reader:
            return None
        
        try:
            data = await self.reader.read(self.READ_BUFFER_SIZE)
            if not data:
                # EOF - connection closed
                self._handle_connection_error("Connection closed by peer")
                return None
            return data
        except Exception as e:
            logger.error(f"Read error: {e}")
            self._handle_connection_error(f"Read error: {e}")
            return None
    
    async def _read_loop(self):
        """Background task to continuously read data"""
        try:
            while self.connected:
                data = await self.read_available()
                if data is None:
                    break
                
                if self.on_data_received:
                    try:
                        self.on_data_received(data)
                    except Exception as e:
                        logger.error(f"Error in data received callback: {e}")
        except asyncio.CancelledError:
            logger.debug("Read loop cancelled")
        except Exception as e:
            logger.error(f"Read loop error: {e}")
            self._handle_connection_error(f"Read loop error: {e}")
    
    def _handle_connection_error(self, reason: str):
        """Handle connection error"""
        if not self.connected:
            return
        
        logger.error(f"Connection error: {reason}")
        self.connected = False
        
        if self.on_connection_closed:
            try:
                self.on_connection_closed(reason)
            except Exception as e:
                logger.error(f"Error in connection closed callback: {e}")
    
    def set_data_received_callback(self, callback: Callable[[bytes], None]):
        """Set callback for received data"""
        self.on_data_received = callback
    
    def set_connection_closed_callback(self, callback: Callable[[str], None]):
        """Set callback for connection closed"""
        self.on_connection_closed = callback


