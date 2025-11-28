# KVM Python SDK Examples

This directory contains example scripts demonstrating how to use the KVM Python SDK.

## Examples

### 1. simple_client.py

Basic connection, authentication, keyboard/mouse control, and video reception.

```bash
python examples/simple_client.py
```

Features demonstrated:
- Connecting to KVM device
- Authentication with username/password
- Receiving video frames
- Sending keyboard events
- Sending mouse events
- Connection callbacks

### 2. save_video.py

Save received H.264 video stream to a file.

```bash
python examples/save_video.py
```

Features demonstrated:
- Saving H.264 frames to file
- Frame counting
- File size tracking

The saved file can be played with:
```bash
ffplay kvm_video_*.h264
vlc kvm_video_*.h264
```

### 3. rtsp_relay.py

Relay KVM video stream as RTSP server (placeholder implementation).

```bash
python examples/rtsp_relay.py
```

**Note:** This is a placeholder implementation. For production use, implement proper RTSP streaming using libraries like:
- gstreamer-python
- aiortsp
- python-vlc

## Configuration

Edit the following variables in each example:

```python
KVM_IP = "192.168.1.100"     # KVM device IP
KVM_PORT = 5900               # KVM device port
KVM_CHANNEL = 0               # Channel number
USERNAME = "admin"            # Authentication username
PASSWORD = "123456"           # Authentication password
```

## Requirements

Make sure you have installed the dependencies:

```bash
pip install -r ../requirements.txt
```

## Keyboard Keysym Values

For keyboard events, use X11 keysym values. Common values are available in `input/keyboard.py`:

```python
from input.keyboard import KeyboardController

# Get keysym for a character
key_code = KeyboardController.get_keysym('a')  # Returns 0x0061

# Send key event
client.send_key_event(key_code, down=1)  # Press
client.send_key_event(key_code, down=0)  # Release
```

## Mouse Coordinates

### Absolute Mode (mouse_type=1)
Coordinates range from 0-65535:
- (0, 0) = top-left corner
- (32768, 32768) = center
- (65535, 65535) = bottom-right corner

### Relative Mode (mouse_type=0)
Coordinates are offsets from current position:
- Positive values move right/down
- Negative values move left/up

## Button Masks

```python
BUTTON_LEFT = 0x01
BUTTON_MIDDLE = 0x02
BUTTON_RIGHT = 0x04
BUTTON_WHEEL_UP = 0x08
BUTTON_WHEEL_DOWN = 0x10
```

Multiple buttons can be combined with OR:
```python
button_mask = 0x01 | 0x04  # Left and right buttons
```

## Error Handling

All examples include basic error handling. For production use, implement more robust error handling and retry logic.

## Troubleshooting

### Connection Issues
- Verify IP and port are correct
- Check firewall settings
- Ensure KVM device is powered on and network-accessible

### Authentication Failures
- Verify username and password
- Check which security types the device supports
- Ensure channel number is correct

### No Video Frames
- Video callback must be set before connecting
- Check that device is sending video
- Verify encoding type is supported (H.264)


