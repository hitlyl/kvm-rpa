"""流程数据模型

定义流程、节点、连线的数据结构。
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class NodeProperties(BaseModel):
    """节点属性（动态字段）"""
    pass


class FlowNode(BaseModel):
    """流程节点模型"""
    id: str = Field(description="节点唯一标识")
    type: str = Field(description="节点类型")
    label: str = Field(default="", description="节点标签")
    x: float = Field(description="X 坐标")
    y: float = Field(description="Y 坐标")
    properties: Dict[str, Any] = Field(default_factory=dict, description="节点属性配置")
    
    class Config:
        extra = "allow"


class FlowEdge(BaseModel):
    """流程连线模型"""
    id: str = Field(description="连线唯一标识")
    source: str = Field(description="源节点 ID")
    target: str = Field(description="目标节点 ID")
    sourceAnchor: Optional[str] = Field(default=None, description="源锚点")
    targetAnchor: Optional[str] = Field(default=None, description="目标锚点")
    type: Optional[str] = Field(default="polyline", description="连线类型")
    properties: Dict[str, Any] = Field(default_factory=dict, description="连线属性")


class Flow(BaseModel):
    """流程模型"""
    id: str = Field(description="流程唯一标识")
    name: str = Field(description="流程名称")
    description: str = Field(default="", description="流程描述")
    version: str = Field(default="1.0", description="流程版本")
    nodes: List[FlowNode] = Field(default_factory=list, description="节点列表")
    edges: List[FlowEdge] = Field(default_factory=list, description="连线列表")
    variables: Dict[str, Any] = Field(default_factory=dict, description="全局变量")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="创建时间")
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="更新时间")
    
    class Config:
        extra = "allow"


class FlowExecutionStatus(BaseModel):
    """流程执行状态"""
    execution_id: str = Field(description="执行 ID")
    flow_id: str = Field(description="流程 ID")
    flow_name: str = Field(description="流程名称")
    status: str = Field(description="执行状态: pending, running, success, failed")
    start_time: str = Field(description="开始时间")
    end_time: Optional[str] = Field(default=None, description="结束时间")
    current_node: Optional[str] = Field(default=None, description="当前执行节点")
    error: Optional[str] = Field(default=None, description="错误信息")
    logs: List[str] = Field(default_factory=list, description="执行日志")

