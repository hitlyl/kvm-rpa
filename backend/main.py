"""KVM RPA 系统主程序 - 流程管理版本

基于流程的 RPA 系统，整合 HTTP API 服务器。
所有处理模块（YOLO、OCR、视频源等）由流程节点按需创建。
支持集成前端静态文件服务。
"""
import sys
import signal
import time
import threading
from pathlib import Path
from typing import Dict, Any, Optional

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.config import get_config_manager
from monitoring.logger import setup_logger
from monitoring.metrics import get_metrics_collector, start_metrics_server
from services.flow_service import FlowService
from api.http_server import HTTPAPIServer
from engine.graph_executor import GraphExecutor
from loguru import logger
import uvicorn


class KVMRPASystem:
    """KVM RPA 系统主类
    
    基于流程的 RPA 系统，所有处理模块由节点按需创建。
    """
    
    def __init__(self, config_path: str = None):
        """初始化系统
        
        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        self.config_manager = get_config_manager()
        if config_path:
            self.config_manager.config_path = config_path
            self.config_manager.reload()
        
        self.config = self.config_manager.config
        
        # 初始化日志
        setup_logger(
            level=self.config.logging.level,
            console=self.config.logging.console,
            file_enabled=self.config.logging.file,
            file_path=self.config.logging.file_path,
            rotation=self.config.logging.rotation,
            retention=self.config.logging.retention
        )
        
        logger.info("=" * 60)
        logger.info("KVM RPA 系统启动 - 流程管理版本")
        logger.info("=" * 60)
        
        # 初始化监控
        self.metrics_collector = get_metrics_collector()
        if self.config.monitoring.enabled:
            start_metrics_server(self.config.monitoring.prometheus_port)
        
        # 流程管理
        self.flow_service: Optional[FlowService] = None
        self.flow_executor: Optional[GraphExecutor] = None
        self.active_flows: Dict[str, Any] = {}  # 当前活跃的流程
        
        # HTTP API 服务器
        self.http_server: Optional[HTTPAPIServer] = None
        self.api_thread: Optional[threading.Thread] = None
        
        # 运行状态
        self.is_running = False
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理函数（Ctrl+C 优雅退出）"""
        logger.warning(f"收到信号 {signum}，准备退出...")
        self.stop()
        sys.exit(0)
    
    def start(self) -> None:
        """启动系统"""
        try:
            # 初始化流程管理
            logger.info("初始化流程管理...")
            self._init_flow_management()
            
            # 启动 HTTP API 服务器
            logger.info("启动 HTTP API 服务器...")
            self._start_api_server()
            
            # 可选：自动加载并执行流程
            if self.config.flows.auto_load:
                logger.info("加载流程...")
                self._load_flows()
                
                if self.config.flows.auto_execute:
                    logger.info("执行流程...")
                    self._execute_flows()
            
            self.is_running = True
            logger.success("系统启动成功")
            
            # 保持主线程运行
            self._keep_running()
            
        except Exception as e:
            logger.exception(f"系统启动失败: {e}")
            self.stop()
    
    def _init_flow_management(self) -> None:
        """初始化流程管理"""
        # 创建流程服务
        flows_dir = self.config.flows.directory
        self.flow_service = FlowService(flows_dir)
        
        # 创建流程执行器
        self.flow_executor = GraphExecutor(self)
        
        logger.info(f"流程管理已初始化，流程目录: {flows_dir}")
    
    def _start_api_server(self) -> None:
        """启动 HTTP API 服务器（支持静态文件服务）"""
        from fastapi.staticfiles import StaticFiles
        from fastapi.responses import FileResponse
        
        # 创建 HTTP API 服务器
        self.http_server = HTTPAPIServer(system_instance=self)
        app = self.http_server.get_app()
        
        # 静态文件目录（如果存在则挂载）
        static_dir = Path(__file__).parent / "static"
        
        if static_dir.exists():
            logger.info(f"挂载静态文件服务: {static_dir}")
            
            # 挂载 assets 目录
            assets_dir = static_dir / "assets"
            if assets_dir.exists():
                app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
            
            # 添加根路径处理，返回 index.html
            @app.get("/")
            async def read_root():
                index_file = static_dir / "index.html"
                if index_file.exists():
                    return FileResponse(str(index_file))
                return {"message": "KVM-RPA System", "docs": "/docs"}
            
            # 处理其他前端路由（SPA）
            @app.get("/{full_path:path}")
            async def catch_all(full_path: str):
                # 如果是 API 路径，跳过
                if full_path.startswith("api/") or full_path.startswith("ws/") or full_path.startswith("health"):
                    return {"error": "Not found"}
                
                # 检查文件是否存在
                file_path = static_dir / full_path
                if file_path.is_file():
                    return FileResponse(str(file_path))
                
                # 否则返回 index.html（SPA 路由）
                index_file = static_dir / "index.html"
                if index_file.exists():
                    return FileResponse(str(index_file))
                
                return {"error": "Not found"}
            
            logger.info("前端静态文件服务已启用")
        else:
            logger.info("未找到静态文件目录，仅提供 API 服务")
        
        # 在独立线程中运行 API 服务器
        host = self.config.api.host
        port = self.config.api.port
        
        def run_server():
            uvicorn.run(app, host=host, port=port, log_level="info")
        
        self.api_thread = threading.Thread(target=run_server, daemon=True)
        self.api_thread.start()
        
        logger.info(f"HTTP API 服务器已启动: http://{host}:{port}")
        logger.info(f"API 文档: http://{host}:{port}/docs")
        if static_dir.exists():
            logger.info(f"前端界面: http://{host}:{port}/")
    
    def _load_flows(self) -> None:
        """加载流程"""
        flows = self.flow_service.list_flows()
        
        if not flows:
            logger.warning("未找到任何流程文件")
            logger.info("可以通过 API 创建流程：POST /api/flows")
            return
        
        logger.info(f"找到 {len(flows)} 个流程")
    
    def _execute_flows(self) -> None:
        """执行所有流程"""
        flows = self.flow_service.list_flows()
        
        for flow_info in flows:
            flow_id = flow_info['id']
            flow = self.flow_service.get_flow(flow_id)
            
            if flow:
                logger.info(f"准备执行流程: {flow.name}")
                self.flow_executor.execute_flow(flow)
                self.active_flows[flow_id] = {
                    'flow': flow,
                    'status': 'running',
                    'start_time': time.time()
                }
    
    def execute_flow_by_id(self, flow_id: str) -> bool:
        """通过ID执行指定流程
        
        Args:
            flow_id: 流程ID
            
        Returns:
            bool: 是否成功启动
        """
        flow = self.flow_service.get_flow(flow_id)
        if not flow:
            logger.error(f"流程不存在: {flow_id}")
            return False
        
        logger.info(f"执行流程: {flow.name}")
        result = self.flow_executor.execute_flow(flow)
        
        self.active_flows[flow_id] = {
            'flow': flow,
            'status': 'completed' if result else 'failed',
            'start_time': time.time()
        }
        
        return result
    
    def _keep_running(self) -> None:
        """保持主线程运行"""
        logger.info("系统运行中，按 Ctrl+C 停止...")
        
        try:
            while self.is_running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("收到中断信号")
    
    def stop(self) -> None:
        """停止系统"""
        if not self.is_running:
            return
        
        logger.info("正在停止系统...")
        self.is_running = False
        
        # 停止活跃流程
        for flow_id, flow_info in self.active_flows.items():
            logger.info(f"停止流程: {flow_info['flow'].name}")
        
        logger.info("系统已停止")


def main():
    """主入口函数"""
    # 可选：从命令行参数读取配置文件路径
    config_path = None
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
        logger.info(f"使用配置文件: {config_path}")
    
    # 创建并启动系统
    system = KVMRPASystem(config_path=config_path)
    system.start()


if __name__ == "__main__":
    main()
