"""
DES Cipher implementation for VNC authentication

Port of DesCipher.java to Python
Uses pydes library for DES encryption
"""

import pyDes


class DesCipher:
    """DES encryption/decryption for VNC authentication"""
    
    def __init__(self, key: bytes):
        """
        Initialize DES cipher with key
        
        Args:
            key: 8-byte DES key
        """
        if len(key) != 8:
            raise ValueError("DES key must be 8 bytes")
        
        # VNC uses DES with bit-reversed key bytes
        # Each byte needs to be bit-reversed
        reversed_key = bytes([self._reverse_bits(b) for b in key])
        
        # Create DES cipher instance
        self.des = pyDes.des(reversed_key)
    
    @staticmethod
    def _reverse_bits(byte: int) -> int:
        """Reverse bits in a byte (VNC-specific requirement)"""
        result = 0
        for i in range(8):
            if byte & (1 << i):
                result |= 1 << (7 - i)
        return result
    
    def encrypt(self, data: bytes, offset: int = 0) -> bytes:
        """
        Encrypt 8 bytes of data
        
        Args:
            data: Data to encrypt
            offset: Offset in data to start encryption
            
        Returns:
            Encrypted 8 bytes
        """
        block = data[offset:offset+8]
        if len(block) != 8:
            # Pad with zeros if needed
            block = block + b'\x00' * (8 - len(block))
        
        return self.des.encrypt(block)
    
    def encrypt_in_place(self, data: bytearray, src_offset: int, dst_offset: int):
        """
        Encrypt 8 bytes in place
        
        Args:
            data: Bytearray to encrypt in place
            src_offset: Source offset
            dst_offset: Destination offset
        """
        block = bytes(data[src_offset:src_offset+8])
        encrypted = self.des.encrypt(block)
        data[dst_offset:dst_offset+8] = encrypted
    
    def decrypt(self, data: bytes, offset: int = 0) -> bytes:
        """
        Decrypt 8 bytes of data
        
        Args:
            data: Data to decrypt
            offset: Offset in data to start decryption
            
        Returns:
            Decrypted 8 bytes
        """
        block = data[offset:offset+8]
        return self.des.decrypt(block)


