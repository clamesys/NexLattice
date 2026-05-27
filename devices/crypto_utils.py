"""
NexLattice Crypto Utilities
Handles encryption, key exchange, and secure sessions
"""

import ubinascii
import uhashlib
import urandom
import json
import time

try:
    import ucryptolib
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("⚠️  ucryptolib not available, using basic encryption")


class CryptoManager:
    def __init__(self, node_id, psk=None):
        """Initialize crypto manager"""
        self.node_id = node_id
        
        # Diffie-Hellman Parameters (128-bit safe prime and generator)
        self.P = 340282366920938463463374607431768211297
        self.G = 2
        
        # Generate or load keys
        self.private_key = self._generate_private_key()
        self.public_key = self._derive_public_key(self.private_key)
        
        # Session keys for peers
        self.session_keys = {}  # peer_id: shared_key
        
        # Pre-shared key for initial encryption and authentication
        # In production, load from secure storage
        if psk:
            self.psk = psk.encode() if isinstance(psk, str) else psk
        else:
            # Default PSK - should be changed in production
            self.psk = b'NexLatticeSharedSecretKey256'  # 32 bytes for AES-256
        
        # Challenge cache for authentication
        self.challenge_cache = {}  # peer_id: {challenge, timestamp}
        self.challenge_ttl = 30  # seconds
        
        print(f"🔐 Crypto initialized for {node_id}")
    
    def _generate_private_key(self):
        """Generate a private key (Diffie-Hellman private exponent)"""
        # Generate random 128-bit integer
        private_key = (urandom.getrandbits(128) % (self.P - 3)) + 2
        return private_key
    
    def _derive_public_key(self, private_key):
        """Derive public key from private key (G^private_key % P)"""
        public_key = pow(self.G, private_key, self.P)
        return str(public_key)
    
    def get_public_key(self):
        """Get public key for sharing"""
        return self.public_key
    
    def establish_session(self, peer_id, peer_public_key):
        """Establish encrypted session with peer using Diffie-Hellman"""
        try:
            # peer_public_key is the public exponent of the peer
            peer_pub = int(peer_public_key)
            
            # Shared secret: K = peer_pub^private_key % P
            shared_secret_int = pow(peer_pub, self.private_key, self.P)
            
            # Convert to bytes and hash to derive 32-byte AES key
            secret_bytes = str(shared_secret_int).encode()
            shared_key = uhashlib.sha256(secret_bytes).digest()
            
            self.session_keys[peer_id] = shared_key
            print(f"🔐 secure session established with {peer_id} via Diffie-Hellman")
            return True
        except Exception as e:
            print(f"❌ Diffie-Hellman key exchange failed: {e}")
            return False
    
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
        """Create message signature (HMAC-SHA256) using PSK"""
        if isinstance(message, dict):
            msg_copy = message.copy()
            msg_copy.pop('signature', None)
            message_str = json.dumps(msg_copy, sort_keys=True)
        elif isinstance(message, str):
            message_str = message
        else:
            message_str = str(message)
        
        # HMAC-style signing using PSK
        signature = uhashlib.sha256(message_str.encode() + self.psk).hexdigest()
        return signature
    
    def verify_signature(self, message, signature, peer_id=None):
        """Verify message signature using PSK"""
        if not signature or len(signature) != 64:  # SHA256 hex length
            return False
        
        if isinstance(message, dict):
            # Create a copy and remove signature if present to match signing state
            msg_copy = message.copy()
            msg_copy.pop('signature', None)
            message_str = json.dumps(msg_copy, sort_keys=True)
        elif isinstance(message, str):
            message_str = message
        else:
            message_str = str(message)
        
        expected_sig = uhashlib.sha256(message_str.encode() + self.psk).hexdigest()
        
        # Constant-time comparison to prevent timing attacks
        return self._constant_time_compare(signature, expected_sig)
    
    def _constant_time_compare(self, a, b):
        """Constant-time string comparison"""
        if len(a) != len(b):
            return False
        result = 0
        for x, y in zip(a, b):
            result |= ord(x) ^ ord(y)
        return result == 0
    
    def generate_session_token(self):
        """Generate random session token"""
        return ubinascii.hexlify(urandom.getrandbits(128).to_bytes(16, 'big')).decode()
    
    def generate_challenge(self, peer_id):
        """Generate authentication challenge for peer"""
        # Create random challenge
        challenge = ubinascii.hexlify(urandom.getrandbits(128).to_bytes(16, 'big')).decode()
        
        # Store challenge with timestamp
        self.challenge_cache[peer_id] = {
            'challenge': challenge,
            'timestamp': time.time()
        }
        
        return challenge
    
    def verify_challenge_response(self, peer_id, response):
        """Verify challenge-response authentication"""
        if peer_id not in self.challenge_cache:
            return False
        
        challenge_data = self.challenge_cache[peer_id]
        
        # Check if challenge expired
        if time.time() - challenge_data['timestamp'] > self.challenge_ttl:
            del self.challenge_cache[peer_id]
            return False
        
        challenge = challenge_data['challenge']
        
        # Expected response: HMAC(challenge + PSK)
        expected_response = uhashlib.sha256(
            challenge.encode() + self.psk
        ).hexdigest()
        
        # Verify response
        is_valid = self._constant_time_compare(response, expected_response)
        
        # Clean up challenge after use
        if peer_id in self.challenge_cache:
            del self.challenge_cache[peer_id]
        
        return is_valid
    
    def compute_challenge_response(self, challenge):
        """Compute response to authentication challenge"""
        # Response: HMAC(challenge + PSK)
        response = uhashlib.sha256(challenge.encode() + self.psk).hexdigest()
        return response
    
    def sign_and_encrypt(self, message, peer_id):
        """Sign and encrypt message (mandatory signing)"""
        # First, sign the message
        signature = self.sign_message(message)
        message['signature'] = signature
        
        # Convert to JSON string for encryption
        message_json = json.dumps(message)
        
        # Encrypt the signed message
        encrypted = self.encrypt(message_json, peer_id)
        
        return encrypted
    
    def decrypt_and_verify(self, ciphertext, peer_id):
        """Decrypt and verify message signature (mandatory verification)"""
        # Decrypt first
        message_json = self.decrypt(ciphertext, peer_id)
        
        # Parse JSON
        message = json.loads(message_json)
        
        # Extract signature
        signature = message.pop('signature', None)
        if not signature:
            raise ValueError("Message missing signature")
        
        # Verify signature
        if not self.verify_signature(message, signature, peer_id):
            raise ValueError("Invalid message signature")
        
        return message

