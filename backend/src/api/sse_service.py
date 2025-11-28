"""SSE 消息服务

提供流程执行状态的实时推送功能。
支持多客户端订阅同一流程的状态更新。
"""
import asyncio
import json
import time
from typing import Dict, Set, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from loguru import logger


class SSEMessageType(str, Enum):
    """SSE 消息类型"""
    NODE_START = "node_start"           # 节点开始执行
    NODE_COMPLETE = "node_complete"     # 节点执行完成
    NODE_ERROR = "node_error"           # 节点执行错误
    LOOP_START = "loop_start"           # 循环开始
    LOOP_COMPLETE = "loop_complete"     # 循环完成
    FLOW_START = "flow_start"           # 流程启动
    FLOW_STOP = "flow_stop"             # 流程停止
    FLOW_ERROR = "flow_error"           # 流程错误
    FLOW_STATUS = "flow_status"         # 流程状态更新
    DEBUG = "debug"                     # 调试信息
    FRAME_UPDATE = "frame_update"       # 帧更新（仅通知，不含数据）


@dataclass
class SSEMessage:
    """SSE 消息"""
    type: SSEMessageType
    flow_id: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_sse_format(self) -> str:
        """转换为 SSE 格式字符串"""
        payload = {
            "type": self.type.value,
            "flow_id": self.flow_id,
            "data": self.data,
            "timestamp": self.timestamp
        }
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


class SSEManager:
    """SSE 连接管理器
    
    管理所有流程的 SSE 订阅者，支持按流程 ID 广播消息。
    """
    
    _instance: Optional['SSEManager'] = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        # flow_id -> Set[asyncio.Queue]
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}
        # 全局订阅者（接收所有流程的消息）
        self._global_subscribers: Set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()
        
        logger.info("SSE 管理器初始化完成")
    
    async def subscribe(self, flow_id: Optional[str] = None) -> asyncio.Queue:
        """订阅流程事件
        
        Args:
            flow_id: 流程 ID，None 表示订阅所有流程
            
        Returns:
            消息队列
        """
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        
        async with self._lock:
            if flow_id is None:
                self._global_subscribers.add(queue)
                logger.debug("新增全局 SSE 订阅者")
            else:
                if flow_id not in self._subscribers:
                    self._subscribers[flow_id] = set()
                self._subscribers[flow_id].add(queue)
                logger.debug(f"新增 SSE 订阅者: flow_id={flow_id}")
        
        return queue
    
    async def unsubscribe(self, queue: asyncio.Queue, flow_id: Optional[str] = None) -> None:
        """取消订阅
        
        Args:
            queue: 消息队列
            flow_id: 流程 ID
        """
        async with self._lock:
            if flow_id is None:
                self._global_subscribers.discard(queue)
                logger.debug("移除全局 SSE 订阅者")
            else:
                if flow_id in self._subscribers:
                    self._subscribers[flow_id].discard(queue)
                    if not self._subscribers[flow_id]:
                        del self._subscribers[flow_id]
                    logger.debug(f"移除 SSE 订阅者: flow_id={flow_id}")
    
    async def broadcast(self, message: SSEMessage) -> None:
        """广播消息到订阅者
        
        Args:
            message: SSE 消息
        """
        flow_id = message.flow_id
        sse_data = message.to_sse_format()
        
        async with self._lock:
            # 发送给特定流程的订阅者
            if flow_id in self._subscribers:
                for queue in list(self._subscribers[flow_id]):
                    try:
                        queue.put_nowait(sse_data)
                    except asyncio.QueueFull:
                        # 队列满了，移除这个订阅者
                        self._subscribers[flow_id].discard(queue)
                        logger.warning(f"SSE 队列已满，移除订阅者: flow_id={flow_id}")
            
            # 发送给全局订阅者
            for queue in list(self._global_subscribers):
                try:
                    queue.put_nowait(sse_data)
                except asyncio.QueueFull:
                    self._global_subscribers.discard(queue)
                    logger.warning("SSE 全局队列已满，移除订阅者")
    
    def broadcast_sync(self, message: SSEMessage) -> None:
        """同步广播消息（供非异步代码调用）
        
        Args:
            message: SSE 消息
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(self.broadcast(message), loop)
            else:
                loop.run_until_complete(self.broadcast(message))
        except RuntimeError:
            # 没有事件循环，创建一个临时的
            asyncio.run(self.broadcast(message))
    
    def get_subscriber_count(self, flow_id: Optional[str] = None) -> int:
        """获取订阅者数量"""
        if flow_id is None:
            return len(self._global_subscribers)
        return len(self._subscribers.get(flow_id, set()))


# 全局单例获取函数
def get_sse_manager() -> SSEManager:
    """获取 SSE 管理器单例"""
    return SSEManager()


# 便捷的消息发送函数
def send_node_start(flow_id: str, node_id: str, node_label: str, node_type: str) -> None:
    """发送节点开始执行消息"""
    manager = get_sse_manager()
    message = SSEMessage(
        type=SSEMessageType.NODE_START,
        flow_id=flow_id,
        data={
            "node_id": node_id,
            "node_label": node_label,
            "node_type": node_type
        }
    )
    manager.broadcast_sync(message)


def send_node_complete(flow_id: str, node_id: str, node_label: str, 
                       node_type: str, success: bool, duration_ms: float,
                       result: Any = None, extra_data: Optional[Dict[str, Any]] = None) -> None:
    """发送节点执行完成消息
    
    Args:
        flow_id: 流程 ID
        node_id: 节点 ID
        node_label: 节点标签
        node_type: 节点类型
        success: 是否成功
        duration_ms: 执行时长（毫秒）
        result: 节点执行结果（可选）
        extra_data: 额外数据（可选）
    """
    manager = get_sse_manager()
    data = {
        "node_id": node_id,
        "node_label": node_label,
        "node_type": node_type,
        "success": success,
        "duration_ms": duration_ms,
        "result": result
    }
    # 合并额外数据
    if extra_data:
        data.update(extra_data)
    
    message = SSEMessage(
        type=SSEMessageType.NODE_COMPLETE,
        flow_id=flow_id,
        data=data
    )
    manager.broadcast_sync(message)


def send_node_error(flow_id: str, node_id: str, node_label: str, 
                    node_type: str, error: str) -> None:
    """发送节点执行错误消息"""
    manager = get_sse_manager()
    message = SSEMessage(
        type=SSEMessageType.NODE_ERROR,
        flow_id=flow_id,
        data={
            "node_id": node_id,
            "node_label": node_label,
            "node_type": node_type,
            "error": error
        }
    )
    manager.broadcast_sync(message)


def send_loop_start(flow_id: str, loop_count: int) -> None:
    """发送循环开始消息"""
    manager = get_sse_manager()
    message = SSEMessage(
        type=SSEMessageType.LOOP_START,
        flow_id=flow_id,
        data={"loop_count": loop_count}
    )
    manager.broadcast_sync(message)


def send_loop_complete(flow_id: str, loop_count: int, duration_ms: float) -> None:
    """发送循环完成消息"""
    manager = get_sse_manager()
    message = SSEMessage(
        type=SSEMessageType.LOOP_COMPLETE,
        flow_id=flow_id,
        data={
            "loop_count": loop_count,
            "duration_ms": duration_ms
        }
    )
    manager.broadcast_sync(message)


def send_flow_start(flow_id: str, flow_name: str) -> None:
    """发送流程启动消息"""
    manager = get_sse_manager()
    message = SSEMessage(
        type=SSEMessageType.FLOW_START,
        flow_id=flow_id,
        data={"flow_name": flow_name}
    )
    manager.broadcast_sync(message)


def send_flow_stop(flow_id: str, flow_name: str, loop_count: int) -> None:
    """发送流程停止消息"""
    manager = get_sse_manager()
    message = SSEMessage(
        type=SSEMessageType.FLOW_STOP,
        flow_id=flow_id,
        data={
            "flow_name": flow_name,
            "loop_count": loop_count
        }
    )
    manager.broadcast_sync(message)


def send_flow_error(flow_id: str, flow_name: str, error: str, error_node: Optional[str] = None) -> None:
    """发送流程错误消息"""
    manager = get_sse_manager()
    message = SSEMessage(
        type=SSEMessageType.FLOW_ERROR,
        flow_id=flow_id,
        data={
            "flow_name": flow_name,
            "error": error,
            "error_node": error_node
        }
    )
    manager.broadcast_sync(message)


def send_debug(flow_id: str, message_text: str, data: Optional[Dict] = None) -> None:
    """发送调试消息"""
    manager = get_sse_manager()
    message = SSEMessage(
        type=SSEMessageType.DEBUG,
        flow_id=flow_id,
        data={
            "message": message_text,
            **(data or {})
        }
    )
    manager.broadcast_sync(message)

