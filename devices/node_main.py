"""
NexLattice Node Main - Entry point for ESP32 mesh network nodes
Handles discovery, routing, and secure communication
"""

import network
import time
import json
import ubinascii
from network_manager import NetworkManager
from crypto_utils import CryptoManager
from message_router import MessageRouter

class NexLatticeNode:
    def __init__(self, config_path='/config.json'):
        """Initialize the NexLattice node"""
        print("🚀 NexLattice Node Starting...")
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.node_id = self.config['node_id']
        self.node_name = self.config['node_name']
        
        # Initialize managers
        self.crypto = CryptoManager(self.node_id)
        self.network = NetworkManager(self.node_id, self.node_name, self.config)
        self.router = MessageRouter(self.node_id, self.network, self.crypto)
        
        # State
        self.running = False
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'messages_forwarded': 0,
            'uptime': 0
        }
        
        print(f"✅ Node initialized: {self.node_name} ({self.node_id})")
    
    def start(self):
        """Start the node and join the mesh network"""
        print("🌐 Connecting to WiFi...")
        
        # Connect to WiFi
        if not self.network.connect_wifi(
            self.config['wifi_ssid'],
            self.config['wifi_password']
        ):
            print("❌ Failed to connect to WiFi")
            return False
        
        print(f"✅ Connected! IP: {self.network.get_ip()}")
        
        # Start network services
        self.network.start_discovery()
        self.network.start_message_listener(self.handle_message)
        
        # Start periodic tasks
        self.running = True
        self.run_main_loop()
        
        return True
    
    def handle_message(self, message, sender_addr):
        """Handle incoming messages"""
        try:
            msg_data = json.loads(message)
            msg_type = msg_data.get('type')
            
            if msg_type == 'DISCOVERY':
                self.handle_discovery(msg_data, sender_addr)
            elif msg_type == 'DISCOVERY_RESPONSE':
                self.handle_discovery_response(msg_data, sender_addr)
            elif msg_type == 'KEY_EXCHANGE':
                self.handle_key_exchange(msg_data, sender_addr)
            elif msg_type == 'DATA':
                self.handle_data_message(msg_data, sender_addr)
            elif msg_type == 'PING':
                self.handle_ping(msg_data, sender_addr)
            
            self.stats['messages_received'] += 1
            
        except Exception as e:
            print(f"❌ Error handling message: {e}")
    
    def handle_discovery(self, msg_data, sender_addr):
        """Handle discovery broadcast from peer"""
        peer_id = msg_data.get('node_id')
        peer_name = msg_data.get('node_name')
        public_key = msg_data.get('public_key')
        
        print(f"🔍 Discovery from {peer_name} ({peer_id})")
        
        # Add peer
        self.network.add_peer(peer_id, peer_name, sender_addr[0], public_key)
        
        # Send response
        response = {
            'type': 'DISCOVERY_RESPONSE',
            'node_id': self.node_id,
            'node_name': self.node_name,
            'public_key': self.crypto.get_public_key(),
            'timestamp': time.time()
        }
        
        self.network.send_direct(json.dumps(response), sender_addr[0])
    
    def handle_discovery_response(self, msg_data, sender_addr):
        """Handle discovery response from peer"""
        peer_id = msg_data.get('node_id')
        peer_name = msg_data.get('node_name')
        public_key = msg_data.get('public_key')
        
        print(f"✅ Discovery response from {peer_name} ({peer_id})")
        
        # Add peer
        self.network.add_peer(peer_id, peer_name, sender_addr[0], public_key)
    
    def handle_key_exchange(self, msg_data, sender_addr):
        """Handle encrypted key exchange"""
        peer_id = msg_data.get('node_id')
        session_key = msg_data.get('session_key')
        
        # Establish secure session
        if self.crypto.establish_session(peer_id, session_key):
            print(f"🔐 Secure session established with {peer_id}")
    
    def handle_data_message(self, msg_data, sender_addr):
        """Handle data message (direct or forwarded)"""
        dest_id = msg_data.get('destination')
        source_id = msg_data.get('source')
        payload = msg_data.get('payload')
        hop_count = msg_data.get('hop_count', 0)
        
        # Check if message is for this node
        if dest_id == self.node_id:
            print(f"📨 Message from {source_id}: {payload}")
            # Decrypt if encrypted
            if msg_data.get('encrypted'):
                payload = self.crypto.decrypt(payload, source_id)
                print(f"🔓 Decrypted: {payload}")
        else:
            # Forward message
            print(f"📤 Forwarding message from {source_id} to {dest_id}")
            self.router.forward_message(msg_data)
            self.stats['messages_forwarded'] += 1
    
    def handle_ping(self, msg_data, sender_addr):
        """Handle ping request for latency measurement"""
        peer_id = msg_data.get('node_id')
        
        # Send pong response
        pong = {
            'type': 'PONG',
            'node_id': self.node_id,
            'timestamp': time.time()
        }
        
        self.network.send_direct(json.dumps(pong), sender_addr[0])
    
    def send_message(self, dest_id, payload, encrypted=True):
        """Send a message to another node"""
        message = {
            'type': 'DATA',
            'source': self.node_id,
            'destination': dest_id,
            'payload': payload,
            'encrypted': encrypted,
            'hop_count': 0,
            'timestamp': time.time()
        }
        
        if encrypted:
            message['payload'] = self.crypto.encrypt(payload, dest_id)
        
        # Use router to send
        success = self.router.route_message(message)
        
        if success:
            self.stats['messages_sent'] += 1
            print(f"✅ Message sent to {dest_id}")
        else:
            print(f"❌ Failed to send message to {dest_id}")
        
        return success
    
    def run_main_loop(self):
        """Main loop for periodic tasks"""
        last_discovery = 0
        last_health_check = 0
        last_stats_report = 0
        start_time = time.time()
        
        DISCOVERY_INTERVAL = 30  # seconds
        HEALTH_CHECK_INTERVAL = 10  # seconds
        STATS_REPORT_INTERVAL = 60  # seconds
        
        print("🔄 Entering main loop...")
        
        while self.running:
            try:
                current_time = time.time()
                self.stats['uptime'] = int(current_time - start_time)
                
                # Periodic discovery broadcast
                if current_time - last_discovery > DISCOVERY_INTERVAL:
                    self.network.broadcast_discovery(self.crypto.get_public_key())
                    last_discovery = current_time
                
                # Health check for peers
                if current_time - last_health_check > HEALTH_CHECK_INTERVAL:
                    self.network.check_peer_health()
                    last_health_check = current_time
                
                # Report stats to dashboard
                if current_time - last_stats_report > STATS_REPORT_INTERVAL:
                    self.report_stats()
                    last_stats_report = current_time
                
                time.sleep(0.1)  # Small delay to prevent tight loop
                
            except KeyboardInterrupt:
                print("\n⏹️  Stopping node...")
                self.stop()
                break
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
    
    def report_stats(self):
        """Report node statistics to dashboard"""
        stats_data = {
            'type': 'STATS',
            'node_id': self.node_id,
            'node_name': self.node_name,
            'peers': self.network.get_peer_list(),
            'stats': self.stats,
            'timestamp': time.time()
        }
        
        # Send to dashboard server if configured
        dashboard_ip = self.config.get('dashboard_ip')
        if dashboard_ip:
            try:
                self.network.send_to_dashboard(json.dumps(stats_data), dashboard_ip)
                print(f"📊 Stats reported: {len(self.network.peers)} peers, {self.stats['messages_sent']} sent")
            except Exception as e:
                print(f"⚠️  Could not report stats: {e}")
    
    def stop(self):
        """Stop the node gracefully"""
        self.running = False
        self.network.stop()
        print("✅ Node stopped")
    
    def get_status(self):
        """Get current node status"""
        return {
            'node_id': self.node_id,
            'node_name': self.node_name,
            'ip': self.network.get_ip(),
            'peers': len(self.network.peers),
            'stats': self.stats
        }


def main():
    """Entry point"""
    node = NexLatticeNode()
    node.start()


if __name__ == '__main__':
    main()

