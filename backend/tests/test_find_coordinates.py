#!/usr/bin/env python3
"""
坐标定位工具 - 用于找到按钮的准确位置

在指定区域内进行网格点击测试，每次点击后保存截图，帮助定位按钮坐标
"""

import sys
import os
import logging
import subprocess
import tempfile
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

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


class H264Decoder:
    """H.264 解码器 - 使用 FFmpeg 解码"""
    
    def __init__(self):
        self.ffmpeg_available = check_ffmpeg()
        self.temp_dir = tempfile.mkdtemp(prefix='kvm_coord_test_')
        self.frame_index = 0
        self.sps = None
        self.pps = None
        self.last_decoded_frame = None
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix='h264_decoder')
    
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
    
    def decode(self, frame_data: bytes) -> Optional[np.ndarray]:
        """解码 H.264 帧"""
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
                with self._lock:
                    self.last_decoded_frame = img
                return img
            
            return None
            
        except Exception as e:
            logging.debug(f"Decode error: {e}")
            return None
    
    def decode_async(self, frame_data: bytes):
        """异步解码（在线程池中执行）"""
        self._executor.submit(self.decode, frame_data)
    
    def get_last_frame(self) -> Optional[np.ndarray]:
        """获取最后解码的帧"""
        with self._lock:
            return self.last_decoded_frame
    
    def close(self):
        """清理资源"""
        self._executor.shutdown(wait=False)
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except:
            pass


class CoordinateTester:
    """坐标测试器"""
    
    def __init__(self, output_dir: str = "coordinate_test_screenshots"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.frame_count = 0
        
        # 解码器
        self.decoder = H264Decoder()
        self.h264_buffer = bytearray()
        self.has_keyframe = False
    
    def on_video_frame(self, frame_data: bytes, width: int, height: int, encoding_type: int):
        """视频帧回调"""
        self.frame_count += 1
        
        try:
            if encoding_type == ENCODING_H264:
                self._process_h264_frame(frame_data)
            elif len(frame_data) >= width * height * 3:
                # 原始 RGB 数据
                frame_rgb = np.frombuffer(frame_data[:width*height*3], dtype=np.uint8)
                frame_rgb = frame_rgb.reshape((height, width, 3))
                frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                with self.decoder._lock:
                    self.decoder.last_decoded_frame = frame_bgr
        except Exception as e:
            logging.debug(f"Frame processing error: {e}")
    
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
        
        if not self.has_keyframe:
            return
        
        # 异步解码
        self.decoder.decode_async(bytes(self.h264_buffer))
    
    def get_last_frame(self) -> Optional[np.ndarray]:
        """获取最后解码的帧"""
        return self.decoder.get_last_frame()
    
    def save_screenshot(self, label: str) -> bool:
        """保存当前帧的截图"""
        last_frame = self.get_last_frame()
        if last_frame is None:
            print(f"  ⚠️  无可用帧数据，无法保存 {label} 截图")
            return False
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.output_dir / f"{timestamp}_{label}.jpg"
            
            cv2.imwrite(str(filename), last_frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            
            h, w = last_frame.shape[:2]
            print(f"  ✅ 保存截图: {filename.name} ({w}x{h})")
            return True
        
        except Exception as e:
            print(f"  ❌ 保存截图失败: {e}")
            return False
    
    def close(self):
        """清理资源"""
        self.decoder.close()


def test_coordinates():
    """测试不同坐标点"""
    
    # KVM 配置
    KVM_IP = "192.168.0.100"
    KVM_PORT = 5900
    KVM_CHANNEL = 0
    USERNAME = "admin"
    PASSWORD = "123456"
    
    # 测试坐标点列表
    TEST_POINTS = [
        (100, 210, "左上角"),
        (120, 228, "中心点"),
        (140, 228, "右中"),
        (146, 273, "原坐标"),
    ]
    
    # 检查 FFmpeg
    ffmpeg_ok = check_ffmpeg()
    
    print("=" * 70)
    print("坐标定位工具 - 通过截图对比找到正确的按钮坐标")
    print("=" * 70)
    print(f"KVM 地址: {KVM_IP}:{KVM_PORT}")
    print(f"FFmpeg: {'可用 ✅' if ffmpeg_ok else '不可用 ❌'}")
    print()
    print("将依次测试以下坐标点：")
    for i, (x, y, label) in enumerate(TEST_POINTS, 1):
        print(f"  {i}. ({x:3d}, {y:3d}) - {label}")
    print("=" * 70)
    print()
    
    if not ffmpeg_ok:
        print("⚠️  警告: FFmpeg 不可用，无法保存截图")
        return 1
    
    # 创建测试器
    tester = CoordinateTester()
    
    # 创建客户端
    client = KVMClient()
    client.set_video_callback(tester.on_video_frame)
    
    try:
        print("🔌 正在连接到 KVM...")
        client.connect(
            ip=KVM_IP,
            port=KVM_PORT,
            channel=KVM_CHANNEL,
            username=USERNAME,
            password=PASSWORD,
            timeout=30.0
        )
        print("✅ 连接成功!\n")
        
        # 设置鼠标为绝对坐标模式
        print("🖱️  设置鼠标为绝对坐标模式...")
        client.set_mouse_type(1)
        time.sleep(0.5)
        print()
        
        # 等待视频解码
        print("📺 等待视频流...")
        for i in range(20):
            time.sleep(0.3)
            last_frame = tester.get_last_frame()
            if last_frame is not None:
                video_height, video_width = last_frame.shape[:2]
                print(f"   ✓ 已解码视频帧 ({tester.frame_count} 帧已接收)")
                print(f"   ✓ 视频分辨率: {video_width}x{video_height}")
                break
            if i % 2 == 0:
                print(f"   等待解码... ({tester.frame_count} 帧已接收)", end='\r')
        print()
        
        if tester.get_last_frame() is None:
            print("⚠️  警告: 未能解码视频帧，但会继续测试...")
        print()
        
        # 保存初始截图
        print("📸 保存初始截图...")
        time.sleep(0.3)
        tester.save_screenshot("00_initial")
        print()
        
        # 测试每个坐标
        for i, (x, y, label) in enumerate(TEST_POINTS, 1):
            print(f"[{i}/{len(TEST_POINTS)}] 测试坐标 ({x}, {y}) - {label}")
            print(f"  📍 位置: ({x}, {y})")
            
            # 点击
            print(f"  🖱️  点击...")
            client.send_mouse_event_raw(x, y, 0)  # 移动
            time.sleep(0.1)
            client.send_mouse_event_raw(x, y, 0x01)  # 按下
            time.sleep(0.05)
            client.send_mouse_event_raw(x, y, 0)  # 释放
            
            # 等待界面响应
            print(f"  ⏳ 等待 1 秒...")
            time.sleep(1.0)
            
            # 截图
            print(f"  📸 截图...")
            time.sleep(0.3)
            tester.save_screenshot(f"{i:02d}_{label.replace('（', '_').replace('）', '')}")
            print()
        
        print("=" * 70)
        print("✅ 测试完成!")
        print(f"   收到视频帧: {tester.frame_count}")
        print(f"   截图目录: {tester.output_dir}/")
        print("=" * 70)
        print()
        print("💡 提示:")
        print("   1. 查看截图目录中的所有截图")
        print("   2. 对比每张截图，找到界面发生变化的那一张")
        print("   3. 该截图对应的坐标就是正确的按钮位置")
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
        # 清理资源
        tester.close()
        
        # 断开连接
        print()
        print("🔌 正在断开连接...")
        client.disconnect()
        print("✅ 已断开连接")
    
    return 0


if __name__ == "__main__":
    exit_code = test_coordinates()
    sys.exit(exit_code)
