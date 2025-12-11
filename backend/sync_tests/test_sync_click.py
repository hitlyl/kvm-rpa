#!/usr/bin/env python3
"""
同步 KVM 客户端鼠标点击测试

与 tests/test_click_button.py 功能相同，但使用同步客户端实现
"""

import sys
import os
import time
import logging
import argparse

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加 src 路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from sync_client import SyncKVMClient

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV 不可用，无法保存截图")


# 默认配置
class Config:
    """测试配置"""
    kvm_ip = "192.168.0.100"
    kvm_port = 5900
    kvm_channel = 0
    username = "admin"
    password = "123456"
    click_x = 150
    click_y = 287


def save_screenshot(frame, filename: str):
    """保存截图"""
    if not CV2_AVAILABLE or frame is None:
        return
    
    output_dir = os.path.join(os.path.dirname(__file__), 'sync_click_screenshots')
    os.makedirs(output_dir, exist_ok=True)
    
    filepath = os.path.join(output_dir, filename)
    cv2.imwrite(filepath, frame)
    logger.info(f"截图已保存: {filepath}")


def test_sync_click(config: Config):
    """测试同步鼠标点击"""
    logger.info("=" * 60)
    logger.info("同步 KVM 客户端鼠标点击测试")
    logger.info("=" * 60)
    
    # 创建客户端
    client = SyncKVMClient()
    
    try:
        # 连接 KVM
        logger.info(f"正在连接 KVM: {config.kvm_ip}:{config.kvm_port}")
        
        if not client.connect(
            ip=config.kvm_ip,
            port=config.kvm_port,
            channel=config.kvm_channel,
            username=config.username,
            password=config.password,
            timeout=10.0
        ):
            logger.error("连接失败")
            return False
        
        logger.info("连接成功！")
        
        # 设置鼠标为绝对坐标模式
        logger.info("设置鼠标为绝对坐标模式...")
        client.set_mouse_type(1)
        time.sleep(0.5)
        logger.info("鼠标模式设置完成")
        
        # 等待视频帧
        logger.info("等待视频帧...")
        for i in range(20):
            frame = client.get_latest_frame(timeout=0)
            if frame is not None:
                logger.info(f"收到视频帧: {frame.shape[1]}x{frame.shape[0]}")
                save_screenshot(frame, "before_click.jpg")
                break
            time.sleep(0.5)
        else:
            logger.warning("未收到视频帧，继续测试...")
        
        # 执行3次点击测试
        for click_num in range(1, 4):
            logger.info(f"\n--- 第 {click_num} 次点击 ---")
            
            # 移动到位置
            logger.info(f"移动到位置: ({config.click_x}, {config.click_y})")
            client.send_mouse_event_raw(config.click_x, config.click_y, 0)
            time.sleep(0.1)
            
            # 按下左键
            logger.info("按下左键")
            client.send_mouse_event_raw(config.click_x, config.click_y, 0x01)
            time.sleep(0.05)
            
            # 释放左键
            logger.info("释放左键")
            client.send_mouse_event_raw(config.click_x, config.click_y, 0)
            time.sleep(0.05)
            
            logger.info(f"点击 {click_num} 完成")
            
            # 等待并截图
            time.sleep(1.0)
            frame = client.get_latest_frame(timeout=2.0)
            if frame is not None:
                save_screenshot(frame, f"after_click_{click_num}.jpg")
        
        logger.info("\n" + "=" * 60)
        logger.info("测试完成！")
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error(f"测试异常: {e}", exc_info=True)
        return False
        
    finally:
        # 断开连接
        logger.info("断开连接...")
        client.disconnect()
        logger.info("已断开连接")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='同步 KVM 客户端鼠标点击测试')
    parser.add_argument('--ip', default="192.168.0.100", help='KVM IP 地址')
    parser.add_argument('--port', type=int, default=5900, help='KVM 端口')
    parser.add_argument('--channel', type=int, default=0, help='通道号')
    parser.add_argument('--username', default="admin", help='用户名')
    parser.add_argument('--password', default="123456", help='密码')
    parser.add_argument('--x', type=int, default=150, help='点击 X 坐标')
    parser.add_argument('--y', type=int, default=287, help='点击 Y 坐标')
    parser.add_argument('--debug', action='store_true', help='启用调试日志')
    
    args = parser.parse_args()
    
    # 创建配置
    config = Config()
    config.kvm_ip = args.ip
    config.kvm_port = args.port
    config.kvm_channel = args.channel
    config.username = args.username
    config.password = args.password
    config.click_x = args.x
    config.click_y = args.y
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 运行测试
    success = test_sync_click(config)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
