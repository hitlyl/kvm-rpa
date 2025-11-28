"""图流程执行器

负责执行基于节点和连线的图结构流程。
支持异步执行和循环模式，与 FlowRunContext 配合使用。
节点执行失败时自动停止流程并返回错误信息。
支持 SSE 消息发送。
"""
import asyncio
import time
from typing import Dict, List, Any, Optional, Union, Tuple
from loguru import logger

from nodes import get_node_class
from api.sse_service import send_node_start, send_node_complete, send_node_error


class AsyncGraphExecutor:
    """异步图流程执行器
    
    支持异步节点执行和流程循环。
    与 FlowRunContext 配合使用，共享状态和缓存。
    """

    def __init__(self, context):
        """初始化异步图执行器
        
        Args:
            context: FlowRunContext 流程运行上下文
        """
        self.context = context
        self.is_running = False

    async def execute_once(self, flow_data: Dict[str, Any]) -> bool:
        """执行一轮流程
        
        从数据源节点开始，按拓扑顺序执行所有节点。
        
        Args:
            flow_data: 流程数据（包含 nodes 和 edges）
            
        Returns:
            bool: 执行是否成功
        """
        success, _ = await self.execute_once_with_error(flow_data)
        return success

    async def execute_once_with_error(self, flow_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """执行一轮流程（返回错误信息）
        
        从数据源节点开始，按拓扑顺序执行所有节点。
        任意节点执行失败将停止流程。
        
        Args:
            flow_data: 流程数据（包含 nodes 和 edges）
            
        Returns:
            Tuple[bool, Optional[str]]: (执行是否成功, 错误信息)
        """
        try:
            self.is_running = True
            
            # 获取节点和边
            nodes_data = flow_data.get('nodes', [])
            edges_data = flow_data.get('edges', [])
            
            if not nodes_data:
                return False, "流程没有节点"
            
            # 构建节点字典和邻接表
            nodes = {node['id']: node for node in nodes_data}
            adj_list = {node_id: [] for node_id in nodes}
            in_degree = {node_id: 0 for node_id in nodes}
            
            for edge in edges_data:
                source = edge.get('source')
                target = edge.get('target')
                if source and target and source in nodes and target in nodes:
                    adj_list[source].append({
                        'target': target,
                        'properties': edge.get('properties', {})
                    })
                    in_degree[target] += 1
            
            # 查找起始节点（入度为0的节点）
            start_nodes = [node_id for node_id, degree in in_degree.items() if degree == 0]
            
            if not start_nodes:
                return False, "未找到起始节点"
            
            # 使用队列按拓扑顺序执行
            queue = start_nodes[:]
            executed = set()
            
            while queue and self.is_running:
                # 检查停止请求
                if hasattr(self.context, 'stop_requested') and self.context.stop_requested:
                    logger.info("流程执行被停止")
                    return False, "用户停止"
                
                # 检查暂停请求
                while hasattr(self.context, 'pause_requested') and self.context.pause_requested:
                    if hasattr(self.context, 'stop_requested') and self.context.stop_requested:
                        return False, "用户停止"
                    await asyncio.sleep(0.1)
                
                current_node_id = queue.pop(0)
                
                # 避免重复执行
                if current_node_id in executed:
                    continue
                
                current_node = nodes[current_node_id]
                node_type = current_node.get('type', 'unknown')
                # 确保 node_label 是字符串
                node_label = current_node.get('label') or current_node.get('name') or node_type or current_node_id
                if not isinstance(node_label, str):
                    node_label = str(node_label) if node_label else current_node_id
                
                # 更新上下文中的当前节点信息
                self.context.current_node_id = current_node_id
                if hasattr(self.context, 'current_node_label'):
                    self.context.current_node_label = node_label
                if hasattr(self.context, 'current_node_type'):
                    self.context.current_node_type = node_type
                
                logger.debug(f"执行节点: {node_label} ({node_type})")
                
                # 发送节点开始 SSE 消息
                flow_id = getattr(self.context, 'flow_id', '')
                if flow_id:
                    send_node_start(flow_id, current_node_id, node_label, node_type)
                
                # 执行节点
                node_start_time = time.time()
                result, error_msg = await self._execute_node_with_error(current_node)
                node_duration_ms = (time.time() - node_start_time) * 1000
                
                executed.add(current_node_id)
                
                if hasattr(self.context, 'total_node_executions'):
                    self.context.total_node_executions += 1
                
                # 记录执行日志
                if hasattr(self.context, 'log_node_execution'):
                    self.context.log_node_execution(
                        current_node_id, node_label, node_type,
                        success=(result is not False),
                        error=error_msg
                    )
                
                # 条件节点返回 True/False 是正常的逻辑结果，不是执行失败
                # 只有非条件节点返回 False 才算执行失败
                is_condition_node = node_type == 'condition'
                
                # 如果节点执行失败，停止流程（条件节点除外）
                if result is False and not is_condition_node:
                    error_info = error_msg or f"节点 [{node_label}] 执行失败"
                    
                    # 发送节点错误 SSE 消息
                    if flow_id:
                        send_node_error(flow_id, current_node_id, node_label, node_type, error_info)
                    
                    logger.error(f"节点执行失败，停止流程: {error_info}")
                    return False, error_info
                
                # 发送节点完成 SSE 消息
                if flow_id:
                    # 条件节点时包含结果信息
                    extra_data = {'condition_result': result} if is_condition_node else None
                    send_node_complete(
                        flow_id, current_node_id, node_label, node_type,
                        success=True, duration_ms=node_duration_ms,
                        extra_data=extra_data
                    )
                
                # 确定下一个节点
                next_nodes_added = False
                for edge_info in adj_list[current_node_id]:
                    target_id = edge_info['target']
                    edge_props = edge_info['properties']
                    
                    # 处理条件分支
                    if is_condition_node:
                        branch = edge_props.get('branch', '').lower()
                        result_str = str(result).lower()
                        
                        # 匹配分支
                        should_follow = (
                            branch == result_str or 
                            (branch == 'true' and result) or 
                            (branch == 'false' and not result)
                        )
                        
                        if should_follow:
                            if target_id not in executed:
                                queue.append(target_id)
                                next_nodes_added = True
                                logger.debug(f"条件分支: {node_label} -> {branch} 分支")
                    else:
                        # 非条件节点，直接添加后继
                        if target_id not in executed:
                            queue.append(target_id)
                            next_nodes_added = True
                
                # 如果条件节点没有匹配到任何分支，记录警告
                if is_condition_node and not next_nodes_added:
                    logger.warning(f"条件节点 [{node_label}] 结果为 {result}，但没有匹配的分支连线")
                
                # 短暂让出控制权
                await asyncio.sleep(0)
            
            return True, None
            
        except Exception as e:
            logger.exception(f"流程执行异常: {e}")
            return False, str(e)
        finally:
            self.is_running = False

    async def _execute_node_with_error(self, node: Dict[str, Any]) -> Tuple[Any, Optional[str]]:
        """执行单个节点（返回错误信息）
        
        Args:
            node: 节点数据
            
        Returns:
            Tuple[Any, Optional[str]]: (节点执行结果, 错误信息)
        """
        node_type = node.get('type', 'unknown')
        node_id = node.get('id', 'unknown')
        # 确保 node_label 是字符串
        node_label = node.get('label') or node.get('name') or node_type or node_id
        if not isinstance(node_label, str):
            node_label = str(node_label) if node_label else node_id
        node_class = get_node_class(node_type)
        
        if not node_class:
            error_msg = f"未知的节点类型: {node_type}"
            logger.warning(error_msg)
            return True, None  # 未知类型跳过，不算失败
        
        try:
            # 创建节点实例
            node_instance = node_class()
            properties = node.get('properties', {})
            
            # 设置当前节点 ID 到上下文
            self.context.current_node_id = node_id
            
            # 验证参数
            is_valid, errors = node_instance.validate(properties)
            if not is_valid:
                error_msg = f"节点 [{node_label}] 参数验证失败: {errors}"
                logger.error(error_msg)
                return False, error_msg
            
            # 执行节点（支持异步和同步）
            if asyncio.iscoroutinefunction(node_instance.execute):
                result = await node_instance.execute(self.context, properties)
            else:
                # 同步节点在线程池中执行，避免阻塞事件循环
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    node_instance.execute,
                    self.context,
                    properties
                )
            
            logger.debug(f"节点执行完成 [{node_label}]: {result}")
            
            if result is False:
                # 尝试获取上下文中的错误信息
                error_msg = None
                if hasattr(self.context, 'last_error') and self.context.last_error:
                    error_msg = self.context.last_error
                else:
                    error_msg = f"节点 [{node_label}] 执行返回失败"
                return False, error_msg
            
            return result, None
            
        except Exception as e:
            error_msg = f"节点 [{node_label}] 执行异常: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    async def _execute_node(self, node: Dict[str, Any]) -> Any:
        """执行单个节点（兼容旧接口）"""
        result, _ = await self._execute_node_with_error(node)
        return result


# 保留旧的同步执行器以兼容
class GraphExecutor:
    """同步图流程执行器（兼容旧代码）"""

    def __init__(self, system_instance=None):
        """初始化图执行器"""
        self.system = system_instance
        self.is_running = False
        self.current_flow_id = None

    def execute_flow(self, flow_data: Any) -> bool:
        """执行流程（同步版本，兼容旧接口）"""
        try:
            self.is_running = True
            
            if hasattr(flow_data, 'model_dump'):
                flow = flow_data.model_dump()
            else:
                flow = flow_data
                
            self.current_flow_id = flow.get('id')
            logger.info(f"开始执行图流程: {flow.get('name')}")
            
            from engine.context import ExecutionContext
            context = ExecutionContext()
            context.system = self.system
            
            nodes = {node['id']: node for node in flow.get('nodes', [])}
            edges = flow.get('edges', [])
            
            adj_list = {node_id: [] for node_id in nodes}
            in_degree = {node_id: 0 for node_id in nodes}
            
            for edge in edges:
                source = edge.get('source')
                target = edge.get('target')
                if source and target:
                    adj_list[source].append({
                        'target': target,
                        'properties': edge.get('properties', {})
                    })
                    in_degree[target] += 1
            
            start_nodes = [node_id for node_id, degree in in_degree.items() if degree == 0]
            
            if not start_nodes:
                logger.warning("未找到起始节点")
                return False
            
            queue = start_nodes[:]
            
            while queue and self.is_running:
                current_node_id = queue.pop(0)
                current_node = nodes[current_node_id]
                
                logger.debug(f"执行节点: {current_node.get('label', current_node_id)}")
                
                result = self._execute_node_sync(current_node, context)
                
                if result is False:
                    logger.error(f"节点执行失败: {current_node_id}")
                    return False
                
                for edge_info in adj_list[current_node_id]:
                    target_id = edge_info['target']
                    edge_props = edge_info['properties']
                    
                    if current_node['type'] == 'condition':
                        branch = edge_props.get('branch', '').lower()
                        if str(result).lower() == branch:
                            queue.append(target_id)
                    else:
                        queue.append(target_id)
            
            logger.success(f"图流程执行完成: {flow.get('name')}")
            return True
            
        except Exception as e:
            logger.exception(f"图流程执行异常: {e}")
            return False
        finally:
            self.is_running = False

    def _execute_node_sync(self, node: Dict[str, Any], context) -> Any:
        """同步执行单个节点"""
        node_type = node.get('type')
        node_id = node.get('id')
        node_class = get_node_class(node_type)
        
        if not node_class:
            logger.warning(f"未知的节点类型: {node_type}")
            return True
        
        try:
            node_instance = node_class()
            properties = node.get('properties', {})
            context.current_node_id = node_id
            
            is_valid, errors = node_instance.validate(properties)
            if not is_valid:
                logger.error(f"节点参数验证失败 [{node_type}]: {errors}")
                return False
            
            result = node_instance.execute(context, properties)
            return result
            
        except Exception as e:
            logger.error(f"节点执行异常 [{node_type}]: {e}")
            return False
