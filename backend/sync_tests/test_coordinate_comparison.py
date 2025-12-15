#!/usr/bin/env python3
"""
坐标系统对比测试

测试像素坐标和归一化坐标 (0-65535) 哪种能正确移动鼠标
"""

import sys
import os
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from sync_client import SyncKVMClient


def main():
    """主函数"""
    KVM_IP = "192.168.0.100"
    KVM_PORT = 5900
    KVM_CHANNEL = 0
    USERNAME = "admin"
    PASSWORD = "123456"
    
    print("=" * 70)
    print("坐标系统对比测试")
    print("=" * 70)
    
    client = SyncKVMClient()
    
    try:
        print("\n[1] 连接 KVM...")
        if not client.connect(KVM_IP, KVM_PORT, KVM_CHANNEL, USERNAME, PASSWORD, timeout=30.0):
            print("❌ 连接失败")
            return 1
        
        # 获取视频分辨率
        video_width, video_height = 1280, 1024  # 从日志中看到的分辨率
        print(f"   视频分辨率: {video_width}x{video_height}")
        
        print("\n[2] 设置鼠标为绝对坐标模式...")
        client.set_mouse_type(1)
        time.sleep(1.0)
        
        print("\n" + "=" * 70)
        print("测试 A: 使用像素坐标")
        print("=" * 70)
        
        # 像素坐标测试
        pixel_positions = [
            ("左上角", 100, 100),
            ("中心", video_width // 2, video_height // 2),
            ("右下角", video_width - 100, video_height - 100),
        ]
        
        for name, px, py in pixel_positions:
            print(f"\n发送像素坐标 ({px}, {py}) - {name}")
            client.send_mouse_event_raw(px, py, 0)
            print("   请检查鼠标是否移动到正确位置...")
            time.sleep(2.0)
        
        print("\n" + "=" * 70)
        print("测试 B: 使用归一化坐标 (0-65535)")
        print("=" * 70)
        
        # 归一化坐标测试
        normalized_positions = [
            ("左上角", int(100 / video_width * 65535), int(100 / video_height * 65535)),
            ("中心", 32768, 32768),  # 屏幕中心
            ("右下角", int((video_width - 100) / video_width * 65535), 
                       int((video_height - 100) / video_height * 65535)),
        ]
        
        for name, nx, ny in normalized_positions:
            print(f"\n发送归一化坐标 ({nx}, {ny}) - {name}")
            client.send_mouse_event_raw(nx, ny, 0)
            print("   请检查鼠标是否移动到正确位置...")
            time.sleep(2.0)
        
        print("\n" + "=" * 70)
        print("测试 C: 使用 MouseEventPacket (带 mouse_type=1)")
        print("=" * 70)
        
        # 使用 MouseEventPacket 的 send_mouse_event 方法
        print("\n使用 send_mouse_event(像素坐标, type=1)...")
        for name, px, py in pixel_positions:
            print(f"\n发送 ({px}, {py}) - {name}")
            client.send_mouse_event(px, py, 0, mouse_type=1)
            print("   请检查鼠标是否移动到正确位置...")
            time.sleep(2.0)
        
        print("\n" + "=" * 70)
        print("测试 D: 使用 send_mouse_event(归一化坐标, type=1)")
        print("=" * 70)
        
        for name, nx, ny in normalized_positions:
            print(f"\n发送 ({nx}, {ny}) - {name}")
            client.send_mouse_event(nx, ny, 0, mouse_type=1)
            print("   请检查鼠标是否移动到正确位置...")
            time.sleep(2.0)
        
        print("\n" + "=" * 70)
        print("测试完成！")
        print("请告诉我哪种坐标系统使鼠标正确移动：")
        print("  A) 像素坐标 send_mouse_event_raw")
        print("  B) 归一化坐标 send_mouse_event_raw")
        print("  C) 像素坐标 send_mouse_event(type=1)")
        print("  D) 归一化坐标 send_mouse_event(type=1)")
        print("=" * 70)
        
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













