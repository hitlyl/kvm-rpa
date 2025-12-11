#!/usr/bin/env python3
"""
同步 KVM 客户端鼠标完整测试

同时测试三种坐标模式：
1. 像素坐标（与 Java ViewerSample.encodeMouseEvent 一致）
2. 归一化坐标 0-65535（与 Python send_mouse_event 一致）
3. 相对坐标（与 Java SendMouseEventDemo 一致）

通过截图验证哪种模式有效。
"""

import sys
import os
import time
import argparse
import logging
import struct

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

import cv2
from sync_client import SyncKVMClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Config:
    kvm_ip = "192.168.0.100"
    kvm_port = 5900
    kvm_channel = 0
    username = "admin"
    password = "123456"
    output_dir = "mouse_complete_test"


def save_screenshot(frame, label: str) -> bool:
    if frame is None:
        print(f"  ⚠️  无帧数据: {label}")
        return False
    os.makedirs(Config.output_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{label}.jpg"
    filepath = os.path.join(Config.output_dir, filename)
    cv2.imwrite(filepath, frame)
    h, w = frame.shape[:2]
    print(f"  ✅ 保存: {filename} ({w}x{h})")
    return True


def send_mouse_packet(client, packet: bytes, description: str):
    """发送鼠标数据包并打印详情"""
    print(f"     {description}")
    print(f"     数据包: {packet.hex().upper()}")
    client._protocol.connection.send(packet)


def build_abs_pixel(x: int, y: int, mask: int = 0) -> bytes:
    """绝对模式 - 像素坐标（与 Java ViewerSample 一致）"""
    x = max(0, x)
    y = max(0, y)
    packet = bytearray(6)
    packet[0] = 5  # PointerEvent
    packet[1] = mask & 0xFF
    packet[2:4] = struct.pack(">H", x & 0xFFFF)  # big-endian unsigned short
    packet[4:6] = struct.pack(">H", y & 0xFFFF)
    return bytes(packet)


def build_abs_normalized(x: int, y: int, mask: int = 0) -> bytes:
    """绝对模式 - 归一化坐标 0-65535（与 Python MouseEventPacket 一致）"""
    x = max(0, min(65535, x))
    y = max(0, min(65535, y))
    packet = bytearray(6)
    packet[0] = 5  # PointerEvent
    packet[1] = mask & 0xFF
    packet[2:4] = struct.pack(">H", x & 0xFFFF)
    packet[4:6] = struct.pack(">H", y & 0xFFFF)
    return bytes(packet)


def build_rel(dx: int, dy: int, mask: int = 0) -> bytes:
    """相对模式 - 偏移量（与 Java SendMouseEventDemo 一致）"""
    packet = bytearray(6)
    packet[0] = 5  # PointerEvent
    packet[1] = (mask | 0x80) & 0xFF  # 相对模式标志
    packet[2:4] = struct.pack(">h", dx)  # big-endian signed short
    packet[4:6] = struct.pack(">h", dy)
    return bytes(packet)


def build_mouse_type(mouse_type: int) -> bytes:
    """鼠标类型设置包"""
    packet = bytearray(4)
    packet[0] = 110  # SetMouseType (0x6E)
    packet[1] = mouse_type
    return bytes(packet)


def pixel_to_normalized(px: int, py: int, width: int, height: int) -> tuple:
    """像素坐标转归一化坐标"""
    nx = int(px / width * 65535)
    ny = int(py / height * 65535)
    return (nx, ny)


def test_mode_A(client, vw, vh):
    """测试A: 绝对模式 + 像素坐标"""
    print("\n" + "=" * 60)
    print("🔬 测试 A: 绝对模式 + 像素坐标")
    print("   （与 Java ViewerSample.encodeMouseEvent 一致）")
    print("=" * 60)
    
    # 设置绝对模式
    print("\n  📝 设置鼠标绝对模式...")
    client._protocol.connection.send(build_mouse_type(1))
    time.sleep(0.5)
    
    positions = [
        ("A1_center", vw // 2, vh // 2),
        ("A2_topleft", 100, 100),
        ("A3_topright", vw - 100, 100),
        ("A4_bottomright", vw - 100, vh - 100),
    ]
    
    for label, px, py in positions:
        print(f"\n  测试 {label}: 像素({px}, {py})")
        packet = build_abs_pixel(px, py, 0)
        send_mouse_packet(client, packet, f"像素坐标: ({px}, {py})")
        time.sleep(0.8)
        frame = client.get_latest_frame(timeout=2.0)
        save_screenshot(frame, label)


def test_mode_B(client, vw, vh):
    """测试B: 绝对模式 + 归一化坐标 (0-65535)"""
    print("\n" + "=" * 60)
    print("🔬 测试 B: 绝对模式 + 归一化坐标 (0-65535)")
    print("   （与 Python test_mouse_with_screenshot.py 一致）")
    print("=" * 60)
    
    # 设置绝对模式
    print("\n  📝 设置鼠标绝对模式...")
    client._protocol.connection.send(build_mouse_type(1))
    time.sleep(0.5)
    
    pixel_positions = [
        ("B1_center", vw // 2, vh // 2),
        ("B2_topleft", 100, 100),
        ("B3_topright", vw - 100, 100),
        ("B4_bottomright", vw - 100, vh - 100),
    ]
    
    for label, px, py in pixel_positions:
        nx, ny = pixel_to_normalized(px, py, vw, vh)
        print(f"\n  测试 {label}: 像素({px}, {py}) -> 归一化({nx}, {ny})")
        packet = build_abs_normalized(nx, ny, 0)
        send_mouse_packet(client, packet, f"归一化坐标: ({nx}, {ny})")
        time.sleep(0.8)
        frame = client.get_latest_frame(timeout=2.0)
        save_screenshot(frame, label)


def test_mode_C(client, vw, vh):
    """测试C: 相对模式 + 偏移量"""
    print("\n" + "=" * 60)
    print("🔬 测试 C: 相对模式 + 偏移量")
    print("   （与 Java SendMouseEventDemo 一致）")
    print("=" * 60)
    
    # 设置相对模式
    print("\n  📝 设置鼠标相对模式...")
    client._protocol.connection.send(build_mouse_type(0))
    time.sleep(0.5)
    
    # 截图：起始位置
    print("\n  测试 C1: 起始位置")
    frame = client.get_latest_frame(timeout=2.0)
    save_screenshot(frame, "C1_start")
    
    # 向右下移动
    print("\n  测试 C2: 向右下移动 200 像素...")
    for _ in range(50):
        packet = build_rel(4, 4, 0)
        client._protocol.connection.send(packet)
        time.sleep(0.01)
    time.sleep(0.5)
    frame = client.get_latest_frame(timeout=2.0)
    save_screenshot(frame, "C2_after_rightdown")
    
    # 向左上移动
    print("\n  测试 C3: 向左上移动 200 像素...")
    for _ in range(50):
        packet = build_rel(-4, -4, 0)
        client._protocol.connection.send(packet)
        time.sleep(0.01)
    time.sleep(0.5)
    frame = client.get_latest_frame(timeout=2.0)
    save_screenshot(frame, "C3_after_leftup")


def test_mode_D(client, vw, vh):
    """测试D: 不设置鼠标类型，直接发送"""
    print("\n" + "=" * 60)
    print("🔬 测试 D: 不设置鼠标类型，直接发送")
    print("   （测试设备默认行为）")
    print("=" * 60)
    
    positions = [
        ("D1_pixel_center", "pixel", vw // 2, vh // 2),
        ("D2_norm_center", "norm", vw // 2, vh // 2),
    ]
    
    for label, mode, px, py in positions:
        print(f"\n  测试 {label}:")
        if mode == "pixel":
            packet = build_abs_pixel(px, py, 0)
            send_mouse_packet(client, packet, f"像素坐标 (不带 0x80): ({px}, {py})")
        else:
            nx, ny = pixel_to_normalized(px, py, vw, vh)
            packet = build_abs_normalized(nx, ny, 0)
            send_mouse_packet(client, packet, f"归一化坐标 (不带 0x80): ({nx}, {ny})")
        time.sleep(0.8)
        frame = client.get_latest_frame(timeout=2.0)
        save_screenshot(frame, label)


def main():
    parser = argparse.ArgumentParser(description="同步 KVM 鼠标完整测试")
    parser.add_argument("--ip", default=Config.kvm_ip)
    parser.add_argument("--port", type=int, default=Config.kvm_port)
    parser.add_argument("--channel", type=int, default=Config.kvm_channel)
    parser.add_argument("--username", default=Config.username)
    parser.add_argument("--password", default=Config.password)
    args = parser.parse_args()
    
    Config.kvm_ip = args.ip
    Config.kvm_port = args.port
    Config.kvm_channel = args.channel
    Config.username = args.username
    Config.password = args.password
    
    print("=" * 60)
    print("同步 KVM 客户端鼠标完整测试")
    print("=" * 60)
    print(f"KVM: {Config.kvm_ip}:{Config.kvm_port}")
    print("=" * 60)
    
    client = SyncKVMClient()
    
    try:
        print("\n🔌 连接中...")
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
        
        # 获取视频分辨率
        print("\n📺 等待视频...")
        vw, vh = 0, 0
        for _ in range(30):
            time.sleep(0.2)
            frame = client.get_latest_frame(timeout=0)
            if frame is not None:
                vh, vw = frame.shape[:2]
                print(f"   ✓ 分辨率: {vw}x{vh}")
                break
        
        if vw == 0:
            print("   ⚠️  使用默认分辨率 1280x1024")
            vw, vh = 1280, 1024
        
        # 执行所有测试
        test_mode_A(client, vw, vh)  # 绝对 + 像素
        test_mode_B(client, vw, vh)  # 绝对 + 归一化
        test_mode_C(client, vw, vh)  # 相对 + 偏移
        test_mode_D(client, vw, vh)  # 不设置类型
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成!")
        print(f"📁 截图目录: {Config.output_dir}/")
        print("=" * 60)
        print("\n💡 请检查截图，确定哪种模式下鼠标位置有变化:")
        print("   - 测试 A (绝对+像素): 如果有效，使用像素坐标")
        print("   - 测试 B (绝对+归一化): 如果有效，使用 0-65535 坐标")
        print("   - 测试 C (相对+偏移): 如果有效，鼠标会相对移动")
        print("   - 测试 D (不设置类型): 测试设备默认行为")
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










