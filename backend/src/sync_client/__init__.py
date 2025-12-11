"""
同步 KVM 客户端包

提供纯同步的 KVM 客户端实现，避免异步调度的复杂性。

主要类：
- SyncKVMClient: 同步 KVM 客户端
- SyncConnection: 同步 TCP 连接
- SyncProtocolHandler: 同步协议处理器
- FrameBuffer: 线程安全帧缓存

使用示例：
    from sync_client import SyncKVMClient
    
    client = SyncKVMClient()
    if client.connect('192.168.0.100', 5900, 0, 'admin', '123456'):
        # 设置绝对坐标模式
        client.set_mouse_type(1)
        time.sleep(0.5)
        
        # 鼠标点击
        client.send_mouse_event_raw(100, 200, 0)  # 移动
        time.sleep(0.1)
        client.send_mouse_event_raw(100, 200, 1)  # 左键按下
        time.sleep(0.05)
        client.send_mouse_event_raw(100, 200, 0)  # 释放
        
        # 获取视频帧
        frame = client.get_latest_frame()
        
        client.disconnect()
"""

from .sync_kvm_client import SyncKVMClient
from .sync_connection import SyncConnection
from .sync_protocol import SyncProtocolHandler
from .frame_buffer import FrameBuffer

__all__ = [
    'SyncKVMClient',
    'SyncConnection', 
    'SyncProtocolHandler',
    'FrameBuffer'
]

__version__ = '1.0.0'

