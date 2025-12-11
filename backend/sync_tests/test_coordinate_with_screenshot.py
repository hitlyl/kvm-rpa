#!/usr/bin/env python3
"""
坐标系统对比测试（带截图）

测试像素坐标和归一化坐标 (0-65535) 哪种能正确移动鼠标
每次移动后截图保存，便于对比
"""

import sys
import os
import time
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

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


def main():
    """主函数"""
    KVM_IP = "192.168.0.100"
    KVM_PORT = 5900
    KVM_CHANNEL = 0
    USERNAME = "admin"
    PASSWORD = "123456"
    
    # 创建输出目录
    output_dir = Path("coordinate_test_screenshots")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("坐标系统对比测试（带截图）")
    print("=" * 70)
    print(f"截图保存目录: {output_dir}/")
    print()
    
    client = SyncKVMClient()
    
    def save_screenshot(frame, test_name: str, position_name: str, coords: str):
        """保存截图"""
        if frame is None:
            print(f"   ⚠️  无可用帧")
            return
        
        timestamp = datetime.now().strftime('%H%M%S')
        filename = output_dir / f"{test_name}_{position_name}_{coords}_{timestamp}.jpg"
        cv2.imwrite(str(filename), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        h, w = frame.shape[:2]
        print(f"   ✅ 截图: {filename.name} ({w}x{h})")
    
    try:
        print("[1] 连接 KVM...")
        if not client.connect(KVM_IP, KVM_PORT, KVM_CHANNEL, USERNAME, PASSWORD, timeout=30.0):
            print("❌ 连接失败")
            return 1
        
        print(f"   ✅ 连接成功")
        
        # 等待视频帧
        print("\n[2] 等待视频帧...")
        video_width = 0
        video_height = 0
        
        for i in range(20):
            time.sleep(0.3)
            frame = client.get_latest_frame(timeout=0)
            if frame is not None:
                video_height, video_width = frame.shape[:2]
                print(f"   ✅ 视频分辨率: {video_width}x{video_height}")
                break
        
        if video_width == 0:
            print("   ⚠️  使用默认分辨率 1280x1024")
            video_width, video_height = 1280, 1024
        
        print("\n[3] 设置鼠标为绝对坐标模式...")
        client.set_mouse_type(1)
        time.sleep(1.0)
        
        # 保存初始截图
        print("\n[4] 保存初始截图...")
        frame = client.get_latest_frame(timeout=1.0)
        save_screenshot(frame, "00_initial", "initial", "before_test")
        
        # =====================================================
        # 测试 A: 像素坐标 + send_mouse_event_raw
        # =====================================================
        print("\n" + "=" * 70)
        print("测试 A: 像素坐标 + send_mouse_event_raw")
        print("=" * 70)
        
        test_positions_pixel = [
            ("center", video_width // 2, video_height // 2),
            ("top_left", 50, 50),
            ("bottom_right", video_width - 50, video_height - 50),
        ]
        
        for name, px, py in test_positions_pixel:
            print(f"\n   发送像素坐标 ({px}, {py}) - {name}")
            client.send_mouse_event_raw(px, py, 0)
            time.sleep(1.0)
            frame = client.get_latest_frame(timeout=1.0)
            save_screenshot(frame, "A_pixel_raw", name, f"{px}_{py}")
        
        # =====================================================
        # 测试 B: 归一化坐标 (0-65535) + send_mouse_event_raw
        # =====================================================
        print("\n" + "=" * 70)
        print("测试 B: 归一化坐标 (0-65535) + send_mouse_event_raw")
        print("=" * 70)
        
        test_positions_normalized = [
            ("center", 32768, 32768),  # 屏幕中心
            ("top_left", int(50 / video_width * 65535), int(50 / video_height * 65535)),
            ("bottom_right", int((video_width - 50) / video_width * 65535), 
                            int((video_height - 50) / video_height * 65535)),
        ]
        
        for name, nx, ny in test_positions_normalized:
            print(f"\n   发送归一化坐标 ({nx}, {ny}) - {name}")
            client.send_mouse_event_raw(nx, ny, 0)
            time.sleep(1.0)
            frame = client.get_latest_frame(timeout=1.0)
            save_screenshot(frame, "B_norm_raw", name, f"{nx}_{ny}")
        
        # =====================================================
        # 测试 C: 像素坐标 + send_mouse_event(type=1)
        # =====================================================
        print("\n" + "=" * 70)
        print("测试 C: 像素坐标 + send_mouse_event(type=1)")
        print("=" * 70)
        
        for name, px, py in test_positions_pixel:
            print(f"\n   发送 ({px}, {py}) - {name}")
            client.send_mouse_event(px, py, 0, mouse_type=1)
            time.sleep(1.0)
            frame = client.get_latest_frame(timeout=1.0)
            save_screenshot(frame, "C_pixel_event", name, f"{px}_{py}")
        
        # =====================================================
        # 测试 D: 归一化坐标 + send_mouse_event(type=1)
        # =====================================================
        print("\n" + "=" * 70)
        print("测试 D: 归一化坐标 + send_mouse_event(type=1)")
        print("=" * 70)
        
        for name, nx, ny in test_positions_normalized:
            print(f"\n   发送 ({nx}, {ny}) - {name}")
            client.send_mouse_event(nx, ny, 0, mouse_type=1)
            time.sleep(1.0)
            frame = client.get_latest_frame(timeout=1.0)
            save_screenshot(frame, "D_norm_event", name, f"{nx}_{ny}")
        
        print("\n" + "=" * 70)
        print("测试完成！")
        print("=" * 70)
        print(f"\n截图已保存到: {output_dir}/")
        print("\n请检查截图，观察哪组测试中鼠标位置有明显变化：")
        print("  A_pixel_raw_*.jpg     - 测试 A: 像素坐标 + send_mouse_event_raw")
        print("  B_norm_raw_*.jpg      - 测试 B: 归一化坐标 + send_mouse_event_raw")
        print("  C_pixel_event_*.jpg   - 测试 C: 像素坐标 + send_mouse_event(type=1)")
        print("  D_norm_event_*.jpg    - 测试 D: 归一化坐标 + send_mouse_event(type=1)")
        print("\n鼠标应该在 center、top_left、bottom_right 三个位置之间移动。")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        print("\n断开连接...")
        client.disconnect()
        print("✅ 已断开")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())










