"""KVM客户端同步包装器

将异步KVM客户端包装为同步接口,在独立线程中运行asyncio事件循环

重构版本：使用发送线程解耦发送和接收操作
"""
import asyncio
import threading
import time
from queue import Queue, Empty
from typing import Optional, Callable, Dict, Any, Tuple
from concurrent.futures import Future
from dataclasses import dataclass
from enum import Enum
from loguru import logger

# 导入KVM客户端(从python_client包)
import sys
from pathlib import Path

# 将src目录添加到sys.path(python_client在src下)
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# 从python_client包导入
from python_client import KVMClient


class SendCommandType(Enum):
    """发送命令类型"""
    MOUSE_EVENT = "mouse_event"
    MOUSE_CLICK = "mouse_click"
    KEY_EVENT = "key_event"


@dataclass
class SendCommand:
    """发送命令"""
    cmd_type: SendCommandType
    args: Tuple
    kwargs: Dict


class KVMClientWrapper:
    """KVM客户端同步包装器
    
    在独立线程中运行asyncio事件循环,提供同步接口
    
    重构版本特点：
    - 使用发送线程解耦发送和接收
    - 发送操作不会被接收操作阻塞
    """
    
    def __init__(self):
        """初始化KVM客户端包装器"""
        self.client: Optional[KVMClient] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.thread: Optional[threading.Thread] = None
        
        # 连接参数
        self.ip: Optional[str] = None
        self.port: int = 5900
        self.channel: int = 0
        self.username: Optional[str] = None
        self.password: Optional[str] = None
        
        # 视频帧队列(线程安全)
        self.frame_queue: Queue = Queue(maxsize=10)
        self.frame_callback: Optional[Callable] = None
        
        # 发送命令队列(线程安全)
        self._send_queue: Queue = Queue(maxsize=100)
        self._send_thread: Optional[threading.Thread] = None
        self._send_running = False
        
        # 连接状态
        self.connected = False
        self.running = False
        
        # 统计信息
        self.stats = {
            'total_frames': 0,
            'dropped_frames': 0,
            'connection_time': 0.0,
            'sent_commands': 0
        }
        
        logger.info("KVM客户端包装器初始化完成")
    
    def connect(
        self,
        ip: str,
        port: int = 5900,
        channel: int = 0,
        username: str = "admin",
        password: str = "admin",
        timeout: float = 10.0
    ) -> bool:
        """连接到KVM设备(同步接口)"""
        if self.connected:
            logger.warning("已经连接到KVM设备")
            return True
        
        # 保存连接参数
        self.ip = ip
        self.port = port
        self.channel = channel
        self.username = username
        self.password = password
        
        logger.info(f"正在连接到KVM: {ip}:{port} 通道{channel}")
        
        # 启动事件循环线程
        if not self.running:
            self._start_event_loop()
        
        # 在事件循环中执行连接
        future = self._run_coroutine(
            self._async_connect(timeout=timeout)
        )
        
        try:
            result = future.result(timeout=timeout + 2.0)
            if result:
                self.connected = True
                # 启动发送线程
                self._start_send_thread()
                logger.success(f"成功连接到KVM: {ip}:{port}")
            else:
                logger.error(f"连接KVM失败: {ip}:{port}")
            return result
        except Exception as e:
            logger.error(f"连接KVM异常: {e}")
            return False
    
    def disconnect(self) -> None:
        """断开KVM连接(同步接口)"""
        if not self.connected:
            return
        
        logger.info("正在断开KVM连接...")
        
        # 先设置 connected = False，让发送线程停止
        self.connected = False
        
        # 停止发送线程
        self._stop_send_thread()
        
        # 在事件循环中执行断开
        if self.running and self.loop:
            try:
                future = self._run_coroutine(self._async_disconnect())
                future.result(timeout=5.0)
            except TimeoutError:
                logger.warning("断开连接超时，强制停止")
            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e) if str(e) else "(无详细信息)"
                logger.warning(f"断开连接时发生异常 [{error_type}]: {error_msg}")
        
        # 停止事件循环
        self._stop_event_loop()
        
        logger.info("KVM连接已断开")
    
    def get_frame(self, timeout: float = 1.0) -> Optional[bytes]:
        """获取视频帧(同步接口)"""
        if not self.connected:
            logger.warning("未连接到KVM设备")
            return None
        
        try:
            frame_data = self.frame_queue.get(timeout=timeout)
            return frame_data
        except Empty:
            return None
    
    def send_key_event(self, key_code: int, down: int) -> None:
        """发送键盘事件(同步接口)"""
        if not self.connected or not self.client:
            logger.warning("未连接到KVM设备")
            return
        
        # 将命令放入发送队列
        cmd = SendCommand(
            cmd_type=SendCommandType.KEY_EVENT,
            args=(key_code, down),
            kwargs={}
        )
        self._enqueue_send_command(cmd)
    
    def send_mouse_event(self, x: int, y: int, button_mask: int = 0, mouse_type: int = 1) -> None:
        """发送鼠标事件(同步接口)"""
        if not self.connected or not self.client:
            logger.warning("未连接到KVM设备")
            return
        
        # 将命令放入发送队列
        cmd = SendCommand(
            cmd_type=SendCommandType.MOUSE_EVENT,
            args=(x, y, button_mask, mouse_type),
            kwargs={}
        )
        self._enqueue_send_command(cmd)
    
    def send_mouse_click(self, x: int, y: int, button: int = 0x01) -> None:
        """发送鼠标点击(同步接口)"""
        if not self.connected or not self.client:
            logger.warning("未连接到KVM设备")
            return
        
        # 将命令放入发送队列
        cmd = SendCommand(
            cmd_type=SendCommandType.MOUSE_CLICK,
            args=(x, y, button),
            kwargs={}
        )
        self._enqueue_send_command(cmd)
        logger.debug(f"鼠标点击命令已入队: ({x}, {y}), button={button}")
    
    def _enqueue_send_command(self, cmd: SendCommand) -> None:
        """将发送命令放入队列"""
        try:
            self._send_queue.put_nowait(cmd)
        except:
            logger.warning("发送队列已满，丢弃命令")
    
    def _start_send_thread(self) -> None:
        """启动发送线程"""
        if self._send_running:
            return
        
        self._send_running = True
        self._send_thread = threading.Thread(target=self._send_thread_func, daemon=True)
        self._send_thread.start()
        logger.info("发送线程已启动")
    
    def _stop_send_thread(self) -> None:
        """停止发送线程"""
        self._send_running = False
        
        if self._send_thread and self._send_thread.is_alive():
            # 放入一个空命令唤醒线程
            try:
                self._send_queue.put_nowait(None)
            except:
                pass
            self._send_thread.join(timeout=2.0)
        
        self._send_thread = None
        logger.debug("发送线程已停止")
    
    def _send_thread_func(self) -> None:
        """发送线程函数 - 从队列中取出命令并发送"""
        logger.info("发送线程开始运行")
        sent_count = 0
        
        try:
            while self._send_running and self.connected:
                try:
                    # 阻塞等待命令，超时 100ms
                    cmd = self._send_queue.get(timeout=0.1)
                    
                    # 检查是否是停止信号
                    if cmd is None:
                        logger.debug("发送线程收到停止信号")
                        break
                    
                    # 执行发送命令
                    self._execute_send_command_sync(cmd)
                    sent_count += 1
                    self.stats['sent_commands'] = sent_count
                    
                except Empty:
                    # 队列为空，继续等待
                    continue
                except Exception as e:
                    logger.error(f"发送线程异常: {e}", exc_info=True)
        finally:
            logger.info(f"发送线程结束，已发送 {sent_count} 个命令")
    
    def _execute_send_command_sync(self, cmd: SendCommand) -> None:
        """同步执行发送命令（在发送线程中调用）
        
        直接调用 KVMClient 的同步方法，它们内部会使用 connection.write
        """
        try:
            if not self.client or not self.connected:
                logger.warning("客户端未连接，跳过发送命令")
                return
            
            if not self.loop or not self.loop.is_running():
                logger.warning("事件循环未运行，跳过发送命令")
                return
            
            if cmd.cmd_type == SendCommandType.KEY_EVENT:
                key_code, down = cmd.args
                # 使用 call_soon_threadsafe 在事件循环中执行
                self.loop.call_soon_threadsafe(
                    lambda: self.client.send_key_event(key_code, down)
                )
                time.sleep(0.01)  # 给事件循环时间处理
                
            elif cmd.cmd_type == SendCommandType.MOUSE_EVENT:
                x, y, button_mask, mouse_type = cmd.args
                self.loop.call_soon_threadsafe(
                    lambda: self.client.send_mouse_event(x, y, button_mask, mouse_type)
                )
                time.sleep(0.01)
                
            elif cmd.cmd_type == SendCommandType.MOUSE_CLICK:
                x, y, button = cmd.args
                logger.info(f"执行鼠标点击: ({x}, {y}), button={button}")
                
                # 使用 call_soon_threadsafe 调度到事件循环
                self.loop.call_soon_threadsafe(
                    lambda: self.client.send_mouse_click(x, y, button)
                )
                
                # 等待事件循环处理
                time.sleep(0.1)
                logger.info(f"鼠标点击已调度: ({x}, {y})")
                
        except Exception as e:
            logger.error(f"执行发送命令失败: {type(e).__name__}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        video_stats = {}
        if self.client:
            video_stats = self.client.get_video_stats()
        
        return {
            **self.stats,
            **video_stats,
            'connected': self.connected,
            'frame_queue_size': self.frame_queue.qsize(),
            'send_queue_size': self._send_queue.qsize()
        }
    
    # ========== 内部方法 ==========
    
    def _start_event_loop(self) -> None:
        """启动asyncio事件循环线程"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._event_loop_thread, daemon=True)
        self.thread.start()
        
        # 等待事件循环就绪
        time.sleep(0.2)
        logger.debug("事件循环线程已启动")
    
    def _stop_event_loop(self) -> None:
        """停止asyncio事件循环线程"""
        if not self.running:
            return
        
        self.running = False
        
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3.0)
        
        self.loop = None
        self.thread = None
        logger.debug("事件循环线程已停止")
    
    def _event_loop_thread(self) -> None:
        """事件循环线程函数"""
        try:
            # 创建新的事件循环
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # 运行事件循环
            self.loop.run_forever()
            
        except Exception as e:
            logger.error(f"事件循环异常: {e}")
        finally:
            if self.loop:
                self.loop.close()
            logger.debug("事件循环已退出")
    
    def _run_coroutine(self, coro) -> Future:
        """在事件循环中运行协程"""
        if not self.loop:
            raise RuntimeError("事件循环未运行")
        
        return asyncio.run_coroutine_threadsafe(coro, self.loop)
    
    async def _async_connect(self, timeout: float = 10.0) -> bool:
        """异步连接到KVM设备"""
        try:
            # 创建KVM客户端
            self.client = KVMClient()
            
            # 设置视频回调
            self.client.set_video_callback(self._on_video_frame)
            
            # 连接到KVM
            start_time = time.time()
            result = await self.client.connect(
                ip=self.ip,
                port=self.port,
                channel=self.channel,
                username=self.username,
                password=self.password,
                timeout=timeout
            )
            
            if result:
                self.stats['connection_time'] = time.time() - start_time
            
            return result
            
        except Exception as e:
            logger.error(f"异步连接异常: {e}")
            return False
    
    async def _async_disconnect(self) -> None:
        """异步断开KVM连接"""
        try:
            if self.client:
                try:
                    await asyncio.wait_for(self.client.disconnect(), timeout=3.0)
                except asyncio.TimeoutError:
                    logger.warning("KVM 断开连接超时，强制关闭")
                except asyncio.CancelledError:
                    logger.debug("KVM 断开操作被取消")
                finally:
                    self.client = None
        except Exception as e:
            logger.error(f"异步断开异常: {e}")
            self.client = None
    
    def _on_video_frame(self, frame_data: bytes, width: int, height: int, encoding_type: int) -> None:
        """视频帧回调"""
        try:
            # 更新统计
            self.stats['total_frames'] += 1
            
            # 放入队列
            try:
                self.frame_queue.put_nowait({
                    'data': frame_data,
                    'width': width,
                    'height': height,
                    'encoding_type': encoding_type,
                    'timestamp': time.time()
                })
            except:
                # 队列满,丢弃最旧的帧
                try:
                    self.frame_queue.get_nowait()
                    self.frame_queue.put_nowait({
                        'data': frame_data,
                        'width': width,
                        'height': height,
                        'encoding_type': encoding_type,
                        'timestamp': time.time()
                    })
                    self.stats['dropped_frames'] += 1
                except:
                    pass
            
            # 调用用户回调
            if self.frame_callback:
                self.frame_callback(frame_data, width, height, encoding_type)
                
        except Exception as e:
            logger.error(f"视频帧回调异常: {e}")
    
    def set_frame_callback(self, callback: Callable) -> None:
        """设置视频帧回调函数"""
        self.frame_callback = callback
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.connected and self.client is not None and self.client.is_connected()
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.disconnect()
