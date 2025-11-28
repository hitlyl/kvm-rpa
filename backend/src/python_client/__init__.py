"""
KVM Python SDK

A Python SDK for connecting to KVM devices with support for:
- Authentication (VNC, Centralized)
- Keyboard and mouse control
- H.264 video streaming
- Optional RTSP server
"""

__version__ = "1.0.0"
__author__ = "KVM SDK Team"

from .kvm_client import KVMClient

__all__ = ["KVMClient"]


