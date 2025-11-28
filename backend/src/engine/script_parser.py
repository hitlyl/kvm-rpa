"""脚本解析器模块

解析 YAML 格式的流程脚本，支持触发器、动作、条件判断、循环等。
"""
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import yaml
from loguru import logger


class ScriptParser:
    """脚本解析器
    
    解析 YAML 格式的 RPA 流程脚本。
    
    脚本格式示例:
    ```yaml
    name: "安装向导流程"
    description: "自动完成软件安装向导"
    version: "1.0"
    
    triggers:
      - type: ocr
        text_contains: "欢迎"
        min_confidence: 0.7
    
    variables:
      install_path: "C:\\Program Files\\MyApp"
      retry_count: 0
    
    actions:
      - type: ocr_check
        text: "下一步"
        timeout: 10
        on_success:
          - type: click
            target: trigger_bbox
          - type: wait
            duration: 1.0
      
      - type: conditional
        condition:
          variable: retry_count
          operator: "<"
          value: 3
        then:
          - type: input
            text: "${install_path}"
        else:
          - type: log
            message: "重试次数已达上限"
    ```
    """
    
    def __init__(self):
        """初始化脚本解析器"""
        pass
    
    def parse_file(self, script_path: str) -> Dict[str, Any]:
        """解析脚本文件
        
        Args:
            script_path: 脚本文件路径
            
        Returns:
            解析后的脚本字典
        """
        script_file = Path(script_path)
        
        if not script_file.exists():
            raise FileNotFoundError(f"脚本文件不存在: {script_path}")
        
        with open(script_file, 'r', encoding='utf-8') as f:
            script_dict = yaml.safe_load(f)
        
        logger.info(f"解析脚本文件: {script_path}")
        return self.parse_dict(script_dict)
    
    def parse_dict(self, script_dict: Dict[str, Any]) -> Dict[str, Any]:
        """解析脚本字典
        
        Args:
            script_dict: 脚本字典
            
        Returns:
            验证后的脚本字典
        """
        # 验证必需字段
        if 'name' not in script_dict:
            script_dict['name'] = 'Unnamed Script'
        
        if 'actions' not in script_dict:
            raise ValueError("脚本缺少 'actions' 字段")
        
        # 设置默认值
        script_dict.setdefault('description', '')
        script_dict.setdefault('version', '1.0')
        script_dict.setdefault('triggers', [])
        script_dict.setdefault('variables', {})
        script_dict.setdefault('on_error', 'stop')  # stop, continue, retry
        
        logger.info(f"脚本解析完成: {script_dict['name']} v{script_dict['version']}")
        return script_dict
    
    def parse_string(self, script_yaml: str) -> Dict[str, Any]:
        """解析 YAML 字符串
        
        Args:
            script_yaml: YAML 格式的脚本字符串
            
        Returns:
            解析后的脚本字典
        """
        script_dict = yaml.safe_load(script_yaml)
        return self.parse_dict(script_dict)
    
    def validate_script(self, script: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证脚本格式
        
        Args:
            script: 脚本字典
            
        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []
        
        # 检查必需字段
        if 'name' not in script:
            errors.append("缺少 'name' 字段")
        
        if 'actions' not in script:
            errors.append("缺少 'actions' 字段")
        elif not isinstance(script['actions'], list):
            errors.append("'actions' 必须是列表")
        elif len(script['actions']) == 0:
            errors.append("'actions' 不能为空")
        
        # 检查 triggers 格式
        if 'triggers' in script:
            if not isinstance(script['triggers'], list):
                errors.append("'triggers' 必须是列表")
            else:
                for i, trigger in enumerate(script['triggers']):
                    if 'type' not in trigger:
                        errors.append(f"trigger[{i}] 缺少 'type' 字段")
        
        # 检查 variables 格式
        if 'variables' in script:
            if not isinstance(script['variables'], dict):
                errors.append("'variables' 必须是字典")
        
        # 检查动作格式
        for i, action in enumerate(script.get('actions', [])):
            if not isinstance(action, dict):
                errors.append(f"action[{i}] 必须是字典")
                continue
            if 'type' not in action:
                errors.append(f"action[{i}] 缺少 'type' 字段")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def save_script(self, script: Dict[str, Any], output_path: str) -> None:
        """保存脚本到文件
        
        Args:
            script: 脚本字典
            output_path: 输出文件路径
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(script, f, allow_unicode=True, default_flow_style=False)
        
        logger.info(f"脚本已保存: {output_path}")

