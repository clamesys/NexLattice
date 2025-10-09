# NexLattice Quick Start Guide

Get your mesh network running in 15 minutes! ⚡

## Option 1: Test with Simulator (No Hardware)

Perfect for understanding the system before deploying to hardware.

### Step 1: Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### Step 2: Start Dashboard

**Windows:**
```bash
scripts\start_dashboard.bat
```

**macOS/Linux:**
```bash
chmod +x scripts/start_dashboard.sh
./scripts/start_dashboard.sh
```

Or manually:
```bash
cd dashboard
python app.py
```

Dashboard will open at: **http://localhost:8080**

### Step 3: Run Simulator

In a new terminal:

```bash
# Activate venv first
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run simulator
python scripts/test_simulator.py
```

You'll see:
- ✅ 5 virtual nodes created
- 🔍 Peer discovery
- 📨 Test messages sent
- 📊 Network statistics
- Option to integrate with dashboard

Open dashboard in browser to see live visualization!

## Option 2: Deploy to ESP32 Hardware

### Prerequisites

- 5× ESP32 development boards
- USB cables
- WiFi network
- Python 3.8+ installed

### Step 1: Install ESP32 Tools

```bash
pip install esptool adafruit-ampy pyserial
```

### Step 2: Download MicroPython Firmware

1. Go to: https://micropython.org/download/esp32/
2. Download latest stable firmware (e.g., `esp32-20231005-v1.21.0.bin`)
3. Save to project folder

### Step 3: Flash MicroPython

```bash
# Find your port:
# Windows: COM3, COM4, etc.
# macOS: /dev/cu.usbserial-*
# Linux: /dev/ttyUSB0, /dev/ttyUSB1

# Erase flash
esptool.py --port COM3 erase_flash

# Flash firmware
esptool.py --chip esp32 --port COM3 write_flash -z 0x1000 esp32-*.bin
```

Repeat for all 5 ESP32 boards.

### Step 4: Configure Network

Edit each config file with your WiFi details:

**devices/config.json** (Node 1)
**devices/config_node2.json** (Node 2)
**devices/config_node3.json** (Node 3)
**devices/config_node4.json** (Node 4)
**devices/config_node5.json** (Node 5)

Change these fields:
```json
{
  "wifi_ssid": "YourNetworkName",
  "wifi_password": "YourPassword",
  "dashboard_ip": "192.168.1.XXX"  // Your computer's IP
}
```

**Find your computer's IP:**
- Windows: `ipconfig` (look for IPv4 Address)
- macOS/Linux: `ifconfig` or `ip addr`

### Step 5: Upload Code to ESP32

Using the helper script:

```bash
# Upload to Node 1 on COM3
python scripts/upload_to_esp32.py COM3 1

# Upload to Node 2 on COM4
python scripts/upload_to_esp32.py COM4 2

# Continue for all 5 nodes...
```

Or manually with ampy:

```bash
# Set port
export AMPY_PORT=COM3  # Windows: set AMPY_PORT=COM3

# Upload files for Node 1
ampy put devices/node_main.py /node_main.py
ampy put devices/network_manager.py /network_manager.py
ampy put devices/crypto_utils.py /crypto_utils.py
ampy put devices/message_router.py /message_router.py
ampy put devices/config.json /config.json
```

### Step 6: Start Dashboard

```bash
cd dashboard
python app.py
```

Open browser: **http://localhost:8080**

### Step 7: Power Up Nodes

1. Connect first ESP32 to power/USB
2. Press RESET button
3. Wait ~30 seconds
4. Repeat for remaining ESP32s
5. Watch dashboard - nodes should appear!

### Step 8: Monitor Serial Output (Optional)

**Using screen (macOS/Linux):**
```bash
screen /dev/ttyUSB0 115200
```

**Using PuTTY (Windows):**
- Port: COM3
- Speed: 115200
- Connection type: Serial

You should see:
```
🚀 NexLattice Node Starting...
✅ Node initialized: NexLattice Node 1 (node_001)
🌐 Connecting to WiFi...
✅ Connected! IP: 192.168.1.101
🔍 Discovery service started
📨 Message listener started
🔄 Entering main loop...
```

## Verify Everything Works

### Check Dashboard
- ✅ Shows 5 nodes
- ✅ Shows network connections (links)
- ✅ Nodes have "online" status (green)
- ✅ Statistics updating

### Test Message Sending

Create `test_message.py`:

```python
import requests
import time

DASHBOARD_URL = "http://localhost:8080"

# Send test message
response = requests.post(f"{DASHBOARD_URL}/api/send_message", json={
    "source": "node_001",
    "destination": "node_005",
    "message": "Hello from Node 1!"
})

print(response.json())
```

Run it:
```bash
python test_message.py
```

Check serial monitors - Node 5 should receive the message!

## Troubleshooting

### Dashboard shows 0 nodes

**Problem**: Nodes can't reach dashboard

**Solutions**:
1. Check `dashboard_ip` in config files matches your PC's IP
2. Disable firewall temporarily or allow port 8080
3. Make sure nodes and PC on same WiFi network
4. Try `dashboard_ip: "192.168.1.255"` (broadcast)

### Nodes not discovering each other

**Problem**: No peer connections showing

**Solutions**:
1. All nodes must be on same WiFi
2. Wait 60 seconds for discovery
3. Check router allows device-to-device communication
4. Try different WiFi network (some routers block P2P)
5. Reduce `discovery_interval` to 10 seconds for testing

### Upload fails

**Problem**: Can't upload to ESP32

**Solutions**:
1. Check USB cable (must support data, not just power)
2. Install CH340/CP2102 drivers if needed
3. Close any serial monitors before uploading
4. Try different USB port
5. Reset ESP32 before upload

### "Out of memory" on ESP32

**Problem**: ESP32 crashes with MemoryError

**Solutions**:
1. Use ESP32 with PSRAM (4MB models)
2. Reduce `max_peers` in config to 5
3. Flash firmware with SPIRAM support
4. Use ESP32-WROVER instead of WROOM

## Next Steps

Once everything is working:

1. 📖 **Read Documentation**: See `docs/` folder
2. 🧪 **Run Tests**: Follow `tests/test_plan.md`
3. 🔧 **Customize**: Modify code for your use case
4. 📈 **Scale Up**: Add more nodes
5. 🔒 **Secure**: Implement custom encryption keys
6. 🌐 **Deploy**: Use in your IoT project!

## Quick Command Reference

### Dashboard
```bash
# Start dashboard
cd dashboard && python app.py

# Access dashboard
http://localhost:8080
```

### Simulator
```bash
# Basic test
python scripts/test_simulator.py

# Advanced test
python scripts/test_simulator.py --advanced
```

### ESP32
```bash
# Flash firmware
esptool.py --port COM3 erase_flash
esptool.py --chip esp32 --port COM3 write_flash -z 0x1000 firmware.bin

# Upload code
python scripts/upload_to_esp32.py COM3 1

# Monitor serial
screen /dev/ttyUSB0 115200
```

## Project Structure

```
NexLattice/
├── devices/          # ESP32 code
├── dashboard/        # Web interface
├── simulator/        # Virtual testing
├── docs/            # Documentation
├── scripts/         # Helper scripts
└── tests/           # Test plans
```

## Support

- 📖 Full docs: `docs/architecture.md`
- 🔧 Setup guide: `docs/setup_instructions.md`
- 🧪 Testing: `tests/test_plan.md`
- 💬 Issues: GitHub Issues

## Success Checklist

- [ ] Dependencies installed
- [ ] Dashboard running
- [ ] Simulator tested (optional)
- [ ] ESP32s flashed with MicroPython
- [ ] Config files updated
- [ ] Code uploaded to all ESP32s
- [ ] All nodes online in dashboard
- [ ] Test message sent successfully

🎉 **Congratulations! Your mesh network is live!** 🎉

---

**Need help?** Check `docs/setup_instructions.md` for detailed troubleshooting.

