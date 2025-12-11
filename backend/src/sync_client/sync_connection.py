"""
同步 TCP 连接管理器

使用标准 socket 实现同步 TCP 通信，参考 Java Connector.java
"""

import socket
import threading
import logging
import time
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class SyncConnection:
    """同步 TCP 连接管理器
    
    功能：
    - 同步连接/断开
    - 同步发送数据
    - 后台线程接收数据
    """
    
    CONNECT_TIMEOUT = 3.0  # 连接超时（秒）
    READ_BUFFER_SIZE = 65536  # 读取缓冲区大小（64KB）
    
    def __init__(self):
        """初始化连接"""
        self._socket: Optional[socket.socket] = None
        self._connected = False
        self._ip = ""
        self._port = 0
        
        # 回调函数
        self._on_data_received: Optional[Callable[[bytes], None]] = None
        self._on_connection_closed: Optional[Callable[[str], None]] = None
        
        # 后台读取线程
        self._read_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # 发送锁（确保线程安全）
        self._send_lock = threading.Lock()
    
    @property
    def connected(self) -> bool:
        """是否已连接"""
        return self._connected
    
    @property
    def ip(self) -> str:
        """服务器 IP"""
        return self._ip
    
    @property
    def port(self) -> int:
        """服务器端口"""
        return self._port
    
    def connect(self, ip: str, port: int) -> bool:
        """连接到服务器
        
        Args:
            ip: 服务器 IP 地址
            port: 服务器端口
            
        Returns:
            是否连接成功
        """
        if self._connected:
            logger.warning("已经连接，请先断开")
            return False
        
        try:
            logger.info(f"正在连接 {ip}:{port}")
            
            # 创建 socket
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(self.CONNECT_TIMEOUT)
            
            # 禁用 Nagle 算法，确保数据立即发送（与异步版本一致）
            self._socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            
            # 连接服务器
            self._socket.connect((ip, port))
            
            # 设置为阻塞模式，但有超时
            self._socket.settimeout(3.0)
            
            self._ip = ip
            self._port = port
            self._connected = True
            self._stop_event.clear()
            
            # 启动后台读取线程
            self._read_thread = threading.Thread(
                target=self._read_loop,
                name="SyncConnection-ReadThread",
                daemon=True
            )
            self._read_thread.start()
            
            logger.info(f"已连接到 {ip}:{port}")
            return True
            
        except socket.timeout:
            logger.error(f"连接超时: {ip}:{port}")
            self._cleanup_socket()
            return False
        except Exception as e:
            logger.error(f"连接失败: {ip}:{port}, 错误: {e}")
            self._cleanup_socket()
            return False
    
    def disconnect(self):
        """断开连接"""
        if not self._connected:
            return
        
        logger.info(f"正在断开连接: {self._ip}:{self._port}")
        
        self._connected = False
        self._stop_event.set()
        
        # 关闭 socket
        self._cleanup_socket()
        
        # 等待读取线程结束
        if self._read_thread and self._read_thread.is_alive():
            self._read_thread.join(timeout=2.0)
        
        logger.info("已断开连接")
    
    def send(self, data: bytes) -> bool:
        """发送数据（线程安全）
        
        Args:
            data: 要发送的数据
            
        Returns:
            是否发送成功
        """
        # 详细的状态检查
        logger.debug(f"send: connected={self._connected}, socket={self._socket is not None}")
        
        if not self._connected:
            logger.warning("无法发送: 连接已断开 (_connected=False)")
            return False
        
        if not self._socket:
            logger.warning("无法发送: socket 为 None")
            return False
        
        with self._send_lock:
            try:
                self._socket.sendall(data)
                logger.info(f"Socket 已发送 {len(data)} 字节: {data.hex().upper()}")
                # 短暂等待确保数据被发送到网络
                # asyncio 的 drain() 会等待发送缓冲区刷新，这里模拟类似行为
                time.sleep(0.005)  # 5ms 延迟
                return True
            except Exception as e:
                logger.error(f"发送失败: {e}")
                self._handle_connection_error(f"发送错误: {e}")
                return False
    
    def set_data_received_callback(self, callback: Callable[[bytes], None]):
        """设置数据接收回调
        
        Args:
            callback: 接收到数据时调用的函数
        """
        self._on_data_received = callback
    
    def set_connection_closed_callback(self, callback: Callable[[str], None]):
        """设置连接关闭回调
        
        Args:
            callback: 连接关闭时调用的函数
        """
        self._on_connection_closed = callback
    
    def _read_loop(self):
        """后台读取循环"""
        logger.debug("读取线程启动")
        recv_count = 0
        
        while self._connected and not self._stop_event.is_set():
            try:
                if not self._socket:
                    break
                
                # 接收数据
                data = self._socket.recv(self.READ_BUFFER_SIZE)
                
                if not data:
                    # 连接被关闭
                    logger.info("服务器关闭连接")
                    self._handle_connection_error("服务器关闭连接")
                    break
                
                recv_count += 1
                logger.debug(f"收到数据 #{recv_count}: {len(data)} 字节")
                
                # 调用回调处理数据
                if self._on_data_received:
                    try:
                        self._on_data_received(data)
                    except Exception as e:
                        logger.error(f"数据处理回调异常: {e}")
                        
            except socket.timeout:
                # 超时是正常的，继续循环
                logger.debug(f"读取超时 (正常), 已接收 {recv_count} 次")
                continue
            except Exception as e:
                if self._connected:
                    logger.error(f"读取错误: {e}")
                    self._handle_connection_error(f"读取错误: {e}")
                break
        
        logger.debug("读取线程退出")
    
    def _handle_connection_error(self, reason: str):
        """处理连接错误"""
        if not self._connected:
            return
        
        logger.error(f"连接错误: {reason}")
        self._connected = False
        
        # 调用连接关闭回调
        if self._on_connection_closed:
            try:
                self._on_connection_closed(reason)
            except Exception as e:
                logger.error(f"连接关闭回调异常: {e}")
    
    def _cleanup_socket(self):
        """清理 socket 资源"""
        if self._socket:
            try:
                self._socket.shutdown(socket.SHUT_RDWR)
            except:
                pass
            try:
                self._socket.close()
            except:
                pass
            self._socket = None

