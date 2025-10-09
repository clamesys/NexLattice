# NexLattice Setup Instructions

Complete guide to deploying and testing the NexLattice mesh network.

## Prerequisites

### Hardware Requirements

- **5× ESP32 Development Boards** (ESP32-WROOM-32 or similar)
- **USB cables** for programming and power
- **Computer** (Windows/macOS/Linux) for development
- **WiFi Router** or create a hotspot

### Software Requirements

- **Python 3.8+** (for dashboard)
- **MicroPython** firmware for ESP32
- **esptool** (for flashing firmware)
- **ampy** or **rshell** (for file transfer to ESP32)

## Step 1: Prepare Your Computer

### Install Python Dependencies

```bash
# Clone or navigate to project directory
cd NexLattice

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dashboard dependencies
pip install -r requirements.txt
```

### Install ESP32 Tools

```bash
# Install esptool
pip install esptool

# Install ampy (for file transfer)
pip install adafruit-ampy

# Or install rshell (alternative)
pip install rshell
```

## Step 2: Flash MicroPython to ESP32

### Download MicroPython Firmware

Visit: https://micropython.org/download/esp32/

Download the latest stable firmware (e.g., `esp32-20231005-v1.21.0.bin`)

### Flash Each ESP32

```bash
# Find your ESP32 port
# Windows: COM3, COM4, etc.
# macOS: /dev/cu.usbserial-*, /dev/tty.usbserial-*
# Linux: /dev/ttyUSB0, /dev/ttyUSB1, etc.

# Erase flash
esptool.py --port COM3 erase_flash

# Flash MicroPython firmware
esptool.py --chip esp32 --port COM3 write_flash -z 0x1000 esp32-20231005-v1.21.0.bin

# Repeat for all 5 ESP32s
```

## Step 3: Configure Network

### Option A: Using Existing WiFi Network

1. Find your WiFi network name (SSID) and password
2. Note your computer's IP address (e.g., `192.168.1.100`)
3. Use this IP as the dashboard IP in config files

### Option B: Create Mobile Hotspot

1. Enable mobile hotspot on your phone or laptop
2. Note the SSID and password
3. Note the hotspot gateway IP (usually `192.168.43.1` or `192.168.137.1`)

## Step 4: Configure Node Files

### Edit config.json for Each Node

Create 5 different config files (one per node):

**Node 1 - config.json**
```json
{
  "node_id": "node_001",
  "node_name": "NexLattice Node 1",
  "wifi_ssid": "YourNetworkSSID",
  "wifi_password": "YourPassword",
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

**Node 2-5**: Same format, just change:
- `node_id`: `"node_002"`, `"node_003"`, `"node_004"`, `"node_005"`
- `node_name`: `"NexLattice Node 2"`, etc.

## Step 5: Upload Code to ESP32 Nodes

### Using ampy

```bash
# Set the serial port (change COM3 to your port)
set AMPY_PORT=COM3
# Or on macOS/Linux:
export AMPY_PORT=/dev/ttyUSB0

# Upload files to Node 1
ampy put devices/node_main.py /node_main.py
ampy put devices/network_manager.py /network_manager.py
ampy put devices/crypto_utils.py /crypto_utils.py
ampy put devices/message_router.py /message_router.py
ampy put devices/config.json /config.json

# Repeat for all 5 nodes (changing config.json each time)
```

### Using rshell

```bash
# Connect to ESP32
rshell --port COM3

# Enter rshell prompt
> cp devices/node_main.py /pyboard/node_main.py
> cp devices/network_manager.py /pyboard/network_manager.py
> cp devices/crypto_utils.py /pyboard/crypto_utils.py
> cp devices/message_router.py /pyboard/message_router.py
> cp devices/config.json /pyboard/config.json
> exit

# Repeat for all 5 nodes
```

### Create boot.py (Optional)

To auto-start the node on boot, create `boot.py`:

```python
import node_main

node_main.main()
```

Upload to each ESP32:
```bash
ampy put boot.py /boot.py
```

## Step 6: Start the Dashboard

### Run Dashboard Server

```bash
# Make sure you're in the project root with virtual environment activated
cd dashboard
python app.py
```

You should see:
```
🚀 NexLattice Dashboard Starting...
==================================================
✅ Dashboard initialized
📊 Access dashboard at: http://localhost:8080
==================================================
```

### Open Dashboard in Browser

Navigate to: **http://localhost:8080**

You should see the NexLattice dashboard interface.

## Step 7: Power Up the Nodes

### Start Nodes One by One

1. **Connect Node 1** via USB
2. Open serial monitor (optional):
   ```bash
   # Using screen (macOS/Linux)
   screen /dev/ttyUSB0 115200
   
   # Using PuTTY (Windows)
   # Connect to COM3 at 115200 baud
   ```

3. Press **RESET** button on ESP32

4. Watch for output:
   ```
   🚀 NexLattice Node Starting...
   ✅ Node initialized: NexLattice Node 1 (node_001)
   🌐 Connecting to WiFi...
   ✅ Connected! IP: 192.168.1.101
   🔍 Discovery service started on port 5000
   📨 Message listener started on port 5001
   🔄 Entering main loop...
   ```

5. **Repeat for all 5 nodes**

## Step 8: Verify Network Operation

### Check Dashboard

1. Refresh dashboard page
2. You should see:
   - **Total Nodes**: 5
   - **Active Nodes**: 5
   - **Network Links**: Multiple connections
   - **Network Topology**: Visual graph showing node connections

### Check Serial Output

On each node's serial monitor, you should see:
```
📢 Discovery broadcast sent to 192.168.1.255
🔍 Discovery from NexLattice Node 2 (node_002)
✅ Discovery response from NexLattice Node 3 (node_003)
👥 Peer added: NexLattice Node 2 (192.168.1.102)
📊 Stats reported: 4 peers, 0 sent
```

## Step 9: Test Message Routing

### Using Python Script

Create `test_messages.py`:

```python
import requests
import time

DASHBOARD_URL = "http://localhost:8080"

def send_test_message(source, destination, message):
    response = requests.post(f"{DASHBOARD_URL}/api/send_message", json={
        "source": source,
        "destination": destination,
        "message": message
    })
    return response.json()

# Test messages
print("Sending test messages...")

# Direct message (Node 1 -> Node 2)
send_test_message("node_001", "node_002", "Hello from Node 1!")
time.sleep(2)

# Multi-hop message (Node 1 -> Node 5)
send_test_message("node_001", "node_005", "Multi-hop test message")
time.sleep(2)

print("Messages sent! Check dashboard and serial monitors.")
```

Run:
```bash
python test_messages.py
```

### Check Serial Monitor

You should see messages being received and forwarded:
```
📨 Message from node_001: Hello from Node 1!
📤 Forwarding message from node_001 to node_005
✅ Message sent to node_005
```

## Troubleshooting

### Nodes Not Connecting to WiFi

**Problem**: `❌ Failed to connect to WiFi`

**Solutions**:
1. Verify SSID and password in `config.json`
2. Check WiFi router is powered on and in range
3. Try 2.4GHz WiFi (ESP32 doesn't support 5GHz)
4. Reduce WiFi security to WPA2 (not WPA3)

### Nodes Not Discovering Each Other

**Problem**: No peers showing up

**Solutions**:
1. Ensure all nodes on same WiFi network
2. Check firewall isn't blocking UDP ports 5000-5001
3. Verify nodes have different IPs
4. Increase discovery interval for testing:
   ```json
   "discovery_interval": 5
   ```

### Dashboard Not Receiving Updates

**Problem**: Dashboard shows 0 nodes

**Solutions**:
1. Verify `dashboard_ip` in `config.json` matches your computer's IP
2. Check dashboard server is running
3. Ensure firewall allows incoming connections on port 8080
4. Check nodes can ping dashboard IP:
   ```python
   # In MicroPython REPL on ESP32
   import socket
   socket.getaddrinfo('192.168.1.100', 8080)
   ```

### Memory Errors on ESP32

**Problem**: `MemoryError` or crashes

**Solutions**:
1. Use ESP32 with PSRAM (4MB+)
2. Reduce peer limit in config:
   ```json
   "max_peers": 5
   ```
3. Optimize code to use less memory
4. Flash firmware with SPIRAM support

### Messages Not Being Forwarded

**Problem**: Multi-hop messages not reaching destination

**Solutions**:
1. Check max_hops setting
2. Verify routing table is building:
   - Add debug print in `message_router.py`:
   ```python
   print(f"Routing table: {self.routing_table}")
   ```
3. Ensure intermediate nodes are online
4. Check message cache isn't blocking (increase TTL)

## Testing Scenarios

### Test 1: Node Discovery
1. Start Node 1
2. Start Node 2
3. Verify they discover each other (check serial output)
4. Check dashboard shows 2 nodes with 1 link

### Test 2: Multi-Node Discovery
1. Start all 5 nodes
2. Wait 60 seconds
3. Check dashboard shows all nodes
4. Verify each node has 2-4 peers

### Test 3: Direct Messaging
1. Send message from Node 1 to Node 2
2. Verify Node 2 receives message
3. Check dashboard message log

### Test 4: Multi-Hop Routing
1. Physically separate nodes (reduce WiFi range)
2. Send message from Node 1 to Node 5
3. Verify message is forwarded through intermediate nodes
4. Check hop count increments

### Test 5: Node Failure
1. Unplug Node 3 (middle node)
2. Wait 120 seconds
3. Verify dashboard shows Node 3 offline
4. Verify routing reconfigures around failed node
5. Test message delivery still works

### Test 6: Network Recovery
1. Plug Node 3 back in
2. Verify it rejoins network
3. Check routing table rebuilds
4. Test full connectivity restored

## Performance Monitoring

### Metrics to Track

1. **Discovery Time**: How long for nodes to find each other
2. **Message Latency**: Time from send to receive
3. **Hop Count**: Average hops for message delivery
4. **Packet Loss**: Percentage of messages not delivered
5. **Node Uptime**: How long nodes stay online

### Dashboard Stats

Monitor these on the dashboard:
- Total nodes / Active nodes ratio
- Messages sent vs. received (should be balanced)
- Messages forwarded (indicates multi-hop routing)
- Network links (should be >= nodes - 1)

## Production Deployment Considerations

### Security Enhancements

1. **Unique PSK**: Generate unique pre-shared key per deployment
2. **Certificate Auth**: Implement proper PKI for production
3. **Key Rotation**: Regularly rotate session keys
4. **Secure Storage**: Store keys in secure flash partition

### Reliability Improvements

1. **Watchdog Timer**: Reset on freeze/crash
2. **OTA Updates**: Remote firmware updates
3. **Logging**: Store events to SD card
4. **Redundancy**: Multiple gateway nodes

### Scale Testing

1. Start with 5 nodes (working configuration)
2. Add nodes incrementally
3. Monitor performance degradation
4. Optimize routing algorithm for scale
5. Test up to 20-50 nodes

## Next Steps

1. ✅ Complete basic setup
2. 🧪 Run all test scenarios
3. 📊 Monitor performance metrics
4. 🔧 Optimize configuration
5. 🚀 Deploy in target environment
6. 📈 Scale up node count
7. 🔐 Implement production security

## Resources

- **MicroPython Docs**: https://docs.micropython.org/
- **ESP32 Reference**: https://docs.espressif.com/projects/esp-idf/
- **Flask-SocketIO**: https://flask-socketio.readthedocs.io/
- **D3.js Examples**: https://d3-graph-gallery.com/

## Support

For issues and questions:
1. Check documentation in `/docs`
2. Review protocol design in `protocol_design.md`
3. Enable debug logging in code
4. Test with simulation mode (if available)

---

**Good luck with your NexLattice deployment! 🚀**

