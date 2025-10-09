# NexLattice Protocol Design

## Protocol Overview

NexLattice implements a lightweight, application-layer mesh networking protocol on top of standard WiFi (802.11). The protocol is designed for:

- **Decentralization**: No single point of failure
- **Security**: End-to-end encryption by default
- **Reliability**: Multi-hop routing with acknowledgments
- **Low Latency**: Optimized for real-time communication
- **Simplicity**: Easy to implement on resource-constrained devices

## Protocol Stack

```
┌─────────────────────────────────┐
│   Application Layer             │
│   (User Messages)               │
├─────────────────────────────────┤
│   NexLattice Protocol Layer     │
│   - Discovery                   │
│   - Routing                     │
│   - Encryption                  │
├─────────────────────────────────┤
│   Transport Layer (UDP/TCP)     │
├─────────────────────────────────┤
│   Network Layer (IP)            │
├─────────────────────────────────┤
│   Link Layer (WiFi 802.11)      │
└─────────────────────────────────┘
```

## Message Format

### Base Message Structure

All NexLattice messages are JSON-encoded with the following base structure:

```json
{
  "type": "MESSAGE_TYPE",
  "node_id": "sender_node_id",
  "timestamp": 1234567890.123,
  ...type-specific fields...
}
```

### Field Specifications

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Message type identifier |
| `node_id` | string | Yes | Sending node's unique identifier |
| `timestamp` | float | Yes | Unix timestamp with milliseconds |

## Discovery Protocol

### Purpose
Enable nodes to automatically find and connect to peers without central coordination.

### Mechanism
- **Broadcasting**: UDP broadcast on discovery port (5000)
- **Interval**: Every 30 seconds (configurable)
- **Response**: Unicast response to sender

### Discovery Message

```json
{
  "type": "DISCOVERY",
  "node_id": "node_001",
  "node_name": "Living Room Sensor",
  "public_key": "04a1b2c3d4e5f6...",
  "timestamp": 1234567890.123,
  "capabilities": ["routing", "encryption"],
  "version": "1.0.0"
}
```

### Discovery Response

```json
{
  "type": "DISCOVERY_RESPONSE",
  "node_id": "node_002",
  "node_name": "Kitchen Hub",
  "public_key": "04f6e5d4c3b2a1...",
  "timestamp": 1234567890.456,
  "capabilities": ["routing", "encryption", "gateway"],
  "version": "1.0.0"
}
```

### Discovery State Machine

```
[INIT] ---> [BROADCASTING] ---> [LISTENING]
              ^                      |
              |                      |
              +----------<-----------+
              (every 30 seconds)
```

### Peer Addition Logic

1. Receive DISCOVERY or DISCOVERY_RESPONSE
2. Validate message format and timestamp
3. Check if peer already exists in peer table
4. If new peer:
   - Add to peer table
   - Store public key
   - Initialize session establishment
5. If existing peer:
   - Update last_seen timestamp
   - Update peer information if changed

## Routing Protocol

### Routing Algorithm

NexLattice uses a **simple hop-by-hop distance-vector routing**:

1. **Direct Route**: If destination is in peer list, send directly
2. **Routing Table Lookup**: Check routing table for next hop
3. **Flooding (Fallback)**: If no route found, flood to all peers

### Routing Table Structure

```python
routing_table = {
    "destination_node_id": {
        "next_hop": "next_node_id",
        "metric": 1,  # hop count
        "updated": timestamp
    }
}
```

### Routing Message Flow

```
Source Node                Intermediate Node              Destination Node
    |                             |                              |
    |------ DATA (hop=0) -------->|                              |
    |                             |                              |
    |                             |------ DATA (hop=1) --------->|
    |                             |                              |
    |                             |<------- ACK (optional) ------|
    |                             |                              |
    |<------ ACK (optional) ------|                              |
```

### Routing Rules

1. **Maximum Hops**: Messages dropped after 5 hops (configurable)
2. **Loop Prevention**: Message ID cache prevents routing loops
3. **Hop Count Increment**: Each forward increments hop_count by 1
4. **TTL**: Messages expire after cache_ttl (60 seconds)

### Route Discovery

NexLattice uses **implicit route discovery**:
- Routes learned through discovery responses
- No explicit route request/reply messages
- Routing table updated when peers announce themselves

### Data Message Format

```json
{
  "type": "DATA",
  "source": "node_001",
  "destination": "node_005",
  "payload": "encrypted_data_here",
  "encrypted": true,
  "hop_count": 0,
  "msg_id": "node_001_1234567890123",
  "timestamp": 1234567890.123,
  "ttl": 60
}
```

## Security Protocol

### Encryption Scheme

**Algorithm**: AES-256-CBC (or AES-128-CBC for MicroPython)

### Key Hierarchy

```
Master Keys (per node)
  └── Private Key (generated)
       └── Public Key (derived)
            └── Session Keys (per peer)
                 └── Message Encryption Keys
```

### Key Exchange Protocol

#### Phase 1: Public Key Exchange
During discovery, nodes exchange public keys in plaintext.

#### Phase 2: Session Key Establishment

```json
{
  "type": "KEY_EXCHANGE",
  "node_id": "node_001",
  "session_key": "encrypted_with_peer_public_key",
  "nonce": "random_nonce",
  "timestamp": 1234567890.123
}
```

#### Phase 3: Secure Communication
All subsequent DATA messages encrypted with session key.

### Encryption Process

```python
def encrypt(plaintext, peer_id):
    # 1. Get session key for peer
    key = session_keys[peer_id]
    
    # 2. Pad plaintext (PKCS7)
    padded = pad(plaintext)
    
    # 3. Generate random IV
    iv = random_bytes(16)
    
    # 4. Encrypt with AES-CBC
    cipher = AES(key, mode=CBC, iv=iv)
    ciphertext = cipher.encrypt(padded)
    
    # 5. Return IV + ciphertext
    return iv + ciphertext
```

### Decryption Process

```python
def decrypt(ciphertext, peer_id):
    # 1. Get session key for peer
    key = session_keys[peer_id]
    
    # 2. Extract IV and ciphertext
    iv = ciphertext[:16]
    encrypted = ciphertext[16:]
    
    # 3. Decrypt with AES-CBC
    cipher = AES(key, mode=CBC, iv=iv)
    padded = cipher.decrypt(encrypted)
    
    # 4. Remove padding
    plaintext = unpad(padded)
    
    return plaintext
```

### Pre-Shared Key (PSK)

For initial handshake before session establishment:
```python
PSK = b'NexLatticeSharedSecretKey256'  # 32 bytes
```

**Note**: In production, PSK should be:
- Unique per deployment
- Securely distributed
- Rotated periodically

### Message Authentication

Optional HMAC for message integrity:

```json
{
  "type": "DATA",
  "source": "node_001",
  "destination": "node_005",
  "payload": "encrypted_data",
  "signature": "hmac_sha256_signature",
  "timestamp": 1234567890.123
}
```

## Health Monitoring Protocol

### Ping/Pong Mechanism

**Purpose**: Measure latency and verify peer connectivity

#### Ping Message

```json
{
  "type": "PING",
  "node_id": "node_001",
  "timestamp": 1234567890.123,
  "sequence": 42
}
```

#### Pong Response

```json
{
  "type": "PONG",
  "node_id": "node_002",
  "timestamp": 1234567890.456,
  "sequence": 42
}
```

### Latency Calculation

```python
latency = (pong_timestamp - ping_timestamp) * 1000  # milliseconds
```

### Peer Health States

| State | Condition | Action |
|-------|-----------|--------|
| **Connected** | Last seen < 60s | Normal operation |
| **Stale** | Last seen 60-120s | Send ping |
| **Disconnected** | Last seen > 120s | Remove from routing table |

### Health Check Interval

- **Ping interval**: 10 seconds
- **Timeout threshold**: 120 seconds
- **Max retries**: 3

## Dashboard Communication Protocol

### Node Status Update

**Method**: HTTP POST  
**Endpoint**: `/api/update_node`  
**Frequency**: Every 60 seconds

```json
{
  "type": "STATS",
  "node_id": "node_001",
  "node_name": "Living Room Sensor",
  "peers": [
    {
      "id": "node_002",
      "name": "Kitchen Hub",
      "ip": "192.168.1.102",
      "last_seen": 1234567890.123,
      "latency": 23.5,
      "connected": true
    }
  ],
  "stats": {
    "messages_sent": 42,
    "messages_received": 38,
    "messages_forwarded": 15,
    "uptime": 3600
  },
  "timestamp": 1234567890.123
}
```

### Dashboard Response

```json
{
  "success": true,
  "timestamp": 1234567890.456
}
```

### WebSocket Events

Dashboard pushes updates to web clients via WebSocket:

#### Events from Server

| Event | Payload | Description |
|-------|---------|-------------|
| `initial_state` | Network state | Sent on client connect |
| `node_update` | Node info | Node status changed |
| `node_status` | Status change | Node online/offline |
| `new_message` | Message data | New message logged |

#### Events from Client

| Event | Payload | Description |
|-------|---------|-------------|
| `connect` | None | Client connected |
| `disconnect` | None | Client disconnected |
| `request_update` | None | Manual refresh request |

## Error Handling

### Error Codes

| Code | Description | Recovery Action |
|------|-------------|-----------------|
| `E001` | Malformed JSON | Drop packet |
| `E002` | Unknown message type | Log and ignore |
| `E003` | Decryption failed | Request key exchange |
| `E004` | Max hops exceeded | Drop packet |
| `E005` | Routing loop detected | Drop packet |
| `E006` | Peer not found | Trigger discovery |
| `E007` | Network timeout | Retry transmission |

### Error Message Format

```json
{
  "type": "ERROR",
  "node_id": "node_001",
  "error_code": "E003",
  "error_message": "Decryption failed",
  "original_message_id": "node_002_1234567890",
  "timestamp": 1234567890.123
}
```

## Performance Optimization

### Message Batching

Multiple small messages can be batched:

```json
{
  "type": "BATCH",
  "node_id": "node_001",
  "messages": [
    {...message1...},
    {...message2...},
    {...message3...}
  ],
  "timestamp": 1234567890.123
}
```

### Compression

For large payloads, optional compression:

```json
{
  "type": "DATA",
  "source": "node_001",
  "destination": "node_005",
  "payload": "compressed_data",
  "compressed": true,
  "compression_type": "zlib",
  "original_size": 1024,
  "timestamp": 1234567890.123
}
```

## Protocol Versioning

### Version Negotiation

Nodes announce protocol version in discovery:

```json
{
  "type": "DISCOVERY",
  "node_id": "node_001",
  "version": "1.0.0",
  "supported_versions": ["1.0.0", "0.9.0"],
  ...
}
```

### Backward Compatibility

- Minor version changes: Optional features
- Major version changes: Breaking changes
- Nodes negotiate to highest common version

## Debugging and Diagnostics

### Debug Message Types

For development and troubleshooting:

```json
{
  "type": "DEBUG",
  "node_id": "node_001",
  "debug_type": "routing_table_dump",
  "data": {...routing_table...},
  "timestamp": 1234567890.123
}
```

### Trace Messages

For message path tracking:

```json
{
  "type": "DATA",
  "source": "node_001",
  "destination": "node_005",
  "payload": "data",
  "trace": [
    "node_001",
    "node_002",
    "node_003"
  ],
  "timestamp": 1234567890.123
}
```

## Protocol Extensions

### Future Protocol Features

1. **Multicast Groups**: Group messaging support
2. **QoS Levels**: Priority-based message delivery
3. **Acknowledgments**: Reliable message delivery
4. **Flow Control**: Congestion management
5. **Neighbor Discovery**: Enhanced peer finding
6. **Route Optimization**: Better path selection

---

**Protocol Version**: 1.0.0  
**Specification Status**: Draft  
**Last Updated**: October 2025

