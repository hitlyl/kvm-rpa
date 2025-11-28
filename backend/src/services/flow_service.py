"""流程管理服务

负责流程的 CRUD 操作、验证、模板管理等。
"""
import os
import json
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from loguru import logger

from models.flow import Flow, FlowNode, FlowEdge


class FlowService:
    """流程管理服务"""
    
    def __init__(self, flows_dir: str = "flows"):
        """初始化流程服务
        
        Args:
            flows_dir: 流程存储目录
        """
        self.flows_dir = Path(flows_dir)
        self.flows_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"流程服务已初始化，存储目录: {self.flows_dir}")
    
    def list_flows(self) -> List[Dict[str, Any]]:
        """列出所有流程
        
        Returns:
            流程列表（简要信息）
        """
        flows = []
        
        for flow_file in self.flows_dir.glob("*.json"):
            try:
                with open(flow_file, 'r', encoding='utf-8') as f:
                    flow_data = json.load(f)
                    flows.append({
                        'id': flow_data.get('id'),
                        'name': flow_data.get('name'),
                        'description': flow_data.get('description', ''),
                        'version': flow_data.get('version', '1.0'),
                        'node_count': len(flow_data.get('nodes', [])),
                        'created_at': flow_data.get('created_at'),
                        'updated_at': flow_data.get('updated_at')
                    })
            except Exception as e:
                logger.error(f"读取流程文件失败 {flow_file}: {e}")
        
        # 按更新时间倒序排序
        flows.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        return flows
    
    def get_flow(self, flow_id: str) -> Optional[Flow]:
        """获取流程详情
        
        Args:
            flow_id: 流程 ID
            
        Returns:
            Flow 对象或 None
        """
        flow_file = self.flows_dir / f"{flow_id}.json"
        
        if not flow_file.exists():
            logger.warning(f"流程不存在: {flow_id}")
            return None
        
        try:
            with open(flow_file, 'r', encoding='utf-8') as f:
                flow_data = json.load(f)
                return Flow(**flow_data)
        except Exception as e:
            logger.error(f"加载流程失败 {flow_id}: {e}")
            return None
    
    def create_flow(self, flow_data: Dict[str, Any]) -> Flow:
        """创建新流程
        
        Args:
            flow_data: 流程数据
            
        Returns:
            Flow 对象
        """
        # 生成流程 ID
        if 'id' not in flow_data or not flow_data['id']:
            flow_data['id'] = str(uuid.uuid4())
        
        # 设置时间戳
        now = datetime.now().isoformat()
        flow_data['created_at'] = now
        flow_data['updated_at'] = now
        
        # 创建 Flow 对象
        flow = Flow(**flow_data)
        
        # 保存到文件
        self._save_flow(flow)
        
        logger.info(f"流程已创建: {flow.name} ({flow.id})")
        return flow
    
    def update_flow(self, flow_id: str, flow_data: Dict[str, Any]) -> Optional[Flow]:
        """更新流程
        
        Args:
            flow_id: 流程 ID
            flow_data: 更新的流程数据
            
        Returns:
            更新后的 Flow 对象或 None
        """
        # 确保 ID 一致
        flow_data['id'] = flow_id
        
        # 更新时间戳
        flow_data['updated_at'] = datetime.now().isoformat()
        
        # 保留原创建时间
        existing_flow = self.get_flow(flow_id)
        if existing_flow:
            flow_data['created_at'] = existing_flow.created_at
        
        # 创建 Flow 对象
        try:
            flow = Flow(**flow_data)
            self._save_flow(flow)
            logger.info(f"流程已更新: {flow.name} ({flow.id})")
            return flow
        except Exception as e:
            logger.error(f"更新流程失败 {flow_id}: {e}")
            return None
    
    def delete_flow(self, flow_id: str) -> bool:
        """删除流程
        
        Args:
            flow_id: 流程 ID
            
        Returns:
            bool: 是否成功删除
        """
        flow_file = self.flows_dir / f"{flow_id}.json"
        
        if not flow_file.exists():
            logger.warning(f"流程不存在: {flow_id}")
            return False
        
        try:
            flow_file.unlink()
            logger.info(f"流程已删除: {flow_id}")
            return True
        except Exception as e:
            logger.error(f"删除流程失败 {flow_id}: {e}")
            return False
    
    def validate_flow(self, flow: Flow) -> Tuple[bool, List[str]]:
        """验证流程
        
        Args:
            flow: Flow 对象
            
        Returns:
            (是否有效, 错误列表)
        """
        errors = []
        
        # 检查基本字段
        if not flow.name:
            errors.append("流程名称不能为空")
        
        if not flow.nodes or len(flow.nodes) == 0:
            errors.append("流程至少需要一个节点")
        
        # 检查节点 ID 唯一性
        node_ids = [node.id for node in flow.nodes]
        if len(node_ids) != len(set(node_ids)):
            errors.append("存在重复的节点 ID")
        
        # 检查连线有效性
        for edge in flow.edges:
            if edge.source not in node_ids:
                errors.append(f"连线 {edge.id} 的源节点 {edge.source} 不存在")
            if edge.target not in node_ids:
                errors.append(f"连线 {edge.id} 的目标节点 {edge.target} 不存在")
        
        # 检查循环依赖
        if self._has_cycle(flow):
            errors.append("流程存在循环依赖")
        
        # 检查孤立节点（没有输入也没有输出的节点）
        connected_nodes = set()
        for edge in flow.edges:
            connected_nodes.add(edge.source)
            connected_nodes.add(edge.target)
        
        isolated_nodes = [node.id for node in flow.nodes if node.id not in connected_nodes]
        if isolated_nodes and len(flow.nodes) > 1:
            logger.warning(f"存在孤立节点: {isolated_nodes}")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def _has_cycle(self, flow: Flow) -> bool:
        """检查流程是否存在循环依赖
        
        Args:
            flow: Flow 对象
            
        Returns:
            bool: 是否存在循环
        """
        # 构建邻接表
        graph = {node.id: [] for node in flow.nodes}
        for edge in flow.edges:
            graph[edge.source].append(edge.target)
        
        # DFS 检测环
        visited = set()
        rec_stack = set()
        
        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for neighbor in graph.get(node_id, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for node in flow.nodes:
            if node.id not in visited:
                if dfs(node.id):
                    return True
        
        return False
    
    def _save_flow(self, flow: Flow) -> None:
        """保存流程到文件
        
        Args:
            flow: Flow 对象
        """
        flow_file = self.flows_dir / f"{flow.id}.json"
        
        with open(flow_file, 'w', encoding='utf-8') as f:
            json.dump(flow.model_dump(), f, ensure_ascii=False, indent=2)
    
    def get_templates(self) -> List[Dict[str, Any]]:
        """获取流程模板
        
        Returns:
            模板列表
        """
        templates = [
            {
                'id': 'template_simple_click',
                'name': '简单点击流程',
                'description': '演示基本的 RTSP → OCR → 点击流程',
                'template': self._create_simple_click_template()
            },
            {
                'id': 'template_condition',
                'name': '条件分支示例',
                'description': '演示条件判断和分支执行',
                'template': self._create_condition_template()
            }
        ]
        return templates
    
    def _create_simple_click_template(self) -> Dict[str, Any]:
        """创建简单点击流程模板"""
        return {
            'name': '简单点击流程',
            'description': '从模板创建',
            'nodes': [
                {
                    'id': 'node_1',
                    'type': 'rtsp_source',
                    'label': 'RTSP 视频源',
                    'x': 100,
                    'y': 200,
                    'properties': {
                        'url': 'rtsp://localhost:554/stream',
                        'fps': 8,
                        'resolution': [1280, 720]
                    }
                },
                {
                    'id': 'node_2',
                    'type': 'ocr_recognition',
                    'label': 'OCR 识别',
                    'x': 300,
                    'y': 200,
                    'properties': {
                        'lang': ['ch', 'en'],
                        'conf_threshold': 0.6
                    }
                },
                {
                    'id': 'node_3',
                    'type': 'mouse_action',
                    'label': '鼠标点击',
                    'x': 500,
                    'y': 200,
                    'properties': {
                        'action_type': 'click',
                        'button': 'left',
                        'use_trigger_position': True
                    }
                }
            ],
            'edges': [
                {
                    'id': 'edge_1',
                    'source': 'node_1',
                    'target': 'node_2'
                },
                {
                    'id': 'edge_2',
                    'source': 'node_2',
                    'target': 'node_3'
                }
            ]
        }
    
    def _create_condition_template(self) -> Dict[str, Any]:
        """创建条件分支模板"""
        return {
            'name': '条件分支示例',
            'description': '从模板创建',
            'nodes': [
                {
                    'id': 'node_1',
                    'type': 'rtsp_source',
                    'label': 'RTSP 视频源',
                    'x': 100,
                    'y': 200,
                    'properties': {}
                },
                {
                    'id': 'node_2',
                    'type': 'condition',
                    'label': '条件判断',
                    'x': 300,
                    'y': 200,
                    'properties': {
                        'condition_type': 'expression',
                        'expression': '${count} > 5'
                    }
                },
                {
                    'id': 'node_3',
                    'type': 'log',
                    'label': '日志 - True',
                    'x': 500,
                    'y': 100,
                    'properties': {
                        'message': '条件为真',
                        'level': 'info'
                    }
                },
                {
                    'id': 'node_4',
                    'type': 'log',
                    'label': '日志 - False',
                    'x': 500,
                    'y': 300,
                    'properties': {
                        'message': '条件为假',
                        'level': 'warning'
                    }
                }
            ],
            'edges': [
                {
                    'id': 'edge_1',
                    'source': 'node_1',
                    'target': 'node_2'
                },
                {
                    'id': 'edge_2',
                    'source': 'node_2',
                    'target': 'node_3',
                    'properties': {'branch': 'true'}
                },
                {
                    'id': 'edge_3',
                    'source': 'node_2',
                    'target': 'node_4',
                    'properties': {'branch': 'false'}
                }
            ]
        }

