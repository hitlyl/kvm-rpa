"""WebSocket 服务模块

提供 WebSocket 接口，用于实时推送画面、检测结果和系统指标。
"""
import json
import asyncio
import base64
from typing import Set, Optional
import cv2
import numpy as np
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger


class WebSocketManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        """初始化连接管理器"""
        # 不同类型的连接
        self.frame_connections: Set[WebSocket] = set()
        self.inference_connections: Set[WebSocket] = set()
        self.metrics_connections: Set[WebSocket] = set()
        
        logger.info("WebSocket 管理器已初始化")
    
    async def connect(self, websocket: WebSocket, connection_type: str) -> None:
        """新连接
        
        Args:
            websocket: WebSocket 连接
            connection_type: 连接类型 (frame, inference, metrics)
        """
        await websocket.accept()
        
        if connection_type == "frame":
            self.frame_connections.add(websocket)
        elif connection_type == "inference":
            self.inference_connections.add(websocket)
        elif connection_type == "metrics":
            self.metrics_connections.add(websocket)
        
        logger.info(f"WebSocket 连接: {connection_type}, 当前连接数: {self._get_connection_count(connection_type)}")
    
    def disconnect(self, websocket: WebSocket, connection_type: str) -> None:
        """断开连接
        
        Args:
            websocket: WebSocket 连接
            connection_type: 连接类型
        """
        if connection_type == "frame":
            self.frame_connections.discard(websocket)
        elif connection_type == "inference":
            self.inference_connections.discard(websocket)
        elif connection_type == "metrics":
            self.metrics_connections.discard(websocket)
        
        logger.info(f"WebSocket 断开: {connection_type}, 当前连接数: {self._get_connection_count(connection_type)}")
    
    def _get_connection_count(self, connection_type: str) -> int:
        """获取指定类型的连接数"""
        if connection_type == "frame":
            return len(self.frame_connections)
        elif connection_type == "inference":
            return len(self.inference_connections)
        elif connection_type == "metrics":
            return len(self.metrics_connections)
        return 0
    
    async def broadcast_frame(self, frame: np.ndarray, quality: int = 80) -> None:
        """广播帧到所有帧连接
        
        Args:
            frame: 图像帧 (BGR 格式)
            quality: JPEG 质量 (1-100)
        """
        if not self.frame_connections:
            return
        
        try:
            # 编码为 JPEG
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # 构造消息
            message = {
                "type": "frame",
                "data": frame_base64,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            # 广播到所有连接
            disconnected = set()
            for connection in self.frame_connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"发送帧失败: {e}")
                    disconnected.add(connection)
            
            # 清理断开的连接
            for conn in disconnected:
                self.frame_connections.discard(conn)
                
        except Exception as e:
            logger.error(f"广播帧失败: {e}")
    
    async def broadcast_inference(
        self,
        detection_results: list,
        ocr_results: list
    ) -> None:
        """广播推理结果
        
        Args:
            detection_results: YOLO 检测结果
            ocr_results: OCR 识别结果
        """
        if not self.inference_connections:
            return
        
        try:
            message = {
                "type": "inference",
                "data": {
                    "detections": detection_results,
                    "ocr": ocr_results,
                    "detection_count": len(detection_results),
                    "ocr_count": len(ocr_results)
                },
                "timestamp": asyncio.get_event_loop().time()
            }
            
            disconnected = set()
            for connection in self.inference_connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"发送推理结果失败: {e}")
                    disconnected.add(connection)
            
            for conn in disconnected:
                self.inference_connections.discard(conn)
                
        except Exception as e:
            logger.error(f"广播推理结果失败: {e}")
    
    async def broadcast_metrics(self, metrics: dict) -> None:
        """广播系统指标
        
        Args:
            metrics: 指标字典
        """
        if not self.metrics_connections:
            return
        
        try:
            message = {
                "type": "metrics",
                "data": metrics,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            disconnected = set()
            for connection in self.metrics_connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"发送指标失败: {e}")
                    disconnected.add(connection)
            
            for conn in disconnected:
                self.metrics_connections.discard(conn)
                
        except Exception as e:
            logger.error(f"广播指标失败: {e}")
    
    def has_frame_clients(self) -> bool:
        """是否有帧连接客户端"""
        return len(self.frame_connections) > 0
    
    def has_inference_clients(self) -> bool:
        """是否有推理结果连接客户端"""
        return len(self.inference_connections) > 0
    
    def has_metrics_clients(self) -> bool:
        """是否有指标连接客户端"""
        return len(self.metrics_connections) > 0


class WebSocketServer:
    """WebSocket 服务器
    
    提供三个 WebSocket 端点：
    - /ws/frame: 实时画面流
    - /ws/inference: YOLO 与 OCR 结果
    - /ws/metrics: 性能指标
    """
    
    def __init__(self, system_instance=None):
        """初始化 WebSocket 服务器
        
        Args:
            system_instance: KVM RPA 系统实例
        """
        self.system = system_instance
        self.manager = WebSocketManager()
        
        logger.info("WebSocket 服务器已初始化")
    
    def register_routes(self, app) -> None:
        """注册 WebSocket 路由
        
        Args:
            app: FastAPI 应用实例
        """
        
        @app.websocket("/ws/frame")
        async def websocket_frame(websocket: WebSocket):
            """实时画面流 WebSocket"""
            await self.manager.connect(websocket, "frame")
            try:
                # 保持连接并接收客户端消息（如控制命令）
                while True:
                    try:
                        data = await websocket.receive_text()
                        # 处理客户端命令（如调整质量、暂停等）
                        command = json.loads(data)
                        logger.debug(f"收到帧客户端命令: {command}")
                    except WebSocketDisconnect:
                        break
                    except Exception as e:
                        logger.warning(f"处理帧客户端消息失败: {e}")
                        await asyncio.sleep(0.1)
            finally:
                self.manager.disconnect(websocket, "frame")
        
        @app.websocket("/ws/inference")
        async def websocket_inference(websocket: WebSocket):
            """推理结果 WebSocket"""
            await self.manager.connect(websocket, "inference")
            try:
                while True:
                    try:
                        data = await websocket.receive_text()
                        command = json.loads(data)
                        logger.debug(f"收到推理客户端命令: {command}")
                    except WebSocketDisconnect:
                        break
                    except Exception as e:
                        logger.warning(f"处理推理客户端消息失败: {e}")
                        await asyncio.sleep(0.1)
            finally:
                self.manager.disconnect(websocket, "inference")
        
        @app.websocket("/ws/metrics")
        async def websocket_metrics(websocket: WebSocket):
            """系统指标 WebSocket"""
            await self.manager.connect(websocket, "metrics")
            try:
                while True:
                    try:
                        data = await websocket.receive_text()
                        command = json.loads(data)
                        logger.debug(f"收到指标客户端命令: {command}")
                    except WebSocketDisconnect:
                        break
                    except Exception as e:
                        logger.warning(f"处理指标客户端消息失败: {e}")
                        await asyncio.sleep(0.1)
            finally:
                self.manager.disconnect(websocket, "metrics")
        
        logger.info("WebSocket 路由已注册")
    
    def get_manager(self) -> WebSocketManager:
        """获取连接管理器
        
        Returns:
            WebSocketManager: 管理器实例
        """
        return self.manager

