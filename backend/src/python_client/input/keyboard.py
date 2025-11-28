"""
Keyboard controller

Provides keyboard event building and X11 keysym mappings
"""

from ..protocol.packets import KeyEventPacket


class KeyboardController:
    """Keyboard event controller"""
    
    # Common X11 keysym values
    KEYSYMS = {
        # Letters
        'a': 0x0061, 'b': 0x0062, 'c': 0x0063, 'd': 0x0064,
        'e': 0x0065, 'f': 0x0066, 'g': 0x0067, 'h': 0x0068,
        'i': 0x0069, 'j': 0x006a, 'k': 0x006b, 'l': 0x006c,
        'm': 0x006d, 'n': 0x006e, 'o': 0x006f, 'p': 0x0070,
        'q': 0x0071, 'r': 0x0072, 's': 0x0073, 't': 0x0074,
        'u': 0x0075, 'v': 0x0076, 'w': 0x0077, 'x': 0x0078,
        'y': 0x0079, 'z': 0x007a,
        
        'A': 0x0041, 'B': 0x0042, 'C': 0x0043, 'D': 0x0044,
        'E': 0x0045, 'F': 0x0046, 'G': 0x0047, 'H': 0x0048,
        'I': 0x0049, 'J': 0x004a, 'K': 0x004b, 'L': 0x004c,
        'M': 0x004d, 'N': 0x004e, 'O': 0x004f, 'P': 0x0050,
        'Q': 0x0051, 'R': 0x0052, 'S': 0x0053, 'T': 0x0054,
        'U': 0x0055, 'V': 0x0056, 'W': 0x0057, 'X': 0x0058,
        'Y': 0x0059, 'Z': 0x005a,
        
        # Numbers
        '0': 0x0030, '1': 0x0031, '2': 0x0032, '3': 0x0033,
        '4': 0x0034, '5': 0x0035, '6': 0x0036, '7': 0x0037,
        '8': 0x0038, '9': 0x0039,
        
        # Function keys
        'F1': 0xffbe, 'F2': 0xffbf, 'F3': 0xffc0, 'F4': 0xffc1,
        'F5': 0xffc2, 'F6': 0xffc3, 'F7': 0xffc4, 'F8': 0xffc5,
        'F9': 0xffc6, 'F10': 0xffc7, 'F11': 0xffc8, 'F12': 0xffc9,
        
        # Special keys
        'Return': 0xff0d, 'Enter': 0xff0d,
        'BackSpace': 0xff08,
        'Tab': 0xff09,
        'Escape': 0xff1b, 'Esc': 0xff1b,
        'Delete': 0xffff,
        'Home': 0xff50,
        'End': 0xff57,
        'Page_Up': 0xff55, 'PageUp': 0xff55,
        'Page_Down': 0xff56, 'PageDown': 0xff56,
        'Left': 0xff51,
        'Up': 0xff52,
        'Right': 0xff53,
        'Down': 0xff54,
        
        # Modifiers
        'Shift_L': 0xffe1, 'Shift_R': 0xffe2,
        'Control_L': 0xffe3, 'Control_R': 0xffe4, 'Ctrl': 0xffe3,
        'Alt_L': 0xffe9, 'Alt_R': 0xffea, 'Alt': 0xffe9,
        'Meta_L': 0xffe7, 'Meta_R': 0xffe8,
        'Super_L': 0xffeb, 'Super_R': 0xffec,
        'Caps_Lock': 0xffe5,
        
        # Symbols
        ' ': 0x0020, 'Space': 0x0020,
        '!': 0x0021, '"': 0x0022, '#': 0x0023, '$': 0x0024,
        '%': 0x0025, '&': 0x0026, "'": 0x0027, '(': 0x0028,
        ')': 0x0029, '*': 0x002a, '+': 0x002b, ',': 0x002c,
        '-': 0x002d, '.': 0x002e, '/': 0x002f,
        ':': 0x003a, ';': 0x003b, '<': 0x003c, '=': 0x003d,
        '>': 0x003e, '?': 0x003f, '@': 0x0040,
        '[': 0x005b, '\\': 0x005c, ']': 0x005d, '^': 0x005e,
        '_': 0x005f, '`': 0x0060,
        '{': 0x007b, '|': 0x007c, '}': 0x007d, '~': 0x007e,
    }
    
    @staticmethod
    def get_keysym(key: str) -> int:
        """
        Get X11 keysym for a key
        
        Args:
            key: Key name or character
            
        Returns:
            X11 keysym value
        """
        return KeyboardController.KEYSYMS.get(key, ord(key) if len(key) == 1 else 0)
    
    @staticmethod
    def create_key_event(key_code: int, down: int) -> bytes:
        """
        Create keyboard event packet
        
        Args:
            key_code: X11 keysym value
            down: 1 for press, 0 for release
            
        Returns:
            Packet bytes
        """
        packet = KeyEventPacket(key_code, down)
        return packet.build_rfb()
    
    @staticmethod
    def create_key_press(key: str) -> bytes:
        """
        Create key press event
        
        Args:
            key: Key name or character
            
        Returns:
            Packet bytes
        """
        keysym = KeyboardController.get_keysym(key)
        return KeyboardController.create_key_event(keysym, KeyEventPacket.DOWN)
    
    @staticmethod
    def create_key_release(key: str) -> bytes:
        """
        Create key release event
        
        Args:
            key: Key name or character
            
        Returns:
            Packet bytes
        """
        keysym = KeyboardController.get_keysym(key)
        return KeyboardController.create_key_event(keysym, KeyEventPacket.UP)


