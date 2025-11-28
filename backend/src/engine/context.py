"""执行上下文模块

管理流程执行的上下文信息，包括变量、状态、检测结果等。
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from loguru import logger


class ExecutionContext:
    """执行上下文
    
    存储流程执行过程中的状态和数据，支持变量管理、历史记录等。
    """
    
    def __init__(self):
        """初始化执行上下文"""
        # 变量存储
        self.variables: Dict[str, Any] = {}
        
        # 当前帧数据
        self.current_frame: Optional[Any] = None
        self.current_timestamp: Optional[float] = None
        
        # 检测和识别结果
        self.detection_results: List[Dict[str, Any]] = []
        self.ocr_results: List[Dict[str, Any]] = []
        
        # 计数器
        self.counters: Dict[str, int] = {}
        
        # 执行历史
        self.action_history: List[Dict[str, Any]] = []
        
        # 状态标志
        self.flags: Dict[str, bool] = {}
        
        # 元数据
        self.metadata = {
            'start_time': datetime.now().isoformat(),
            'script_name': None,
            'script_id': None
        }
        
        logger.debug("执行上下文已创建")
    
    def set_variable(self, name: str, value: Any) -> None:
        """设置变量
        
        Args:
            name: 变量名
            value: 变量值
        """
        self.variables[name] = value
        logger.debug(f"设置变量: {name} = {value}")
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """获取变量
        
        Args:
            name: 变量名
            default: 默认值
            
        Returns:
            变量值
        """
        return self.variables.get(name, default)
    
    def has_variable(self, name: str) -> bool:
        """检查变量是否存在
        
        Args:
            name: 变量名
            
        Returns:
            bool: 是否存在
        """
        return name in self.variables
    
    def delete_variable(self, name: str) -> None:
        """删除变量
        
        Args:
            name: 变量名
        """
        if name in self.variables:
            del self.variables[name]
            logger.debug(f"删除变量: {name}")
    
    def increment_counter(self, name: str, amount: int = 1) -> int:
        """递增计数器
        
        Args:
            name: 计数器名称
            amount: 递增量
            
        Returns:
            int: 新的计数值
        """
        if name not in self.counters:
            self.counters[name] = 0
        self.counters[name] += amount
        return self.counters[name]
    
    def get_counter(self, name: str) -> int:
        """获取计数器值
        
        Args:
            name: 计数器名称
            
        Returns:
            int: 计数值
        """
        return self.counters.get(name, 0)
    
    def reset_counter(self, name: str) -> None:
        """重置计数器
        
        Args:
            name: 计数器名称
        """
        self.counters[name] = 0
    
    def set_flag(self, name: str, value: bool = True) -> None:
        """设置标志
        
        Args:
            name: 标志名称
            value: 标志值
        """
        self.flags[name] = value
        logger.debug(f"设置标志: {name} = {value}")
    
    def get_flag(self, name: str) -> bool:
        """获取标志
        
        Args:
            name: 标志名称
            
        Returns:
            bool: 标志值
        """
        return self.flags.get(name, False)
    
    def update_frame_data(
        self,
        frame: Any,
        timestamp: float,
        detection_results: List[Dict[str, Any]],
        ocr_results: List[Dict[str, Any]]
    ) -> None:
        """更新当前帧数据
        
        Args:
            frame: 当前帧
            timestamp: 时间戳
            detection_results: 检测结果
            ocr_results: OCR 结果
        """
        self.current_frame = frame
        self.current_timestamp = timestamp
        self.detection_results = detection_results
        self.ocr_results = ocr_results
    
    def record_action(
        self,
        action_type: str,
        action_params: Dict[str, Any],
        status: str,
        error: Optional[str] = None
    ) -> None:
        """记录动作执行
        
        Args:
            action_type: 动作类型
            action_params: 动作参数
            status: 执行状态 (success, error)
            error: 错误信息（如有）
        """
        record = {
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type,
            'params': action_params,
            'status': status,
            'error': error
        }
        self.action_history.append(record)
        
        # 限制历史记录数量（保留最近 100 条）
        if len(self.action_history) > 100:
            self.action_history.pop(0)
    
    def get_action_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取动作历史
        
        Args:
            limit: 返回条数限制
            
        Returns:
            动作历史列表
        """
        if limit:
            return self.action_history[-limit:]
        return self.action_history.copy()
    
    def clear_history(self) -> None:
        """清空历史记录"""
        self.action_history.clear()
        logger.debug("动作历史已清空")
    
    def reset(self) -> None:
        """重置上下文（保留元数据）"""
        self.variables.clear()
        self.current_frame = None
        self.current_timestamp = None
        self.detection_results.clear()
        self.ocr_results.clear()
        self.counters.clear()
        self.action_history.clear()
        self.flags.clear()
        logger.info("执行上下文已重置")
    
    def to_dict(self) -> Dict[str, Any]:
        """导出为字典
        
        Returns:
            上下文字典
        """
        return {
            'variables': self.variables.copy(),
            'counters': self.counters.copy(),
            'flags': self.flags.copy(),
            'metadata': self.metadata.copy(),
            'detection_count': len(self.detection_results),
            'ocr_count': len(self.ocr_results),
            'history_count': len(self.action_history)
        }

