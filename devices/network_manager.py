"""
NexLattice Network Manager
Handles WiFi connection, peer discovery, and low-level communication
"""

import network
import socket
import time
import json
import _thread

class NetworkManager:
    def __init__(self, node_id, node_name, config):
        """Initialize network manager"""
        self.node_id = node_id
        self.node_name = node_name
        self.config = config
        
        # WiFi
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        
        # Sockets
        self.discovery_port = config.get('discovery_port', 5000)
        self.message_port = config.get('message_port', 5001)
        self.dashboard_port = config.get('dashboard_port', 8080)
        
        self.discovery_socket = None
        self.message_socket = None
        
        # Peers
        self.peers = {}  # peer_id: {name, ip, public_key, last_seen, latency}
        
        # State
        self.connected = False
    
    def connect_wifi(self, ssid, password, timeout=10):
        """Connect to WiFi network"""
        if not self.wlan.isconnected():
            print(f"Connecting to {ssid}...")
            self.wlan.connect(ssid, password)
            
            start = time.time()
            while not self.wlan.isconnected():
                if time.time() - start > timeout:
                    return False
                time.sleep(0.5)
        
        self.connected = True
        return True
    
    def get_ip(self):
        """Get current IP address"""
        if self.wlan.isconnected():
            return self.wlan.ifconfig()[0]
        return None
    
    def start_discovery(self):
        """Start UDP discovery service"""
        try:
            self.discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.discovery_socket.bind(('', self.discovery_port))
            self.discovery_socket.setblocking(False)
            print(f"🔍 Discovery service started on port {self.discovery_port}")
            
            # Start listener thread
            _thread.start_new_thread(self._discovery_listener, ())
            
        except Exception as e:
            print(f"❌ Failed to start discovery: {e}")
    
    def _discovery_listener(self):
        """Listen for discovery broadcasts"""
        while self.connected:
            try:
                data, addr = self.discovery_socket.recvfrom(1024)
                # Discovery packets handled by main message handler
                print(f"📡 Discovery packet from {addr[0]}")
            except OSError:
                time.sleep(0.1)  # Non-blocking, so sleep briefly
            except Exception as e:
                print(f"❌ Discovery listener error: {e}")
    
    def broadcast_discovery(self, public_key):
        """Broadcast discovery message to find peers"""
        discovery_msg = {
            'type': 'DISCOVERY',
            'node_id': self.node_id,
            'node_name': self.node_name,
            'public_key': public_key,
            'timestamp': time.time()
        }
        
        try:
            # Broadcast to subnet
            broadcast_ip = self._get_broadcast_ip()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(json.dumps(discovery_msg).encode(), (broadcast_ip, self.message_port))
            sock.close()
            print(f"📢 Discovery broadcast sent to {broadcast_ip}")
        except Exception as e:
            print(f"❌ Discovery broadcast failed: {e}")
    
    def _get_broadcast_ip(self):
        """Get broadcast IP for current subnet"""
        ip = self.get_ip()
        if ip:
            parts = ip.split('.')
            parts[-1] = '255'
            return '.'.join(parts)
        return '255.255.255.255'
    
    def start_message_listener(self, message_handler):
        """Start TCP message listener"""
        try:
            self.message_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.message_socket.bind(('', self.message_port))
            self.message_socket.setblocking(False)
            print(f"📨 Message listener started on port {self.message_port}")
            
            # Start listener thread
            _thread.start_new_thread(self._message_listener, (message_handler,))
            
        except Exception as e:
            print(f"❌ Failed to start message listener: {e}")
    
    def _message_listener(self, message_handler):
        """Listen for incoming messages"""
        while self.connected:
            try:
                data, addr = self.message_socket.recvfrom(2048)
                message = data.decode('utf-8')
                message_handler(message, addr)
            except OSError:
                time.sleep(0.05)
            except Exception as e:
                print(f"❌ Message listener error: {e}")
    
    def send_direct(self, message, dest_ip):
        """Send message directly to specific IP"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(message.encode(), (dest_ip, self.message_port))
            sock.close()
            return True
        except Exception as e:
            print(f"❌ Failed to send to {dest_ip}: {e}")
            return False
    
    def send_to_dashboard(self, data, dashboard_ip):
        """Send data to dashboard server via HTTP POST"""
        try:
            # Simple HTTP POST request
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((dashboard_ip, self.dashboard_port))
            
            request = f"POST /api/update_node HTTP/1.1\r\n"
            request += f"Host: {dashboard_ip}\r\n"
            request += "Content-Type: application/json\r\n"
            request += f"Content-Length: {len(data)}\r\n"
            request += "\r\n"
            request += data
            
            sock.send(request.encode())
            sock.close()
            return True
        except Exception as e:
            print(f"⚠️  Dashboard send failed: {e}")
            return False
    
    def add_peer(self, peer_id, peer_name, peer_ip, public_key):
        """Add or update peer information"""
        if peer_id == self.node_id:
            return  # Don't add self
        
        self.peers[peer_id] = {
            'name': peer_name,
            'ip': peer_ip,
            'public_key': public_key,
            'last_seen': time.time(),
            'latency': None,
            'connected': True
        }
        
        print(f"👥 Peer added: {peer_name} ({peer_ip})")
    
    def get_peer(self, peer_id):
        """Get peer information"""
        return self.peers.get(peer_id)
    
    def get_peer_list(self):
        """Get list of all peers"""
        return [
            {
                'id': peer_id,
                'name': info['name'],
                'ip': info['ip'],
                'last_seen': info['last_seen'],
                'latency': info.get('latency'),
                'connected': info.get('connected', True)
            }
            for peer_id, info in self.peers.items()
        ]
    
    def check_peer_health(self):
        """Check health of all peers and update status"""
        current_time = time.time()
        timeout = 60  # seconds
        
        for peer_id, info in self.peers.items():
            if current_time - info['last_seen'] > timeout:
                info['connected'] = False
                print(f"⚠️  Peer timeout: {info['name']}")
            
            # Send ping to measure latency
            self._ping_peer(peer_id, info['ip'])
    
    def _ping_peer(self, peer_id, peer_ip):
        """Send ping to peer to measure latency"""
        try:
            ping_msg = {
                'type': 'PING',
                'node_id': self.node_id,
                'timestamp': time.time()
            }
            self.send_direct(json.dumps(ping_msg), peer_ip)
        except Exception as e:
            print(f"⚠️  Ping failed for {peer_id}: {e}")
    
    def update_peer_latency(self, peer_id, latency):
        """Update peer latency measurement"""
        if peer_id in self.peers:
            self.peers[peer_id]['latency'] = latency
            self.peers[peer_id]['last_seen'] = time.time()
            self.peers[peer_id]['connected'] = True
    
    def stop(self):
        """Stop network services"""
        self.connected = False
        
        if self.discovery_socket:
            self.discovery_socket.close()
        
        if self.message_socket:
            self.message_socket.close()
        
        print("🛑 Network services stopped")

