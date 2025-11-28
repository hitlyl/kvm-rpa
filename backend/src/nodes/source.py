"""数据源节点

包含 RTSP 视频源、KVM 视频源节点。
KVM 视频源使用连接池管理器，支持多流程共享同一 KVM 连接。
"""
import time
import base64
from typing import Dict, Any
from loguru import logger

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from nodes.base import BaseNode, NodeConfig, NodePropertyDef, NodeActionDef
from nodes import register_node
from api.sse_service import send_debug


@register_node
class RTSPSourceNode(BaseNode):
    """RTSP 视频源节点"""
    
    @classmethod
    def get_config(cls) -> NodeConfig:
        return NodeConfig(
            type="rtsp_source",
            label="RTSP 视频源",
            category="source",
            icon="VideoCamera",
            color="#5470C6",
            description="从 RTSP 流获取视频帧",
            properties=[
                NodePropertyDef(
                    key="url",
                    label="RTSP 地址",
                    type="text",
                    required=True,
                    placeholder="rtsp://..."
                ),
                NodePropertyDef(
                    key="fps",
                    label="帧率",
                    type="number",
                    default=8
                ),
                NodePropertyDef(
                    key="resolution",
                    label="分辨率",
                    type="select",
                    default=[1280, 720],
                    options=[
                        {"label": "1280x720", "value": [1280, 720]},
                        {"label": "1920x1080", "value": [1920, 1080]}
                    ]
                )
            ]
        )
    
    def execute(self, context: Any, properties: Dict[str, Any]) -> Any:
        """执行 RTSP 采集"""
        if hasattr(context, 'system') and context.system and hasattr(context.system, 'rtsp_capture'):
            frame_data = context.system.rtsp_capture.get_frame(timeout=2.0)
            if frame_data:
                context.current_frame = frame_data['frame']
                context.current_timestamp = frame_data['timestamp']
                logger.debug(f"RTSP源获取帧成功: {frame_data.get('timestamp')}")
                return True
            else:
                logger.warning("RTSP源获取帧失败")
                return False
        else:
            logger.warning("RTSP采集器未初始化")
            return False


@register_node
class KVMSourceNode(BaseNode):
    """KVM 视频源节点
    
    使用 KVM 连接池管理器获取帧，多流程共享同一 KVM 连接。
    """
    
    @classmethod
    def get_config(cls) -> NodeConfig:
        return NodeConfig(
            type="kvm_source",
            label="KVM 视频源",
            category="source",
            icon="Monitor",
            color="#5470C6",
            description="从 KVM 设备获取视频帧",
            properties=[
                NodePropertyDef(
                    key="ip",
                    label="KVM IP",
                    type="text",
                    required=True,
                    placeholder="192.168.1.100"
                ),
                NodePropertyDef(
                    key="port",
                    label="端口",
                    type="number",
                    default=5900
                ),
                NodePropertyDef(
                    key="channel",
                    label="通道",
                    type="number",
                    default=0
                ),
                NodePropertyDef(
                    key="username",
                    label="用户名",
                    type="text",
                    required=True,
                    default="admin"
                ),
                NodePropertyDef(
                    key="password",
                    label="密码",
                    type="text",
                    required=True,
                    default="admin"
                )
            ],
            actions=[
                NodeActionDef(
                    key="get_preview",
                    label="获取预览图",
                    description="获取 KVM 当前画面截图",
                    returns="image"
                ),
                NodeActionDef(
                    key="test_connection",
                    label="测试连接",
                    description="测试 KVM 连接是否正常",
                    returns="json"
                )
            ]
        )
    
    def execute(self, context: Any, properties: Dict[str, Any]) -> Any:
        """执行 KVM 视频采集
        
        使用 KVM 连接池管理器获取或复用 KVM 连接。
        注意：只在首次执行时调用 get_or_create()，后续循环直接获取帧。
        """
        from kvm.kvm_manager import get_kvm_manager
        
        flow_id = getattr(context, 'flow_id', '')
        
        ip = properties.get('ip', '')
        port = int(properties.get('port', 5900))
        channel = int(properties.get('channel', 0))
        username = properties.get('username', 'admin')
        password = properties.get('password', 'admin')
        
        if not ip:
            error_msg = "KVM IP 地址未配置"
            logger.error(error_msg)
            if hasattr(context, 'last_error'):
                context.last_error = error_msg
            if flow_id:
                send_debug(flow_id, f"KVM: {error_msg}")
            return False
        
        try:
            kvm_manager = get_kvm_manager()
            kvm_key = f"{ip}:{port}:{channel}"
            
            # 检查是否已初始化 KVM 连接（避免每次循环都增加引用计数）
            if not getattr(context, '_kvm_initialized', False) or getattr(context, '_kvm_key', '') != kvm_key:
                # 首次执行或配置变更，获取或创建连接
                if flow_id:
                    send_debug(flow_id, f"KVM: 正在连接 {ip}:{port}...")
                    
                instance = kvm_manager.get_or_create(
                    ip=ip,
                    port=port,
                    channel=channel,
                    username=username,
                    password=password,
                    timeout=30.0
                )
                
                if not instance:
                    error_msg = f"无法连接到 KVM: {ip}:{port}"
                    logger.error(error_msg)
                    if hasattr(context, 'last_error'):
                        context.last_error = error_msg
                    if flow_id:
                        send_debug(flow_id, f"KVM: {error_msg}")
                    return False
                
                # 标记已初始化
                context._kvm_initialized = True
                context._kvm_key = kvm_key
                
                # 保存 KVM 配置到上下文（供后续节点使用）
                context.kvm_config = {
                    'ip': ip,
                    'port': port,
                    'channel': channel,
                    'username': username,
                    'password': password
                }
                logger.info(f"KVM 连接已初始化: {kvm_key}")
                if flow_id:
                    send_debug(flow_id, f"KVM: 连接成功 {ip}:{port}")
            
            # 获取最新帧（带自动重连）
            frame = kvm_manager.get_frame_with_reconnect(
                ip=ip,
                port=port,
                channel=channel,
                username=username,
                password=password,
                timeout=2.0
            )
            
            if frame is not None:
                context.current_frame = frame
                context.current_timestamp = time.time()
                logger.debug(f"KVM 获取帧成功: {ip}:{port}, shape={frame.shape}")
                return True
            else:
                error_msg = f"KVM 获取帧失败: {ip}:{port}"
                logger.warning(error_msg)
                if hasattr(context, 'last_error'):
                    context.last_error = error_msg
                if flow_id:
                    send_debug(flow_id, f"KVM: 获取帧失败，可能需要重连")
                return False
                
        except Exception as e:
            error_msg = f"KVM 视频采集异常: {e}"
            logger.error(error_msg)
            if hasattr(context, 'last_error'):
                context.last_error = error_msg
            if flow_id:
                send_debug(flow_id, f"KVM: 异常 - {str(e)}")
            return False
    
    def execute_action(self, action: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """执行节点交互方法
        
        Args:
            action: 交互方法标识
            properties: 节点属性值
            
        Returns:
            执行结果
        """
        if action == "get_preview":
            return self._action_get_preview(properties)
        elif action == "test_connection":
            return self._action_test_connection(properties)
        else:
            return {
                "success": False,
                "type": "none",
                "error": f"不支持的交互方法: {action}"
            }
    
    def _action_get_preview(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """获取 KVM 预览图"""
        from kvm.kvm_manager import get_kvm_manager
        
        ip = properties.get('ip', '')
        port = int(properties.get('port', 5900))
        channel = int(properties.get('channel', 0))
        username = properties.get('username', 'admin')
        password = properties.get('password', 'admin')
        
        if not ip:
            return {
                "success": False,
                "type": "image",
                "error": "KVM IP 地址未配置"
            }
        
        try:
            kvm_manager = get_kvm_manager()
            
            # 获取或创建连接
            instance = kvm_manager.get_or_create(
                ip=ip,
                port=port,
                channel=channel,
                username=username,
                password=password,
                timeout=30.0
            )
            
            if not instance:
                return {
                    "success": False,
                    "type": "image",
                    "error": f"无法连接到 KVM: {ip}:{port}"
                }
            
            # 获取帧
            frame = kvm_manager.get_frame(ip, port, channel, timeout=3.0)
            
            if frame is None:
                return {
                    "success": False,
                    "type": "image",
                    "error": "获取帧失败"
                }
            
            # 转换为 Base64
            if CV2_AVAILABLE:
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                image_base64 = base64.b64encode(buffer).decode('utf-8')
                
                return {
                    "success": True,
                    "type": "image",
                    "data": {
                        "format": "jpeg",
                        "base64": image_base64,
                        "width": frame.shape[1],
                        "height": frame.shape[0]
                    }
                }
            else:
                return {
                    "success": False,
                    "type": "image",
                    "error": "OpenCV 未安装，无法编码图片"
                }
                
        except Exception as e:
            logger.error(f"获取 KVM 预览图失败: {e}")
            return {
                "success": False,
                "type": "image",
                "error": str(e)
            }
    
    def _action_test_connection(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """测试 KVM 连接"""
        from kvm.kvm_manager import get_kvm_manager
        
        ip = properties.get('ip', '')
        port = int(properties.get('port', 5900))
        channel = int(properties.get('channel', 0))
        username = properties.get('username', 'admin')
        password = properties.get('password', 'admin')
        
        if not ip:
            return {
                "success": False,
                "type": "json",
                "error": "KVM IP 地址未配置"
            }
        
        try:
            kvm_manager = get_kvm_manager()
            
            start_time = time.time()
            instance = kvm_manager.get_or_create(
                ip=ip,
                port=port,
                channel=channel,
                username=username,
                password=password,
                timeout=10.0
            )
            connect_time = time.time() - start_time
            
            if instance and instance.connected:
                return {
                    "success": True,
                    "type": "json",
                    "data": {
                        "connected": True,
                        "connect_time_ms": int(connect_time * 1000),
                        "frame_width": instance.frame_width,
                        "frame_height": instance.frame_height,
                        "has_frame": instance.last_frame is not None
                    }
                }
            else:
                return {
                    "success": False,
                    "type": "json",
                    "data": {
                        "connected": False,
                        "connect_time_ms": int(connect_time * 1000)
                    },
                    "error": "连接失败"
                }
                
        except Exception as e:
            logger.error(f"测试 KVM 连接失败: {e}")
            return {
                "success": False,
                "type": "json",
                "error": str(e)
            }
