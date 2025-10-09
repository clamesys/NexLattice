# NexLattice Architecture Documentation

## Overview

NexLattice is a decentralized mesh networking protocol designed for IoT devices, enabling secure peer-to-peer communication without requiring a central gateway. The system implements automatic peer discovery, multi-hop routing, end-to-end encryption, and real-time network monitoring.

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   NexLattice Network                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────┐       ┌──────┐       ┌──────┐                │
│  │Node 1│◄─────►│Node 2│◄─────►│Node 3│                │
│  └───┬──┘       └───┬──┘       └───┬──┘                │
│      │              │              │                     │
│      └──────────────┼──────────────┘                     │
│                     │                                    │
│                 ┌───▼──┐                                 │
│                 │Node 4│                                 │
│                 └───┬──┘                                 │
│                     │                                    │
│                 ┌───▼──┐                                 │
│                 │Node 5│                                 │
│                 └──────┘                                 │
│                     │                                    │
└─────────────────────┼────────────────────────────────────┘
                      │
                      ▼
              ┌───────────────┐
              │   Dashboard   │
              │  (Monitoring) │
              └───────────────┘
```

## Core Components

### 1. Device Layer (ESP32 Nodes)

#### **node_main.py**
- **Purpose**: Main entry point and orchestrator
- **Responsibilities**:
  - Initialize all subsystems (network, crypto, router)
  - Handle incoming messages and dispatch to appropriate handlers
  - Manage periodic tasks (discovery, health checks, stats reporting)
  - Coordinate message sending and receiving

#### **network_manager.py**
- **Purpose**: Low-level network communication
- **Responsibilities**:
  - WiFi connection management
  - UDP broadcast for peer discovery
  - Message transmission (unicast/broadcast)
  - Peer registry management
  - Latency measurement and health monitoring
  - Dashboard communication

#### **crypto_utils.py**
- **Purpose**: Security and encryption
- **Responsibilities**:
  - Key generation (public/private keys)
  - Symmetric encryption (AES-CBC)
  - Session key establishment
  - Message signing and verification
  - Fallback encryption for limited platforms

#### **message_router.py**
- **Purpose**: Message routing and forwarding
- **Responsibilities**:
  - Route calculation and next-hop determination
  - Multi-hop message forwarding
  - Loop prevention (message caching)
  - Routing table management
  - Hop count limiting

### 2. Dashboard Layer (Python/Flask)

#### **app.py**
- **Purpose**: Backend server and API
- **Responsibilities**:
  - Receive node status updates
  - Maintain network state
  - WebSocket communication with frontend
  - REST API endpoints
  - Topology calculation
  - Node timeout detection

#### **index.html & dashboard.js**
- **Purpose**: Web-based visualization
- **Responsibilities**:
  - Real-time network topology visualization (D3.js)
  - Node status display
  - Message log viewing
  - Statistics dashboard
  - WebSocket client connection

## Protocol Design

### Message Types

#### 1. **DISCOVERY**
Broadcast periodically to find new peers.

```json
{
  "type": "DISCOVERY",
  "node_id": "node_001",
  "node_name": "NexLattice Node 1",
  "public_key": "abc123...",
  "timestamp": 1234567890.123
}
```

#### 2. **DISCOVERY_RESPONSE**
Unicast response to discovery broadcast.

```json
{
  "type": "DISCOVERY_RESPONSE",
  "node_id": "node_002",
  "node_name": "NexLattice Node 2",
  "public_key": "def456...",
  "timestamp": 1234567890.456
}
```

#### 3. **KEY_EXCHANGE**
Establish encrypted session between peers.

```json
{
  "type": "KEY_EXCHANGE",
  "node_id": "node_001",
  "session_key": "encrypted_session_key",
  "timestamp": 1234567890.789
}
```

#### 4. **DATA**
Actual message payload (direct or forwarded).

```json
{
  "type": "DATA",
  "source": "node_001",
  "destination": "node_005",
  "payload": "Hello, Node 5!",
  "encrypted": true,
  "hop_count": 2,
  "msg_id": "node_001_1234567890",
  "timestamp": 1234567890.123
}
```

#### 5. **PING/PONG**
Latency measurement and health check.

```json
{
  "type": "PING",
  "node_id": "node_001",
  "timestamp": 1234567890.123
}
```

#### 6. **STATS**
Node status reporting to dashboard.

```json
{
  "type": "STATS",
  "node_id": "node_001",
  "node_name": "NexLattice Node 1",
  "peers": [...],
  "stats": {
    "messages_sent": 42,
    "messages_received": 38,
    "messages_forwarded": 15,
    "uptime": 3600
  },
  "timestamp": 1234567890.123
}
```

## Network Operations

### 1. Peer Discovery Flow

```
Node 1                          Node 2
  |                               |
  |------ DISCOVERY (UDP) ------->|
  |                               |
  |<-- DISCOVERY_RESPONSE --------|
  |                               |
  |------ KEY_EXCHANGE ---------->|
  |                               |
  |<----- KEY_EXCHANGE ------------|
  |                               |
  [Secure session established]
```

### 2. Multi-Hop Routing Flow

```
Node 1 → Node 2 → Node 3 → Node 4 → Node 5

Message path:
1. Node 1: Sends DATA to Node 5 (hop_count=0)
2. Node 2: Receives, increments hop_count=1, forwards
3. Node 3: Receives, increments hop_count=2, forwards
4. Node 4: Receives, increments hop_count=3, forwards
5. Node 5: Receives, processes message
```

### 3. Loop Prevention

Each node maintains a message cache:
- Store `msg_id` (source_node + timestamp) for each forwarded message
- Before forwarding, check if `msg_id` exists in cache
- If exists → drop message (loop detected)
- If not exists → forward and add to cache
- Cache entries expire after TTL (60 seconds)

## Security Model

### Encryption Layers

1. **Transport Layer**: AES-256-CBC for message encryption
2. **Session Layer**: Peer-to-peer session keys via key exchange
3. **Pre-Shared Key (PSK)**: Fallback for initial handshake

### Key Management

```
┌─────────────┐
│  Node Init  │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ Generate Private │
│      Key         │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Derive Public    │
│      Key         │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Share Public Key │
│  via Discovery   │
└──────────────────┘
```

### Authentication Flow

1. Nodes exchange public keys during discovery
2. Session keys derived from shared secrets
3. Each message encrypted with peer's session key
4. Optional message signing for integrity verification

## Performance Characteristics

### Latency

- **Direct peer-to-peer**: ~10-50ms (WiFi RTT)
- **Single hop forward**: +10-30ms per hop
- **Maximum hops**: 5 (configurable)
- **Discovery interval**: 30 seconds
- **Health check interval**: 10 seconds

### Scalability

- **Tested configuration**: 5 nodes
- **Theoretical maximum**: 50+ nodes (limited by WiFi bandwidth)
- **Peer limit per node**: 10 (configurable)
- **Message throughput**: ~100 messages/second per node

### Resource Usage (ESP32)

- **RAM**: ~20-40 KB per node instance
- **Flash**: ~100-150 KB program size
- **CPU**: ~5-10% at idle, ~30-50% under load
- **Network**: ~1-5 KB/s at idle, ~10-50 KB/s under load

## Failure Handling

### Node Failure

1. Peer health checks detect missing PONG responses
2. After timeout (60s), mark peer as disconnected
3. Remove from routing table
4. Trigger route recalculation
5. Dashboard notifies of node offline

### Message Delivery Failure

1. Try direct send to destination
2. If fails, lookup routing table for next hop
3. If no route, flood message to all peers (last resort)
4. Each node attempts forwarding up to max_hops
5. After max_hops, message dropped

### Network Partition

- Nodes continue operating in isolated partitions
- When connectivity restored, discovery re-establishes links
- Routing tables automatically rebuild
- No data loss for messages within partition

## Dashboard Communication

### Update Protocol

```
ESP32 Node                    Dashboard Server
    |                               |
    |---- HTTP POST /api/update --->|
    |    (node stats + peers)       |
    |                               |
    |<------- 200 OK ---------------|
    |                               |
    |                          [WebSocket]
    |                               |
    |                          Broadcast to
    |                          Web Clients
```

### Data Flow

1. **Node → Dashboard**: HTTP POST every 60 seconds
2. **Dashboard → Clients**: WebSocket push on updates
3. **Clients → Dashboard**: WebSocket for initial state

## Configuration

### Node Configuration (config.json)

```json
{
  "node_id": "unique_node_identifier",
  "node_name": "Human-readable name",
  "wifi_ssid": "Network SSID",
  "wifi_password": "Network password",
  "discovery_port": 5000,
  "message_port": 5001,
  "dashboard_ip": "192.168.1.100",
  "dashboard_port": 8080,
  "encryption_enabled": true,
  "max_peers": 10,
  "discovery_interval": 30,
  "health_check_interval": 10
}
```

## Future Enhancements

### Planned Features

1. **Adaptive Routing**: Dynamic route selection based on latency/bandwidth
2. **QoS Support**: Priority queues for different message types
3. **Mesh Healing**: Automatic network reconfiguration on failures
4. **IPv6 Support**: Larger address space for scalability
5. **Energy Optimization**: Sleep modes and power-aware routing
6. **Certificate-based Auth**: PKI infrastructure for production deployments
7. **OTA Updates**: Over-the-air firmware updates through mesh

### Research Topics

- **Routing Algorithms**: AODV, OLSR, or hybrid approaches
- **Congestion Control**: TCP-like mechanisms for mesh
- **Multicast**: Efficient group communication
- **Time Synchronization**: Distributed clock synchronization
- **Blockchain Integration**: Immutable message logging

## Testing Recommendations

1. **Unit Tests**: Test each component independently
2. **Integration Tests**: Test component interactions
3. **Network Tests**: Simulate various topologies
4. **Stress Tests**: High message rates and node counts
5. **Failure Tests**: Random node/link failures
6. **Security Tests**: Penetration testing and encryption validation

## Deployment Guide

See `setup_instructions.md` for detailed deployment steps.

## Troubleshooting

See `protocol_design.md` for protocol-level debugging information.

---

**Version**: 1.0  
**Last Updated**: October 2025  
**License**: MIT

