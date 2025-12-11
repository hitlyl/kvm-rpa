#!/usr/bin/env python3
"""
同步 KVM 客户端鼠标模式测试

参考 Java SendMouseEventDemo.java 测试相对和绝对模式的鼠标移动。
通过截图验证鼠标位置变化。
"""

import sys
import os
import time
import argparse
import logging
import struct

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

import cv2
from sync_client import SyncKVMClient

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Config:
    """测试配置"""
    kvm_ip = "192.168.0.100"
    kvm_port = 5900
    kvm_channel = 0
    username = "admin"
    password = "123456"
    output_dir = "mouse_mode_screenshots"


def save_screenshot(frame, label: str) -> bool:
    """保存截图"""
    if frame is None:
        print(f"  ⚠️  无帧数据，无法保存 {label}")
        return False
    
    os.makedirs(Config.output_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{label}.jpg"
    filepath = os.path.join(Config.output_dir, filename)
    
    cv2.imwrite(filepath, frame)
    h, w = frame.shape[:2]
    print(f"  ✅ 保存: {filename} ({w}x{h})")
    return True


def build_mouse_event_abs(x: int, y: int, mask: int = 0) -> bytes:
    """构建绝对模式鼠标事件包（与 Java MouseEventPacket type=1 一致）"""
    # 确保非负
    x = max(0, x)
    y = max(0, y)
    
    packet = bytearray(6)
    packet[0] = 5  # WriteNormalType.PointerEvent
    packet[1] = mask & 0xFF  # 绝对模式不设置 0x80
    packet[2:4] = struct.pack(">H", x & 0xFFFF)  # big-endian unsigned short
    packet[4:6] = struct.pack(">H", y & 0xFFFF)
    
    return bytes(packet)


def build_mouse_event_rel(dx: int, dy: int, mask: int = 0) -> bytes:
    """构建相对模式鼠标事件包（与 Java MouseEventPacket type=0 一致）"""
    packet = bytearray(6)
    packet[0] = 5  # WriteNormalType.PointerEvent
    packet[1] = (mask | 0x80) & 0xFF  # 相对模式设置 0x80 标志
    packet[2:4] = struct.pack(">h", dx)  # big-endian signed short
    packet[4:6] = struct.pack(">h", dy)
    
    return bytes(packet)


def build_mouse_type_packet(mouse_type: int) -> bytes:
    """构建鼠标类型设置包（与 Java MouseTypePacket 一致）"""
    packet = bytearray(4)
    packet[0] = 110  # WriteNormalType.SetMouseType (0x6E)
    packet[1] = mouse_type & 0xFF  # 0=相对, 1=绝对
    return bytes(packet)


def test_relative_mouse(client: SyncKVMClient):
    """测试相对模式鼠标移动 (参考 SendMouseEventDemo.java)"""
    print("\n" + "=" * 60)
    print("🔬 测试 1: 相对模式鼠标移动")
    print("=" * 60)
    
    # 设置为相对模式
    print("  📝 设置鼠标为相对模式 (type=0)...")
    rel_type_packet = build_mouse_type_packet(0)
    print(f"     数据包: {rel_type_packet.hex().upper()}")
    client._protocol.connection.send(rel_type_packet)
    time.sleep(0.5)
    
    # 截图：移动前
    print("  📸 移动前截图...")
    frame = client.get_latest_frame(timeout=2.0)
    save_screenshot(frame, "01_rel_before")
    
    # 相对移动：向右下移动 (参考 SendMouseEventDemo.java)
    print("  🖱️  相对移动：向右下角移动 50 步...")
    for i in range(50):
        packet = build_mouse_event_rel(4, 4, 0)
        client._protocol.connection.send(packet)
        time.sleep(0.01)  # 小延迟
    
    time.sleep(0.5)
    
    # 截图：向右下移动后
    print("  📸 向右下移动后截图...")
    frame = client.get_latest_frame(timeout=2.0)
    save_screenshot(frame, "02_rel_after_rightdown")
    
    # 相对移动：向左上移动
    print("  🖱️  相对移动：向左上角移动 50 步...")
    for i in range(50):
        packet = build_mouse_event_rel(-4, -4, 0)
        client._protocol.connection.send(packet)
        time.sleep(0.01)
    
    time.sleep(0.5)
    
    # 截图：向左上移动后
    print("  📸 向左上移动后截图...")
    frame = client.get_latest_frame(timeout=2.0)
    save_screenshot(frame, "03_rel_after_leftup")
    
    print("  ✅ 相对模式测试完成")


def test_absolute_mouse(client: SyncKVMClient, video_width: int, video_height: int):
    """测试绝对模式鼠标移动"""
    print("\n" + "=" * 60)
    print("🔬 测试 2: 绝对模式鼠标移动")
    print("=" * 60)
    
    # 设置为绝对模式
    print("  📝 设置鼠标为绝对模式 (type=1)...")
    abs_type_packet = build_mouse_type_packet(1)
    print(f"     数据包: {abs_type_packet.hex().upper()}")
    client._protocol.connection.send(abs_type_packet)
    time.sleep(0.5)
    
    # 测试位置列表（像素坐标）
    positions = [
        ("中心", video_width // 2, video_height // 2),
        ("左上角", 100, 100),
        ("右上角", video_width - 100, 100),
        ("右下角", video_width - 100, video_height - 100),
        ("左下角", 100, video_height - 100),
    ]
    
    for i, (label, px, py) in enumerate(positions, 1):
        print(f"\n  [{i}/{len(positions)}] 测试位置: {label} ({px}, {py})")
        
        # 构建并发送绝对坐标鼠标事件
        packet = build_mouse_event_abs(px, py, 0)
        print(f"     数据包: {packet.hex().upper()}")
        client._protocol.connection.send(packet)
        
        time.sleep(0.8)
        
        # 截图
        frame = client.get_latest_frame(timeout=2.0)
        save_screenshot(frame, f"{10+i:02d}_abs_{label}")
    
    print("\n  ✅ 绝对模式测试完成")


def test_mixed_mode(client: SyncKVMClient, video_width: int, video_height: int):
    """测试混合模式：先绝对定位，再相对移动"""
    print("\n" + "=" * 60)
    print("🔬 测试 3: 混合模式（绝对定位 + 相对移动）")
    print("=" * 60)
    
    # 先用绝对模式移到中心
    print("  📝 设置绝对模式，移动到中心...")
    client._protocol.connection.send(build_mouse_type_packet(1))
    time.sleep(0.3)
    
    center_x, center_y = video_width // 2, video_height // 2
    packet = build_mouse_event_abs(center_x, center_y, 0)
    print(f"     绝对定位到 ({center_x}, {center_y}): {packet.hex().upper()}")
    client._protocol.connection.send(packet)
    time.sleep(0.5)
    
    frame = client.get_latest_frame(timeout=2.0)
    save_screenshot(frame, "20_mixed_center")
    
    # 切换到相对模式，向右移动
    print("  📝 切换到相对模式，向右移动 100 像素...")
    client._protocol.connection.send(build_mouse_type_packet(0))
    time.sleep(0.3)
    
    for i in range(25):
        packet = build_mouse_event_rel(4, 0, 0)
        client._protocol.connection.send(packet)
        time.sleep(0.01)
    
    time.sleep(0.5)
    
    frame = client.get_latest_frame(timeout=2.0)
    save_screenshot(frame, "21_mixed_right")
    
    print("  ✅ 混合模式测试完成")


def main():
    parser = argparse.ArgumentParser(description="同步 KVM 鼠标模式测试")
    parser.add_argument("--ip", default=Config.kvm_ip, help="KVM IP 地址")
    parser.add_argument("--port", type=int, default=Config.kvm_port, help="KVM 端口")
    parser.add_argument("--channel", type=int, default=Config.kvm_channel, help="通道号")
    parser.add_argument("--username", default=Config.username, help="用户名")
    parser.add_argument("--password", default=Config.password, help="密码")
    args = parser.parse_args()
    
    Config.kvm_ip = args.ip
    Config.kvm_port = args.port
    Config.kvm_channel = args.channel
    Config.username = args.username
    Config.password = args.password
    
    print("=" * 60)
    print("同步 KVM 客户端鼠标模式综合测试")
    print("=" * 60)
    print(f"KVM: {Config.kvm_ip}:{Config.kvm_port}, 通道: {Config.kvm_channel}")
    print("=" * 60)
    
    client = SyncKVMClient()
    
    try:
        print("\n🔌 正在连接...")
        if not client.connect(
            ip=Config.kvm_ip,
            port=Config.kvm_port,
            channel=Config.kvm_channel,
            username=Config.username,
            password=Config.password,
            timeout=30.0
        ):
            print("❌ 连接失败")
            return 1
        
        print("✅ 连接成功!")
        
        # 等待视频帧获取分辨率
        print("\n📺 等待视频流...")
        video_width, video_height = 0, 0
        for _ in range(30):
            time.sleep(0.2)
            frame = client.get_latest_frame(timeout=0)
            if frame is not None:
                video_height, video_width = frame.shape[:2]
                print(f"   ✓ 视频分辨率: {video_width}x{video_height}")
                break
        
        if video_width == 0:
            print("   ⚠️  未获取到视频，使用默认分辨率 1280x1024")
            video_width, video_height = 1280, 1024
        
        # 执行测试
        test_relative_mouse(client)
        test_absolute_mouse(client, video_width, video_height)
        test_mixed_mode(client, video_width, video_height)
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成！")
        print(f"📁 截图保存在: {Config.output_dir}/")
        print("=" * 60)
        print("\n💡 请查看截图，比较不同模式下鼠标位置是否变化：")
        print("   - 相对模式：鼠标应该随移动命令偏移")
        print("   - 绝对模式：鼠标应该跳到指定像素位置")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        return 1
    finally:
        print("\n🔌 断开连接...")
        client.disconnect()
        print("✅ 已断开")


if __name__ == "__main__":
    sys.exit(main())

