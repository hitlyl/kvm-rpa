"""
Hex and byte conversion utilities

Port of HexUtils.java to Python
"""

import struct


class HexUtils:
    """Utility class for byte/hex/int conversions"""
    
    @staticmethod
    def bytes_to_hex_string(data: bytes) -> str:
        """Convert bytes to hex string"""
        if not data:
            return ""
        return data.hex().upper()
    
    @staticmethod
    def hex_string_to_bytes(hex_string: str) -> bytes:
        """Convert hex string to bytes"""
        if not hex_string:
            return b""
        # Remove any spaces or formatting
        hex_string = hex_string.replace(" ", "").replace(":", "")
        if len(hex_string) % 2 != 0:
            hex_string = "0" + hex_string
        return bytes.fromhex(hex_string)
    
    @staticmethod
    def int_to_bytes_big_endian(value: int) -> bytes:
        """Convert int to 4 bytes (big-endian)"""
        return struct.pack(">I", value)
    
    @staticmethod
    def int_to_bytes_little_endian(value: int) -> bytes:
        """Convert int to 4 bytes (little-endian)"""
        return struct.pack("<I", value)
    
    @staticmethod
    def bytes_to_int_big_endian(data: bytes, offset: int = 0) -> int:
        """Convert 4 bytes to int (big-endian)"""
        return struct.unpack(">I", data[offset:offset+4])[0]
    
    @staticmethod
    def bytes_to_int_little_endian(data: bytes, offset: int = 0) -> int:
        """Convert 4 bytes to int (little-endian)"""
        return struct.unpack("<I", data[offset:offset+4])[0]
    
    @staticmethod
    def unsigned_short_to_bytes(value: int) -> bytes:
        """Convert unsigned short to 2 bytes (big-endian)"""
        return struct.pack(">H", value & 0xFFFF)
    
    @staticmethod
    def bytes_to_unsigned_short(data: bytes, offset: int = 0) -> int:
        """Convert 2 bytes to unsigned short (big-endian)"""
        return struct.unpack(">H", data[offset:offset+2])[0]
    
    @staticmethod
    def signed_short_to_bytes(value: int) -> bytes:
        """Convert signed short to 2 bytes (big-endian)"""
        return struct.pack(">h", value)
    
    @staticmethod
    def bytes_to_signed_short(data: bytes, offset: int = 0) -> int:
        """Convert 2 bytes to signed short (big-endian)"""
        return struct.unpack(">h", data[offset:offset+2])[0]
    
    @staticmethod
    def bytes_to_ascii(data: bytes, offset: int = 0, length: int = None) -> str:
        """Convert bytes to ASCII string"""
        if length is None:
            length = len(data) - offset
        return data[offset:offset+length].decode('ascii', errors='ignore').strip()
    
    @staticmethod
    def int_to_4_bytes_big_endian(value: int) -> bytes:
        """Convert int to 4 bytes array (big-endian)"""
        return struct.pack(">I", value)
    
    @staticmethod
    def short_to_2_bytes_big_endian(value: int) -> bytes:
        """Convert short to 2 bytes array (big-endian)"""
        return struct.pack(">H", value & 0xFFFF)


