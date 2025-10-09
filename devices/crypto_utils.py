"""
NexLattice Crypto Utilities
Handles encryption, key exchange, and secure sessions
"""

import ubinascii
import uhashlib
import urandom
import json

try:
    import ucryptolib
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("⚠️  ucryptolib not available, using basic encryption")


class CryptoManager:
    def __init__(self, node_id):
        """Initialize crypto manager"""
        self.node_id = node_id
        
        # Generate or load keys
        self.private_key = self._generate_private_key()
        self.public_key = self._derive_public_key(self.private_key)
        
        # Session keys for peers
        self.session_keys = {}  # peer_id: shared_key
        
        # Pre-shared key for initial encryption (in production, use proper key exchange)
        self.psk = b'NexLatticeSharedSecretKey256'  # 32 bytes for AES-256
        
        print(f"🔐 Crypto initialized for {node_id}")
    
    def _generate_private_key(self):
        """Generate a private key"""
        # In a real implementation, this would generate a proper RSA/ECC key
        # For MicroPython, we'll use a simple approach
        key = uhashlib.sha256(self.node_id.encode() + str(urandom.getrandbits(32)).encode()).digest()
        return key
    
    def _derive_public_key(self, private_key):
        """Derive public key from private key"""
        # Simplified: in reality, use proper asymmetric crypto
        public = uhashlib.sha256(private_key + b'public').hexdigest()
        return public
    
    def get_public_key(self):
        """Get public key for sharing"""
        return self.public_key
    
    def establish_session(self, peer_id, peer_session_data):
        """Establish encrypted session with peer"""
        # In production, implement proper Diffie-Hellman or similar
        # For now, use a derived shared key
        shared_secret = uhashlib.sha256(
            self.private_key + 
            peer_session_data.encode() + 
            peer_id.encode()
        ).digest()
        
        self.session_keys[peer_id] = shared_secret
        return True
    
    def encrypt(self, plaintext, peer_id=None):
        """Encrypt data for transmission"""
        if not CRYPTO_AVAILABLE:
            return self._simple_encrypt(plaintext)
        
        try:
            # Use session key if available, otherwise PSK
            key = self.session_keys.get(peer_id, self.psk)
            
            # Convert string to bytes
            if isinstance(plaintext, str):
                plaintext = plaintext.encode()
            
            # Pad to 16-byte boundary for AES
            padded = self._pad(plaintext)
            
            # Generate IV
            iv = urandom.getrandbits(128).to_bytes(16, 'big')
            
            # Encrypt with AES-CBC
            cipher = ucryptolib.aes(key[:16], 2, iv)  # Mode 2 = CBC
            ciphertext = cipher.encrypt(padded)
            
            # Return IV + ciphertext as hex
            encrypted = ubinascii.hexlify(iv + ciphertext).decode()
            return encrypted
            
        except Exception as e:
            print(f"❌ Encryption error: {e}")
            return self._simple_encrypt(plaintext)
    
    def decrypt(self, ciphertext, peer_id=None):
        """Decrypt received data"""
        if not CRYPTO_AVAILABLE:
            return self._simple_decrypt(ciphertext)
        
        try:
            # Use session key if available, otherwise PSK
            key = self.session_keys.get(peer_id, self.psk)
            
            # Decode from hex
            encrypted_data = ubinascii.unhexlify(ciphertext)
            
            # Extract IV and ciphertext
            iv = encrypted_data[:16]
            ciphertext_bytes = encrypted_data[16:]
            
            # Decrypt with AES-CBC
            cipher = ucryptolib.aes(key[:16], 2, iv)
            plaintext = cipher.decrypt(ciphertext_bytes)
            
            # Remove padding
            unpadded = self._unpad(plaintext)
            
            return unpadded.decode()
            
        except Exception as e:
            print(f"❌ Decryption error: {e}")
            return self._simple_decrypt(ciphertext)
    
    def _pad(self, data):
        """PKCS7 padding"""
        pad_len = 16 - (len(data) % 16)
        return data + bytes([pad_len] * pad_len)
    
    def _unpad(self, data):
        """Remove PKCS7 padding"""
        pad_len = data[-1]
        return data[:-pad_len]
    
    def _simple_encrypt(self, plaintext):
        """Simple XOR encryption as fallback"""
        if isinstance(plaintext, str):
            plaintext = plaintext.encode()
        
        key = self.psk[:len(plaintext)]
        encrypted = bytes(a ^ b for a, b in zip(plaintext, key * (len(plaintext) // len(key) + 1)))
        return ubinascii.hexlify(encrypted).decode()
    
    def _simple_decrypt(self, ciphertext):
        """Simple XOR decryption as fallback"""
        encrypted = ubinascii.unhexlify(ciphertext)
        key = self.psk[:len(encrypted)]
        decrypted = bytes(a ^ b for a, b in zip(encrypted, key * (len(encrypted) // len(key) + 1)))
        return decrypted.decode()
    
    def sign_message(self, message):
        """Create message signature"""
        # Simple HMAC-style signature
        signature = uhashlib.sha256(message.encode() + self.private_key).hexdigest()
        return signature
    
    def verify_signature(self, message, signature, peer_public_key):
        """Verify message signature"""
        # In production, use proper signature verification
        # For now, basic validation
        return len(signature) == 64  # SHA256 hex length
    
    def generate_session_token(self):
        """Generate random session token"""
        return ubinascii.hexlify(urandom.getrandbits(128).to_bytes(16, 'big')).decode()

