#!/usr/bin/env python3
"""
KVM视频截图测试程序

连接到KVM设备后,每秒保存一张视频帧为JPG图片
使用 FFmpeg 子进程解码 H.264 视频流
"""

import asyncio
import sys
import os
import logging
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

# 设置日志级别为INFO，减少调试输出
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 添加python_client路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from python_client import KVMClient

# 编码类型常量 (来自 Java EncodingType)
ENCODING_H264 = 7
ENCODING_H265 = 9

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("警告: 未安装opencv-python,无法保存JPG图片")
    print("请运行: pip install opencv-python")
    sys.exit(1)


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
    """H.264 解码器，使用 FFmpeg 子进程"""
    
    def __init__(self):
        """初始化解码器"""
        self.ffmpeg_available = check_ffmpeg()
        if not self.ffmpeg_available:
            logging.warning("FFmpeg 不可用，H.264 解码功能将受限")
        
        # H.264 流缓冲区（累积 NAL 单元）
        self.h264_buffer = bytearray()
        
        # SPS/PPS 参数集（需要保存用于解码）
        self.sps = None
        self.pps = None
        self.vps = None  # H.265 用
        
        # 临时文件目录
        self.temp_dir = tempfile.mkdtemp(prefix='kvm_h264_')
        
        # 帧计数器
        self.frame_index = 0
        
    def _get_nal_type(self, data: bytes) -> int:
        """获取 NAL 单元类型"""
        if len(data) < 1:
            return -1
        # H.264 NAL type 在第一个字节的低 5 位
        return data[0] & 0x1F
    
    def _find_start_codes(self, data: bytes) -> list:
        """查找所有 NAL 起始码位置"""
        positions = []
        i = 0
        while i < len(data) - 3:
            # 查找 00 00 00 01 或 00 00 01
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
        """从数据中提取 SPS/PPS"""
        start_codes = self._find_start_codes(data)
        
        for i, (pos, length) in enumerate(start_codes):
            # 获取 NAL 单元数据（到下一个起始码或结尾）
            nal_start = pos + length
            if i + 1 < len(start_codes):
                nal_end = start_codes[i + 1][0]
            else:
                nal_end = len(data)
            
            nal_data = data[nal_start:nal_end]
            if len(nal_data) < 1:
                continue
            
            nal_type = self._get_nal_type(nal_data)
            
            # NAL type 7 = SPS, 8 = PPS
            if nal_type == 7:
                self.sps = data[pos:nal_end]
                logging.debug(f"Found SPS, size: {len(self.sps)}")
            elif nal_type == 8:
                self.pps = data[pos:nal_end]
                logging.debug(f"Found PPS, size: {len(self.pps)}")
    
    def decode(self, frame_data: bytes) -> np.ndarray:
        """
        解码 H.264 帧数据
        
        Args:
            frame_data: H.264 NAL 单元数据
            
        Returns:
            解码后的 BGR 图像，失败返回 None
        """
        if not self.ffmpeg_available:
            return None
        
        try:
            # 尝试提取 SPS/PPS
            self._extract_sps_pps(frame_data)
            
            # 构建完整的 H.264 数据（包含 SPS/PPS + 当前帧）
            h264_data = bytearray()
            
            if self.sps:
                h264_data.extend(self.sps)
            if self.pps:
                h264_data.extend(self.pps)
            
            # 确保帧数据有起始码
            if not frame_data.startswith(b'\x00\x00\x00\x01') and not frame_data.startswith(b'\x00\x00\x01'):
                h264_data.extend(b'\x00\x00\x00\x01')
            h264_data.extend(frame_data)
            
            # 使用 FFmpeg 解码
            self.frame_index += 1
            output_file = os.path.join(self.temp_dir, f'frame_{self.frame_index}.jpg')
            
            # FFmpeg 命令：从 stdin 读取 H.264，输出一帧 JPEG
            cmd = [
                'ffmpeg',
                '-f', 'h264',           # 输入格式
                '-i', 'pipe:0',          # 从 stdin 读取
                '-vframes', '1',         # 只输出一帧
                '-f', 'image2',          # 输出图像
                '-y',                    # 覆盖输出文件
                output_file
            ]
            
            result = subprocess.run(
                cmd,
                input=bytes(h264_data),
                capture_output=True,
                timeout=5
            )
            
            if result.returncode == 0 and os.path.exists(output_file):
                # 读取解码后的图像
                img = cv2.imread(output_file)
                # 删除临时文件
                os.remove(output_file)
                return img
            
            return None
            
        except subprocess.TimeoutExpired:
            logging.warning("FFmpeg 解码超时")
            return None
        except Exception as e:
            logging.debug(f"H.264 解码失败: {e}")
            return None
    
    def close(self):
        """清理临时文件"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except:
            pass


class VideoScreenshotSaver:
    """视频截图保存器"""
    
    def __init__(self, output_dir: str = "screenshots"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.frame_count = 0
        self.saved_count = 0
        self.last_save_time = 0
        
        # H.264 解码器
        self.h264_decoder = H264Decoder()
        
        # 最后一帧图像（用于在解码失败时显示）
        self.last_frame = None
        
        # 累积的 H.264 数据（用于关键帧检测）
        self.h264_buffer = bytearray()
        self.has_keyframe = False
        
    def on_video_frame(self, frame_data: bytes, width: int, height: int, encoding_type: int):
        """视频帧回调"""
        current_time = asyncio.get_event_loop().time()
        self.frame_count += 1
        
        try:
            frame = None
            
            if encoding_type == ENCODING_H264:
                # H.264 编码
                frame = self._process_h264_frame(frame_data)
            elif encoding_type == ENCODING_H265:
                # H.265 编码 (暂不支持)
                logging.debug("H.265编码暂不支持")
            elif len(frame_data) >= width * height * 3:
                # 原始 RGB 数据
                frame = self._decode_raw_frame(frame_data, width, height)
            else:
                logging.debug(f"未知编码类型: {encoding_type}, 帧大小: {len(frame_data)}")
            
            # 保存最后成功解码的帧
            if frame is not None:
                self.last_frame = frame
            
            # 每秒保存一次
            if current_time - self.last_save_time < 1.0:
                return
            
            self.last_save_time = current_time
            
            # 保存帧
            if self.last_frame is not None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
                filename = self.output_dir / f"frame_{timestamp}.jpg"
                
                cv2.imwrite(str(filename), self.last_frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                self.saved_count += 1
                
                h, w = self.last_frame.shape[:2]
                print(f"📸 保存截图 #{self.saved_count}: {filename.name} ({w}x{h})")
        
        except Exception as e:
            logging.error(f"处理视频帧失败: {e}")
    
    def _process_h264_frame(self, frame_data: bytes) -> np.ndarray:
        """处理 H.264 帧"""
        # 检查是否是关键帧（IDR 帧，NAL type 5）或 SPS（NAL type 7）
        if len(frame_data) > 4:
            # 跳过起始码
            nal_offset = 0
            if frame_data[:4] == b'\x00\x00\x00\x01':
                nal_offset = 4
            elif frame_data[:3] == b'\x00\x00\x01':
                nal_offset = 3
            
            if nal_offset > 0 and len(frame_data) > nal_offset:
                nal_type = frame_data[nal_offset] & 0x1F
                
                # SPS (7), PPS (8), IDR (5) 都表示新的 GOP
                if nal_type in (5, 7, 8):
                    self.has_keyframe = True
                    # 重置缓冲区，开始新的 GOP
                    if nal_type == 7:  # SPS 表示新序列
                        self.h264_buffer = bytearray()
        
        # 累积数据
        self.h264_buffer.extend(frame_data)
        
        # 只有在有关键帧后才尝试解码
        if not self.has_keyframe:
            return None
        
        # 尝试解码累积的数据
        return self.h264_decoder.decode(bytes(self.h264_buffer))
    
    def _decode_raw_frame(self, frame_data: bytes, width: int, height: int) -> np.ndarray:
        """解码原始帧数据"""
        try:
            expected_size = width * height * 3
            if len(frame_data) < expected_size:
                return None
            
            # 转换为numpy数组
            frame_rgb = np.frombuffer(frame_data[:expected_size], dtype=np.uint8)
            frame_rgb = frame_rgb.reshape((height, width, 3))
            
            # RGB转BGR(OpenCV使用BGR)
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            
            return frame_bgr
        
        except Exception as e:
            logging.error(f"解码原始帧失败: {e}")
            return None
    
    def close(self):
        """关闭资源"""
        if self.h264_decoder is not None:
            self.h264_decoder.close()


async def main():
    """主函数"""
    
    # KVM配置
    KVM_IP = "192.168.0.100"
    KVM_PORT = 5900
    KVM_CHANNEL = 0
    USERNAME = "admin"
    PASSWORD = "123456"
    
    # 输出目录
    output_dir = "screenshots"
    
    # 检查 FFmpeg
    ffmpeg_ok = check_ffmpeg()
    
    print("=" * 60)
    print("KVM视频截图测试程序")
    print("=" * 60)
    print(f"KVM地址: {KVM_IP}:{KVM_PORT}")
    print(f"通道: {KVM_CHANNEL}")
    print(f"用户名: {USERNAME}")
    print(f"输出目录: {output_dir}/")
    print(f"截图间隔: 1秒")
    print(f"FFmpeg: {'可用 ✅' if ffmpeg_ok else '不可用 ❌ (请安装 ffmpeg)'}")
    print("=" * 60)
    print()
    
    if not ffmpeg_ok:
        print("⚠️  警告: FFmpeg 不可用，H.264 视频将无法解码")
        print("    请安装 FFmpeg: brew install ffmpeg (macOS) 或 apt install ffmpeg (Linux)")
        print()
    
    # 创建截图保存器
    saver = VideoScreenshotSaver(output_dir)
    
    # 创建KVM客户端
    client = KVMClient()
    client.set_video_callback(saver.on_video_frame)
    
    try:
        print(f"🔌 正在连接到KVM...")
        
        # 连接到KVM
        await client.connect(
            ip=KVM_IP,
            port=KVM_PORT,
            channel=KVM_CHANNEL,
            username=USERNAME,
            password=PASSWORD,
            timeout=30.0
        )
        
        print("✅ 连接成功!")
        print("📺 开始接收视频并保存截图... (按Ctrl+C停止)")
        print()
        
        # 保持连接并接收视频
        try:
            while True:
                await asyncio.sleep(1)
                
                # 每秒打印统计信息
                stats = client.get_video_stats()
                print(f"   收到帧数: {saver.frame_count}, "
                      f"已保存: {saver.saved_count}, "
                      f"分辨率: {stats.get('width', 0)}x{stats.get('height', 0)}, "
                      f"编码: {stats.get('encoding_type', 0)}", 
                      end='\r')
        
        except KeyboardInterrupt:
            print("\n\n⏹️  停止...")
    
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
        # 关闭资源
        saver.close()
        
        # 断开连接
        print()
        print("🔌 正在断开连接...")
        await client.disconnect()
        
        print("=" * 60)
        print(f"✅ 已保存 {saver.saved_count} 张截图到: {output_dir}/")
        print("=" * 60)
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
