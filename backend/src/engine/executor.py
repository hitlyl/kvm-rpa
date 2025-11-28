"""流程执行器模块

执行解析后的脚本，支持条件分支、循环、等待、变量替换等高级功能。
"""
import time
import re
from typing import Dict, List, Any, Optional, Callable, Tuple
from loguru import logger

from .context import ExecutionContext
from .script_parser import ScriptParser


class ScriptExecutor:
    """脚本执行器
    
    执行 YAML 脚本中定义的动作序列，支持高级流程控制。
    """
    
    def __init__(self, kvm_adapter, yolo_detector=None, ocr_engine=None):
        """初始化执行器
        
        Args:
            kvm_adapter: 键鼠控制适配器
            yolo_detector: YOLO 检测器（可选）
            ocr_engine: OCR 引擎（可选）
        """
        self.kvm_adapter = kvm_adapter
        self.yolo_detector = yolo_detector
        self.ocr_engine = ocr_engine
        
        self.parser = ScriptParser()
        self.context: Optional[ExecutionContext] = None
        
        # 统计信息
        self.stats = {
            'scripts_executed': 0,
            'actions_executed': 0,
            'errors': 0
        }
        
        logger.info("脚本执行器已初始化")
    
    def execute_script(
        self,
        script: Dict[str, Any],
        initial_context: Optional[ExecutionContext] = None
    ) -> ExecutionContext:
        """执行脚本
        
        Args:
            script: 脚本字典
            initial_context: 初始上下文（可选）
            
        Returns:
            ExecutionContext: 执行后的上下文
        """
        # 验证脚本
        is_valid, errors = self.parser.validate_script(script)
        if not is_valid:
            error_msg = f"脚本验证失败: {', '.join(errors)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 创建或使用上下文
        if initial_context:
            self.context = initial_context
        else:
            self.context = ExecutionContext()
        
        # 设置脚本元数据
        self.context.metadata['script_name'] = script.get('name')
        self.context.metadata['script_id'] = script.get('id')
        
        # 初始化变量
        for var_name, var_value in script.get('variables', {}).items():
            self.context.set_variable(var_name, var_value)
        
        logger.info(f"开始执行脚本: {script.get('name')}")
        
        try:
            # 执行动作序列
            actions = script.get('actions', [])
            self._execute_actions(actions)
            
            self.stats['scripts_executed'] += 1
            logger.success(f"脚本执行完成: {script.get('name')}")
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.exception(f"脚本执行失败: {e}")
            
            # 错误处理策略
            on_error = script.get('on_error', 'stop')
            if on_error == 'stop':
                raise
            elif on_error == 'continue':
                logger.warning("继续执行（忽略错误）")
        
        return self.context
    
    def _execute_actions(self, actions: List[Dict[str, Any]]) -> None:
        """执行动作序列
        
        Args:
            actions: 动作列表
        """
        for action in actions:
            self._execute_single_action(action)
    
    def _execute_single_action(self, action: Dict[str, Any]) -> None:
        """执行单个动作
        
        Args:
            action: 动作字典
        """
        action_type = action.get('type')
        logger.debug(f"执行动作: {action_type}")
        
        self.stats['actions_executed'] += 1
        
        try:
            # 替换变量
            action = self._substitute_variables(action)
            
            # 根据类型执行不同的动作
            if action_type == 'click':
                self._action_click(action)
            elif action_type == 'move':
                self._action_move(action)
            elif action_type == 'input':
                self._action_input(action)
            elif action_type == 'key':
                self._action_key(action)
            elif action_type == 'wait':
                self._action_wait(action)
            elif action_type == 'drag':
                self._action_drag(action)
            elif action_type == 'ocr_check':
                self._action_ocr_check(action)
            elif action_type == 'detection_check':
                self._action_detection_check(action)
            elif action_type == 'conditional':
                self._action_conditional(action)
            elif action_type == 'loop':
                self._action_loop(action)
            elif action_type == 'set_variable':
                self._action_set_variable(action)
            elif action_type == 'log':
                self._action_log(action)
            else:
                logger.warning(f"未知的动作类型: {action_type}")
            
            # 记录成功
            self.context.record_action(action_type, action, 'success')
            
        except Exception as e:
            logger.error(f"动作执行失败: {action_type}, 错误: {e}")
            self.context.record_action(action_type, action, 'error', str(e))
            raise
    
    def _substitute_variables(self, obj: Any) -> Any:
        """递归替换对象中的变量引用 ${var_name}
        
        Args:
            obj: 要处理的对象
            
        Returns:
            替换后的对象
        """
        if isinstance(obj, str):
            # 替换字符串中的变量
            pattern = r'\$\{([^}]+)\}'
            
            def replace_var(match):
                var_name = match.group(1)
                value = self.context.get_variable(var_name)
                return str(value) if value is not None else match.group(0)
            
            return re.sub(pattern, replace_var, obj)
        
        elif isinstance(obj, dict):
            return {k: self._substitute_variables(v) for k, v in obj.items()}
        
        elif isinstance(obj, list):
            return [self._substitute_variables(item) for item in obj]
        
        else:
            return obj
    
    def _action_click(self, action: Dict[str, Any]) -> None:
        """执行点击动作"""
        x, y = self._resolve_coordinates(action.get('target'))
        button = action.get('button', 'left')
        clicks = action.get('clicks', 1)
        self.kvm_adapter.send_mouse_click(button, clicks, int(x), int(y))
    
    def _action_move(self, action: Dict[str, Any]) -> None:
        """执行移动动作"""
        x, y = self._resolve_coordinates(action.get('target'))
        mode = action.get('mode', 'absolute')
        self.kvm_adapter.send_mouse_move(int(x), int(y), mode)
    
    def _action_input(self, action: Dict[str, Any]) -> None:
        """执行输入动作"""
        text = action.get('text', '')
        self.kvm_adapter.send_key_input(text)
    
    def _action_key(self, action: Dict[str, Any]) -> None:
        """执行按键动作"""
        if 'combination' in action:
            keys = action['combination']
            self.kvm_adapter.send_key_combination(keys)
        elif 'key' in action:
            key = action['key']
            self.kvm_adapter.send_key_press(key)
    
    def _action_wait(self, action: Dict[str, Any]) -> None:
        """执行等待动作"""
        duration = action.get('duration', 1.0)
        time.sleep(duration)
    
    def _action_drag(self, action: Dict[str, Any]) -> None:
        """执行拖拽动作"""
        x1, y1 = self._resolve_coordinates(action.get('from'))
        x2, y2 = self._resolve_coordinates(action.get('to'))
        button = action.get('button', 'left')
        self.kvm_adapter.send_mouse_drag(int(x1), int(y1), int(x2), int(y2), button)
    
    def _action_ocr_check(self, action: Dict[str, Any]) -> None:
        """执行 OCR 检查动作"""
        if not self.ocr_engine or not self.context.current_frame:
            logger.warning("OCR 引擎或当前帧不可用")
            return
        
        target_text = action.get('text', '')
        timeout = action.get('timeout', 10)
        match_mode = action.get('match_mode', 'contains')
        
        start_time = time.time()
        found = False
        
        while time.time() - start_time < timeout:
            # OCR 识别
            ocr_results = self.ocr_engine.find_text(
                self.context.current_frame,
                target_text,
                match_mode
            )
            
            if ocr_results:
                found = True
                # 更新上下文
                self.context.ocr_results = ocr_results
                break
            
            time.sleep(0.5)
        
        if found:
            # 执行成功的动作
            if 'on_success' in action:
                self._execute_actions(action['on_success'])
        else:
            # 执行失败的动作
            if 'on_failure' in action:
                self._execute_actions(action['on_failure'])
            else:
                raise TimeoutError(f"OCR 检查超时: 未找到文本 '{target_text}'")
    
    def _action_detection_check(self, action: Dict[str, Any]) -> None:
        """执行检测检查动作"""
        if not self.yolo_detector or not self.context.current_frame:
            logger.warning("YOLO 检测器或当前帧不可用")
            return
        
        target_label = action.get('label', '')
        timeout = action.get('timeout', 10)
        
        start_time = time.time()
        found = False
        
        while time.time() - start_time < timeout:
            # YOLO 检测
            detection_results = self.yolo_detector.detect(self.context.current_frame)
            
            # 查找目标标签
            for det in detection_results:
                if det['label'] == target_label:
                    found = True
                    self.context.detection_results = detection_results
                    break
            
            if found:
                break
            
            time.sleep(0.5)
        
        if found:
            if 'on_success' in action:
                self._execute_actions(action['on_success'])
        else:
            if 'on_failure' in action:
                self._execute_actions(action['on_failure'])
            else:
                raise TimeoutError(f"检测超时: 未找到标签 '{target_label}'")
    
    def _action_conditional(self, action: Dict[str, Any]) -> None:
        """执行条件分支动作"""
        condition = action.get('condition', {})
        
        # 评估条件
        if self._evaluate_condition(condition):
            # 执行 then 分支
            if 'then' in action:
                self._execute_actions(action['then'])
        else:
            # 执行 else 分支
            if 'else' in action:
                self._execute_actions(action['else'])
    
    def _action_loop(self, action: Dict[str, Any]) -> None:
        """执行循环动作"""
        loop_type = action.get('loop_type', 'count')
        actions = action.get('actions', [])
        
        if loop_type == 'count':
            # 计数循环
            count = action.get('count', 1)
            for i in range(count):
                self.context.set_variable('loop_index', i)
                self._execute_actions(actions)
        
        elif loop_type == 'while':
            # 条件循环
            condition = action.get('condition', {})
            max_iterations = action.get('max_iterations', 100)
            iteration = 0
            
            while self._evaluate_condition(condition) and iteration < max_iterations:
                self.context.set_variable('loop_index', iteration)
                self._execute_actions(actions)
                iteration += 1
    
    def _action_set_variable(self, action: Dict[str, Any]) -> None:
        """执行设置变量动作"""
        name = action.get('name')
        value = action.get('value')
        
        if name:
            self.context.set_variable(name, value)
    
    def _action_log(self, action: Dict[str, Any]) -> None:
        """执行日志动作"""
        message = action.get('message', '')
        level = action.get('level', 'info')
        
        if level == 'debug':
            logger.debug(message)
        elif level == 'info':
            logger.info(message)
        elif level == 'warning':
            logger.warning(message)
        elif level == 'error':
            logger.error(message)
    
    def _evaluate_condition(self, condition: Dict[str, Any]) -> bool:
        """评估条件表达式
        
        Args:
            condition: 条件字典
            
        Returns:
            bool: 条件是否满足
        """
        # 变量比较
        if 'variable' in condition:
            var_name = condition['variable']
            var_value = self.context.get_variable(var_name)
            operator = condition.get('operator', '==')
            target_value = condition.get('value')
            
            if operator == '==':
                return var_value == target_value
            elif operator == '!=':
                return var_value != target_value
            elif operator == '>':
                return var_value > target_value
            elif operator == '<':
                return var_value < target_value
            elif operator == '>=':
                return var_value >= target_value
            elif operator == '<=':
                return var_value <= target_value
        
        # 标志检查
        if 'flag' in condition:
            flag_name = condition['flag']
            return self.context.get_flag(flag_name)
        
        # 默认返回 False
        return False
    
    def _resolve_coordinates(self, target: Any) -> Tuple[float, float]:
        """解析坐标
        
        Args:
            target: 目标描述
            
        Returns:
            (x, y) 坐标
        """
        if isinstance(target, (list, tuple)) and len(target) == 2:
            return float(target[0]), float(target[1])
        
        if isinstance(target, str):
            if target == 'trigger_bbox':
                # 使用触发结果的中心点
                if self.context.ocr_results:
                    bbox_rect = self.context.ocr_results[0]['bbox_rect']
                    x = bbox_rect[0] + bbox_rect[2] / 2
                    y = bbox_rect[1] + bbox_rect[3] / 2
                    return x, y
                elif self.context.detection_results:
                    center = self.context.detection_results[0]['center']
                    return center[0], center[1]
        
        raise ValueError(f"无法解析坐标: {target}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()

