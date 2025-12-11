#!/usr/bin/env python3
"""
KVM 数据源节点帧获取测试
测试通过 KVMManager 获取的图片是否正常（非灰色）
"""

import sys
import os
import time

# 添加 src 路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from kvm.kvm_manager import KVMManager
import cv2
from loguru import logger

def main():
    # KVM 配置
    KVM_IP = "192.168.0.100"
    KVM_PORT = 5900
    KVM_CHANNEL = 0
    USERNAME = "admin"
    PASSWORD = "123456"
    
    print("=" * 70)
    print("KVM 数据源节点帧获取测试")
    print("=" * 70)
    print(f"KVM 地址: {KVM_IP}:{KVM_PORT}")
    print(f"通道: {KVM_CHANNEL}")
    print("=" * 70)
    print()
    
    # 创建 KVM 管理器
    kvm_manager = KVMManager()
    
    try:
        # 连接 KVM
        print("🔌 正在连接到 KVM...")
        instance = kvm_manager.get_or_create(
            ip=KVM_IP,
            port=KVM_PORT,
            channel=KVM_CHANNEL,
            username=USERNAME,
            password=PASSWORD,
            timeout=30.0
        )
        
        if not instance or not instance.connected:
            print("❌ 连接失败")
            return 1
        
        print("✅ 连接成功!")
        print()
        
        # 等待视频帧
        print("📺 等待视频帧...")
        for i in range(30):
            time.sleep(0.5)
            
            frame = kvm_manager.get_latest_frame(KVM_IP, KVM_PORT, KVM_CHANNEL, timeout=1.0)
            if frame is not None:
                print(f"✅ 获取到帧: shape={frame.shape}, dtype={frame.dtype}")
                
                # 检查是否是灰色图（所有通道值相同）
                if len(frame.shape) == 3 and frame.shape[2] == 3:
                    # 取中心区域100x100像素
                    h, w = frame.shape[:2]
                    center_y, center_x = h // 2, w // 2
                    roi = frame[center_y-50:center_y+50, center_x-50:center_x+50]
                    
                    # 计算每个通道的标准差
                    std_b = roi[:, :, 0].std()
                    std_g = roi[:, :, 1].std()
                    std_r = roi[:, :, 2].std()
                    
                    # 计算通道间差异
                    mean_b = roi[:, :, 0].mean()
                    mean_g = roi[:, :, 1].mean()
                    mean_r = roi[:, :, 2].mean()
                    
                    print(f"   通道标准差: B={std_b:.2f}, G={std_g:.2f}, R={std_r:.2f}")
                    print(f"   通道均值: B={mean_b:.2f}, G={mean_g:.2f}, R={mean_r:.2f}")
                    
                    # 判断是否是灰色图
                    channel_diff = max(abs(mean_b - mean_g), abs(mean_g - mean_r), abs(mean_b - mean_r))
                    if channel_diff < 5:
                        print("   ⚠️  警告: 图像可能是灰色的（通道差异很小）")
                    else:
                        print("   ✅ 图像正常（有色彩）")
                
                # 保存测试截图
                output_file = "test_kvm_source_frame.jpg"
                cv2.imwrite(output_file, frame)
                print(f"   📸 已保存截图: {output_file}")
                print()
                print("=" * 70)
                print("✅ 测试完成!")
                print("=" * 70)
                return 0
            
            if i % 2 == 0:
                print(f"   等待中... ({i}/30)", end='\r')
        
        print()
        print("❌ 超时：未能获取到视频帧")
        return 1
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # 清理连接
        print()
        print("🔌 正在断开连接...")
        kvm_manager.release(KVM_IP, KVM_PORT, KVM_CHANNEL)
        print("✅ 已断开连接")

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

