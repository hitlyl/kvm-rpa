"""节点基类定义

定义所有节点的基类和配置结构。
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field


class NodePropertyDef(BaseModel):
    """节点属性定义
    
    支持属性间的依赖关系，根据其他属性的值动态显示/隐藏当前属性。
    """
    key: str = Field(description="属性键名")
    label: str = Field(description="属性标签")
    type: str = Field(description="属性类型: text, number, select, boolean, textarea, array")
    default: Any = Field(default=None, description="默认值")
    options: Optional[List[Dict[str, Any]]] = Field(default=None, description="选项列表(用于select类型)")
    placeholder: Optional[str] = Field(default=None, description="占位符文本")
    required: bool = Field(default=False, description="是否必需")
    depends_on: Optional[str] = Field(default=None, description="依赖的属性键名")
    depends_value: Optional[Any] = Field(default=None, description="依赖属性需要的值(支持单值或列表)")
    group: Optional[str] = Field(default=None, description="属性分组名称")


class NodeActionDef(BaseModel):
    """节点交互方法定义"""
    key: str = Field(description="方法标识")
    label: str = Field(description="显示名称")
    description: str = Field(description="方法描述")
    returns: str = Field(description="返回类型: image, text, json, none")


class NodeConfig(BaseModel):
    """节点配置"""
    type: str = Field(description="节点类型标识")
    label: str = Field(description="节点显示名称")
    category: str = Field(description="节点类别: source, process, logic, action, util")
    icon: str = Field(description="节点图标")
    color: str = Field(description="节点颜色")
    description: str = Field(description="节点描述")
    properties: List[NodePropertyDef] = Field(default_factory=list, description="节点属性定义列表")
    actions: List[NodeActionDef] = Field(default_factory=list, description="节点交互方法列表")


class BaseNode(ABC):
    """节点基类
    
    所有节点都应该继承此基类，并实现 get_config 和 execute 方法。
    """
    
    def __init__(self):
        """初始化节点"""
        pass
    
    @classmethod
    @abstractmethod
    def get_config(cls) -> NodeConfig:
        """返回节点配置
        
        Returns:
            NodeConfig: 节点配置对象
        """
        pass
    
    @abstractmethod
    def execute(self, context: Any, properties: Dict[str, Any]) -> Any:
        """执行节点逻辑
        
        Args:
            context: 执行上下文，包含系统状态和数据
            properties: 节点配置的属性值
            
        Returns:
            Any: 执行结果，通常返回 bool 表示成功/失败，
                 对于条件节点可能返回分支名称
        """
        pass
    
    def validate(self, properties: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证节点参数
        
        Args:
            properties: 节点配置的属性值
            
        Returns:
            tuple[bool, List[str]]: (是否有效, 错误列表)
        """
        errors = []
        config = self.get_config()
        
        for prop_def in config.properties:
            if prop_def.required and prop_def.key not in properties:
                errors.append(f"缺少必需参数: {prop_def.label}")
        
        return len(errors) == 0, errors
    
    def execute_action(self, action: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """执行节点交互方法
        
        子类可重写此方法实现具体的交互功能。
        
        Args:
            action: 交互方法标识
            properties: 节点属性值
            
        Returns:
            Dict[str, Any]: 执行结果
                - success: bool 是否成功
                - type: str 返回类型 (image/text/json/none)
                - data: Any 返回数据
                - error: str 错误信息（失败时）
        """
        return {
            "success": False,
            "type": "none",
            "error": f"节点 {self.get_config().type} 不支持交互方法: {action}"
        }




