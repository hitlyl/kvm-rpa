"""
VNC Authentication implementation

Port of VncAuthPacket.java to Python
"""

from .des_cipher import DesCipher
from ..utils.hex_utils import HexUtils


class VncAuth:
    """VNC authentication with DES encryption"""
    
    CHALLENGE_LENGTH = 16
    
    def __init__(self, challenge: bytes, username: str, password: str):
        """
        Initialize VNC authentication
        
        Args:
            challenge: 16-byte challenge from server
            username: Username for authentication
            password: Password for authentication
        """
        if len(challenge) != self.CHALLENGE_LENGTH:
            raise ValueError(f"Challenge must be {self.CHALLENGE_LENGTH} bytes")
        
        self.challenge = bytearray(challenge)
        self.username = username
        self.password = password
    
    def encrypt(self) -> bytes:
        """
        Encrypt the challenge with password
        
        Returns:
            Encrypted authentication response packet
        """
        # Prepare DES key from password (pad to 8 bytes)
        key = bytearray(8)
        password_bytes = self.password.encode('utf-8')
        pwd_len = min(len(password_bytes), 8)
        
        for i in range(8):
            if i < pwd_len:
                key[i] = password_bytes[i]
            else:
                key[i] = 0
        
        # Create DES cipher
        des = DesCipher(bytes(key))
        
        # Encrypt challenge in two 8-byte blocks
        for j in range(0, 16, 8):
            des.encrypt_in_place(self.challenge, j, j)
        
        # Build response packet:
        # - 4 bytes: length (little-endian) = 16 + username_length + 1
        # - username bytes (ASCII)
        # - 1 byte: 0xAA separator
        # - 16 bytes: encrypted challenge
        
        username_bytes = self.username.encode('ascii')
        total_length = 16 + len(username_bytes) + 1
        
        length_bytes = HexUtils.int_to_bytes_little_endian(total_length)
        
        # Build final packet
        result = bytearray()
        result.extend(length_bytes)
        result.extend(username_bytes)
        result.append(0xAA)  # Separator
        result.extend(self.challenge)
        
        return bytes(result)


class CentralizeAuth:
    """Centralized authentication"""
    
    def __init__(self, username: str, password: str):
        """
        Initialize centralized authentication
        
        Args:
            username: Username for authentication
            password: Password for authentication
        """
        self.username = username
        self.password = password
    
    def build_user_account_packet(self) -> bytes:
        """
        Build user account packet for centralized auth
        
        Returns:
            User account packet (17 bytes)
        """
        username_bytes = self.username.encode('ascii')
        
        # Packet format:
        # - 1 byte: 0x10 (16)
        # - 16 bytes: username (padded with zeros)
        
        user_msg = bytearray(17)
        user_msg[0] = 16
        
        # Copy username bytes (max 16 bytes)
        for i in range(min(len(username_bytes), 16)):
            user_msg[i + 1] = username_bytes[i]
        
        return bytes(user_msg)


