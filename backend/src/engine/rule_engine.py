"""基础规则引擎

提供简单的规则匹配和动作执行功能，支持基于检测和 OCR 结果的触发条件。
"""
import time
from typing import List, Dict, Any, Optional, Callable, Tuple
from loguru import logger


class RuleEngine:
    """规则引擎
    
    支持声明式规则定义，根据检测和 OCR 结果触发相应的动作。
    
    规则格式示例:
    {
        "name": "点击下一步按钮",
        "enabled": true,
        "trigger": {
            "type": "ocr",  # 或 "detection", "combined"
            "text_contains": "下一步",
            "min_confidence": 0.8
        },
        "actions": [
            {"type": "click", "target": "trigger_bbox"},
            {"type": "wait", "duration": 1.0}
        ]
    }
    """
    
    def __init__(self, kvm_adapter):
        """初始化规则引擎
        
        Args:
            kvm_adapter: 键鼠控制适配器实例
        """
        self.kvm_adapter = kvm_adapter
        self.rules: List[Dict[str, Any]] = []
        
        # 统计信息
        self.stats = {
            'total_evaluations': 0,
            'total_triggers': 0,
            'total_actions': 0,
            'failed_actions': 0
        }
        
        logger.info("规则引擎已初始化")
    
    def register_rule(self, rule: Dict[str, Any]) -> None:
        """注册规则
        
        Args:
            rule: 规则字典
        """
        # 验证规则格式
        if 'name' not in rule:
            rule['name'] = f"rule_{len(self.rules)}"
        
        if 'enabled' not in rule:
            rule['enabled'] = True
        
        if 'trigger' not in rule or 'actions' not in rule:
            logger.error(f"无效的规则格式: {rule}")
            return
        
        self.rules.append(rule)
        logger.info(f"规则已注册: {rule['name']}")
    
    def clear_rules(self) -> None:
        """清空所有规则"""
        self.rules.clear()
        logger.info("所有规则已清空")
    
    def evaluate(
        self,
        detection_results: List[Dict[str, Any]],
        ocr_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """评估当前帧是否触发任何规则
        
        Args:
            detection_results: YOLO 检测结果列表
            ocr_results: OCR 识别结果列表
            
        Returns:
            触发的规则列表
        """
        self.stats['total_evaluations'] += 1
        triggered_rules = []
        
        for rule in self.rules:
            # 跳过禁用的规则
            if not rule.get('enabled', True):
                continue
            
            # 评估触发条件
            if self._check_trigger(rule['trigger'], detection_results, ocr_results):
                triggered_rules.append({
                    'rule': rule,
                    'detection_results': detection_results,
                    'ocr_results': ocr_results
                })
                self.stats['total_triggers'] += 1
                logger.info(f"规则触发: {rule['name']}")
        
        return triggered_rules
    
    def _check_trigger(
        self,
        trigger: Dict[str, Any],
        detection_results: List[Dict[str, Any]],
        ocr_results: List[Dict[str, Any]]
    ) -> bool:
        """检查触发条件是否满足
        
        Args:
            trigger: 触发条件字典
            detection_results: 检测结果
            ocr_results: OCR 结果
            
        Returns:
            bool: 是否触发
        """
        trigger_type = trigger.get('type', 'ocr')
        
        if trigger_type == 'ocr':
            return self._check_ocr_trigger(trigger, ocr_results)
        elif trigger_type == 'detection':
            return self._check_detection_trigger(trigger, detection_results)
        elif trigger_type == 'combined':
            # 组合触发：同时满足 OCR 和检测条件
            ocr_ok = self._check_ocr_trigger(trigger.get('ocr', {}), ocr_results)
            det_ok = self._check_detection_trigger(trigger.get('detection', {}), detection_results)
            return ocr_ok and det_ok
        else:
            logger.warning(f"未知的触发类型: {trigger_type}")
            return False
    
    def _check_ocr_trigger(
        self,
        trigger: Dict[str, Any],
        ocr_results: List[Dict[str, Any]]
    ) -> bool:
        """检查 OCR 触发条件
        
        Args:
            trigger: 触发条件
            ocr_results: OCR 结果
            
        Returns:
            bool: 是否满足条件
        """
        # 文本包含检查
        if 'text_contains' in trigger:
            target_text = trigger['text_contains']
            min_conf = trigger.get('min_confidence', 0.5)
            case_sensitive = trigger.get('case_sensitive', False)
            
            for ocr in ocr_results:
                text = ocr['text']
                conf = ocr['conf']
                
                # 置信度检查
                if conf < min_conf:
                    continue
                
                # 文本匹配
                if not case_sensitive:
                    text = text.lower()
                    target_text = target_text.lower()
                
                if target_text in text:
                    return True
        
        # 文本精确匹配
        if 'text_equals' in trigger:
            target_text = trigger['text_equals']
            min_conf = trigger.get('min_confidence', 0.5)
            case_sensitive = trigger.get('case_sensitive', False)
            
            for ocr in ocr_results:
                text = ocr['text']
                conf = ocr['conf']
                
                if conf < min_conf:
                    continue
                
                if not case_sensitive:
                    text = text.lower()
                    target_text = target_text.lower()
                
                if text == target_text:
                    return True
        
        # 文本正则匹配
        if 'text_regex' in trigger:
            import re
            pattern = trigger['text_regex']
            min_conf = trigger.get('min_confidence', 0.5)
            
            for ocr in ocr_results:
                if ocr['conf'] < min_conf:
                    continue
                
                if re.search(pattern, ocr['text']):
                    return True
        
        return False
    
    def _check_detection_trigger(
        self,
        trigger: Dict[str, Any],
        detection_results: List[Dict[str, Any]]
    ) -> bool:
        """检查检测触发条件
        
        Args:
            trigger: 触发条件
            detection_results: 检测结果
            
        Returns:
            bool: 是否满足条件
        """
        # 标签匹配
        if 'label' in trigger:
            target_label = trigger['label']
            min_conf = trigger.get('min_confidence', 0.5)
            
            for det in detection_results:
                if det['label'] == target_label and det['conf'] >= min_conf:
                    return True
        
        # 检测数量条件
        if 'min_count' in trigger:
            min_count = trigger['min_count']
            label = trigger.get('label')
            
            if label:
                # 特定标签的数量
                count = sum(1 for det in detection_results if det['label'] == label)
            else:
                # 所有检测的数量
                count = len(detection_results)
            
            if count >= min_count:
                return True
        
        return False
    
    def execute_actions(
        self,
        actions: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """执行动作序列
        
        Args:
            actions: 动作列表
            context: 执行上下文（包含检测和 OCR 结果）
            
        Returns:
            bool: 是否全部执行成功
        """
        context = context or {}
        success = True
        
        for action in actions:
            try:
                if not self._execute_single_action(action, context):
                    success = False
                    if action.get('required', False):
                        # 必需动作失败，中止后续执行
                        logger.error(f"必需动作执行失败，中止: {action}")
                        break
            except Exception as e:
                logger.exception(f"执行动作失败: {action}, 错误: {e}")
                self.stats['failed_actions'] += 1
                success = False
                if action.get('required', False):
                    break
        
        return success
    
    def _execute_single_action(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """执行单个动作
        
        Args:
            action: 动作字典
            context: 执行上下文
            
        Returns:
            bool: 是否执行成功
        """
        action_type = action.get('type')
        self.stats['total_actions'] += 1
        
        try:
            if action_type == 'click':
                return self._action_click(action, context)
            elif action_type == 'move':
                return self._action_move(action, context)
            elif action_type == 'input':
                return self._action_input(action, context)
            elif action_type == 'key':
                return self._action_key(action, context)
            elif action_type == 'wait':
                return self._action_wait(action, context)
            elif action_type == 'drag':
                return self._action_drag(action, context)
            else:
                logger.warning(f"未知的动作类型: {action_type}")
                return False
        except Exception as e:
            logger.exception(f"动作执行异常: {e}")
            return False
    
    def _action_click(self, action: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """执行点击动作"""
        target = action.get('target')
        button = action.get('button', 'left')
        clicks = action.get('clicks', 1)
        
        # 解析目标坐标
        x, y = self._resolve_coordinates(target, context)
        if x is None or y is None:
            logger.error(f"无法解析点击坐标: {target}")
            return False
        
        self.kvm_adapter.send_mouse_click(button=button, clicks=clicks, x=int(x), y=int(y))
        return True
    
    def _action_move(self, action: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """执行鼠标移动动作"""
        target = action.get('target')
        mode = action.get('mode', 'absolute')
        
        x, y = self._resolve_coordinates(target, context)
        if x is None or y is None:
            logger.error(f"无法解析移动坐标: {target}")
            return False
        
        self.kvm_adapter.send_mouse_move(int(x), int(y), mode=mode)
        return True
    
    def _action_input(self, action: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """执行文本输入动作"""
        text = action.get('text', '')
        self.kvm_adapter.send_key_input(text)
        return True
    
    def _action_key(self, action: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """执行按键动作"""
        if 'combination' in action:
            # 组合键
            keys = action['combination']
            self.kvm_adapter.send_key_combination(keys)
        elif 'key' in action:
            # 单键
            key = action['key']
            self.kvm_adapter.send_key_press(key)
        else:
            logger.error("按键动作缺少 'combination' 或 'key' 参数")
            return False
        return True
    
    def _action_wait(self, action: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """执行等待动作"""
        duration = action.get('duration', 1.0)
        self.kvm_adapter.wait(duration)
        return True
    
    def _action_drag(self, action: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """执行拖拽动作"""
        from_target = action.get('from')
        to_target = action.get('to')
        button = action.get('button', 'left')
        
        x1, y1 = self._resolve_coordinates(from_target, context)
        x2, y2 = self._resolve_coordinates(to_target, context)
        
        if None in (x1, y1, x2, y2):
            logger.error("无法解析拖拽坐标")
            return False
        
        self.kvm_adapter.send_mouse_drag(int(x1), int(y1), int(x2), int(y2), button=button)
        return True
    
    def _resolve_coordinates(
        self,
        target: Any,
        context: Dict[str, Any]
    ) -> Tuple[Optional[float], Optional[float]]:
        """解析目标坐标
        
        Args:
            target: 目标描述（可以是坐标、字符串标识等）
            context: 执行上下文
            
        Returns:
            (x, y) 坐标元组
        """
        # 直接坐标
        if isinstance(target, (list, tuple)) and len(target) == 2:
            return float(target[0]), float(target[1])
        
        # 字符串标识
        if isinstance(target, str):
            if target == 'trigger_bbox':
                # 使用触发该规则的 OCR 或检测结果的中心点
                ocr_results = context.get('ocr_results', [])
                if ocr_results:
                    bbox_rect = ocr_results[0]['bbox_rect']
                    x = bbox_rect[0] + bbox_rect[2] / 2
                    y = bbox_rect[1] + bbox_rect[3] / 2
                    return x, y
                
                detection_results = context.get('detection_results', [])
                if detection_results:
                    center = detection_results[0]['center']
                    return center[0], center[1]
        
        return None, None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()

