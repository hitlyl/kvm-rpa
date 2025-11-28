"""
Video frame handler

Manages video frame reception and callbacks
"""

import logging
from typing import Optional, Callable


logger = logging.getLogger(__name__)


class VideoHandler:
    """Video frame handler with callback support"""
    
    def __init__(self):
        """Initialize video handler"""
        self.on_frame: Optional[Callable[[bytes, int, int, int], None]] = None
        self.frame_count = 0
        self.current_width = 0
        self.current_height = 0
        self.encoding_type = 0
    
    def set_frame_callback(self, callback: Callable[[bytes, int, int, int], None]):
        """
        Set callback for video frames
        
        Args:
            callback: Function(frame_data: bytes, width: int, height: int, encoding_type: int)
        """
        self.on_frame = callback
    
    def handle_frame(self, frame_data: bytes, width: int, height: int, encoding_type: int):
        """
        Handle received video frame
        
        Args:
            frame_data: H.264 frame data
            width: Frame width
            height: Frame height
            encoding_type: Encoding type
        """
        self.frame_count += 1
        
        # Track resolution changes
        if width != self.current_width or height != self.current_height:
            logger.info(f"Resolution changed: {self.current_width}x{self.current_height} -> {width}x{height}")
            self.current_width = width
            self.current_height = height
        
        self.encoding_type = encoding_type
        
        # Invoke callback
        if self.on_frame:
            try:
                self.on_frame(frame_data, width, height, encoding_type)
            except Exception as e:
                logger.error(f"Error in frame callback: {e}", exc_info=True)
    
    def get_stats(self) -> dict:
        """
        Get video statistics
        
        Returns:
            Dictionary with stats
        """
        return {
            'frame_count': self.frame_count,
            'width': self.current_width,
            'height': self.current_height,
            'encoding_type': self.encoding_type
        }


