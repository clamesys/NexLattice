# NexLattice Test Plan

Comprehensive testing strategy for validating the mesh network functionality.

## Test Categories

1. **Unit Tests**: Individual component testing
2. **Integration Tests**: Component interaction testing
3. **System Tests**: End-to-end functionality
4. **Performance Tests**: Latency, throughput, scalability
5. **Reliability Tests**: Failure scenarios and recovery
6. **Security Tests**: Encryption and authentication

## 1. Unit Tests

### 1.1 Crypto Utilities Tests

#### Test: Key Generation
- **Objective**: Verify unique key generation
- **Steps**:
  1. Create CryptoManager instance
  2. Generate private key
  3. Derive public key
- **Expected**: Keys are non-empty and different for each node
- **Pass Criteria**: Public key is 64 hex characters

#### Test: Encryption/Decryption
- **Objective**: Verify message encryption works
- **Steps**:
  1. Encrypt plaintext message
  2. Decrypt ciphertext
  3. Compare with original
- **Expected**: Decrypted text matches original
- **Pass Criteria**: No data loss or corruption

#### Test: Session Key Establishment
- **Objective**: Verify session key exchange
- **Steps**:
  1. Create two nodes
  2. Exchange public keys
  3. Establish session
- **Expected**: Both nodes have shared session key
- **Pass Criteria**: Session established successfully

### 1.2 Network Manager Tests

#### Test: WiFi Connection
- **Objective**: Verify WiFi connection
- **Steps**:
  1. Initialize network manager
  2. Connect to WiFi with valid credentials
  3. Check connection status
- **Expected**: Successfully connected with valid IP
- **Pass Criteria**: `wlan.isconnected()` returns True

#### Test: Discovery Broadcast
- **Objective**: Verify discovery messages sent
- **Steps**:
  1. Start discovery service
  2. Broadcast discovery message
  3. Monitor network traffic
- **Expected**: Discovery packets sent to broadcast address
- **Pass Criteria**: Packet captured on network

#### Test: Peer Management
- **Objective**: Verify peer addition and tracking
- **Steps**:
  1. Add peer to peer list
  2. Update peer status
  3. Remove stale peers
- **Expected**: Peer list accurately reflects network state
- **Pass Criteria**: Correct peer count and information

### 1.3 Message Router Tests

#### Test: Direct Routing
- **Objective**: Verify direct peer message delivery
- **Steps**:
  1. Add peer to routing table
  2. Send message to peer
  3. Verify delivery
- **Expected**: Message delivered directly
- **Pass Criteria**: Hop count = 1

#### Test: Multi-Hop Routing
- **Objective**: Verify message forwarding
- **Steps**:
  1. Create 3-node chain
  2. Send message from Node 1 to Node 3
  3. Track forwarding
- **Expected**: Node 2 forwards message
- **Pass Criteria**: Message delivered with hop_count = 2

#### Test: Loop Prevention
- **Objective**: Verify routing loops prevented
- **Steps**:
  1. Create circular topology
  2. Send message
  3. Monitor for duplicates
- **Expected**: Message cache prevents loops
- **Pass Criteria**: Each message processed once only

#### Test: Max Hops Limit
- **Objective**: Verify hop count enforcement
- **Steps**:
  1. Create 6-node chain
  2. Send message end-to-end
  3. Check delivery
- **Expected**: Message dropped after 5 hops
- **Pass Criteria**: Message not delivered beyond limit

## 2. Integration Tests

### 2.1 Node Initialization Test

- **Objective**: Verify complete node startup
- **Steps**:
  1. Initialize NexLatticeNode
  2. Connect to WiFi
  3. Start all services
- **Expected**: All managers initialized, services running
- **Pass Criteria**: Node enters main loop successfully

### 2.2 Peer Discovery Test

- **Objective**: Verify peer discovery workflow
- **Steps**:
  1. Start Node 1
  2. Start Node 2
  3. Wait for discovery
  4. Check peer lists
- **Expected**: Both nodes discover each other
- **Pass Criteria**: Each node has 1 peer

### 2.3 Encrypted Communication Test

- **Objective**: Verify end-to-end encryption
- **Steps**:
  1. Establish session between nodes
  2. Send encrypted message
  3. Receive and decrypt
- **Expected**: Message decrypted successfully
- **Pass Criteria**: Decrypted payload matches original

### 2.4 Dashboard Integration Test

- **Objective**: Verify node-dashboard communication
- **Steps**:
  1. Start dashboard server
  2. Start node
  3. Wait for stats report
  4. Check dashboard state
- **Expected**: Dashboard receives node updates
- **Pass Criteria**: Node appears in dashboard

## 3. System Tests

### 3.1 Five-Node Network Test

- **Objective**: Verify complete 5-node network operation
- **Setup**: 5 ESP32 nodes on same WiFi
- **Steps**:
  1. Power up all 5 nodes
  2. Wait 60 seconds for discovery
  3. Verify topology in dashboard
  4. Send messages between all pairs
- **Expected**: Full mesh connectivity
- **Pass Criteria**: 
  - All nodes visible in dashboard
  - All message pairs successful (25 tests)
  - Average latency < 100ms

### 3.2 Message Delivery Test

#### Test Case 3.2.1: Direct Delivery
- **Source**: Node 1
- **Destination**: Node 2
- **Expected Hops**: 1
- **Expected Latency**: < 50ms

#### Test Case 3.2.2: Multi-Hop Delivery
- **Source**: Node 1
- **Destination**: Node 5
- **Expected Hops**: 2-4 (depends on topology)
- **Expected Latency**: < 150ms

#### Test Case 3.2.3: Broadcast Test
- **Source**: Node 1
- **Destinations**: All other nodes
- **Expected**: All nodes receive message
- **Pass Criteria**: 100% delivery rate

### 3.3 Network Topology Tests

#### Test: Linear Topology
```
Node1 -- Node2 -- Node3 -- Node4 -- Node5
```
- **Test**: Node1 to Node5 communication
- **Expected**: 4 hops
- **Pass Criteria**: Message delivered

#### Test: Star Topology
```
     Node2
       |
Node1-Node3-Node4
       |
     Node5
```
- **Test**: Node1 to Node5 communication
- **Expected**: 2 hops (via Node3)
- **Pass Criteria**: Message delivered

#### Test: Mesh Topology
```
Node1 - Node2 - Node3
  |       |       |
Node4 - Node5 - Node6
```
- **Test**: Multiple paths available
- **Expected**: Optimal route selected
- **Pass Criteria**: Minimum hop count used

## 4. Performance Tests

### 4.1 Latency Measurement

- **Objective**: Measure message latency
- **Method**: Send 100 messages, measure RTT
- **Metrics**:
  - Min latency
  - Max latency
  - Average latency
  - 95th percentile
- **Pass Criteria**:
  - Average < 100ms
  - 95th percentile < 200ms

### 4.2 Throughput Test

- **Objective**: Measure message throughput
- **Method**: Send continuous messages for 60 seconds
- **Metrics**:
  - Messages per second
  - Bytes per second
  - Packet loss rate
- **Pass Criteria**:
  - > 50 messages/second
  - < 1% packet loss

### 4.3 Concurrent Message Test

- **Objective**: Test multiple simultaneous messages
- **Method**: All nodes send messages simultaneously
- **Metrics**:
  - Collision rate
  - Average delivery time
  - Success rate
- **Pass Criteria**:
  - > 95% success rate
  - No crashes

### 4.4 Scalability Test

- **Objective**: Test network with increasing node count
- **Method**: Add nodes incrementally (5, 10, 15, 20)
- **Metrics**:
  - Discovery time
  - Routing table size
  - Memory usage
  - CPU usage
- **Pass Criteria**:
  - Supports 20+ nodes
  - Discovery < 60 seconds
  - Memory < 100KB per node

## 5. Reliability Tests

### 5.1 Node Failure Test

- **Objective**: Verify network continues with node failure
- **Steps**:
  1. Establish 5-node network
  2. Power off Node 3 (middle node)
  3. Wait 120 seconds
  4. Send messages through network
- **Expected**: Routing reconfigures, messages still delivered
- **Pass Criteria**: > 90% message delivery

### 5.2 Node Recovery Test

- **Objective**: Verify node rejoins after recovery
- **Steps**:
  1. Start with Node 3 offline
  2. Power on Node 3
  3. Wait for rediscovery
  4. Test full connectivity
- **Expected**: Node 3 rejoins network
- **Pass Criteria**: Full mesh restored within 60 seconds

### 5.3 Network Partition Test

- **Objective**: Verify behavior during network split
- **Steps**:
  1. Create 5-node network
  2. Physically separate into two groups
  3. Test intra-group communication
  4. Rejoin groups
- **Expected**: 
  - Each partition operates independently
  - Full connectivity restored on rejoin
- **Pass Criteria**: No data loss within partitions

### 5.4 Message Loss Test

- **Objective**: Measure behavior with packet loss
- **Method**: Introduce artificial packet drops (10%, 25%, 50%)
- **Metrics**:
  - End-to-end delivery rate
  - Retry behavior
  - Recovery time
- **Pass Criteria**: Graceful degradation

### 5.5 Long-Running Stability Test

- **Objective**: Verify 24-hour continuous operation
- **Method**: Run network for 24 hours
- **Metrics**:
  - Uptime per node
  - Memory leaks
  - Crash count
  - Message delivery consistency
- **Pass Criteria**:
  - > 95% uptime
  - No memory leaks
  - Zero crashes

## 6. Security Tests

### 6.1 Encryption Validation

- **Objective**: Verify all messages encrypted
- **Method**: Packet capture and analysis
- **Test**: Decrypt without keys should fail
- **Pass Criteria**: No plaintext in captured packets

### 6.2 Key Exchange Security

- **Objective**: Verify secure session establishment
- **Method**: Monitor key exchange process
- **Test**: Man-in-the-middle attack simulation
- **Pass Criteria**: Keys not compromised

### 6.3 Authentication Test

- **Objective**: Verify only authorized nodes join
- **Method**: Attempt connection with invalid credentials
- **Test**: Unauthorized node attempts to join
- **Pass Criteria**: Unauthorized node rejected

### 6.4 Replay Attack Test

- **Objective**: Prevent message replay
- **Method**: Capture message, replay it
- **Test**: Resend same message
- **Pass Criteria**: Duplicate detected and dropped

## 7. Simulation Tests

### 7.1 Virtual Network Test

- **Objective**: Test without hardware using simulator
- **Method**: Run `network_simulator.py`
- **Scenarios**:
  - Line topology (5 nodes)
  - Star topology (7 nodes)
  - Mesh topology (9 nodes)
  - Random topology (10 nodes)
- **Pass Criteria**: All scenarios complete successfully

### 7.2 Failure Simulation

- **Objective**: Simulate various failure modes
- **Scenarios**:
  - Random node failures
  - Link failures
  - Delayed messages
  - Corrupted packets
- **Pass Criteria**: Network recovers gracefully

## Test Execution Plan

### Phase 1: Unit Testing (Week 1)
- [ ] Crypto utilities tests
- [ ] Network manager tests
- [ ] Message router tests

### Phase 2: Integration Testing (Week 2)
- [ ] Node initialization tests
- [ ] Peer discovery tests
- [ ] Encrypted communication tests
- [ ] Dashboard integration tests

### Phase 3: System Testing (Week 3)
- [ ] Five-node network test
- [ ] Message delivery tests
- [ ] Network topology tests

### Phase 4: Performance Testing (Week 4)
- [ ] Latency measurements
- [ ] Throughput tests
- [ ] Concurrent message tests
- [ ] Scalability tests

### Phase 5: Reliability Testing (Week 5)
- [ ] Node failure tests
- [ ] Network partition tests
- [ ] Long-running stability test

### Phase 6: Security Testing (Week 6)
- [ ] Encryption validation
- [ ] Authentication tests
- [ ] Attack simulation tests

## Test Metrics and KPIs

### Key Performance Indicators

| Metric | Target | Critical |
|--------|--------|----------|
| Discovery Time | < 30s | < 60s |
| Message Latency | < 100ms | < 200ms |
| Delivery Success | > 99% | > 95% |
| Network Uptime | > 99% | > 95% |
| Memory Usage | < 50KB | < 100KB |
| CPU Usage | < 30% | < 50% |
| Max Node Count | 20+ | 10+ |

### Success Criteria

A test passes if:
1. All pass criteria met
2. No crashes or exceptions
3. Performance within targets
4. Logs show expected behavior

## Test Documentation

### For Each Test:
- **Test ID**: Unique identifier
- **Description**: What is being tested
- **Prerequisites**: Setup requirements
- **Steps**: Detailed procedure
- **Expected Results**: What should happen
- **Actual Results**: What actually happened
- **Status**: Pass/Fail/Blocked
- **Notes**: Any observations

### Test Report Template

```
TEST ID: SYS-3.1
TEST NAME: Five-Node Network Test
DATE: 2025-10-09
TESTER: [Your Name]

SETUP:
- 5x ESP32 boards
- WiFi network: TestNet
- Dashboard: Running

RESULTS:
- All nodes discovered: ✅
- Dashboard connectivity: ✅
- Message delivery: 25/25 ✅
- Average latency: 67ms ✅

STATUS: PASS

NOTES:
Node 3 took slightly longer to discover peers (45s vs 30s average).
No issues with message delivery. Performance excellent.
```

## Automated Testing

### Test Automation Tools

1. **pytest**: Python unit tests
2. **Simulator**: Virtual network testing
3. **Shell scripts**: Deployment automation
4. **CI/CD**: GitHub Actions (optional)

### Running Automated Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run with coverage
pytest --cov=devices --cov=dashboard tests/

# Run simulator tests
python simulator/network_simulator.py
```

## Troubleshooting Test Failures

### Common Issues

1. **Discovery Timeout**
   - Check WiFi connectivity
   - Verify UDP ports open
   - Increase discovery interval

2. **Message Delivery Failure**
   - Check routing tables
   - Verify node connectivity
   - Look for network congestion

3. **Dashboard Not Updating**
   - Verify dashboard server running
   - Check firewall settings
   - Validate API endpoints

4. **Encryption Errors**
   - Verify keys exchanged
   - Check ucryptolib availability
   - Validate session establishment

---

**Test Plan Version**: 1.0  
**Last Updated**: October 2025  
**Status**: Ready for Execution

