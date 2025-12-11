#!/usr/bin/env python3
"""
KVM HTTP 代理服务

提供 HTTP 接口来控制 KVM 设备：
- /capture - 截取当前屏幕
- /mouse/move - 移动鼠标
- /mouse/click - 鼠标点击
- /key/send - 发送键盘事件
- /status - 获取连接状态

使用方法:
    python kvm_proxy.py --ip 192.168.0.100 --port 5900 --username admin --password 123456
"""

import argparse
import asyncio
import io
import logging
import os
import subprocess
import sys
import tempfile
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel

# 添加 python_client 路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from python_client import KVMClient

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# H.264 编码类型
ENCODING_H264 = 7


# ============ 请求模型 ============

class MouseMoveRequest(BaseModel):
    """鼠标移动请求"""
    x: int
    y: int


class MouseClickRequest(BaseModel):
    """鼠标点击请求"""
    x: int
    y: int
    button: str = "left"  # left, middle, right
    delay: float = 0.05  # 按下持续时间（秒）


class KeySendRequest(BaseModel):
    """键盘发送请求"""
    key_code: int
    action: str = "click"  # press, release, click


# ============ H.264 解码器 ============

def check_ffmpeg() -> bool:
    """检查 FFmpeg 是否可用"""
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


class H264Decoder:
    """H.264 解码器"""

    def __init__(self):
        self.ffmpeg_available = check_ffmpeg()
        self.temp_dir = tempfile.mkdtemp(prefix='kvm_proxy_')
        self.frame_index = 0
        self.sps: Optional[bytes] = None
        self.pps: Optional[bytes] = None
        self._executor: Optional[ThreadPoolExecutor] = None
        self.running = False

    def _get_nal_type(self, data: bytes) -> int:
        """获取 NAL 单元类型"""
        if len(data) < 1:
            return -1
        return data[0] & 0x1F

    def _find_start_codes(self, data: bytes) -> list:
        """查找所有 NAL 起始码位置"""
        positions = []
        i = 0
        while i < len(data) - 3:
            if data[i:i + 4] == b'\x00\x00\x00\x01':
                positions.append((i, 4))
                i += 4
            elif data[i:i + 3] == b'\x00\x00\x01':
                positions.append((i, 3))
                i += 3
            else:
                i += 1
        return positions

    def _extract_sps_pps(self, data: bytes):
        """提取 SPS/PPS"""
        start_codes = self._find_start_codes(data)
        for i, (pos, length) in enumerate(start_codes):
            nal_start = pos + length
            if i + 1 < len(start_codes):
                nal_end = start_codes[i + 1][0]
            else:
                nal_end = len(data)

            nal_data = data[nal_start:nal_end]
            if len(nal_data) < 1:
                continue

            nal_type = self._get_nal_type(nal_data)
            if nal_type == 7:
                self.sps = data[pos:nal_end]
            elif nal_type == 8:
                self.pps = data[pos:nal_end]

    def decode_to_jpeg(self, frame_data: bytes) -> Optional[bytes]:
        """解码 H.264 帧为 JPEG"""
        if not self.ffmpeg_available:
            return None

        try:
            self._extract_sps_pps(frame_data)

            if not self.sps or not self.pps:
                return None

            h264_data = bytearray()
            h264_data.extend(self.sps)
            h264_data.extend(self.pps)

            if not frame_data.startswith(b'\x00\x00\x00\x01') and not frame_data.startswith(b'\x00\x00\x01'):
                h264_data.extend(b'\x00\x00\x00\x01')
            h264_data.extend(frame_data)

            self.frame_index += 1
            output_file = os.path.join(self.temp_dir, f'frame_{self.frame_index}.jpg')

            cmd = [
                'ffmpeg', '-loglevel', 'error',
                '-f', 'h264', '-i', 'pipe:0',
                '-vframes', '1', '-f', 'image2', '-y', output_file
            ]

            result = subprocess.run(
                cmd, input=bytes(h264_data),
                capture_output=True, timeout=2
            )

            if result.returncode == 0 and os.path.exists(output_file):
                with open(output_file, 'rb') as f:
                    jpeg_data = f.read()
                os.remove(output_file)
                return jpeg_data

            return None

        except Exception as e:
            logger.debug(f"Decode error: {e}")
            return None

    async def decode_async(self, frame_data: bytes) -> Optional[bytes]:
        """异步解码"""
        if not self.running or not self._executor:
            return None

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self.decode_to_jpeg, frame_data)

    def start(self):
        """启动解码器"""
        self.running = True
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix='h264_decoder')
        logger.info("H264 解码器已启动")

    def stop(self):
        """停止解码器"""
        self.running = False
        if self._executor:
            self._executor.shutdown(wait=False)
            self._executor = None
        logger.info("H264 解码器已停止")

    def cleanup(self):
        """清理临时文件"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception:
            pass


# ============ KVM 代理管理器 ============

@dataclass
class KVMConfig:
    """KVM 连接配置"""
    ip: str
    port: int
    channel: int
    username: str
    password: str


class KVMProxyManager:
    """KVM 代理管理器"""

    def __init__(self, config: KVMConfig):
        self.config = config
        self.client: Optional[KVMClient] = None
        self.decoder = H264Decoder()

        # 视频帧状态
        self.frame_count = 0
        self.video_width = 0
        self.video_height = 0
        self.last_frame_data: Optional[bytes] = None
        self.last_jpeg: Optional[bytes] = None
        self.h264_buffer = bytearray()
        self.has_keyframe = False

        # 锁
        self._frame_lock = asyncio.Lock()

    def _on_video_frame(self, frame_data: bytes, width: int, height: int, encoding_type: int):
        """视频帧回调（非阻塞）"""
        self.frame_count += 1
        self.video_width = width
        self.video_height = height

        if encoding_type == ENCODING_H264:
            self._process_h264_frame(frame_data)

    def _process_h264_frame(self, frame_data: bytes):
        """处理 H.264 帧"""
        if len(frame_data) > 4:
            nal_offset = 0
            if frame_data[:4] == b'\x00\x00\x00\x01':
                nal_offset = 4
            elif frame_data[:3] == b'\x00\x00\x01':
                nal_offset = 3

            if nal_offset > 0 and len(frame_data) > nal_offset:
                nal_type = frame_data[nal_offset] & 0x1F
                if nal_type in (5, 7, 8):
                    self.has_keyframe = True
                    if nal_type == 7:
                        self.h264_buffer = bytearray()

        self.h264_buffer.extend(frame_data)

        if self.has_keyframe:
            self.last_frame_data = bytes(self.h264_buffer)

    async def connect(self) -> bool:
        """连接到 KVM"""
        if self.client and self.client.is_connected():
            return True

        self.client = KVMClient()
        self.client.set_video_callback(self._on_video_frame)
        self.decoder.start()

        try:
            await self.client.connect(
                ip=self.config.ip,
                port=self.config.port,
                channel=self.config.channel,
                username=self.config.username,
                password=self.config.password,
                timeout=30.0
            )

            # 设置鼠标为绝对坐标模式
            self.client.set_mouse_type(1)

            logger.info(f"已连接到 KVM {self.config.ip}:{self.config.port}")
            return True

        except Exception as e:
            logger.error(f"连接 KVM 失败: {e}")
            self.decoder.stop()
            return False

    async def disconnect(self):
        """断开连接"""
        if self.client:
            await self.client.disconnect()
            self.client = None
        self.decoder.stop()
        self.decoder.cleanup()
        logger.info("已断开 KVM 连接")

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.client is not None and self.client.is_connected()

    async def capture(self) -> Optional[bytes]:
        """截取当前屏幕，返回 JPEG 数据"""
        if not self.is_connected():
            return None

        if self.last_frame_data is None:
            return None

        # 解码最新帧
        jpeg_data = await self.decoder.decode_async(self.last_frame_data)
        if jpeg_data:
            self.last_jpeg = jpeg_data

        return self.last_jpeg

    def mouse_move(self, x: int, y: int):
        """移动鼠标"""
        if not self.is_connected():
            return False

        self.client.send_mouse_event_raw(x, y, 0)
        return True

    async def mouse_click(self, x: int, y: int, button: str = "left", delay: float = 0.05):
        """
        鼠标点击

        Args:
            x: X 坐标
            y: Y 坐标
            button: 按钮 (left, middle, right)
            delay: 按下和释放之间的延时（秒），默认 50ms
        """
        if not self.is_connected():
            return False

        button_mask = {
            "left": 0x01,
            "middle": 0x02,
            "right": 0x04
        }.get(button, 0x01)

        # 移动到位置
        self.client.send_mouse_event_raw(x, y, 0)
        await asyncio.sleep(0.01)  # 短暂延时确保移动生效

        # 按下按钮
        self.client.send_mouse_event_raw(x, y, button_mask)
        await asyncio.sleep(delay)  # 按下持续时间

        # 释放按钮
        self.client.send_mouse_event_raw(x, y, 0)
        return True

    def key_send(self, key_code: int, action: str = "click"):
        """发送键盘事件"""
        if not self.is_connected():
            return False

        if action == "press":
            self.client.send_key_press(key_code)
        elif action == "release":
            self.client.send_key_release(key_code)
        else:  # click
            self.client.send_key_press(key_code)
            self.client.send_key_release(key_code)
        return True

    def get_status(self) -> dict:
        """获取状态信息"""
        return {
            "connected": self.is_connected(),
            "kvm_ip": self.config.ip,
            "kvm_port": self.config.port,
            "channel": self.config.channel,
            "frame_count": self.frame_count,
            "video_width": self.video_width,
            "video_height": self.video_height,
            "has_keyframe": self.has_keyframe,
            "ffmpeg_available": self.decoder.ffmpeg_available
        }


# ============ 全局管理器 ============

manager: Optional[KVMProxyManager] = None


# ============ FastAPI 应用 ============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global manager

    # 启动时连接 KVM
    if manager:
        logger.info("正在连接 KVM...")
        connected = await manager.connect()
        if connected:
            # 等待视频流就绪
            logger.info("等待视频流...")
            for _ in range(30):
                await asyncio.sleep(0.3)
                if manager.has_keyframe:
                    logger.info(f"视频流就绪: {manager.video_width}x{manager.video_height}")
                    break
        else:
            logger.error("KVM 连接失败")

    yield

    # 关闭时断开连接
    if manager:
        await manager.disconnect()


app = FastAPI(
    title="KVM HTTP 代理",
    description="通过 HTTP 接口控制 KVM 设备",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/status")
async def get_status():
    """获取连接状态"""
    if not manager:
        raise HTTPException(status_code=500, detail="代理未初始化")
    return JSONResponse(content=manager.get_status())


@app.get("/capture")
async def capture(
        wait: float = Query(0.0, description="截图前等待时间（秒）"),
        quality: int = Query(90, description="JPEG 质量（1-100）")
):
    """
    截取当前屏幕

    返回 JPEG 图片
    """
    if not manager:
        raise HTTPException(status_code=500, detail="代理未初始化")

    if not manager.is_connected():
        raise HTTPException(status_code=503, detail="KVM 未连接")

    if wait > 0:
        await asyncio.sleep(wait)

    jpeg_data = await manager.capture()
    if not jpeg_data:
        raise HTTPException(status_code=503, detail="无可用视频帧")

    return Response(
        content=jpeg_data,
        media_type="image/jpeg",
        headers={"Content-Disposition": "inline; filename=capture.jpg"}
    )


@app.post("/mouse/move")
async def mouse_move(request: MouseMoveRequest):
    """
    移动鼠标

    - x: X 坐标（像素）
    - y: Y 坐标（像素）
    """
    if not manager:
        raise HTTPException(status_code=500, detail="代理未初始化")

    if not manager.is_connected():
        raise HTTPException(status_code=503, detail="KVM 未连接")

    success = manager.mouse_move(request.x, request.y)
    if not success:
        raise HTTPException(status_code=500, detail="发送鼠标移动失败")

    return {"success": True, "x": request.x, "y": request.y}


@app.post("/mouse/click")
async def mouse_click(request: MouseClickRequest):
    """
    鼠标点击

    - x: X 坐标（像素）
    - y: Y 坐标（像素）
    - button: 按钮（left, middle, right）
    - delay: 按下持续时间（秒），默认 0.05
    """
    if not manager:
        raise HTTPException(status_code=500, detail="代理未初始化")

    if not manager.is_connected():
        raise HTTPException(status_code=503, detail="KVM 未连接")

    success = await manager.mouse_click(request.x, request.y, request.button, request.delay)
    if not success:
        raise HTTPException(status_code=500, detail="发送鼠标点击失败")

    return {"success": True, "x": request.x, "y": request.y, "button": request.button, "delay": request.delay}


@app.post("/key/send")
async def key_send(request: KeySendRequest):
    """
    发送键盘事件

    - key_code: X11 键码
    - action: 动作（press, release, click）
    """
    if not manager:
        raise HTTPException(status_code=500, detail="代理未初始化")

    if not manager.is_connected():
        raise HTTPException(status_code=503, detail="KVM 未连接")

    success = manager.key_send(request.key_code, request.action)
    if not success:
        raise HTTPException(status_code=500, detail="发送键盘事件失败")

    return {"success": True, "key_code": request.key_code, "action": request.action}


# ============ 主入口 ============

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="KVM HTTP 代理服务",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python kvm_proxy.py --ip 192.168.0.100 --port 5900 --username admin --password 123456
  python kvm_proxy.py --ip 192.168.0.100 --channel 1 --http-port 8080

API 接口:
  GET  /status       - 获取连接状态
  GET  /capture      - 截取当前屏幕（返回 JPEG）
  POST /mouse/move   - 移动鼠标 {"x": 100, "y": 200}
  POST /mouse/click  - 鼠标点击 {"x": 100, "y": 200, "button": "left"}
  POST /key/send     - 发送键盘 {"key_code": 65, "action": "click"}
        """
    )

    parser.add_argument("--ip", required=True, help="KVM IP 地址")
    parser.add_argument("--port", type=int, default=5900, help="KVM 端口（默认 5900）")
    parser.add_argument("--channel", type=int, default=0, help="KVM 通道（默认 0）")
    parser.add_argument("--username", default="admin", help="用户名（默认 admin）")
    parser.add_argument("--password", default="123456", help="密码（默认 123456）")
    parser.add_argument("--http-port", type=int, default=8000, help="HTTP 服务端口（默认 8000）")
    parser.add_argument("--http-host", default="0.0.0.0", help="HTTP 服务地址（默认 0.0.0.0）")

    return parser.parse_args()


def main():
    """主函数"""
    global manager

    args = parse_args()

    # 检查 FFmpeg
    if not check_ffmpeg():
        logger.warning("FFmpeg 不可用，截图功能将无法工作")
        logger.warning("请安装: brew install ffmpeg (macOS) 或 apt install ffmpeg (Linux)")

    # 创建配置
    config = KVMConfig(
        ip=args.ip,
        port=args.port,
        channel=args.channel,
        username=args.username,
        password=args.password
    )

    # 创建管理器
    manager = KVMProxyManager(config)

    # 启动 HTTP 服务
    logger.info(f"启动 KVM HTTP 代理服务: http://{args.http_host}:{args.http_port}")
    logger.info(f"KVM 配置: {args.ip}:{args.port} channel={args.channel} user={args.username}")
    logger.info("API 文档: http://localhost:{}/docs".format(args.http_port))

    uvicorn.run(
        app,
        host=args.http_host,
        port=args.http_port,
        log_level="info"
    )


if __name__ == "__main__":
    main()

