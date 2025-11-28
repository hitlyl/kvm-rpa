"""HTTP API 服务模块

基于 FastAPI 提供 REST API 接口，用于流程管理、配置管理等。
"""
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from loguru import logger


# ========== 请求/响应模型 ==========

class StandardResponse(BaseModel):
    """标准化响应模型"""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: str = Field(description="ok 或 error")
    message: str = Field(description="响应消息")
    data: Optional[Any] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ConfigUpdateRequest(BaseModel):
    """配置更新请求"""
    updates: Dict[str, Any] = Field(description="要更新的配置项")


# ========== HTTP API 服务器 ==========

class HTTPAPIServer:
    """HTTP API 服务器
    
    提供 REST API 接口用于系统管理和控制。
    """
    
    def __init__(self, system_instance=None):
        """初始化 API 服务器
        
        Args:
            system_instance: KVM RPA 系统实例
        """
        self.system = system_instance
        self.app = FastAPI(
            title="KVM RPA API",
            description="KVM RPA 系统 REST API - 基于流程的 RPA 系统",
            version="2.0.0"
        )
        # 保存系统实例到 app state
        self.app.state.system = self.system
        
        # 配置 CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
        
        # 注册路由
        self._register_routes()
        
        logger.info("HTTP API 服务器已初始化")
    
    def _register_routes(self) -> None:
        """注册 API 路由"""
        
        # 注册流程管理路由
        try:
            from api.flow_routes import flow_router
            self.app.include_router(flow_router)
            logger.info("流程管理路由已注册")
        except Exception as e:
            logger.warning(f"注册流程路由失败: {e}")
        
        # 注册节点管理路由
        try:
            from api.node_routes import node_router
            self.app.include_router(node_router)
            logger.info("节点管理路由已注册")
        except Exception as e:
            logger.warning(f"注册节点路由失败: {e}")
        
        # 注册 SSE 事件流路由
        try:
            from api.sse_routes import sse_router
            self.app.include_router(sse_router)
            logger.info("SSE 事件流路由已注册")
        except Exception as e:
            logger.warning(f"注册 SSE 路由失败: {e}")
        
        # ========== 健康检查 ==========
        
        @self.app.get("/health", tags=["System"])
        async def health_check():
            """健康检查"""
            return StandardResponse(
                status="ok",
                message="Service is healthy",
                data={"service": "kvm-rpa", "version": "2.0.0"}
            )
        
        # ========== 模型管理 ==========
        
        @self.app.post("/api/model/upload", tags=["Model"])
        async def upload_model(file: UploadFile = File(...)) -> StandardResponse:
            """上传模型文件"""
            try:
                from pathlib import Path
                import shutil
                
                # 保存模型文件
                model_dir = Path("models")
                model_dir.mkdir(exist_ok=True)
                
                model_path = model_dir / file.filename
                
                with open(model_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                logger.info(f"模型已上传: {model_path}")
                
                return StandardResponse(
                    status="ok",
                    message="Model uploaded successfully",
                    data={
                        "filename": file.filename,
                        "path": str(model_path)
                    }
                )
            except Exception as e:
                logger.error(f"上传模型失败: {e}")
                return StandardResponse(
                    status="error",
                    message=f"Failed to upload model: {str(e)}"
                )
        
        @self.app.get("/api/model/list", tags=["Model"])
        async def list_models() -> StandardResponse:
            """列出所有模型文件"""
            try:
                from pathlib import Path
                
                model_dir = Path("models")
                if not model_dir.exists():
                    return StandardResponse(
                        status="ok",
                        message="No models found",
                        data={"models": []}
                    )
                
                models = []
                for model_file in model_dir.iterdir():
                    if model_file.is_file():
                        models.append({
                            "name": model_file.name,
                            "path": str(model_file),
                            "size": model_file.stat().st_size,
                            "modified": datetime.fromtimestamp(
                                model_file.stat().st_mtime
                            ).isoformat()
                        })
                
                return StandardResponse(
                    status="ok",
                    message="Models listed",
                    data={"models": models, "count": len(models)}
                )
            except Exception as e:
                logger.error(f"列出模型失败: {e}")
                return StandardResponse(
                    status="error",
                    message=f"Failed to list models: {str(e)}"
                )
        
        # ========== 配置管理 ==========
        
        @self.app.get("/api/config", tags=["Config"])
        async def get_config() -> StandardResponse:
            """获取当前配置"""
            try:
                if self.system:
                    config_dict = self.system.config.model_dump()
                    return StandardResponse(
                        status="ok",
                        message="Configuration retrieved",
                        data=config_dict
                    )
                else:
                    return StandardResponse(
                        status="error",
                        message="System instance not available"
                    )
            except Exception as e:
                logger.error(f"获取配置失败: {e}")
                return StandardResponse(
                    status="error",
                    message=f"Failed to get config: {str(e)}"
                )
        
        @self.app.put("/api/config", tags=["Config"])
        async def update_config(request: ConfigUpdateRequest) -> StandardResponse:
            """更新配置"""
            try:
                if self.system:
                    self.system.config_manager.update(request.updates)
                    
                    logger.info(f"配置已更新: {list(request.updates.keys())}")
                    
                    return StandardResponse(
                        status="ok",
                        message="Configuration updated",
                        data={"updated_keys": list(request.updates.keys())}
                    )
                else:
                    return StandardResponse(
                        status="error",
                        message="System instance not available"
                    )
            except Exception as e:
                logger.error(f"更新配置失败: {e}")
                return StandardResponse(
                    status="error",
                    message=f"Failed to update config: {str(e)}"
                )
        
        # ========== 日志查询 ==========
        
        @self.app.get("/api/logs", tags=["Logs"])
        async def get_logs(
            lines: int = 100,
            level: Optional[str] = None
        ) -> StandardResponse:
            """查询日志"""
            try:
                from pathlib import Path
                
                log_file = Path(self.system.config.logging.file_path)
                
                if not log_file.exists():
                    return StandardResponse(
                        status="ok",
                        message="No logs found",
                        data={"logs": []}
                    )
                
                # 读取最后 N 行
                with open(log_file, 'r', encoding='utf-8') as f:
                    all_lines = f.readlines()
                    last_lines = all_lines[-lines:]
                
                # 级别过滤（如果指定）
                if level:
                    last_lines = [line for line in last_lines if level.upper() in line]
                
                return StandardResponse(
                    status="ok",
                    message="Logs retrieved",
                    data={"logs": last_lines, "count": len(last_lines)}
                )
            except Exception as e:
                logger.error(f"查询日志失败: {e}")
                return StandardResponse(
                    status="error",
                    message=f"Failed to get logs: {str(e)}"
                )
        
        # ========== 系统状态 ==========
        
        @self.app.get("/api/system/stats", tags=["System"])
        async def get_system_stats() -> StandardResponse:
            """获取系统统计信息"""
            try:
                if not self.system:
                    return StandardResponse(
                        status="error",
                        message="System instance not available"
                    )
                
                stats = {
                    'is_running': self.system.is_running,
                    'active_flows_count': len(self.system.active_flows),
                    'active_flows': []
                }
                
                # 活跃流程信息
                for flow_id, flow_info in self.system.active_flows.items():
                    stats['active_flows'].append({
                        'id': flow_id,
                        'name': flow_info['flow'].name,
                        'status': flow_info['status'],
                        'start_time': flow_info['start_time']
                    })
                
                return StandardResponse(
                    status="ok",
                    message="System statistics retrieved",
                    data=stats
                )
            except Exception as e:
                logger.error(f"获取系统统计失败: {e}")
                return StandardResponse(
                    status="error",
                    message=f"Failed to get system stats: {str(e)}"
                )
        
        # ========== 流程执行 ==========
        
        @self.app.post("/api/system/execute/{flow_id}", tags=["System"])
        async def execute_flow(
            flow_id: str,
            background_tasks: BackgroundTasks
        ) -> StandardResponse:
            """执行指定流程"""
            try:
                if not self.system:
                    return StandardResponse(
                        status="error",
                        message="System instance not available"
                    )
                
                # 在后台执行流程
                background_tasks.add_task(
                    self.system.execute_flow_by_id, flow_id
                )
                
                return StandardResponse(
                    status="ok",
                    message="Flow execution started",
                    data={"flow_id": flow_id}
                )
            except Exception as e:
                logger.error(f"执行流程失败: {e}")
                return StandardResponse(
                    status="error",
                    message=f"Failed to execute flow: {str(e)}"
                )
    
    def get_app(self) -> FastAPI:
        """获取 FastAPI 应用实例
        
        Returns:
            FastAPI: 应用实例
        """
        return self.app
