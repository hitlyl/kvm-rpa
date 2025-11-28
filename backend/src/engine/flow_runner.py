"""异步流程运行管理器

支持同时运行多个流程，每个流程在独立协程中循环执行。
流程启动时初始化模型（YOLO/OCR），执行时复用。
节点执行失败时流程自动停止并记录错误信息。
支持 SSE 实时消息推送。
"""
import asyncio
import threading
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from loguru import logger

from engine.context import ExecutionContext
from api.sse_service import (
    send_flow_start, send_flow_stop, send_flow_error,
    send_loop_start, send_loop_complete,
    send_node_start, send_node_complete, send_node_error,
    send_debug
)


class FlowStatus(str, Enum):
    """流程状态"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class FlowRunContext(ExecutionContext):
    """流程运行上下文
    
    扩展 ExecutionContext，增加流程运行控制和缓存。
    """
    # 流程信息
    flow_id: str = ""
    flow_name: str = ""
    
    # 运行控制
    stop_requested: bool = False
    pause_requested: bool = False
    
    # KVM 配置缓存（用于节点获取 KVM 实例）
    kvm_config: Optional[Dict[str, Any]] = None
    
    # 模型实例缓存
    yolo_detectors: Dict[str, Any] = field(default_factory=dict)
    ocr_engines: Dict[str, Any] = field(default_factory=dict)
    
    # 统计信息
    loop_count: int = 0
    total_node_executions: int = 0
    last_loop_time: float = 0.0
    start_time: float = 0.0
    
    # 当前节点信息
    current_node_id: Optional[str] = None
    current_node_label: Optional[str] = None
    current_node_type: Optional[str] = None
    
    # 节点执行历史（保留最近的执行记录）
    node_execution_log: List[Dict[str, Any]] = field(default_factory=list)
    
    # 错误信息
    last_error: Optional[str] = None
    last_error_node: Optional[str] = None
    
    # OCR 匹配结果（供后续节点使用）
    ocr_matched_results: List[Dict[str, Any]] = field(default_factory=list)
    ocr_target_found: bool = False
    matched_text_position: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """初始化父类"""
        super().__init__()
    
    def log_node_execution(self, node_id: str, node_label: str, node_type: str, 
                           success: bool, error: Optional[str] = None):
        """记录节点执行"""
        log_entry = {
            'node_id': node_id,
            'node_label': node_label,
            'node_type': node_type,
            'success': success,
            'error': error,
            'timestamp': datetime.now().isoformat()
        }
        self.node_execution_log.append(log_entry)
        
        # 只保留最近 50 条
        if len(self.node_execution_log) > 50:
            self.node_execution_log.pop(0)
        
        if not success:
            self.last_error = error
            self.last_error_node = node_label


@dataclass
class FlowRunState:
    """流程运行状态"""
    flow_id: str
    flow_name: str
    status: FlowStatus = FlowStatus.STOPPED
    context: Optional[FlowRunContext] = None
    task: Optional[asyncio.Task] = None
    error: Optional[str] = None
    error_node: Optional[str] = None
    
    # 统计
    loop_count: int = 0
    start_time: Optional[datetime] = None
    last_loop_time: Optional[datetime] = None


class FlowRunner:
    """异步流程运行管理器
    
    管理多个流程的并发运行，每个流程在独立协程中循环执行。
    """
    
    _instance: Optional['FlowRunner'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化流程运行管理器"""
        if self._initialized:
            return
        
        self._initialized = True
        self._flows: Dict[str, FlowRunState] = {}
        self._flows_lock = threading.Lock()
        
        # 事件循环
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
        self._running = False
        
        logger.info("流程运行管理器初始化完成")
    
    def _ensure_event_loop(self) -> None:
        """确保事件循环运行中"""
        if self._running and self._loop:
            return
        
        self._running = True
        self._loop_thread = threading.Thread(
            target=self._run_event_loop,
            daemon=True,
            name="FlowRunner-EventLoop"
        )
        self._loop_thread.start()
        
        # 等待事件循环就绪
        time.sleep(0.2)
        logger.debug("流程运行管理器事件循环已启动")
    
    def _run_event_loop(self) -> None:
        """事件循环线程"""
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()
        except Exception as e:
            logger.error(f"事件循环异常: {e}")
        finally:
            if self._loop:
                self._loop.close()
            logger.debug("流程运行管理器事件循环已退出")
    
    def start_flow(self, flow_data: Dict[str, Any]) -> bool:
        """启动流程循环执行
        
        Args:
            flow_data: 流程数据（包含 id, name, nodes, edges）
            
        Returns:
            是否成功启动
        """
        flow_id = flow_data.get('id')
        flow_name = flow_data.get('name', 'Unknown')
        
        if not flow_id:
            logger.error("流程数据缺少 id")
            return False
        
        with self._flows_lock:
            # 检查是否已在运行
            if flow_id in self._flows:
                state = self._flows[flow_id]
                if state.status == FlowStatus.RUNNING:
                    logger.warning(f"流程已在运行中: {flow_name} ({flow_id})")
                    return False
        
        self._ensure_event_loop()
        
        # 创建运行状态
        context = FlowRunContext(
            flow_id=flow_id,
            flow_name=flow_name,
            start_time=time.time()
        )
        
        state = FlowRunState(
            flow_id=flow_id,
            flow_name=flow_name,
            status=FlowStatus.RUNNING,
            context=context,
            start_time=datetime.now()
        )
        
        with self._flows_lock:
            self._flows[flow_id] = state
        
        # 在事件循环中启动任务
        future = asyncio.run_coroutine_threadsafe(
            self._run_flow_loop(flow_data, state),
            self._loop
        )
        
        logger.info(f"流程已启动: {flow_name} ({flow_id})")
        
        # 发送 SSE 消息
        send_flow_start(flow_id, flow_name)
        
        return True
    
    def stop_flow(self, flow_id: str) -> bool:
        """停止流程"""
        with self._flows_lock:
            state = self._flows.get(flow_id)
            if not state:
                logger.warning(f"流程不存在: {flow_id}")
                return False
            
            if state.status not in (FlowStatus.RUNNING, FlowStatus.PAUSED):
                logger.warning(f"流程未在运行: {flow_id}")
                return False
            
            # 设置停止请求
            if state.context:
                state.context.stop_requested = True
            
            state.status = FlowStatus.STOPPED
            
            # 发送 SSE 消息
            loop_count = state.context.loop_count if state.context else 0
            send_flow_stop(flow_id, state.flow_name, loop_count)
        
        logger.info(f"流程已请求停止: {flow_id}")
        return True
    
    def pause_flow(self, flow_id: str) -> bool:
        """暂停流程"""
        with self._flows_lock:
            state = self._flows.get(flow_id)
            if not state or state.status != FlowStatus.RUNNING:
                return False
            
            if state.context:
                state.context.pause_requested = True
            state.status = FlowStatus.PAUSED
        
        logger.info(f"流程已暂停: {flow_id}")
        return True
    
    def resume_flow(self, flow_id: str) -> bool:
        """恢复流程"""
        with self._flows_lock:
            state = self._flows.get(flow_id)
            if not state or state.status != FlowStatus.PAUSED:
                return False
            
            if state.context:
                state.context.pause_requested = False
            state.status = FlowStatus.RUNNING
        
        logger.info(f"流程已恢复: {flow_id}")
        return True
    
    def get_flow_status(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """获取流程状态"""
        with self._flows_lock:
            return self._get_flow_status_unlocked(flow_id)
    
    def _get_flow_status_unlocked(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """获取流程状态（无锁版本，供内部使用）"""
        state = self._flows.get(flow_id)
        if not state:
            return None
        
        context = state.context
        
        result = {
            'flow_id': state.flow_id,
            'flow_name': state.flow_name,
            'status': state.status.value,
            'loop_count': context.loop_count if context else 0,
            'total_node_executions': context.total_node_executions if context else 0,
            'start_time': state.start_time.isoformat() if state.start_time else None,
            'last_loop_time': state.last_loop_time.isoformat() if state.last_loop_time else None,
            'error': state.error,
            'error_node': state.error_node,
        }
        
        # 添加当前节点信息
        if context:
            result['current_node'] = {
                'id': context.current_node_id,
                'label': context.current_node_label,
                'type': context.current_node_type
            }
            result['last_error'] = context.last_error
            result['last_error_node'] = context.last_error_node
            # 最近的节点执行记录
            result['recent_executions'] = context.node_execution_log[-10:] if context.node_execution_log else []
        
        return result
    
    def get_all_running_flows(self) -> List[Dict[str, Any]]:
        """获取所有运行中的流程"""
        result = []
        with self._flows_lock:
            for flow_id, state in self._flows.items():
                if state.status == FlowStatus.RUNNING:
                    status = self._get_flow_status_unlocked(flow_id)
                    if status:
                        result.append(status)
        return result
    
    def get_all_flows_status(self) -> List[Dict[str, Any]]:
        """获取所有流程状态"""
        result = []
        with self._flows_lock:
            for flow_id in self._flows:
                status = self._get_flow_status_unlocked(flow_id)
                if status:
                    result.append(status)
        return result
    
    async def _run_flow_loop(self, flow_data: Dict[str, Any], state: FlowRunState) -> None:
        """流程循环执行协程"""
        from engine.graph_executor import AsyncGraphExecutor
        
        flow_id = state.flow_id
        flow_name = state.flow_name
        context = state.context
        
        logger.info(f"流程循环开始: {flow_name} ({flow_id})")
        
        try:
            # 提取 KVM 配置（如果有）
            self._extract_kvm_config(flow_data, context)
            
            # 初始化模型（在第一次循环前）
            await self._init_models(flow_data, context)
            
            # 创建执行器
            executor = AsyncGraphExecutor(context)
            
            # 循环执行
            while not context.stop_requested:
                loop_start = time.time()
                context.loop_count += 1
                
                logger.debug(f"流程 {flow_name} 开始第 {context.loop_count} 轮")
                
                # 发送循环开始 SSE 消息
                send_loop_start(flow_id, context.loop_count)
                
                # 执行一轮
                success, error_msg = await executor.execute_once_with_error(flow_data)
                
                # 更新统计
                context.last_loop_time = time.time()
                state.last_loop_time = datetime.now()
                state.loop_count = context.loop_count
                
                loop_duration = time.time() - loop_start
                
                # 如果执行失败，停止流程
                if not success:
                    error_info = error_msg or context.last_error or "节点执行失败"
                    state.error = error_info
                    state.error_node = context.last_error_node
                    state.status = FlowStatus.ERROR
                    
                    # 发送错误 SSE 消息
                    send_flow_error(flow_id, flow_name, error_info, context.last_error_node)
                    
                    logger.error(f"流程 {flow_name} 执行失败: {error_info}")
                    break
                
                # 发送循环完成 SSE 消息
                send_loop_complete(flow_id, context.loop_count, loop_duration * 1000)
                
                logger.debug(f"流程 {flow_name} 第 {context.loop_count} 轮完成, 耗时 {loop_duration:.2f}s")
                
                # 短暂休息，避免 CPU 占用过高
                await asyncio.sleep(0.1)
            
            if context.stop_requested:
                logger.info(f"流程循环结束（用户停止）: {flow_name} ({flow_id}), 共执行 {context.loop_count} 轮")
                send_flow_stop(flow_id, flow_name, context.loop_count)
            
        except asyncio.CancelledError:
            logger.info(f"流程被取消: {flow_name} ({flow_id})")
        except Exception as e:
            logger.exception(f"流程执行异常: {flow_name} ({flow_id}): {e}")
            state.status = FlowStatus.ERROR
            state.error = str(e)
        finally:
            # 清理资源
            await self._cleanup_flow(context)
            
            with self._flows_lock:
                if flow_id in self._flows:
                    if self._flows[flow_id].status != FlowStatus.ERROR:
                        self._flows[flow_id].status = FlowStatus.STOPPED
    
    def _extract_kvm_config(self, flow_data: Dict[str, Any], context: FlowRunContext) -> None:
        """从流程中提取 KVM 配置"""
        nodes = flow_data.get('nodes', [])
        
        for node in nodes:
            if node.get('type') == 'kvm_source':
                props = node.get('properties', {})
                context.kvm_config = {
                    'ip': props.get('ip', ''),
                    'port': int(props.get('port', 5900)),
                    'channel': int(props.get('channel', 0)),
                    'username': props.get('username', 'admin'),
                    'password': props.get('password', 'admin')
                }
                logger.debug(f"提取 KVM 配置: {context.kvm_config['ip']}:{context.kvm_config['port']}")
                break
    
    async def _init_models(self, flow_data: Dict[str, Any], context: FlowRunContext) -> None:
        """初始化模型（YOLO/OCR）"""
        nodes = flow_data.get('nodes', [])
        
        for node in nodes:
            node_type = node.get('type')
            node_id = node.get('id')
            props = node.get('properties', {})
            
            if node_type == 'yolo_detection':
                try:
                    from detection.yolo_detector import YOLODetector
                    
                    config_key = f"{node_id}_{props.get('model_path')}_{props.get('backend')}"
                    
                    if config_key not in context.yolo_detectors:
                        detector = YOLODetector(
                            model_path=props.get('model_path', 'models/yolov8n.bmodel'),
                            conf_threshold=float(props.get('conf_threshold', 0.25)),
                            iou_threshold=float(props.get('iou_threshold', 0.45)),
                            backend=props.get('backend', 'auto'),
                            dev_id=int(props.get('dev_id', 0))
                        )
                        context.yolo_detectors[config_key] = detector
                        logger.info(f"YOLO 检测器已初始化: {config_key}")
                except Exception as e:
                    logger.warning(f"初始化 YOLO 检测器失败: {e}")
            
            elif node_type == 'ocr_recognition':
                try:
                    from ocr.ocr_engine import OCREngine
                    
                    config_key = f"{node_id}_{props.get('backend')}_{props.get('det_model')}"
                    
                    if config_key not in context.ocr_engines:
                        engine = OCREngine(
                            lang=props.get('lang', ['ch', 'en']),
                            conf_threshold=float(props.get('conf_threshold', 0.6)),
                            use_angle_cls=props.get('use_angle_cls', True),
                            backend=props.get('backend', 'auto'),
                            det_model=props.get('det_model'),
                            rec_model=props.get('rec_model'),
                            cls_model=props.get('cls_model') or None,
                            dev_id=int(props.get('dev_id', 0))
                        )
                        context.ocr_engines[config_key] = engine
                        logger.info(f"OCR 引擎已初始化: {config_key}")
                except Exception as e:
                    logger.warning(f"初始化 OCR 引擎失败: {e}")
    
    async def _cleanup_flow(self, context: FlowRunContext) -> None:
        """清理流程资源"""
        try:
            if context.kvm_config:
                from kvm.kvm_manager import get_kvm_manager
                manager = get_kvm_manager()
                manager.release(
                    context.kvm_config['ip'],
                    context.kvm_config['port'],
                    context.kvm_config['channel']
                )
            
            context.yolo_detectors.clear()
            context.ocr_engines.clear()
            
            logger.debug(f"流程资源已清理: {context.flow_id}")
            
        except Exception as e:
            logger.error(f"清理流程资源失败: {e}")
    
    def shutdown(self) -> None:
        """关闭管理器，停止所有流程"""
        logger.info("正在关闭流程运行管理器...")
        
        with self._flows_lock:
            for flow_id, state in self._flows.items():
                if state.context:
                    state.context.stop_requested = True
        
        time.sleep(1)
        
        self._running = False
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        
        if self._loop_thread and self._loop_thread.is_alive():
            self._loop_thread.join(timeout=3.0)
        
        logger.info("流程运行管理器已关闭")


def get_flow_runner() -> FlowRunner:
    """获取流程运行管理器单例"""
    return FlowRunner()
