# NexLattice Architecture - Mermaid Diagrams

## 1. Overall System Architecture

```mermaid
graph TB
    subgraph "IoT Devices Layer"
        N1[ESP32 Node 1]
        N2[ESP32 Node 2]
        N3[ESP32 Node 3]
        N4[ESP32 Node 4]
        N5[ESP32 Node 5]
    end
    
    subgraph "WiFi Mesh Network"
        N1 <-->|Encrypted Messages| N2
        N2 <-->|Encrypted Messages| N3
        N3 <-->|Encrypted Messages| N4
        N4 <-->|Encrypted Messages| N5
        N1 -.->|Discovery Broadcast| N3
        N2 -.->|Discovery Broadcast| N5
    end
    
    subgraph "Monitoring Layer"
        Dashboard[Web Dashboard<br/>Flask + SocketIO]
        WebClient[Web Browser<br/>D3.js Visualization]
    end
    
    N1 -->|HTTP Status| Dashboard
    N2 -->|HTTP Status| Dashboard
    N3 -->|HTTP Status| Dashboard
    N4 -->|HTTP Status| Dashboard
    N5 -->|HTTP Status| Dashboard
    
    Dashboard <-->|WebSocket| WebClient
    
    style N1 fill:#10b981,stroke:#059669,color:#fff
    style N2 fill:#10b981,stroke:#059669,color:#fff
    style N3 fill:#10b981,stroke:#059669,color:#fff
    style N4 fill:#10b981,stroke:#059669,color:#fff
    style N5 fill:#10b981,stroke:#059669,color:#fff
    style Dashboard fill:#34d399,stroke:#059669,color:#000
    style WebClient fill:#6ee7b7,stroke:#059669,color:#000
```

## 2. Node Internal Architecture

```mermaid
graph LR
    subgraph "ESP32 Node"
        Main[node_main.py<br/>Main Controller]
        
        subgraph "Core Managers"
            NetMgr[network_manager.py<br/>Network Manager]
            CryptoMgr[crypto_utils.py<br/>Crypto Manager]
            Router[message_router.py<br/>Message Router]
        end
        
        subgraph "Network Services"
            Discovery[UDP Discovery<br/>Port 5000]
            Messages[UDP Messaging<br/>Port 5001]
            Dashboard[HTTP Client<br/>Stats Reporter]
        end
        
        subgraph "Data Stores"
            PeerList[(Peer List)]
            RoutingTable[(Routing Table)]
            MsgCache[(Message Cache)]
            SessionKeys[(Session Keys)]
        end
        
        Main --> NetMgr
        Main --> CryptoMgr
        Main --> Router
        
        NetMgr --> Discovery
        NetMgr --> Messages
        NetMgr --> Dashboard
        NetMgr --> PeerList
        
        Router --> RoutingTable
        Router --> MsgCache
        Router --> NetMgr
        
        CryptoMgr --> SessionKeys
    end
    
    WiFi[WiFi Network] <--> Discovery
    WiFi <--> Messages
    DashServer[Dashboard Server] <--> Dashboard
    
    style Main fill:#10b981,stroke:#059669,color:#fff
    style NetMgr fill:#34d399,stroke:#059669,color:#000
    style CryptoMgr fill:#34d399,stroke:#059669,color:#000
    style Router fill:#34d399,stroke:#059669,color:#000
```

## 3. Message Flow - Discovery Process

```mermaid
sequenceDiagram
    participant N1 as Node 1
    participant N2 as Node 2
    participant N3 as Node 3
    
    Note over N1,N3: Discovery Phase
    
    N1->>N1: Generate Keys
    N2->>N2: Generate Keys
    N3->>N3: Generate Keys
    
    N1->>+N2: UDP Broadcast DISCOVERY<br/>(node_id, name, public_key)
    N1->>+N3: UDP Broadcast DISCOVERY
    
    N2->>N1: DISCOVERY_RESPONSE<br/>(node_id, name, public_key)
    N3->>N1: DISCOVERY_RESPONSE
    
    Note over N1,N2: Session Establishment
    
    N1->>N2: KEY_EXCHANGE<br/>(encrypted session key)
    N2->>N1: KEY_EXCHANGE<br/>(encrypted session key)
    
    Note over N1,N2: Secure Channel Ready
    
    N1->>N1: Add N2 to peer list
    N2->>N2: Add N1 to peer list
    N1->>N1: Update routing table
    N2->>N2: Update routing table
```

## 4. Message Flow - Multi-Hop Routing

```mermaid
sequenceDiagram
    participant N1 as Node 1<br/>(Source)
    participant N2 as Node 2<br/>(Hop 1)
    participant N3 as Node 3<br/>(Hop 2)
    participant N4 as Node 4<br/>(Destination)
    
    Note over N1,N4: Multi-Hop Message Delivery
    
    N1->>N1: Encrypt message<br/>for Node 4
    N1->>N1: Check routing table
    N1->>N1: Next hop: Node 2
    
    N1->>N2: DATA Message<br/>(src=N1, dst=N4, hop=0)
    
    N2->>N2: Check destination
    N2->>N2: Not for me, forward
    N2->>N2: Increment hop count
    N2->>N2: Cache message ID
    
    N2->>N3: DATA Message<br/>(src=N1, dst=N4, hop=1)
    
    N3->>N3: Check destination
    N3->>N3: Not for me, forward
    N3->>N3: Increment hop count
    N3->>N3: Cache message ID
    
    N3->>N4: DATA Message<br/>(src=N1, dst=N4, hop=2)
    
    N4->>N4: Check destination
    N4->>N4: For me! Process
    N4->>N4: Decrypt message
    N4->>N4: Deliver to application
    
    Note over N1,N4: Message delivered in 2 hops
```

## 5. Protocol Stack

```mermaid
graph TB
    subgraph "Application Layer"
        UserApp[User Application<br/>Message Payload]
    end
    
    subgraph "NexLattice Protocol Layer"
        Discovery[Discovery Protocol<br/>UDP Broadcast]
        Routing[Routing Protocol<br/>Hop-by-Hop]
        Encryption[Encryption Layer<br/>AES-256-CBC]
        HealthCheck[Health Monitoring<br/>Ping/Pong]
    end
    
    subgraph "Transport Layer"
        UDP[UDP<br/>Ports 5000-5001]
        HTTP[HTTP<br/>Dashboard API]
    end
    
    subgraph "Network Layer"
        IP[IP Layer<br/>IPv4]
    end
    
    subgraph "Link Layer"
        WiFi[WiFi 802.11<br/>2.4GHz]
    end
    
    UserApp --> Encryption
    Encryption --> Routing
    Routing --> Discovery
    Discovery --> UDP
    HealthCheck --> UDP
    Routing --> HTTP
    UDP --> IP
    HTTP --> IP
    IP --> WiFi
    
    style UserApp fill:#10b981,stroke:#059669,color:#fff
    style Discovery fill:#34d399,stroke:#059669,color:#000
    style Routing fill:#34d399,stroke:#059669,color:#000
    style Encryption fill:#34d399,stroke:#059669,color:#000
    style HealthCheck fill:#34d399,stroke:#059669,color:#000
```

## 6. Dashboard Architecture

```mermaid
graph TB
    subgraph "Frontend - Browser"
        HTML[index.html<br/>Dashboard UI]
        D3[dashboard.js<br/>D3.js + WebSocket]
        Viz[Network Visualization<br/>Interactive Graph]
    end
    
    subgraph "Backend - Flask Server"
        FlaskApp[app.py<br/>Flask Application]
        
        subgraph "API Endpoints"
            REST[REST API<br/>/api/network_state<br/>/api/update_node<br/>/api/stats]
        end
        
        subgraph "Real-Time"
            WS[WebSocket Server<br/>Flask-SocketIO]
        end
        
        subgraph "State Management"
            NetState[(Network State<br/>Nodes & Links)]
            MsgLog[(Message Log)]
        end
        
        subgraph "Background Tasks"
            Timeout[Node Timeout Checker<br/>Threading]
            Topology[Topology Calculator]
        end
    end
    
    subgraph "Data Sources"
        ESP32[ESP32 Nodes<br/>HTTP POST]
    end
    
    HTML --> D3
    D3 --> Viz
    D3 <-->|WebSocket| WS
    D3 -->|HTTP GET| REST
    
    ESP32 -->|HTTP POST| REST
    REST --> NetState
    REST --> MsgLog
    REST --> WS
    
    WS --> D3
    Timeout --> NetState
    Topology --> NetState
    
    style HTML fill:#6ee7b7,stroke:#059669,color:#000
    style D3 fill:#6ee7b7,stroke:#059669,color:#000
    style Viz fill:#6ee7b7,stroke:#059669,color:#000
    style FlaskApp fill:#34d399,stroke:#059669,color:#000
    style WS fill:#10b981,stroke:#059669,color:#fff
```

## 7. Security Architecture

```mermaid
graph TB
    subgraph "Key Management"
        KeyGen[Private Key Generation<br/>SHA-256 Hash]
        PubKey[Public Key Derivation]
        SessionKey[Session Key Exchange]
    end
    
    subgraph "Encryption Pipeline"
        Plaintext[Plaintext Message]
        Padding[PKCS7 Padding]
        IV[Random IV Generation]
        AES[AES-256-CBC Encryption]
        Ciphertext[Encrypted Message]
    end
    
    subgraph "Session Management"
        PSK[Pre-Shared Key<br/>Initial Handshake]
        PerPeer[Per-Peer Session Keys<br/>Secure Communication]
    end
    
    subgraph "Security Features"
        LoopPrev[Loop Prevention<br/>Message Cache]
        HopLimit[Hop Count Limit<br/>Max 5 Hops]
        Timeout[Peer Timeout<br/>120 Seconds]
    end
    
    KeyGen --> PubKey
    PubKey --> SessionKey
    SessionKey --> PerPeer
    PSK --> SessionKey
    
    Plaintext --> Padding
    Padding --> IV
    IV --> AES
    PerPeer --> AES
    AES --> Ciphertext
    
    style KeyGen fill:#10b981,stroke:#059669,color:#fff
    style AES fill:#10b981,stroke:#059669,color:#fff
    style PerPeer fill:#34d399,stroke:#059669,color:#000
    style LoopPrev fill:#34d399,stroke:#059669,color:#000
```

## 8. Data Flow - Complete Message Journey

```mermaid
graph LR
    subgraph "Node 1 - Source"
        App1[Application]
        Enc1[Encrypt]
        Route1[Router]
        Net1[Network]
    end
    
    subgraph "Node 2 - Hop"
        Net2[Network]
        Route2[Router]
        Cache2[Check Cache]
        Forward2[Forward]
    end
    
    subgraph "Node 3 - Destination"
        Net3[Network]
        Route3[Router]
        Dec3[Decrypt]
        App3[Application]
    end
    
    App1 -->|Plaintext| Enc1
    Enc1 -->|Ciphertext| Route1
    Route1 -->|Add Headers| Net1
    Net1 -->|UDP| Net2
    
    Net2 --> Route2
    Route2 --> Cache2
    Cache2 -->|Not Duplicate| Forward2
    Forward2 -->|UDP| Net3
    
    Net3 --> Route3
    Route3 -->|Destination Match| Dec3
    Dec3 -->|Plaintext| App3
    
    style App1 fill:#10b981,stroke:#059669,color:#fff
    style Enc1 fill:#34d399,stroke:#059669,color:#000
    style Route1 fill:#34d399,stroke:#059669,color:#000
    style Route2 fill:#34d399,stroke:#059669,color:#000
    style Dec3 fill:#34d399,stroke:#059669,color:#000
    style App3 fill:#10b981,stroke:#059669,color:#fff
```

## 9. Node State Machine

```mermaid
stateDiagram-v2
    [*] --> Init: Power On
    Init --> Connecting: Start WiFi
    Connecting --> Discovery: WiFi Connected
    Connecting --> Error: Connection Failed
    
    Discovery --> Active: Peers Found
    Discovery --> Waiting: No Peers Yet
    Waiting --> Discovery: Retry After Timeout
    
    Active --> Communicating: Send/Receive Messages
    Communicating --> Active: Message Processed
    
    Active --> HealthCheck: Periodic Check
    HealthCheck --> Active: Peers Healthy
    HealthCheck --> Recovery: Peer Timeout
    
    Recovery --> Active: Routes Updated
    
    Active --> Reporting: Stats Interval
    Reporting --> Active: Dashboard Updated
    
    Error --> Init: Retry
    Active --> [*]: Shutdown
    
    note right of Init
        Initialize managers
        Load configuration
        Generate keys
    end note
    
    note right of Discovery
        Broadcast discovery
        Exchange public keys
        Build peer list
    end note
    
    note right of Active
        Ready to route messages
        Maintain routing table
        Monitor peer health
    end note
```

## 10. Routing Algorithm Flow

```mermaid
flowchart TD
    Start([Receive Message]) --> CheckDest{Destination<br/>is Me?}
    
    CheckDest -->|Yes| Decrypt[Decrypt Message]
    Decrypt --> Deliver[Deliver to Application]
    Deliver --> End([Done])
    
    CheckDest -->|No| CheckCache{Message ID<br/>in Cache?}
    CheckCache -->|Yes| Drop[Drop - Loop Detected]
    Drop --> End
    
    CheckCache -->|No| CheckHops{Hop Count<br/>< Max?}
    CheckHops -->|No| Drop2[Drop - Max Hops]
    Drop2 --> End
    
    CheckHops -->|Yes| AddCache[Add to Cache]
    AddCache --> IncHop[Increment Hop Count]
    IncHop --> CheckDirect{Direct<br/>Peer?}
    
    CheckDirect -->|Yes| SendDirect[Send Directly]
    SendDirect --> Stats[Update Stats]
    Stats --> End
    
    CheckDirect -->|No| CheckRoute{Route in<br/>Table?}
    CheckRoute -->|Yes| SendVia[Send via Next Hop]
    SendVia --> Stats
    
    CheckRoute -->|No| Flood[Flood to All Peers]
    Flood --> Stats
    
    style Start fill:#10b981,stroke:#059669,color:#fff
    style Deliver fill:#10b981,stroke:#059669,color:#fff
    style Drop fill:#ef4444,stroke:#dc2626,color:#fff
    style Drop2 fill:#ef4444,stroke:#dc2626,color:#fff
    style SendDirect fill:#34d399,stroke:#059669,color:#000
    style End fill:#10b981,stroke:#059669,color:#fff
```

## 11. Dashboard Real-Time Updates

```mermaid
sequenceDiagram
    participant Node as ESP32 Node
    participant API as Flask REST API
    participant State as Network State
    participant WS as WebSocket Server
    participant Client as Web Browser
    
    Note over Client: Page Load
    Client->>WS: Connect WebSocket
    WS->>Client: initial_state event<br/>(all nodes & topology)
    
    Note over Node: Every 60 seconds
    Node->>API: POST /api/update_node<br/>(stats, peers)
    API->>State: Update node data
    API->>State: Recalculate topology
    State->>WS: Broadcast update
    WS->>Client: node_update event<br/>(new data)
    
    Client->>Client: Update D3.js graph
    Client->>Client: Refresh statistics
    
    Note over State: Background Thread
    State->>State: Check node timeouts
    State->>WS: node_status event<br/>(offline)
    WS->>Client: Update node status
    Client->>Client: Mark node offline (red)
```

## 12. Deployment Architecture

```mermaid
graph TB
    subgraph "Development Environment"
        Dev[Developer Laptop]
        Simulator[Python Simulator]
        Dev --> Simulator
    end
    
    subgraph "Testing Environment"
        TestDash[Test Dashboard<br/>localhost:8080]
        TestNode1[Test ESP32 Node 1]
        TestNode2[Test ESP32 Node 2]
        TestNode3[Test ESP32 Node 3]
        
        TestNode1 --> TestDash
        TestNode2 --> TestDash
        TestNode3 --> TestDash
    end
    
    subgraph "Production Environment"
        ProdDash[Production Dashboard<br/>Cloud Server]
        
        subgraph "IoT Network"
            Prod1[ESP32 Node 1]
            Prod2[ESP32 Node 2]
            Prod3[ESP32 Node 3]
            Prod4[ESP32 Node 4]
            Prod5[ESP32 Node 5]
        end
        
        Prod1 --> ProdDash
        Prod2 --> ProdDash
        Prod3 --> ProdDash
        Prod4 --> ProdDash
        Prod5 --> ProdDash
    end
    
    Dev -->|Test| TestDash
    TestDash -->|Deploy| ProdDash
    
    style Dev fill:#6ee7b7,stroke:#059669,color:#000
    style TestDash fill:#34d399,stroke:#059669,color:#000
    style ProdDash fill:#10b981,stroke:#059669,color:#fff
```

---

## How to View These Diagrams

### In GitHub
These diagrams will render automatically when viewing this file on GitHub.

### In VS Code
Install the "Markdown Preview Mermaid Support" extension.

### Online
Copy any diagram code block and paste it into: https://mermaid.live/

### In Documentation Tools
Most modern documentation tools (GitBook, Docusaurus, MkDocs) support Mermaid natively.

---

**Generated for NexLattice Project**  
*Last Updated: October 2025*

