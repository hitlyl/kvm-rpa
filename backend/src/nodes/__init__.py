"""节点注册表

管理所有节点类的注册和获取。
"""
from typing import Dict, Type, List, Optional
from loguru import logger

# 延迟导入以避免循环依赖
BaseNode = None
NodeConfig = None


def _ensure_imports():
    """确保导入必要的类"""
    global BaseNode, NodeConfig
    if BaseNode is None:
        from .base import BaseNode as _BaseNode, NodeConfig as _NodeConfig
        BaseNode = _BaseNode
        NodeConfig = _NodeConfig


# 全局节点注册表
NODE_REGISTRY: Dict[str, Type] = {}


def register_node(cls: Type) -> Type:
    """节点注册装饰器
    
    Args:
        cls: 节点类
        
    Returns:
        Type: 返回原始类（用于装饰器）
    """
    _ensure_imports()
    
    try:
        config = cls.get_config()
        NODE_REGISTRY[config.type] = cls
        logger.info(f"节点已注册: {config.type} - {config.label}")
    except Exception as e:
        logger.error(f"注册节点失败 {cls.__name__}: {e}")
    
    return cls


def get_all_node_configs() -> List:
    """获取所有节点配置
    
    Returns:
        List[NodeConfig]: 所有已注册节点的配置列表
    """
    _ensure_imports()
    
    configs = []
    for node_class in NODE_REGISTRY.values():
        try:
            config = node_class.get_config()
            configs.append(config)
        except Exception as e:
            logger.error(f"获取节点配置失败 {node_class.__name__}: {e}")
    
    return configs


def get_node_class(node_type: str) -> Optional[Type]:
    """根据类型获取节点类
    
    Args:
        node_type: 节点类型标识
        
    Returns:
        Optional[Type[BaseNode]]: 节点类，如果不存在则返回 None
    """
    return NODE_REGISTRY.get(node_type)


def get_registered_node_types() -> List[str]:
    """获取所有已注册的节点类型
    
    Returns:
        List[str]: 节点类型列表
    """
    return list(NODE_REGISTRY.keys())


# 导入所有节点模块以触发注册
def _register_all_nodes():
    """注册所有节点
    
    这个函数会导入所有节点模块，触发装饰器执行，完成节点注册。
    """
    try:
        from . import source
        from . import process
        from . import logic
        from . import action
        from . import util
        logger.info(f"所有节点模块已加载，共注册 {len(NODE_REGISTRY)} 个节点")
    except ImportError as e:
        logger.warning(f"导入节点模块时出错（可能是首次创建）: {e}")


# 模块加载时自动注册所有节点
try:
    _register_all_nodes()
except Exception as e:
    logger.warning(f"自动注册节点时出错: {e}")





