"""逻辑节点

包含条件判断、循环、变量操作等逻辑节点。
条件节点支持 OCR 文本匹配、检测结果判断等多种条件类型。
"""
from typing import Dict, Any, Optional, List, Tuple
from loguru import logger

from nodes.base import BaseNode, NodeConfig, NodePropertyDef
from nodes import register_node


def _find_text_in_ocr_results(
    ocr_results: List[Dict],
    target_text: str,
    match_mode: str = "contains"
) -> Optional[Dict]:
    """在 OCR 结果中查找指定文本
    
    Args:
        ocr_results: OCR 识别结果列表
        target_text: 目标文本
        match_mode: 匹配模式 ("exact" | "contains")
        
    Returns:
        匹配的结果项，未找到返回 None
    """
    if not ocr_results or not target_text:
        return None
    
    for result in ocr_results:
        text = result.get('text', '')
        
        if match_mode == "exact":
            if text == target_text:
                return result
        else:  # contains
            if target_text in text:
                return result
    
    return None


@register_node
class ConditionNode(BaseNode):
    """条件判断节点
    
    支持多种条件类型：
    - ocr_text_found: 检查 OCR 是否识别到指定文本
    - detection_found: 检查是否检测到目标
    - variable: 变量比较
    - expression: 表达式求值
    
    当条件为真时返回 True，条件为假时返回 False。
    下游节点根据边的 branch 属性（true/false）决定是否执行。
    """
    
    @classmethod
    def get_config(cls) -> NodeConfig:
        return NodeConfig(
            type="condition",
            label="条件判断",
            category="logic",
            icon="Sort",
            color="#FAC858",
            description="根据条件执行不同分支（从此节点发出的连线需配置 True/False 分支）",
            properties=[
                # 条件类型选择
                NodePropertyDef(
                    key="condition_type",
                    label="条件类型",
                    type="select",
                    default="ocr_text_found",
                    options=[
                        {"label": "OCR 文本匹配", "value": "ocr_text_found"},
                        {"label": "OCR 有结果", "value": "ocr_has_result"},
                        {"label": "检测到目标", "value": "detection_found"},
                        {"label": "变量比较", "value": "variable"},
                        {"label": "表达式", "value": "expression"}
                    ]
                ),
                
                # === OCR 文本匹配相关属性 ===
                NodePropertyDef(
                    key="target_text",
                    label="目标文本",
                    type="text",
                    required=True,
                    placeholder="OCR 结果中要查找的文本",
                    depends_on="condition_type",
                    depends_value="ocr_text_found",
                    group="ocr"
                ),
                NodePropertyDef(
                    key="match_mode",
                    label="匹配模式",
                    type="select",
                    default="contains",
                    options=[
                        {"label": "包含", "value": "contains"},
                        {"label": "精确匹配", "value": "exact"}
                    ],
                    depends_on="condition_type",
                    depends_value="ocr_text_found",
                    group="ocr"
                ),
                
                # === OCR 有结果（无需配置，只要有识别结果即为 True） ===
                # 此类型不需要额外属性
                
                # === 检测到目标相关属性 ===
                NodePropertyDef(
                    key="target_label",
                    label="目标标签",
                    type="text",
                    placeholder="检测目标的标签（留空表示任意目标）",
                    depends_on="condition_type",
                    depends_value="detection_found",
                    group="detection"
                ),
                
                # === 变量比较相关属性 ===
                NodePropertyDef(
                    key="variable_name",
                    label="变量名",
                    type="text",
                    required=True,
                    placeholder="要比较的变量名",
                    depends_on="condition_type",
                    depends_value="variable",
                    group="variable"
                ),
                NodePropertyDef(
                    key="compare_operator",
                    label="比较运算符",
                    type="select",
                    default="==",
                    options=[
                        {"label": "等于", "value": "=="},
                        {"label": "不等于", "value": "!="},
                        {"label": "大于", "value": ">"},
                        {"label": "小于", "value": "<"},
                        {"label": "大于等于", "value": ">="},
                        {"label": "小于等于", "value": "<="}
                    ],
                    depends_on="condition_type",
                    depends_value="variable",
                    group="variable"
                ),
                NodePropertyDef(
                    key="compare_value",
                    label="比较值",
                    type="text",
                    required=True,
                    placeholder="比较的值",
                    depends_on="condition_type",
                    depends_value="variable",
                    group="variable"
                ),
                
                # === 表达式相关属性 ===
                NodePropertyDef(
                    key="expression",
                    label="表达式",
                    type="textarea",
                    required=True,
                    placeholder="例如: ${count} > 5 && ${status} == 'active'",
                    depends_on="condition_type",
                    depends_value="expression",
                    group="expression"
                )
            ]
        )
    
    def execute(self, context: Any, properties: Dict[str, Any]) -> Any:
        """执行条件判断"""
        try:
            condition_type = properties.get('condition_type', 'ocr_text_found')
            logger.debug(f"条件判断: 类型={condition_type}")
            
            result = False
            
            if condition_type == 'ocr_text_found':
                result = self._check_ocr_text(context, properties)
            
            elif condition_type == 'ocr_has_result':
                result = self._check_ocr_has_result(context)
            
            elif condition_type == 'detection_found':
                result = self._check_detection(context, properties)
            
            elif condition_type == 'variable':
                result = self._check_variable(context, properties)
            
            elif condition_type == 'expression':
                result = self._check_expression(context, properties)
            
            else:
                logger.warning(f"未知的条件类型: {condition_type}")
                return False
            
            logger.info(f"条件判断结果: {condition_type} -> {result}")
            return result
                
        except Exception as e:
            logger.error(f"条件判断异常: {type(e).__name__}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return False
    
    def _check_ocr_has_result(self, context: Any) -> bool:
        """检查 OCR 是否有任何识别结果"""
        ocr_results = getattr(context, 'ocr_results', [])
        has_result = bool(ocr_results) and len(ocr_results) > 0
        
        if has_result:
            logger.info(f"OCR 有结果: 共 {len(ocr_results)} 个文本区域")
            # 保存到上下文
            if hasattr(context, 'ocr_target_found'):
                context.ocr_target_found = True
        else:
            logger.debug("OCR 无结果")
        
        return has_result
    
    def _check_ocr_text(self, context: Any, properties: Dict[str, Any]) -> bool:
        """检查 OCR 文本匹配"""
        target_text = properties.get('target_text', '')
        match_mode = properties.get('match_mode', 'contains')
        
        if not target_text:
            logger.warning("目标文本未指定")
            return False
        
        ocr_results = getattr(context, 'ocr_results', [])
        if not ocr_results:
            logger.debug(f"OCR 结果为空，条件 '{target_text}' 不满足")
            return False
        
        # 查找目标文本
        matched = _find_text_in_ocr_results(ocr_results, target_text, match_mode)
        
        if matched:
            logger.info(f"OCR 匹配成功: '{target_text}'")
            
            # 保存匹配结果到上下文（供后续鼠标操作节点使用）
            if hasattr(context, 'ocr_matched_results'):
                context.ocr_matched_results = [matched]
            if hasattr(context, 'ocr_target_found'):
                context.ocr_target_found = True
            
            return True
        else:
            logger.debug(f"OCR 未匹配: '{target_text}'")
            return False
    
    def _check_detection(self, context: Any, properties: Dict[str, Any]) -> bool:
        """检查检测结果"""
        target_label = properties.get('target_label', '')
        
        detection_results = getattr(context, 'detection_results', [])
        if not detection_results:
            logger.debug("检测结果为空")
            return False
        
        if target_label:
            # 查找指定标签
            for result in detection_results:
                if result.get('label') == target_label:
                    logger.info(f"检测到目标: {target_label}")
                    return True
            logger.debug(f"未检测到目标: {target_label}")
            return False
        else:
            # 任意检测结果
            logger.info(f"检测到 {len(detection_results)} 个目标")
            return True
    
    def _check_variable(self, context: Any, properties: Dict[str, Any]) -> bool:
        """检查变量比较"""
        var_name = properties.get('variable_name', '')
        operator = properties.get('compare_operator', '==')
        compare_value = properties.get('compare_value', '')
        
        if not var_name:
            logger.warning("变量名未指定")
            return False
        
        # 获取变量值
        variables = getattr(context, 'variables', {})
        actual_value = variables.get(var_name)
        
        if actual_value is None:
            logger.debug(f"变量 '{var_name}' 不存在")
            return False
        
        try:
            # 尝试转换为数字比较
            if compare_value.replace('.', '').replace('-', '').isdigit():
                actual_num = float(actual_value)
                compare_num = float(compare_value)
                
                if operator == '==':
                    result = actual_num == compare_num
                elif operator == '!=':
                    result = actual_num != compare_num
                elif operator == '>':
                    result = actual_num > compare_num
                elif operator == '<':
                    result = actual_num < compare_num
                elif operator == '>=':
                    result = actual_num >= compare_num
                elif operator == '<=':
                    result = actual_num <= compare_num
                else:
                    result = False
            else:
                # 字符串比较
                actual_str = str(actual_value)
                if operator == '==':
                    result = actual_str == compare_value
                elif operator == '!=':
                    result = actual_str != compare_value
                else:
                    result = False
            
            logger.debug(f"变量比较: {var_name}({actual_value}) {operator} {compare_value} = {result}")
            return result
            
        except (ValueError, TypeError) as e:
            logger.error(f"变量比较失败: {e}")
            return False
    
    def _check_expression(self, context: Any, properties: Dict[str, Any]) -> bool:
        """检查表达式"""
        expression = properties.get('expression', '')
        
        if not expression:
            logger.warning("表达式为空")
            return False
        
        # 简单实现：检查是否有检测或 OCR 结果
        if hasattr(context, 'detection_results') and context.detection_results:
            return True
        if hasattr(context, 'ocr_results') and context.ocr_results:
            return True
        
        return False


@register_node
class LoopNode(BaseNode):
    """循环节点
    
    在图执行模式下，循环通常由 FlowRunner 的外层循环实现。
    此节点主要用于控制循环次数和计数。
    """
    
    @classmethod
    def get_config(cls) -> NodeConfig:
        return NodeConfig(
            type="loop",
            label="循环",
            category="logic",
            icon="Refresh",
            color="#FAC858",
            description="控制循环执行",
            properties=[
                NodePropertyDef(
                    key="loop_type",
                    label="循环类型",
                    type="select",
                    default="count",
                    options=[
                        {"label": "固定次数", "value": "count"},
                        {"label": "条件循环", "value": "while"}
                    ]
                ),
                NodePropertyDef(
                    key="count",
                    label="循环次数",
                    type="number",
                    default=1,
                    depends_on="loop_type",
                    depends_value="count"
                ),
                NodePropertyDef(
                    key="while_condition",
                    label="循环条件",
                    type="text",
                    placeholder="例如: ${count} < 10",
                    depends_on="loop_type",
                    depends_value="while"
                )
            ]
        )
    
    def execute(self, context: Any, properties: Dict[str, Any]) -> Any:
        """执行循环控制"""
        logger.debug("循环节点执行（循环由 FlowRunner 外层控制）")
        return True


@register_node
class VariableNode(BaseNode):
    """变量操作节点"""
    
    @classmethod
    def get_config(cls) -> NodeConfig:
        return NodeConfig(
            type="variable",
            label="变量操作",
            category="logic",
            icon="Box",
            color="#FAC858",
            description="设置或操作变量",
            properties=[
                NodePropertyDef(
                    key="operation",
                    label="操作",
                    type="select",
                    default="set",
                    options=[
                        {"label": "设置", "value": "set"},
                        {"label": "递增", "value": "increment"},
                        {"label": "递减", "value": "decrement"}
                    ]
                ),
                NodePropertyDef(
                    key="variable_name",
                    label="变量名",
                    type="text",
                    required=True,
                    placeholder="变量名称"
                ),
                NodePropertyDef(
                    key="value",
                    label="值",
                    type="text",
                    placeholder="要设置的值",
                    depends_on="operation",
                    depends_value="set"
                ),
                NodePropertyDef(
                    key="increment_value",
                    label="增量",
                    type="number",
                    default=1,
                    depends_on="operation",
                    depends_value=["increment", "decrement"]
                )
            ]
        )
    
    def execute(self, context: Any, properties: Dict[str, Any]) -> Any:
        """执行变量操作"""
        try:
            name = properties.get('variable_name', '')
            value = properties.get('value', '')
            operation = properties.get('operation', 'set')
            
            if not name:
                logger.warning("变量名为空")
                return False
            
            if not hasattr(context, 'variables'):
                context.variables = {}
            
            if operation == 'set':
                context.variables[name] = value
                logger.debug(f"设置变量: {name} = {value}")
                
            elif operation == 'increment':
                current = context.variables.get(name, 0)
                try:
                    context.variables[name] = float(current) + 1
                except (ValueError, TypeError):
                    context.variables[name] = 1
                logger.debug(f"递增变量: {name} = {context.variables[name]}")
                
            elif operation == 'decrement':
                current = context.variables.get(name, 0)
                try:
                    context.variables[name] = float(current) - 1
                except (ValueError, TypeError):
                    context.variables[name] = -1
                logger.debug(f"递减变量: {name} = {context.variables[name]}")
            
            return True
            
        except Exception as e:
            logger.error(f"变量操作失败: {e}")
            return False
