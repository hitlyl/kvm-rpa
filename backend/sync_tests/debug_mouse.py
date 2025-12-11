#!/usr/bin/env python3
"""
简化的鼠标调试测试

只测试基本的鼠标移动功能，输出详细日志
"""

import sys
import os
import time
import logging

# 启用详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 添加 src 路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from sync_client import SyncKVMClient


def main():
    """主函数"""
    # KVM 配置
    KVM_IP = "192.168.0.100"
    KVM_PORT = 5900
    KVM_CHANNEL = 0
    USERNAME = "admin"
    PASSWORD = "123456"
    
    print("=" * 70)
    print("鼠标移动调试测试")
    print("=" * 70)
    
    client = SyncKVMClient()
    
    try:
        print("\n[1] 连接 KVM...")
        if not client.connect(KVM_IP, KVM_PORT, KVM_CHANNEL, USERNAME, PASSWORD, timeout=30.0):
            print("❌ 连接失败")
            return 1
        
        print(f"✅ 连接成功")
        print(f"   is_connected: {client.is_connected()}")
        print(f"   is_authenticated: {client.is_authenticated()}")
        print(f"   protocol.stage: {client._protocol.stage}")
        print(f"   protocol.is_normal: {client._protocol.is_normal}")
        
        print("\n[2] 设置鼠标为绝对坐标模式...")
        client.set_mouse_type(1)
        time.sleep(0.5)
        print(f"   protocol.stage: {client._protocol.stage}")
        
        print("\n[3] 发送鼠标移动到 (100, 100)...")
        client.send_mouse_event_raw(100, 100, 0)
        time.sleep(0.5)
        
        print("\n[4] 发送鼠标移动到 (500, 500)...")
        client.send_mouse_event_raw(500, 500, 0)
        time.sleep(0.5)
        
        print("\n[5] 发送鼠标移动到 (960, 540)（中心）...")
        client.send_mouse_event_raw(960, 540, 0)
        time.sleep(0.5)
        
        print("\n[6] 测试鼠标点击...")
        # 移动
        client.send_mouse_event_raw(960, 540, 0)
        time.sleep(0.1)
        # 按下左键
        client.send_mouse_event_raw(960, 540, 0x01)
        time.sleep(0.1)
        # 释放左键
        client.send_mouse_event_raw(960, 540, 0)
        time.sleep(0.5)
        
        print("\n✅ 测试完成")
        print("   请检查 KVM 远程屏幕上鼠标是否有移动")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        print("\n[7] 断开连接...")
        client.disconnect()
        print("✅ 已断开")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())










