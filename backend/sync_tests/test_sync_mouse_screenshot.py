#!/usr/bin/env python3
"""
同步 KVM 客户端鼠标移动与截图综合测试

测试流程：
1. 移动鼠标到左上角，截图
2. 移动鼠标到中心，截图
3. 移动鼠标到右下角，截图
等等...

重要说明：
- 使用 send_mouse_event_raw() 方法，与 Java SDK ViewerSample.encodeMouseEvent 一致
- 直接发送像素坐标（0-width, 0-height），不进行归一化
- 设备端根据当前鼠标模式（绝对/相对）解释坐标
"""

import sys
import os
import time
import logging
import argparse
from datetime import datetime
from pathlib import Path

# 默认使用 INFO 级别，使用 --debug 参数可切换到 DEBUG 级别
logger = logging.getLogger(__name__)

# 添加 src 路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from sync_client import SyncKVMClient

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("警告: 未安装 opencv-python，无法保存截图")
    print("请运行: pip install opencv-python")
    sys.exit(1)


class Config:
    """测试配置"""
    kvm_ip = "192.168.0.100"
    kvm_port = 5900
    kvm_channel = 0
    username = "admin"
    password = "123456"


class MouseScreenshotTester:
    """鼠标移动与截图测试器（同步版本）"""
    
    def __init__(self, output_dir: str = "sync_mouse_screenshots"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.screenshot_count = 0
    
    def save_screenshot(self, frame, label: str) -> bool:
        """保存当前帧的截图"""
        if frame is None:
            print(f"  ⚠️  无可用帧数据，无法保存 {label} 截图")
            return False
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            # 清理标签中的特殊字符
            safe_label = label.replace('(', '_').replace(')', '_').replace(',', '_').replace(' ', '_')
            filename = self.output_dir / f"{timestamp}_{safe_label}.jpg"
            
            cv2.imwrite(str(filename), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            self.screenshot_count += 1
            
            h, w = frame.shape[:2]
            print(f"  ✅ 保存截图: {filename.name} ({w}x{h})")
            return True
        
        except Exception as e:
            print(f"  ❌ 保存截图失败: {e}")
            return False


def run_test(config: Config):
    """运行鼠标移动与截图测试"""
    
    print("=" * 70)
    print("同步 KVM 客户端鼠标移动与截图综合测试")
    print("=" * 70)
    print(f"KVM 地址: {config.kvm_ip}:{config.kvm_port}")
    print(f"通道: {config.kvm_channel}")
    print(f"用户名: {config.username}")
    print("=" * 70)
    print()
    
    # 创建测试器
    tester = MouseScreenshotTester()
    
    # 创建同步 KVM 客户端
    client = SyncKVMClient()
    
    try:
        print("🔌 正在连接到 KVM...")
        
        # 连接到 KVM
        if not client.connect(
            ip=config.kvm_ip,
            port=config.kvm_port,
            channel=config.kvm_channel,
            username=config.username,
            password=config.password,
            timeout=30.0
        ):
            print("❌ 连接失败")
            return 1
        
        print("✅ 连接成功!")
        print(f"   连接状态: {client.is_connected()}")
        print(f"   认证状态: {client.is_authenticated()}")
        print(f"   协议阶段: {client._protocol.stage}")
        print()
        
        # 设置鼠标为绝对坐标模式
        print("🖱️  设置鼠标为绝对坐标模式...")
        client.set_mouse_type(1)
        print(f"  ⏳ 等待设备响应鼠标模式设置...")
        time.sleep(2.0)  # 增加等待时间，确保设备完全切换到绝对坐标模式
        print(f"   协议阶段: {client._protocol.stage}")
        print()
        
        # 获取协议初始化时的分辨率（设备报告的真实分辨率）
        protocol_width, protocol_height = client.get_resolution()
        print(f"📺 协议分辨率: {protocol_width}x{protocol_height}")
        
        # 等待视频帧
        print("📺 等待视频流...")
        frame = None
        
        for i in range(20):
            time.sleep(0.3)
            frame = client.get_latest_frame(timeout=0)
            if frame is not None:
                frame_height, frame_width = frame.shape[:2]
                print(f"   ✓ 收到视频帧")
                print(f"   ✓ 解码帧分辨率: {frame_width}x{frame_height}")
                break
            if i % 2 == 0:
                print(f"   等待视频帧...", end='\r')
        
        print()
        
        # 使用协议分辨率作为鼠标坐标系统（关键修复！）
        video_width = protocol_width
        video_height = protocol_height
        print(f"✅ 使用协议分辨率作为鼠标坐标系: {video_width}x{video_height}")
        
        if frame is None:
            print("⚠️  警告: 未能获取视频帧，但会继续测试...")
        print()
        
        # 定义测试位置（像素坐标）
        # 注意：Java SDK 的 ViewerSample.encodeMouseEvent 直接使用像素坐标（unsignedShort）
        # 不进行归一化，直接发送原始像素坐标值
        test_positions = [
            ("原点_0_0", 0, 0),
            ("左上角", 50, 50),
            ("上边中点", video_width // 2, 50),
            ("右上角", video_width - 50, 50),
            ("右边中点", video_width - 50, video_height // 2),
            ("右下角", video_width - 50, video_height - 50),
            ("下边中点", video_width // 2, video_height - 50),
            ("左下角", 50, video_height - 50),
            ("左边中点", 50, video_height // 2),
            ("中心", video_width // 2, video_height // 2),
            ("最大坐标", video_width - 1, video_height - 1),
        ]
        
        print(f"📍 测试位置数量: {len(test_positions)}")
        print(f"   坐标系统分辨率: {video_width}x{video_height} （协议报告）")
        print(f"   坐标模式: 直接像素坐标（与 Java SDK ViewerSample 一致）")
        print()
        
        # 执行测试序列
        for i, (label, pixel_x, pixel_y) in enumerate(test_positions, 1):
            print(f"[{i}/{len(test_positions)}] 测试: {label}")
            print(f"  📍 像素坐标: ({pixel_x}, {pixel_y})")
            
            # 计算坐标的十六进制表示（用于调试）
            x_hex = f"0x{(pixel_x >> 8) & 0xFF:02X}{pixel_x & 0xFF:02X}"
            y_hex = f"0x{(pixel_y >> 8) & 0xFF:02X}{pixel_y & 0xFF:02X}"
            print(f"  🔢 坐标十六进制: X={x_hex}, Y={y_hex}")
            
            # 发送前检查状态
            print(f"  📊 发送前状态: connected={client.is_connected()}, "
                  f"authenticated={client.is_authenticated()}, "
                  f"stage={client._protocol.stage}")
            
            # 使用 send_mouse_event_raw 发送鼠标移动命令（与 Java SDK 一致）
            print(f"  🖱️  发送鼠标移动命令 (send_mouse_event_raw，像素坐标)...")
            client.send_mouse_event_raw(pixel_x, pixel_y, 0)
            
            # 等待鼠标移动和视频更新
            print(f"  ⏳ 等待鼠标移动生效...")
            time.sleep(0.8)
            
            # 获取最新帧
            frame = client.get_latest_frame(timeout=1.0)
            
            # 截图
            print(f"  📸 保存截图...")
            success = tester.save_screenshot(frame, f"{i:02d}_{label}")
            
            if success:
                print(f"  ✅ 测试点 {i} 完成")
            else:
                print(f"  ⚠️  测试点 {i} 截图失败")
            
            print()
        
        print("=" * 70)
        print("✅ 测试完成!")
        print(f"   保存截图: {tester.screenshot_count}/{len(test_positions)}")
        print(f"   截图目录: {tester.output_dir}/")
        print("=" * 70)
        print()
        print("💡 提示:")
        print("   1. 请检查截图中鼠标位置是否与标签一致")
        print("   2. 如果鼠标位置不正确，可能是坐标系统问题")
        print("   3. 可以尝试调整等待时间或坐标计算方式")
        print("=" * 70)
        
        return 0
    
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        # 断开连接
        print()
        print("🔌 正在断开连接...")
        client.disconnect()
        print("✅ 已断开连接")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='同步 KVM 客户端鼠标移动与截图测试')
    parser.add_argument('--ip', default="192.168.0.100", help='KVM IP 地址')
    parser.add_argument('--port', type=int, default=5900, help='KVM 端口')
    parser.add_argument('--channel', type=int, default=0, help='通道号')
    parser.add_argument('--username', default="admin", help='用户名')
    parser.add_argument('--password', default="123456", help='密码')
    parser.add_argument('--debug', action='store_true', help='启用调试日志')
    
    args = parser.parse_args()
    
    # 设置日志级别
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建配置
    config = Config()
    config.kvm_ip = args.ip
    config.kvm_port = args.port
    config.kvm_channel = args.channel
    config.username = args.username
    config.password = args.password
    
    # 运行测试
    exit_code = run_test(config)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

