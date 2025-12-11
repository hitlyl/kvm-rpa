"""动作节点

包含鼠标操作、键盘操作、等待等动作节点。
使用 KVM 连接池进行鼠标和键盘操作。
"""
import re
import time
from typing import Dict, Any, Optional, Tuple
from loguru import logger

from nodes.base import BaseNode, NodeConfig, NodePropertyDef
from nodes import register_node
from api.sse_service import send_debug


def _get_kvm_config(context: Any) -> Optional[Dict[str, Any]]:
    """从上下文获取 KVM 配置"""
    if hasattr(context, 'kvm_config') and context.kvm_config:
        return context.kvm_config
    return None


def _find_text_position(
    ocr_results: list, 
    target_text: str, 
    match_mode: str = "contains"
) -> Optional[Tuple[int, int]]:
    """在 OCR 结果中查找指定文本的位置
    
    Args:
        ocr_results: OCR 结果列表
        target_text: 目标文本或正则表达式
        match_mode: 匹配模式 ("contains" | "exact" | "regex")
        
    Returns:
        (x, y) 中心坐标，未找到返回 None
    """
    if not ocr_results:
        logger.debug(f"_find_text_position: OCR 结果为空")
        return None
    
    logger.debug(f"_find_text_position: 查找 '{target_text}' (模式={match_mode}), OCR结果数={len(ocr_results)}")
    
    # 编译正则表达式（如果是正则模式）
    regex_pattern = None
    if match_mode == "regex":
        try:
            regex_pattern = re.compile(target_text)
        except re.error as e:
            logger.error(f"正则表达式语法错误: {target_text}, 错误: {e}")
            return None
    
    for result in ocr_results:
        text = result.get('text', '')
        
        # 根据匹配模式判断
        matched = False
        if match_mode == "exact":
            matched = (text == target_text)
        elif match_mode == "regex":
            matched = (regex_pattern and regex_pattern.search(text) is not None)
        else:  # contains
            matched = (target_text in text)
        
        if matched:
            logger.debug(f"_find_text_position: 匹配成功 '{target_text}' in '{text}'")
            # 获取中心坐标
            center = result.get('center')
            if center:
                logger.debug(f"_find_text_position: 使用 center={center}")
                return (int(center[0]), int(center[1]))
            
            # 从 bbox 计算中心
            bbox = result.get('bbox')
            if bbox and len(bbox) >= 4:
                # bbox 格式: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] 或 [x, y, w, h]
                if isinstance(bbox[0], list):
                    x_coords = [p[0] for p in bbox]
                    y_coords = [p[1] for p in bbox]
                    cx = sum(x_coords) / len(x_coords)
                    cy = sum(y_coords) / len(y_coords)
                else:
                    cx = bbox[0] + bbox[2] / 2
                    cy = bbox[1] + bbox[3] / 2
                logger.debug(f"_find_text_position: 从 bbox 计算 center=({cx}, {cy})")
                return (int(cx), int(cy))
    
    logger.debug(f"_find_text_position: 未找到 '{target_text}'")
    return None


@register_node
class MouseActionNode(BaseNode):
    """鼠标操作节点
    
    支持多种位置指定方式：
    - 使用 OCR 匹配结果的位置
    - 指定目标文本查找位置
    - 使用固定坐标
    """
    
    @classmethod
    def get_config(cls) -> NodeConfig:
        return NodeConfig(
            type="mouse_action",
            label="鼠标操作",
            category="action",
            icon="Pointer",
            color="#EE6666",
            description="执行鼠标点击操作",
            properties=[
                NodePropertyDef(
                    key="action_type",
                    label="动作类型",
                    type="select",
                    default="click",
                    options=[
                        {"label": "点击", "value": "click"},
                        {"label": "移动", "value": "move"},
                        {"label": "双击", "value": "double_click"}
                    ]
                ),
                NodePropertyDef(
                    key="button",
                    label="按钮",
                    type="select",
                    default="left",
                    options=[
                        {"label": "左键", "value": "left"},
                        {"label": "右键", "value": "right"},
                        {"label": "中键", "value": "middle"}
                    ],
                    depends_on="action_type",
                    depends_value=["click", "double_click"]
                ),
                NodePropertyDef(
                    key="position_mode",
                    label="位置模式",
                    type="select",
                    default="ocr_match",
                    options=[
                        {"label": "OCR 匹配文本", "value": "ocr_match"},
                        {"label": "固定坐标", "value": "fixed"},
                        {"label": "检测结果", "value": "detection"}
                    ]
                ),
                # OCR 匹配文本模式的属性
                NodePropertyDef(
                    key="target_text",
                    label="目标文本",
                    type="text",
                    required=True,
                    placeholder="在 OCR 结果中查找此文本的位置",
                    depends_on="position_mode",
                    depends_value="ocr_match"
                ),
                NodePropertyDef(
                    key="match_mode",
                    label="匹配模式",
                    type="select",
                    default="contains",
                    options=[
                        {"label": "包含", "value": "contains"},
                        {"label": "精确匹配", "value": "exact"},
                        {"label": "正则表达式", "value": "regex"}
                    ],
                    description="包含: 文本包含目标即匹配; 精确: 完全一致; 正则: 使用正则表达式 (如 下.*步)",
                    depends_on="position_mode",
                    depends_value="ocr_match"
                ),
                # 固定坐标模式的属性
                NodePropertyDef(
                    key="x",
                    label="X 坐标",
                    type="number",
                    default=0,
                    depends_on="position_mode",
                    depends_value="fixed"
                ),
                NodePropertyDef(
                    key="y",
                    label="Y 坐标",
                    type="number",
                    default=0,
                    depends_on="position_mode",
                    depends_value="fixed"
                ),
                # 检测结果模式的属性
                NodePropertyDef(
                    key="detection_label",
                    label="目标标签",
                    type="text",
                    placeholder="检测目标的标签（留空使用第一个结果）",
                    depends_on="position_mode",
                    depends_value="detection"
                ),
                # 偏移（非固定坐标模式可用）
                NodePropertyDef(
                    key="offset_x",
                    label="X 偏移",
                    type="number",
                    default=0,
                    placeholder="相对于匹配位置的X偏移"
                ),
                NodePropertyDef(
                    key="offset_y",
                    label="Y 偏移",
                    type="number",
                    default=0,
                    placeholder="相对于匹配位置的Y偏移"
                )
            ]
        )
    
    def execute(self, context: Any, properties: Dict[str, Any]) -> Any:
        """执行鼠标操作"""
        from kvm.kvm_manager import get_kvm_manager
        
        flow_id = getattr(context, 'flow_id', '')
        loop_count = getattr(context, 'loop_count', 0)
        
        try:
            action_type = properties.get('action_type', 'click')
            button = properties.get('button', 'left')
            position_mode = properties.get('position_mode', 'ocr_match')
            offset_x = int(properties.get('offset_x', 0))
            offset_y = int(properties.get('offset_y', 0))
            
            # 获取 KVM 配置
            kvm_config = _get_kvm_config(context)
            if not kvm_config:
                error_msg = "KVM 配置未找到，请确保流程中包含 KVM 数据源节点"
                logger.error(error_msg)
                if flow_id:
                    send_debug(flow_id, f"❌ 鼠标[{loop_count}]: {error_msg}")
                return False
            
            # 确定点击位置
            x, y = None, None
            position_found = False
            
            if position_mode == 'fixed':
                x = int(properties.get('x', 0))
                y = int(properties.get('y', 0))
                position_found = True
                logger.debug(f"使用固定坐标: ({x}, {y})")
                    
            elif position_mode == 'ocr_match':
                # 根据目标文本在 OCR 结果中查找位置
                target_text = properties.get('target_text', '')
                match_mode = properties.get('match_mode', 'contains')
                
                if not target_text:
                    logger.warning("目标文本未指定，跳过鼠标操作")
                    if flow_id:
                        send_debug(flow_id, f"⚠️ 鼠标[{loop_count}]: 目标文本未指定")
                    return True  # 配置问题，但不是严重错误
                
                ocr_results = getattr(context, 'ocr_results', [])
                
                # 发送 OCR 结果数量到 SSE
                ocr_count = len(ocr_results) if ocr_results else 0
                if flow_id:
                    send_debug(flow_id, f"🔍 鼠标[{loop_count}]: 在 {ocr_count} 个OCR结果中查找 '{target_text}'")
                
                # 打印所有 OCR 结果供调试
                logger.debug(f"OCR 结果数量: {ocr_count}")
                if ocr_results:
                    for i, r in enumerate(ocr_results[:10]):  # 最多显示10个
                        r_text = r.get('text', '')
                        r_center = r.get('center', 'N/A')
                        logger.debug(f"  OCR[{i}]: '{r_text}' @ {r_center}")
                
                pos = _find_text_position(ocr_results, target_text, match_mode)
                if pos:
                    x, y = pos
                    position_found = True
                    logger.info(f"OCR 匹配: 目标='{target_text}'({match_mode}), 位置=({x}, {y})")
                    if flow_id:
                        send_debug(flow_id, f"✅ 鼠标[{loop_count}]: 找到 '{target_text}' @ ({x}, {y})")
                else:
                    logger.info(f"未找到目标文本: '{target_text}'({match_mode})，跳过鼠标操作")
                    # 打印可用的文本供调试
                    if ocr_results:
                        available_texts = [r.get('text', '') for r in ocr_results[:5]]
                        logger.debug(f"可用文本: {available_texts}")
                        if flow_id:
                            send_debug(flow_id, f"⚠️ 鼠标[{loop_count}]: 未找到 '{target_text}'，可用: {available_texts[:3]}")
                    else:
                        if flow_id:
                            send_debug(flow_id, f"⚠️ 鼠标[{loop_count}]: 未找到 '{target_text}'，OCR结果为空")
                    return True  # 未找到文本不是错误，只是跳过操作
                    
            elif position_mode == 'detection':
                detection_label = properties.get('detection_label', '')
                
                if not hasattr(context, 'detection_results') or not context.detection_results:
                    logger.info("没有可用的检测结果，跳过鼠标操作")
                    return True  # 没有检测结果不是错误
                
                # 查找指定标签的检测结果
                target_result = None
                if detection_label:
                    for result in context.detection_results:
                        if result.get('label') == detection_label:
                            target_result = result
                            break
                    if not target_result:
                        logger.info(f"未找到标签为 '{detection_label}' 的检测结果，跳过鼠标操作")
                        return True  # 未找到目标不是错误
                else:
                    # 使用第一个检测结果
                    target_result = context.detection_results[0]
                
                center = target_result.get('center', (0, 0))
                x, y = int(center[0]), int(center[1])
                position_found = True
                logger.debug(f"使用检测结果位置: ({x}, {y})")
            
            # 如果没有找到有效位置，跳过操作
            if not position_found:
                logger.info("未确定点击位置，跳过鼠标操作")
                return True
            
            # 应用偏移
            x += offset_x
            y += offset_y
            
            # 执行鼠标操作
            kvm_manager = get_kvm_manager()
            
            if action_type == 'click':
                if flow_id:
                    send_debug(flow_id, f"🖱️ 鼠标[{loop_count}]: 点击 ({x}, {y}), {button}键")
                logger.info(f"准备鼠标点击: 坐标=({x}, {y}), 按钮={button}")
                
                result = kvm_manager.send_mouse_click(
                    kvm_config['ip'],
                    kvm_config['port'],
                    kvm_config['channel'],
                    x, y, button
                )
                if result:
                    logger.info(f"鼠标点击发送成功: ({x}, {y}), button={button}")
                    if flow_id:
                        send_debug(flow_id, f"✅ 鼠标[{loop_count}]: 点击成功")
                else:
                    logger.error(f"鼠标点击发送失败: ({x}, {y}), button={button}")
                    if flow_id:
                        send_debug(flow_id, f"❌ 鼠标[{loop_count}]: 点击失败")
                return result
                
            elif action_type == 'double_click':
                if flow_id:
                    send_debug(flow_id, f"🖱️ 鼠标[{loop_count}]: 双击 ({x}, {y}), {button}键")
                    
                # 使用新的双击方法
                result = kvm_manager.send_mouse_double_click(
                    kvm_config['ip'],
                    kvm_config['port'],
                    kvm_config['channel'],
                    x, y, button
                )
                if result:
                    logger.info(f"鼠标双击成功: ({x}, {y})")
                    if flow_id:
                        send_debug(flow_id, f"✅ 鼠标[{loop_count}]: 双击成功")
                else:
                    if flow_id:
                        send_debug(flow_id, f"❌ 鼠标[{loop_count}]: 双击失败")
                return result
                
            elif action_type == 'move':
                if flow_id:
                    send_debug(flow_id, f"🖱️ 鼠标[{loop_count}]: 移动到 ({x}, {y})")
                    
                result = kvm_manager.send_mouse_move(
                    kvm_config['ip'],
                    kvm_config['port'],
                    kvm_config['channel'],
                    x, y
                )
                if result:
                    logger.info(f"鼠标移动成功: ({x}, {y})")
                return result
            
            return True
            
        except Exception as e:
            logger.error(f"鼠标操作失败: {e}")
            if flow_id:
                send_debug(flow_id, f"❌ 鼠标[{loop_count}]: 异常 - {str(e)}")
            return False


@register_node
class KeyboardActionNode(BaseNode):
    """键盘操作节点
    
    支持文本输入和特殊按键。
    """
    
    @classmethod
    def get_config(cls) -> NodeConfig:
        return NodeConfig(
            type="keyboard_action",
            label="键盘操作",
            category="action",
            icon="Tickets",
            color="#EE6666",
            description="执行键盘输入操作",
            properties=[
                NodePropertyDef(
                    key="action_type",
                    label="动作类型",
                    type="select",
                    default="input",
                    options=[
                        {"label": "输入文本", "value": "input"},
                        {"label": "按键", "value": "key"},
                        {"label": "组合键", "value": "hotkey"}
                    ]
                ),
                # 输入文本模式
                NodePropertyDef(
                    key="text",
                    label="文本",
                    type="text",
                    required=True,
                    placeholder="要输入的文本",
                    depends_on="action_type",
                    depends_value="input"
                ),
                # 按键模式
                NodePropertyDef(
                    key="key",
                    label="按键",
                    type="select",
                    default="ENTER",
                    options=[
                        {"label": "回车", "value": "ENTER"},
                        {"label": "ESC", "value": "ESC"},
                        {"label": "Tab", "value": "TAB"},
                        {"label": "退格", "value": "BACKSPACE"},
                        {"label": "删除", "value": "DELETE"},
                        {"label": "空格", "value": "SPACE"},
                        {"label": "上", "value": "UP"},
                        {"label": "下", "value": "DOWN"},
                        {"label": "左", "value": "LEFT"},
                        {"label": "右", "value": "RIGHT"},
                        {"label": "Home", "value": "HOME"},
                        {"label": "End", "value": "END"},
                        {"label": "Page Up", "value": "PAGEUP"},
                        {"label": "Page Down", "value": "PAGEDOWN"},
                        {"label": "F1", "value": "F1"},
                        {"label": "F2", "value": "F2"},
                        {"label": "F3", "value": "F3"},
                        {"label": "F4", "value": "F4"},
                        {"label": "F5", "value": "F5"},
                        {"label": "F6", "value": "F6"},
                        {"label": "F7", "value": "F7"},
                        {"label": "F8", "value": "F8"},
                        {"label": "F9", "value": "F9"},
                        {"label": "F10", "value": "F10"},
                        {"label": "F11", "value": "F11"},
                        {"label": "F12", "value": "F12"}
                    ],
                    depends_on="action_type",
                    depends_value="key"
                ),
                # 组合键模式
                NodePropertyDef(
                    key="hotkey",
                    label="组合键",
                    type="select",
                    default="ctrl+c",
                    options=[
                        {"label": "Ctrl+C (复制)", "value": "ctrl+c"},
                        {"label": "Ctrl+V (粘贴)", "value": "ctrl+v"},
                        {"label": "Ctrl+X (剪切)", "value": "ctrl+x"},
                        {"label": "Ctrl+A (全选)", "value": "ctrl+a"},
                        {"label": "Ctrl+Z (撤销)", "value": "ctrl+z"},
                        {"label": "Ctrl+S (保存)", "value": "ctrl+s"},
                        {"label": "Ctrl+F (查找)", "value": "ctrl+f"},
                        {"label": "Alt+Tab (切换窗口)", "value": "alt+tab"},
                        {"label": "Alt+F4 (关闭窗口)", "value": "alt+f4"},
                        {"label": "Win+D (显示桌面)", "value": "win+d"}
                    ],
                    depends_on="action_type",
                    depends_value="hotkey"
                )
            ]
        )
    
    def execute(self, context: Any, properties: Dict[str, Any]) -> Any:
        """执行键盘操作"""
        from kvm.kvm_manager import get_kvm_manager
        
        try:
            action_type = properties.get('action_type', 'input')
            
            # 获取 KVM 配置
            kvm_config = _get_kvm_config(context)
            if not kvm_config:
                logger.error("KVM 配置未找到")
                return False
            
            kvm_manager = get_kvm_manager()
            
            if action_type == 'input':
                text = properties.get('text', '')
                if not text:
                    logger.warning("输入文本为空")
                    return True
                
                result = kvm_manager.send_key_input(
                    kvm_config['ip'],
                    kvm_config['port'],
                    kvm_config['channel'],
                    text
                )
                if result:
                    logger.info(f"键盘输入: {text}")
                return result
                
            elif action_type == 'key':
                key = properties.get('key', 'ENTER')
                result = kvm_manager.send_key_press(
                    kvm_config['ip'],
                    kvm_config['port'],
                    kvm_config['channel'],
                    key
                )
                if result:
                    logger.info(f"按键: {key}")
                return result
            
            return True
            
        except Exception as e:
            logger.error(f"键盘操作失败: {e}")
            return False


@register_node
class WaitNode(BaseNode):
    """等待节点
    
    等待指定的毫秒数。
    """
    
    @classmethod
    def get_config(cls) -> NodeConfig:
        return NodeConfig(
            type="wait",
            label="等待",
            category="action",
            icon="Timer",
            color="#EE6666",
            description="等待指定时间（毫秒）",
            properties=[
                NodePropertyDef(
                    key="duration_ms",
                    label="等待时长（毫秒）",
                    type="number",
                    default=500,
                    placeholder="例如: 500"
                )
            ]
        )
    
    def execute(self, context: Any, properties: Dict[str, Any]) -> Any:
        """执行等待"""
        try:
            duration_ms = int(properties.get('duration_ms', 500))
            duration_s = duration_ms / 1000.0
            
            logger.debug(f"等待 {duration_ms} 毫秒")
            time.sleep(duration_s)
            return True
            
        except Exception as e:
            logger.error(f"等待失败: {e}")
            return False
