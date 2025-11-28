#!/usr/bin/env python3
"""
Simple KVM client example

Demonstrates basic connection, authentication, and video reception
"""

import asyncio
import sys
import os

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
    
    # Create client
    client = KVMClient()
    
    # Define video frame callback
    def on_video_frame(frame_data, width, height, encoding_type):
        """Called when a video frame is received"""
        print(f"📹 Received frame: {width}x{height}, size: {len(frame_data)} bytes, encoding: {encoding_type}")
        
        # Here you can:
        # - Save frame to file
        # - Decode with FFmpeg/OpenCV
        # - Stream via RTSP
        # - etc.
    
    # Define connection callback
    def on_connection_event(event, data):
        """Called on connection events"""
        if event == 'ready':
            print("✅ Connection ready!")
        elif event == 'auth_failed':
            print(f"❌ Authentication failed: {data['reason']}")
        elif event == 'error':
            print(f"❌ Connection error: {data['reason']}")
    
    # Set callbacks
    client.set_video_callback(on_video_frame)
    client.set_connection_callback(on_connection_event)
    
    try:
        print(f"🔌 Connecting to KVM at {KVM_IP}:{KVM_PORT}")
        print(f"   Channel: {KVM_CHANNEL}")
        print(f"   Username: {USERNAME}")
        
        # Connect to KVM
        await client.connect(
            ip=KVM_IP,
            port=KVM_PORT,
            channel=KVM_CHANNEL,
            username=USERNAME,
            password=PASSWORD,
            timeout=10.0
        )
        
        print("✅ Connected successfully!")
        print()
        
        # Example: Send keyboard events
        print("⌨️  Sending keyboard events...")
        from input.keyboard import KeyboardController
        
        # Type "Hello"
        for char in "Hello":
            key_code = KeyboardController.get_keysym(char)
            client.send_key_press(key_code)
            await asyncio.sleep(0.05)
            client.send_key_release(key_code)
            await asyncio.sleep(0.05)
        
        print("   Sent: 'Hello'")
        print()
        
        # Example: Send mouse events
        print("🖱️  Sending mouse events...")
        
        # Move to center of screen (absolute coordinates)
        client.send_mouse_move(32768, 32768, mouse_type=1)
        await asyncio.sleep(0.1)
        
        # Click left button
        client.send_mouse_click(32768, 32768, button=0x01, mouse_type=1)
        
        print("   Moved to center and clicked")
        print()
        
        # Keep connection alive and receive video
        print("📺 Receiving video frames... (Ctrl+C to stop)")
        print()
        
        try:
            while True:
                await asyncio.sleep(1)
                
                # Print stats every second
                stats = client.get_video_stats()
                print(f"   Stats: {stats['frame_count']} frames, "
                      f"{stats['width']}x{stats['height']}", end='\r')
        
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping...")
        
    except TimeoutError as e:
        print(f"\n❌ Connection timeout: {e}")
        return 1
    except ConnectionError as e:
        print(f"\n❌ Connection error: {e}")
        return 1
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


