"""节点 API 路由

提供节点配置查询接口和节点交互功能。
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from pydantic import BaseModel
from loguru import logger

from nodes import get_all_node_configs, get_registered_node_types, get_node_class


class NodeActionRequest(BaseModel):
    """节点交互请求"""
    node_type: str
    action: str
    properties: Dict[str, Any] = {}


# 创建路由器
node_router = APIRouter(prefix="/api/nodes", tags=["Nodes"])


@node_router.get("")
async def get_nodes():
    """获取所有可用节点配置
    
    Returns:
        节点配置列表
    """
    try:
        configs = get_all_node_configs()
        
        # 转换为字典格式
        nodes_data = []
        for config in configs:
            try:
                nodes_data.append(config.model_dump())
            except Exception as e:
                logger.error(f"转换节点配置失败: {e}")
        
        return {
            "status": "ok",
            "message": "Nodes retrieved successfully",
            "data": {
                "nodes": nodes_data,
                "count": len(nodes_data)
            }
        }
    except Exception as e:
        logger.exception(f"获取节点配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@node_router.get("/types")
async def get_node_types():
    """获取所有已注册的节点类型
    
    Returns:
        节点类型列表
    """
    try:
        node_types = get_registered_node_types()
        return {
            "status": "ok",
            "message": "Node types retrieved successfully",
            "data": {
                "types": node_types,
                "count": len(node_types)
            }
        }
    except Exception as e:
        logger.exception(f"获取节点类型失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@node_router.get("/categories")
async def get_node_categories():
    """获取节点按类别分组
    
    Returns:
        按类别分组的节点配置
    """
    try:
        configs = get_all_node_configs()
        
        # 按类别分组
        categories: Dict[str, list] = {}
        for config in configs:
            try:
                config_dict = config.model_dump()
                category = config_dict.get('category', 'other')
                
                if category not in categories:
                    categories[category] = []
                
                categories[category].append(config_dict)
            except Exception as e:
                logger.error(f"处理节点配置失败: {e}")
        
        # 计算统计信息
        category_stats = {
            cat: len(nodes) for cat, nodes in categories.items()
        }
        
        return {
            "status": "ok",
            "message": "Node categories retrieved successfully",
            "data": {
                "categories": categories,
                "stats": category_stats,
                "total": sum(category_stats.values())
            }
        }
    except Exception as e:
        logger.exception(f"获取节点分类失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@node_router.post("/action")
async def execute_node_action(request: NodeActionRequest):
    """执行节点交互方法
    
    Args:
        request: 节点交互请求
        
    Returns:
        交互结果
    """
    try:
        node_class = get_node_class(request.node_type)
        
        if not node_class:
            raise HTTPException(
                status_code=404,
                detail=f"节点类型不存在: {request.node_type}"
            )
        
        # 创建节点实例并执行交互方法
        node_instance = node_class()
        result = node_instance.execute_action(request.action, request.properties)
        
        return {
            "status": "ok" if result.get("success") else "error",
            "message": "Action executed" if result.get("success") else result.get("error", "执行失败"),
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"执行节点交互失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@node_router.get("/{node_type}/actions")
async def get_node_actions(node_type: str):
    """获取节点支持的交互方法
    
    Args:
        node_type: 节点类型
        
    Returns:
        交互方法列表
    """
    try:
        node_class = get_node_class(node_type)
        
        if not node_class:
            raise HTTPException(
                status_code=404,
                detail=f"节点类型不存在: {node_type}"
            )
        
        config = node_class.get_config()
        actions = [action.model_dump() for action in config.actions]
        
        return {
            "status": "ok",
            "message": "Node actions retrieved successfully",
            "data": {
                "node_type": node_type,
                "actions": actions,
                "count": len(actions)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"获取节点交互方法失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

