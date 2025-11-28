#!/usr/bin/env python3
"""
RTSP relay example

Demonstrates connecting to KVM and relaying video via RTSP server
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from video.rtsp_server import KVMClientWithRTSP


async def main():
    """Main example function"""
    
    # Configuration
    KVM_IP = "192.168.1.100"
    KVM_PORT = 5900
    KVM_CHANNEL = 0
    USERNAME = "admin"
    PASSWORD = "123456"
    RTSP_PORT = 8554
    
    # Create client with RTSP server
    client = KVMClientWithRTSP(rtsp_port=RTSP_PORT)
    
    try:
        print(f"🔌 Connecting to KVM at {KVM_IP}:{KVM_PORT}")
        print(f"📡 Starting RTSP server on port {RTSP_PORT}")
        print()
        
        # Connect (this also starts the RTSP server)
        await client.connect(
            ip=KVM_IP,
            port=KVM_PORT,
            channel=KVM_CHANNEL,
            username=USERNAME,
            password=PASSWORD
        )
        
        print("✅ Connected successfully!")
        print()
        print(f"📺 RTSP stream available at:")
        print(f"   rtsp://localhost:{RTSP_PORT}/stream")
        print()
        print("   You can view the stream with:")
        print(f"   vlc rtsp://localhost:{RTSP_PORT}/stream")
        print(f"   ffplay rtsp://localhost:{RTSP_PORT}/stream")
        print()
        print("⚠️  NOTE: This is a placeholder RTSP server.")
        print("   For production use, implement proper RTSP streaming")
        print("   using libraries like gstreamer or aiortsp.")
        print()
        print("📡 Streaming... (Ctrl+C to stop)")
        print()
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping...")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Disconnect
        print("🔌 Disconnecting...")
        await client.disconnect()
        print("✅ Disconnected")
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)


