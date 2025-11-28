"""流程管理 API 路由

提供流程的 CRUD 操作以及流程启动/停止控制。
"""
from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any
from pydantic import BaseModel
from loguru import logger

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.flow_service import FlowService
from models.flow import Flow


# 创建路由器
flow_router = APIRouter(prefix="/api/flows", tags=["Flows"])

# 初始化流程服务
flow_service = FlowService("flows")


# 请求模型
class FlowCreateRequest(BaseModel):
    """创建流程请求"""
    name: str
    description: str = ""
    nodes: list = []
    edges: list = []
    variables: dict = {}


class FlowUpdateRequest(BaseModel):
    """更新流程请求"""
    name: str = None
    description: str = None
    nodes: list = None
    edges: list = None
    variables: dict = None


@flow_router.get("")
async def list_flows():
    """列出所有流程"""
    try:
        flows = flow_service.list_flows()
        return {
            "status": "ok",
            "message": "Flows retrieved successfully",
            "data": {"flows": flows, "count": len(flows)}
        }
    except Exception as e:
        logger.error(f"列出流程失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@flow_router.get("/running")
async def get_running_flows():
    """获取所有运行中的流程"""
    try:
        from engine.flow_runner import get_flow_runner
        runner = get_flow_runner()
        running_flows = runner.get_all_running_flows()
        
        return {
            "status": "ok",
            "message": "Running flows retrieved successfully",
            "data": {
                "flows": running_flows,
                "count": len(running_flows)
            }
        }
    except Exception as e:
        logger.error(f"获取运行中流程失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@flow_router.get("/status/all")
async def get_all_flows_status():
    """获取所有流程的运行状态"""
    try:
        from engine.flow_runner import get_flow_runner
        runner = get_flow_runner()
        all_status = runner.get_all_flows_status()
        
        return {
            "status": "ok",
            "message": "All flows status retrieved successfully",
            "data": {
                "flows": all_status,
                "count": len(all_status)
            }
        }
    except Exception as e:
        logger.error(f"获取流程状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@flow_router.get("/{flow_id}")
async def get_flow(flow_id: str):
    """获取流程详情"""
    flow = flow_service.get_flow(flow_id)
    
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    
    return {
        "status": "ok",
        "message": "Flow retrieved successfully",
        "data": flow.model_dump()
    }


@flow_router.get("/{flow_id}/status")
async def get_flow_status(flow_id: str):
    """获取流程运行状态"""
    try:
        from engine.flow_runner import get_flow_runner
        runner = get_flow_runner()
        status = runner.get_flow_status(flow_id)
        
        if status:
            return {
                "status": "ok",
                "message": "Flow status retrieved successfully",
                "data": status
            }
        else:
            return {
                "status": "ok",
                "message": "Flow is not running",
                "data": {
                    "flow_id": flow_id,
                    "status": "stopped"
                }
            }
    except Exception as e:
        logger.error(f"获取流程状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@flow_router.post("")
async def create_flow(request: Dict[str, Any]):
    """创建新流程"""
    try:
        flow = flow_service.create_flow(request)
        return {
            "status": "ok",
            "message": "Flow created successfully",
            "data": flow.model_dump()
        }
    except Exception as e:
        logger.error(f"创建流程失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@flow_router.put("/{flow_id}")
async def update_flow(flow_id: str, request: Dict[str, Any]):
    """更新流程"""
    flow = flow_service.update_flow(flow_id, request)
    
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found or update failed")
    
    return {
        "status": "ok",
        "message": "Flow updated successfully",
        "data": flow.model_dump()
    }


@flow_router.delete("/{flow_id}")
async def delete_flow(flow_id: str):
    """删除流程"""
    success = flow_service.delete_flow(flow_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Flow not found")
    
    return {
        "status": "ok",
        "message": "Flow deleted successfully"
    }


@flow_router.get("/{flow_id}/validate")
async def validate_flow(flow_id: str):
    """验证流程"""
    flow = flow_service.get_flow(flow_id)
    
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    
    is_valid, errors = flow_service.validate_flow(flow)
    
    return {
        "status": "ok" if is_valid else "error",
        "message": "Flow is valid" if is_valid else "Flow validation failed",
        "data": {
            "is_valid": is_valid,
            "errors": errors
        }
    }


@flow_router.get("/templates/list")
async def get_templates():
    """获取流程模板"""
    templates = flow_service.get_templates()
    return {
        "status": "ok",
        "message": "Templates retrieved successfully",
        "data": {"templates": templates}
    }


@flow_router.post("/{flow_id}/start")
async def start_flow(flow_id: str):
    """启动流程循环执行
    
    流程将在后台循环执行，直到被停止。
    """
    try:
        flow = flow_service.get_flow(flow_id)
        
        if not flow:
            raise HTTPException(status_code=404, detail="Flow not found")
        
        # 使用流程运行管理器启动流程
        from engine.flow_runner import get_flow_runner
        runner = get_flow_runner()
        
        flow_data = flow.model_dump()
        success = runner.start_flow(flow_data)
        
        if success:
            return {
                "status": "ok",
                "message": "Flow started successfully",
                "data": {
                    "flow_id": flow_id,
                    "flow_name": flow.name,
                    "status": "running"
                }
            }
        else:
            return {
                "status": "error",
                "message": "Failed to start flow (may already be running)",
                "data": {
                    "flow_id": flow_id,
                    "status": "error"
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动流程失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@flow_router.post("/{flow_id}/stop")
async def stop_flow(flow_id: str):
    """停止流程执行"""
    try:
        from engine.flow_runner import get_flow_runner
        runner = get_flow_runner()
        
        success = runner.stop_flow(flow_id)
        
        if success:
            return {
                "status": "ok",
                "message": "Flow stopped successfully",
                "data": {
                    "flow_id": flow_id,
                    "status": "stopped"
                }
            }
        else:
            return {
                "status": "error",
                "message": "Failed to stop flow (may not be running)",
                "data": {
                    "flow_id": flow_id
                }
            }
            
    except Exception as e:
        logger.error(f"停止流程失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@flow_router.post("/{flow_id}/pause")
async def pause_flow(flow_id: str):
    """暂停流程执行"""
    try:
        from engine.flow_runner import get_flow_runner
        runner = get_flow_runner()
        
        success = runner.pause_flow(flow_id)
        
        if success:
            return {
                "status": "ok",
                "message": "Flow paused successfully",
                "data": {
                    "flow_id": flow_id,
                    "status": "paused"
                }
            }
        else:
            return {
                "status": "error",
                "message": "Failed to pause flow",
                "data": {
                    "flow_id": flow_id
                }
            }
            
    except Exception as e:
        logger.error(f"暂停流程失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@flow_router.post("/{flow_id}/resume")
async def resume_flow(flow_id: str):
    """恢复流程执行"""
    try:
        from engine.flow_runner import get_flow_runner
        runner = get_flow_runner()
        
        success = runner.resume_flow(flow_id)
        
        if success:
            return {
                "status": "ok",
                "message": "Flow resumed successfully",
                "data": {
                    "flow_id": flow_id,
                    "status": "running"
                }
            }
        else:
            return {
                "status": "error",
                "message": "Failed to resume flow",
                "data": {
                    "flow_id": flow_id
                }
            }
            
    except Exception as e:
        logger.error(f"恢复流程失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 保留旧的 execute 接口以兼容
@flow_router.post("/{flow_id}/execute")
async def execute_flow(flow_id: str, request: Request):
    """执行流程（单次，兼容旧接口）
    
    推荐使用 /start 接口启动流程循环执行。
    """
    return await start_flow(flow_id)
