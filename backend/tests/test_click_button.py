#!/usr/bin/env python3
"""
KVM 鼠标点击测试 - 点击"上一步"按钮

测试流程:
1. 连接 KVM，等待视频解码
2. 点击"上一步"按钮，等待1秒后截图
3. 再点击一次，等待1秒后截图
4. 再点击一次，等待1秒后截图
5. 退出

"""

from __future__ import annotations

import asyncio
import sys
import os
import logging
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

# 设置日志级别
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 添加 python_client 路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from python_client import KVMClient

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("警告: 未安装 opencv-python，无法保存截图")
    print("请运行: pip install opencv-python")
    sys.exit(1)

# H.264 编码类型
ENCODING_H264 = 7


def check_ffmpeg():
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


class AsyncH264Decoder:
    """异步 H.264 解码器 - 使用线程池避免阻塞事件循环"""
    
    def __init__(self):
        self.ffmpeg_available = check_ffmpeg()
        self.temp_dir = tempfile.mkdtemp(prefix='kvm_click_test_')
        self.frame_index = 0
        self.sps = None
        self.pps = None
        
        # 解码结果
        self.last_decoded_frame = None
        self.decode_lock = asyncio.Lock()
        
        # 解码工作标志
        self.running = False
        self._executor = None
    
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
            if data[i:i+4] == b'\x00\x00\x00\x01':
                positions.append((i, 4))
                i += 4
            elif data[i:i+3] == b'\x00\x00\x01':
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
    
    def _decode_sync(self, frame_data: bytes) -> Optional[np.ndarray]:
        """同步解码（在线程池中执行，不阻塞事件循环）"""
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
                img = cv2.imread(output_file)
                os.remove(output_file)
                return img
            
            return None
            
        except Exception as e:
            logging.debug(f"Decode error: {e}")
            return None
    
    async def decode_frame_async(self, frame_data: bytes) -> Optional[np.ndarray]:
        """异步解码帧（在线程池中执行）"""
        if not self.running:
            return None
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self._executor,
                self._decode_sync,
                frame_data
            )
            
            if result is not None:
                self.last_decoded_frame = result
            
            return result
        except Exception as e:
            logging.debug(f"Async decode error: {e}")
            return None
    
    def start(self):
        """启动解码器"""
        from concurrent.futures import ThreadPoolExecutor
        self.running = True
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix='h264_decoder')
        logging.info("H264 decoder started with thread pool")
    
    async def stop(self):
        """停止解码器"""
        self.running = False
        if self._executor:
            self._executor.shutdown(wait=False)
            self._executor = None
        logging.info("H264 decoder stopped")
    
    def close(self):
        """清理临时文件"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except:
            pass


class ClickTester:
    """鼠标点击测试器"""
    
    def __init__(self, output_dir: str = "click_test_screenshots"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.frame_count = 0
        self.last_frame = None
        self.screenshot_count = 0
        
        # 异步解码器
        self.decoder = AsyncH264Decoder()
        self.h264_buffer = bytearray()
        self.has_keyframe = False
        
        # 待处理的帧数据
        self._pending_frame = None
    
    async def start(self):
        """启动测试器"""
        self.decoder.start()
    
    async def stop(self):
        """停止测试器"""
        await self.decoder.stop()
    
    def on_video_frame(self, frame_data: bytes, width: int, height: int, encoding_type: int):
        """视频帧回调（非阻塞）"""
        self.frame_count += 1
        
        try:
            if encoding_type == ENCODING_H264:
                self._process_h264_frame(frame_data)
            elif len(frame_data) >= width * height * 3:
                # 原始 RGB 数据
                frame_rgb = np.frombuffer(frame_data[:width*height*3], dtype=np.uint8)
                frame_rgb = frame_rgb.reshape((height, width, 3))
                frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                self.last_frame = frame_bgr
        except Exception as e:
            logging.debug(f"Frame processing error: {e}")
    
    def _process_h264_frame(self, frame_data: bytes):
        """处理 H.264 帧（非阻塞）"""
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
        
        if not self.has_keyframe:
            return
        
        self._pending_frame = bytes(self.h264_buffer)
    
    async def decode_latest_frame(self):
        """解码最新的帧"""
        if self._pending_frame is None:
            return
        
        frame_data = self._pending_frame
        self._pending_frame = None
        
        result = await self.decoder.decode_frame_async(frame_data)
        if result is not None:
            self.last_frame = result
    
    def save_screenshot(self, label: str) -> bool:
        """保存当前帧的截图"""
        if self.last_frame is None:
            print(f"  ⚠️  无可用帧数据，无法保存 {label} 截图")
            return False
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.output_dir / f"{timestamp}_{label}.jpg"
            
            cv2.imwrite(str(filename), self.last_frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            self.screenshot_count += 1
            
            h, w = self.last_frame.shape[:2]
            print(f"  ✅ 保存截图: {filename.name} ({w}x{h})")
            return True
        
        except Exception as e:
            print(f"  ❌ 保存截图失败: {e}")
            return False
    
    def close(self):
        """清理资源"""
        self.decoder.close()


async def main():
    """主函数"""
    
    # KVM 配置
    KVM_IP = "192.168.0.100"
    KVM_PORT = 5900
    KVM_CHANNEL = 0
    USERNAME = "admin"
    PASSWORD = "123456"
    
    # "上一步"按钮的坐标（根据截图估算）
    # 截图显示按钮在页面左侧，约 x=146, y=273 处
    BUTTON_X = 146
    BUTTON_Y = 273
    
    # 点击次数
    CLICK_COUNT = 3
    
    # 检查 FFmpeg
    ffmpeg_ok = check_ffmpeg()
    
    print("=" * 70)
    print("KVM 鼠标点击测试 - 点击'上一步'按钮")
    print("=" * 70)
    print(f"KVM 地址: {KVM_IP}:{KVM_PORT}")
    print(f"通道: {KVM_CHANNEL}")
    print(f"用户名: {USERNAME}")
    print(f"FFmpeg: {'可用 ✅' if ffmpeg_ok else '不可用 ❌'}")
    print(f"按钮坐标: ({BUTTON_X}, {BUTTON_Y})")
    print(f"点击次数: {CLICK_COUNT}")
    print("=" * 70)
    print()
    
    if not ffmpeg_ok:
        print("⚠️  警告: FFmpeg 不可用，H.264 视频将无法解码，无法保存截图")
        print("    请安装: brew install ffmpeg (macOS) 或 apt install ffmpeg (Linux)")
        print()
        return 1
    
    # 创建测试器
    tester = ClickTester()
    await tester.start()
    
    # 创建 KVM 客户端
    client = KVMClient()
    client.set_video_callback(tester.on_video_frame)
    
    try:
        print("🔌 正在连接到 KVM...")
        
        # 连接到 KVM
        await client.connect(
            ip=KVM_IP,
            port=KVM_PORT,
            channel=KVM_CHANNEL,
            username=USERNAME,
            password=PASSWORD,
            timeout=30.0
        )
        
        print("✅ 连接成功!")
        print()
        
        # 设置鼠标为绝对坐标模式
        print("🖱️  设置鼠标为绝对坐标模式...")
        client.set_mouse_type(1)  # 1 = 绝对坐标
        await asyncio.sleep(0.5)
        print()
        
        # 等待第一帧解码
        print("📺 等待视频流...")
        for i in range(20):
            await asyncio.sleep(0.3)
            await tester.decode_latest_frame()
            if tester.last_frame is not None:
                video_height, video_width = tester.last_frame.shape[:2]
                print(f"   ✓ 已解码视频帧 ({tester.frame_count} 帧已接收)")
                print(f"   ✓ 视频分辨率: {video_width}x{video_height}")
                break
            if i % 2 == 0:
                print(f"   等待解码... ({tester.frame_count} 帧已接收)", end='\r')
        print()
        
        if tester.last_frame is None:
            print("⚠️  警告: 未能解码视频帧，但会继续测试...")
        print()
        
        # 保存初始截图
        print("📸 保存初始截图...")
        await tester.decode_latest_frame()
        tester.save_screenshot("00_initial")
        print()
        
        # 执行点击测试
        for i in range(1, CLICK_COUNT + 1):
            print(f"[{i}/{CLICK_COUNT}] 点击'上一步'按钮")
            print(f"  📍 坐标: ({BUTTON_X}, {BUTTON_Y})")
            
            # 发送鼠标点击
            # 先移动到位置
            print(f"  🖱️  移动鼠标到按钮位置...")
            client.send_mouse_event_raw(BUTTON_X, BUTTON_Y, 0)
            await asyncio.sleep(0.1)
            
            # 按下左键
            print(f"  🖱️  按下左键...")
            client.send_mouse_event_raw(BUTTON_X, BUTTON_Y, 0x01)  # 0x01 = 左键
            await asyncio.sleep(0.05)
            
            # 释放左键
            print(f"  🖱️  释放左键...")
            client.send_mouse_event_raw(BUTTON_X, BUTTON_Y, 0)
            
            # 等待 1 秒
            print(f"  ⏳ 等待 1 秒...")
            await asyncio.sleep(1.0)
            
            # 解码最新帧并截图
            print(f"  📸 截图...")
            for _ in range(3):
                await tester.decode_latest_frame()
                await asyncio.sleep(0.1)
            
            tester.save_screenshot(f"{i:02d}_click_{i}")
            print()
        
        print("=" * 70)
        print("✅ 测试完成!")
        print(f"   收到视频帧: {tester.frame_count}")
        print(f"   保存截图: {tester.screenshot_count}")
        print(f"   截图目录: {tester.output_dir}/")
        print("=" * 70)
        print()
        print("💡 提示:")
        print("   1. 请检查截图中页面内容是否变化")
        print("   2. 如果页面没有响应，可能需要调整按钮坐标")
        print(f"   3. 当前按钮坐标: ({BUTTON_X}, {BUTTON_Y})")
        print("=" * 70)
    
    except TimeoutError as e:
        print(f"\n❌ 连接超时: {e}")
        return 1
    except ConnectionError as e:
        print(f"\n❌ 连接失败: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # 停止测试器
        await tester.stop()
        tester.close()
        
        # 断开连接
        print()
        print("🔌 正在断开连接...")
        await client.disconnect()
        print("✅ 已断开连接")
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

