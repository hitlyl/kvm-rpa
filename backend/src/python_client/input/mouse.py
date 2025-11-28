"""
Mouse controller

Provides mouse event building
"""

from ..protocol.packets import MouseEventPacket


class MouseController:
    """Mouse event controller"""
    
    # Mouse types
    TYPE_RELATIVE = 0
    TYPE_ABSOLUTE = 1
    
    # Button masks
    BUTTON_LEFT = 0x01
    BUTTON_MIDDLE = 0x02
    BUTTON_RIGHT = 0x04
    BUTTON_WHEEL_UP = 0x08
    BUTTON_WHEEL_DOWN = 0x10
    
    @staticmethod
    def create_mouse_event(x: int, y: int, button_mask: int, mouse_type: int) -> bytes:
        """
        Create mouse event packet
        
        Args:
            x: X coordinate
            y: Y coordinate
            button_mask: Button state mask
            mouse_type: 0=relative, 1=absolute
            
        Returns:
            Packet bytes
        """
        packet = MouseEventPacket(x, y, button_mask, mouse_type)
        return packet.build_rfb()
    
    @staticmethod
    def create_absolute_mouse_event(x: int, y: int, buttons: int = 0) -> bytes:
        """
        Create absolute mouse event
        
        Args:
            x: Absolute X coordinate (0-65535)
            y: Absolute Y coordinate (0-65535)
            buttons: Button mask
            
        Returns:
            Packet bytes
        """
        return MouseController.create_mouse_event(
            x, y, buttons, MouseController.TYPE_ABSOLUTE
        )
    
    @staticmethod
    def create_relative_mouse_event(dx: int, dy: int, buttons: int = 0) -> bytes:
        """
        Create relative mouse event
        
        Args:
            dx: Relative X movement
            dy: Relative Y movement
            buttons: Button mask
            
        Returns:
            Packet bytes
        """
        return MouseController.create_mouse_event(
            dx, dy, buttons, MouseController.TYPE_RELATIVE
        )
    
    @staticmethod
    def create_mouse_click(x: int, y: int, button: int = BUTTON_LEFT, 
                          mouse_type: int = TYPE_ABSOLUTE) -> list:
        """
        Create mouse click sequence (press + release)
        
        Args:
            x: X coordinate
            y: Y coordinate
            button: Button to click
            mouse_type: Mouse type
            
        Returns:
            List of packet bytes [press, release]
        """
        press = MouseController.create_mouse_event(x, y, button, mouse_type)
        release = MouseController.create_mouse_event(x, y, 0, mouse_type)
        return [press, release]


