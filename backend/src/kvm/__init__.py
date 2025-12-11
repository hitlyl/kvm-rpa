"""KVM 客户端模块

提供 KVM 设备连接和控制功能。
使用 KVMManager 管理 KVM 连接池。
"""

from .kvm_manager import KVMManager, get_kvm_manager

__all__ = ['KVMManager', 'get_kvm_manager']
