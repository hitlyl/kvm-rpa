#!/usr/bin/env python3
"""
Save video example

Demonstrates saving received H.264 frames to a file
"""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kvm_client import KVMClient


async def main():
    """Main example function"""
    
    # Configuration
    KVM_IP = "192.168.1.100"
    KVM_PORT = 5900
    KVM_CHANNEL = 0
    USERNAME = "admin"
    PASSWORD = "123456"
    
    # Output file
    output_file = f"kvm_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.h264"
    
    # Create client
    client = KVMClient()
    
    # Open output file
    video_file = open(output_file, 'wb')
    frame_count = 0
    
    # Define video frame callback
    def on_video_frame(frame_data, width, height, encoding_type):
        """Called when a video frame is received"""
        nonlocal frame_count
        frame_count += 1
        
        # Write H.264 frame to file
        video_file.write(frame_data)
        video_file.flush()
        
        if frame_count % 30 == 0:  # Print every 30 frames
            print(f"📹 Saved {frame_count} frames ({width}x{height})")
    
    # Set callback
    client.set_video_callback(on_video_frame)
    
    try:
        print(f"🔌 Connecting to KVM at {KVM_IP}:{KVM_PORT}")
        print(f"💾 Saving video to: {output_file}")
        print()
        
        # Connect to KVM
        await client.connect(
            ip=KVM_IP,
            port=KVM_PORT,
            channel=KVM_CHANNEL,
            username=USERNAME,
            password=PASSWORD
        )
        
        print("✅ Connected successfully!")
        print("📺 Recording video... (Ctrl+C to stop)")
        print()
        
        try:
            while True:
                await asyncio.sleep(1)
        
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping recording...")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Close video file
        video_file.close()
        
        # Disconnect
        print("🔌 Disconnecting...")
        await client.disconnect()
        
        print(f"\n✅ Saved {frame_count} frames to {output_file}")
        print(f"   File size: {os.path.getsize(output_file) / 1024 / 1024:.2f} MB")
        print()
        print("   You can play the video with:")
        print(f"   ffplay {output_file}")
        print(f"   vlc {output_file}")
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)


