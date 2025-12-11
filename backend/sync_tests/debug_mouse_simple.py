#!/usr/bin/env python3
"""
简化的鼠标调试测试

尝试不同的初始化序列
"""

import sys
import os
import time
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from sync_client import SyncKVMClient

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


def main():
    KVM_IP = "192.168.0.100"
    KVM_PORT = 5900
    KVM_CHANNEL = 0
    USERNAME = "admin"
    PASSWORD = "123456"
    
    output_dir = Path("debug_screenshots")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("简化鼠标调试测试")
    print("=" * 70)
    
    client = SyncKVMClient()
    screenshot_count = 0
    
    def save_screenshot(name: str):
        nonlocal screenshot_count
        if not CV2_AVAILABLE:
            return
        frame = client.get_latest_frame(timeout=1.0)
        if frame is not None:
            screenshot_count += 1
            filename = output_dir / f"{screenshot_count:02d}_{name}.jpg"
            cv2.imwrite(str(filename), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            print(f"   ✅ 截图: {filename.name}")
    
    try:
        print("\n[1] 连接 KVM...")
        if not client.connect(KVM_IP, KVM_PORT, KVM_CHANNEL, USERNAME, PASSWORD, timeout=30.0):
            print("❌ 连接失败")
            return 1
        
        print(f"   ✅ 连接成功，协议阶段: {client._protocol.stage}")
        
        # 等待视频
        time.sleep(1.0)
        save_screenshot("initial")
        
        # 步骤 1: 请求鼠标类型 (直接发送字节)
        print("\n[2] 请求当前鼠标类型...")
        # MouseTypeRequest: 0x6D 00 00 00
        client._protocol.connection.send(bytes([0x6D, 0x00, 0x00, 0x00]))
        print("   已发送 MouseTypeRequest: 6D000000")
        time.sleep(0.5)
        
        # 步骤 2: 设置绝对坐标模式
        print("\n[3] 设置鼠标为绝对坐标模式...")
        client.set_mouse_type(1)
        time.sleep(0.5)
        
        # 步骤 3: 发送到中心
        print("\n[4] 发送鼠标到中心 (640, 512)...")
        client.send_mouse_event_raw(640, 512, 0)
        time.sleep(1.0)
        save_screenshot("center")
        
        # 步骤 4: 发送到左上角
        print("\n[5] 发送鼠标到左上角 (50, 50)...")
        client.send_mouse_event_raw(50, 50, 0)
        time.sleep(1.0)
        save_screenshot("top_left")
        
        # 步骤 5: 尝试点击
        print("\n[6] 尝试鼠标点击...")
        client.send_mouse_event_raw(640, 512, 0)  # 移动
        time.sleep(0.1)
        client.send_mouse_event_raw(640, 512, 0x01)  # 左键按下
        time.sleep(0.1)
        client.send_mouse_event_raw(640, 512, 0)  # 释放
        time.sleep(1.0)
        save_screenshot("after_click")
        
        # 步骤 6: 尝试使用 MouseEventPacket (type=1)
        print("\n[7] 使用 send_mouse_event(type=1)...")
        client.send_mouse_event(100, 100, 0, mouse_type=1)
        time.sleep(1.0)
        save_screenshot("event_100_100")
        
        client.send_mouse_event(500, 500, 0, mouse_type=1)
        time.sleep(1.0)
        save_screenshot("event_500_500")
        
        # 步骤 7: 尝试发送初始化 (0, 0) 坐标
        print("\n[8] 发送初始化坐标 (0, 0)...")
        client.send_mouse_event_raw(0, 0, 0)
        time.sleep(0.5)
        
        # 再次尝试移动
        print("\n[9] 再次尝试移动到 (640, 512)...")
        client.send_mouse_event_raw(640, 512, 0)
        time.sleep(1.0)
        save_screenshot("final")
        
        print("\n" + "=" * 70)
        print(f"测试完成！截图: {screenshot_count}")
        print(f"截图目录: {output_dir}/")
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

