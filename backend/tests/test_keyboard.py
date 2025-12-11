#!/usr/bin/env python3
"""
测试键盘输入 - 发送 a-z 字符

基于 Java EnKeyMap.java 的键盘映射
"""

import asyncio
import sys
import os
import logging

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from python_client import KVMClient
from python_client.protocol.packets import KeyEventPacket
from python_client.utils.hex_utils import HexUtils

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# KVM 配置
KVM_IP = "192.168.0.100"
KVM_PORT = 5900
KVM_CHANNEL = 0
KVM_USERNAME = "admin"
KVM_PASSWORD = "123456"

# 键盘映射 - 基于 Java EnKeyMap.java
# 注意：Java 代码使用 ASCII 大写字母值 (65-90) 代表小写字母 a-z
# 这似乎是一种自定义映射，可能是设备特定的
KEY_MAP = {
    'a': 65, 'b': 66, 'c': 67, 'd': 68, 'e': 69,
    'f': 70, 'g': 71, 'h': 72, 'i': 73, 'j': 74,
    'k': 75, 'l': 76, 'm': 77, 'n': 78, 'o': 79,
    'p': 80, 'q': 81, 'r': 82, 's': 83, 't': 84,
    'u': 85, 'v': 86, 'w': 87, 'x': 88, 'y': 89,
    'z': 90,
}

# X11 keysym 映射 (标准 VNC 协议)
X11_KEY_MAP = {
    'a': 0x61, 'b': 0x62, 'c': 0x63, 'd': 0x64, 'e': 0x65,
    'f': 0x66, 'g': 0x67, 'h': 0x68, 'i': 0x69, 'j': 0x6a,
    'k': 0x6b, 'l': 0x6c, 'm': 0x6d, 'n': 0x6e, 'o': 0x6f,
    'p': 0x70, 'q': 0x71, 'r': 0x72, 's': 0x73, 't': 0x74,
    'u': 0x75, 'v': 0x76, 'w': 0x77, 'x': 0x78, 'y': 0x79,
    'z': 0x7a,
    ' ': 0x20, '\n': 0xff0d,  # 回车
}

# 特殊键 (Shift 键)
SHIFT_KEY = 65505


def verify_packet_format():
    """验证数据包格式"""
    print("📋 键盘数据包格式验证:")
    print()
    
    # Python KeyEventPacket 参数: (key_code, down)
    # Java KeyEventPacket 参数: (down, key)
    
    # 测试按下 'a' (key code = 65 in Java)
    # Python: KeyEventPacket(key_code=65, down=1)
    packet_down = KeyEventPacket(key_code=65, down=KeyEventPacket.DOWN)
    data_down = packet_down.build_rfb()
    print(f"  按下 'a' (Java key=65): {HexUtils.bytes_to_hex_string(data_down)}")
    print(f"  格式: [type=04][down=01][padding][key=00000041]")
    expected_down = bytes.fromhex("0401000000000041")
    if data_down == expected_down:
        print("  ✓ 匹配!")
    else:
        print(f"  ✗ 不匹配! 生成: {HexUtils.bytes_to_hex_string(data_down)}")
    print()
    
    # 测试释放 'a'
    packet_up = KeyEventPacket(key_code=65, down=KeyEventPacket.UP)
    data_up = packet_up.build_rfb()
    print(f"  释放 'a' (Java key=65): {HexUtils.bytes_to_hex_string(data_up)}")
    expected_up = bytes.fromhex("0400000000000041")
    if data_up == expected_up:
        print("  ✓ 匹配!")
    else:
        print(f"  ✗ 不匹配! 生成: {HexUtils.bytes_to_hex_string(data_up)}")
    print()


async def test_keyboard():
    """测试键盘输入"""
    
    print("=" * 70)
    print("KVM 键盘测试 - 发送 a-z 字符")
    print("=" * 70)
    print()
    
    # 验证数据包格式
    verify_packet_format()
    
    # 连接 KVM
    print("=" * 70)
    print("🔌 连接到 KVM...")
    client = KVMClient()
    
    try:
        connected = await asyncio.wait_for(
            client.connect(KVM_IP, KVM_PORT, KVM_CHANNEL, KVM_USERNAME, KVM_PASSWORD),
            timeout=10
        )
        
        if not connected:
            print("❌ 连接失败!")
            return
        
        print("✅ 连接成功!")
        print()
        
        # 等待连接稳定
        await asyncio.sleep(0.5)
        
        # 测试1: 使用 Java 的键码映射
        print("=" * 70)
        print("测试1: 使用 Java EnKeyMap 映射发送 a-z")
        print("       (key codes: 65-90, 对应 ASCII 大写 A-Z)")
        print("=" * 70)
        print()
        
        print("⌨️  发送: ", end="", flush=True)
        for char in 'abcdefghijklmnopqrstuvwxyz':
            key_code = KEY_MAP[char]
            # 按下
            client.send_key_press(key_code)
            await asyncio.sleep(0.05)
            # 释放
            client.send_key_release(key_code)
            await asyncio.sleep(0.05)
            print(char, end="", flush=True)
        print()
        print()
        
        await asyncio.sleep(1)
        
        # 测试2: 使用标准 X11 keysym
        print("=" * 70)
        print("测试2: 使用标准 X11 keysym 发送 a-z")
        print("       (key codes: 0x61-0x7a, 标准 VNC keysym)")
        print("=" * 70)
        print()
        
        print("⌨️  发送: ", end="", flush=True)
        for char in 'abcdefghijklmnopqrstuvwxyz':
            key_code = X11_KEY_MAP[char]
            # 按下
            client.send_key_press(key_code)
            await asyncio.sleep(0.05)
            # 释放
            client.send_key_release(key_code)
            await asyncio.sleep(0.05)
            print(char, end="", flush=True)
        print()
        print()
        
        await asyncio.sleep(1)
        
        # 测试3: 发送空格和回车
        print("=" * 70)
        print("测试3: 发送空格和回车")
        print("=" * 70)
        print()
        
        print("⌨️  发送空格...")
        client.send_key_press(X11_KEY_MAP[' '])
        await asyncio.sleep(0.05)
        client.send_key_release(X11_KEY_MAP[' '])
        await asyncio.sleep(0.2)
        
        print("⌨️  发送回车...")
        client.send_key_press(X11_KEY_MAP['\n'])
        await asyncio.sleep(0.05)
        client.send_key_release(X11_KEY_MAP['\n'])
        await asyncio.sleep(0.2)
        
        print()
        
        # 测试4: 发送单词 "hello"
        print("=" * 70)
        print("测试4: 发送 'hello'")
        print("=" * 70)
        print()
        
        print("⌨️  发送: ", end="", flush=True)
        for char in 'hello':
            # 使用 X11 keysym
            key_code = X11_KEY_MAP[char]
            client.send_key_press(key_code)
            await asyncio.sleep(0.05)
            client.send_key_release(key_code)
            await asyncio.sleep(0.05)
            print(char, end="", flush=True)
        print()
        print()
        
        print("=" * 70)
        print("✅ 键盘测试完成!")
        print("=" * 70)
        print()
        print("请检查目标设备上是否有文字输入。")
        print("如果没有输入，可能需要:")
        print("  1. 确保目标设备有文本输入焦点（如打开记事本）")
        print("  2. 检查 KVM 设备是否正确配置")
        print()
        
        await asyncio.sleep(1)
        
    except asyncio.TimeoutError:
        print("❌ 连接超时!")
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🔌 断开连接...")
        await client.disconnect()
        print("✅ 完成")


if __name__ == "__main__":
    asyncio.run(test_keyboard())

