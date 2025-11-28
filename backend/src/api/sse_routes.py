"""SSE 事件流 API 路由

提供流程执行状态的实时事件流端点。
"""
import asyncio
from typing import Optional
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from loguru import logger

from api.sse_service import get_sse_manager


# 创建路由器
sse_router = APIRouter(prefix="/api/sse", tags=["SSE"])


async def event_generator(request: Request, flow_id: Optional[str] = None):
    """SSE 事件生成器
    
    Args:
        request: FastAPI 请求对象
        flow_id: 流程 ID，None 表示订阅所有流程
        
    Yields:
        SSE 格式的事件数据
    """
    manager = get_sse_manager()
    queue = await manager.subscribe(flow_id)
    
    try:
        # 发送初始连接消息
        yield f"data: {{\"type\": \"connected\", \"flow_id\": \"{flow_id or 'all'}\"}}\n\n"
        
        while True:
            # 检查客户端是否断开
            if await request.is_disconnected():
                logger.debug(f"SSE 客户端断开: flow_id={flow_id}")
                break
            
            try:
                # 等待消息，超时则发送心跳
                message = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield message
            except asyncio.TimeoutError:
                # 发送心跳保持连接
                yield ": heartbeat\n\n"
                
    except asyncio.CancelledError:
        logger.debug(f"SSE 连接取消: flow_id={flow_id}")
    finally:
        await manager.unsubscribe(queue, flow_id)
        logger.debug(f"SSE 订阅已清理: flow_id={flow_id}")


@sse_router.get("/flows/{flow_id}/events")
async def flow_events(request: Request, flow_id: str):
    """订阅特定流程的事件流
    
    Args:
        flow_id: 流程 ID
        
    Returns:
        SSE 事件流
    """
    logger.info(f"新的 SSE 连接: flow_id={flow_id}")
    
    return StreamingResponse(
        event_generator(request, flow_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 nginx 缓冲
        }
    )


@sse_router.get("/flows/events")
async def all_flows_events(request: Request):
    """订阅所有流程的事件流
    
    Returns:
        SSE 事件流
    """
    logger.info("新的全局 SSE 连接")
    
    return StreamingResponse(
        event_generator(request, None),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@sse_router.get("/status")
async def sse_status():
    """获取 SSE 服务状态
    
    Returns:
        SSE 服务状态信息
    """
    manager = get_sse_manager()
    
    return {
        "status": "ok",
        "message": "SSE service is running",
        "data": {
            "global_subscribers": manager.get_subscriber_count(None),
            "total_flow_subscribers": sum(
                manager.get_subscriber_count(fid) 
                for fid in manager._subscribers.keys()
            )
        }
    }

