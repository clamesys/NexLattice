"""
NexLattice Network Simulator
Test the mesh network virtually before deploying to ESP32s
"""

import random
import time
import json
import threading
from collections import defaultdict
import requests

class SimulatedNode:
    """Simulates a NexLattice node in software"""
    
    def __init__(self, node_id, node_name, position=(0, 0)):
        self.node_id = node_id
        self.node_name = node_name
        self.position = position  # (x, y) for visualization
        
        # Node state
        self.online = True
        self.peers = {}  # peer_id: {name, distance, latency}
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'messages_forwarded': 0,
            'uptime': 0
        }
        
        # Message queue
        self.message_queue = []
        
        # Routing table
        self.routing_table = {}
        
        # Message cache for loop prevention
        self.message_cache = set()
        
        self.start_time = time.time()
        
        print(f"✅ Simulated node created: {self.node_name} ({self.node_id})")
    
    def discover_peer(self, peer_node):
        """Discover and add a peer"""
        if peer_node.node_id == self.node_id or not peer_node.online:
            return
        
        distance = self._calculate_distance(peer_node)
        
        # Only add peer if within range (arbitrary: 300 units)
        if distance <= 300:
            self.peers[peer_node.node_id] = {
                'name': peer_node.node_name,
                'distance': distance,
                'latency': distance / 10.0,  # Simulated latency
                'node': peer_node
            }
            print(f"🔍 {self.node_name}: Discovered {peer_node.node_name} (distance: {distance:.1f})")
    
    def _calculate_distance(self, peer_node):
        """Calculate Euclidean distance to peer"""
        dx = self.position[0] - peer_node.position[0]
        dy = self.position[1] - peer_node.position[1]
        return (dx**2 + dy**2)**0.5
    
    def send_message(self, dest_id, payload):
        """Send a message to destination"""
        if not self.online:
            return False
        
        message = {
            'type': 'DATA',
            'source': self.node_id,
            'destination': dest_id,
            'payload': payload,
            'hop_count': 0,
            'msg_id': f"{self.node_id}_{time.time()}",
            'path': [self.node_id],
            'timestamp': time.time()
        }
        
        self.stats['messages_sent'] += 1
        return self._route_message(message)
    
    def _route_message(self, message):
        """Route message to destination"""
        dest_id = message['destination']
        
        # Check if we're the destination
        if dest_id == self.node_id:
            self._receive_message(message)
            return True
        
        # Check for direct peer
        if dest_id in self.peers and self.peers[dest_id]['node'].online:
            return self._forward_to_peer(message, dest_id)
        
        # Use routing table
        next_hop = self.routing_table.get(dest_id)
        if next_hop and next_hop in self.peers:
            return self._forward_to_peer(message, next_hop)
        
        # Flood to all peers (last resort)
        return self._flood_message(message)
    
    def _forward_to_peer(self, message, peer_id):
        """Forward message to specific peer"""
        if peer_id not in self.peers:
            return False
        
        peer = self.peers[peer_id]['node']
        if not peer.online:
            return False
        
        # Increment hop count
        message['hop_count'] += 1
        message['path'].append(self.node_id)
        
        # Check hop limit
        if message['hop_count'] > 5:
            print(f"❌ {self.node_name}: Max hops exceeded")
            return False
        
        # Simulate network delay
        latency = self.peers[peer_id]['latency']
        time.sleep(latency / 1000.0)  # Convert to seconds
        
        # Forward to peer
        success = peer.receive_from_peer(message)
        
        if success and message['destination'] != peer_id:
            self.stats['messages_forwarded'] += 1
        
        return success
    
    def _flood_message(self, message):
        """Flood message to all peers"""
        msg_id = message['msg_id']
        
        if msg_id in self.message_cache:
            return False
        
        self.message_cache.add(msg_id)
        message['flooded'] = True
        
        success_count = 0
        for peer_id in self.peers:
            if self._forward_to_peer(message.copy(), peer_id):
                success_count += 1
        
        return success_count > 0
    
    def receive_from_peer(self, message):
        """Receive message from peer"""
        if not self.online:
            return False
        
        msg_id = message['msg_id']
        
        # Loop prevention
        if msg_id in self.message_cache:
            return False
        
        self.message_cache.add(msg_id)
        
        # Check if we're the destination
        if message['destination'] == self.node_id:
            self._receive_message(message)
            return True
        else:
            # Forward the message
            return self._route_message(message)
    
    def _receive_message(self, message):
        """Process received message at destination"""
        self.stats['messages_received'] += 1
        
        path_str = ' → '.join(message['path'] + [self.node_id])
        print(f"📨 {self.node_name}: Received message from {message['source']}")
        print(f"   Path: {path_str} ({message['hop_count']} hops)")
        print(f"   Payload: {message['payload']}")
    
    def build_routing_table(self, all_nodes):
        """Build routing table using simple next-hop logic"""
        self.routing_table.clear()
        
        # Direct peers
        for peer_id in self.peers:
            self.routing_table[peer_id] = peer_id
        
        # Multi-hop routes through peers
        for peer_id, peer_info in self.peers.items():
            peer_node = peer_info['node']
            for remote_peer_id in peer_node.peers:
                if remote_peer_id != self.node_id and remote_peer_id not in self.routing_table:
                    self.routing_table[remote_peer_id] = peer_id
    
    def update_stats(self):
        """Update statistics"""
        self.stats['uptime'] = int(time.time() - self.start_time)
    
    def get_status(self):
        """Get node status for reporting"""
        self.update_stats()
        
        return {
            'node_id': self.node_id,
            'node_name': self.node_name,
            'online': self.online,
            'position': self.position,
            'peers': [
                {
                    'id': peer_id,
                    'name': info['name'],
                    'distance': info['distance'],
                    'latency': info['latency'],
                    'connected': info['node'].online
                }
                for peer_id, info in self.peers.items()
            ],
            'stats': self.stats
        }


class NetworkSimulator:
    """Simulates the entire NexLattice mesh network"""
    
    def __init__(self, dashboard_url="http://localhost:8080"):
        self.nodes = {}
        self.dashboard_url = dashboard_url
        self.running = False
        self.sim_thread = None
        
        print("🚀 NexLattice Network Simulator Starting...")
    
    def create_node(self, node_id, node_name, position=(0, 0)):
        """Create a new simulated node"""
        node = SimulatedNode(node_id, node_name, position)
        self.nodes[node_id] = node
        return node
    
    def create_topology(self, topology_type='line', node_count=5):
        """Create a network topology"""
        print(f"📐 Creating {topology_type} topology with {node_count} nodes...")
        
        if topology_type == 'line':
            # Linear topology: Node1 - Node2 - Node3 - Node4 - Node5
            for i in range(node_count):
                x = i * 200
                y = 0
                self.create_node(f"node_{i+1:03d}", f"Node {i+1}", (x, y))
        
        elif topology_type == 'star':
            # Star topology: Central node with others around
            self.create_node("node_001", "Central Node", (200, 200))
            for i in range(1, node_count):
                angle = (i / (node_count - 1)) * 2 * 3.14159
                x = 200 + 150 * math.cos(angle)
                y = 200 + 150 * math.sin(angle)
                self.create_node(f"node_{i+1:03d}", f"Node {i+1}", (x, y))
        
        elif topology_type == 'mesh':
            # Mesh topology: Grid layout
            grid_size = int(node_count ** 0.5) + 1
            for i in range(node_count):
                row = i // grid_size
                col = i % grid_size
                x = col * 200
                y = row * 200
                self.create_node(f"node_{i+1:03d}", f"Node {i+1}", (x, y))
        
        elif topology_type == 'random':
            # Random positions
            for i in range(node_count):
                x = random.randint(0, 500)
                y = random.randint(0, 500)
                self.create_node(f"node_{i+1:03d}", f"Node {i+1}", (x, y))
        
        print(f"✅ Created {len(self.nodes)} nodes")
    
    def run_discovery(self):
        """Run peer discovery for all nodes"""
        print("🔍 Running peer discovery...")
        
        # Each node discovers all other nodes within range
        nodes_list = list(self.nodes.values())
        for node in nodes_list:
            for peer in nodes_list:
                if node != peer:
                    node.discover_peer(peer)
        
        # Build routing tables
        for node in self.nodes.values():
            node.build_routing_table(self.nodes)
        
        print("✅ Discovery complete")
        self.print_network_stats()
    
    def send_test_message(self, source_id, dest_id, payload):
        """Send a test message through the network"""
        if source_id not in self.nodes:
            print(f"❌ Source node {source_id} not found")
            return False
        
        if dest_id not in self.nodes:
            print(f"❌ Destination node {dest_id} not found")
            return False
        
        source = self.nodes[source_id]
        print(f"\n📤 Sending message: {source_id} → {dest_id}")
        print(f"   Payload: {payload}")
        
        success = source.send_message(dest_id, payload)
        
        if success:
            print("✅ Message delivery successful\n")
        else:
            print("❌ Message delivery failed\n")
        
        return success
    
    def simulate_node_failure(self, node_id):
        """Simulate a node going offline"""
        if node_id in self.nodes:
            self.nodes[node_id].online = False
            print(f"💥 Node {node_id} went offline")
            
            # Rebuild routing tables
            for node in self.nodes.values():
                if node.online:
                    node.build_routing_table(self.nodes)
    
    def simulate_node_recovery(self, node_id):
        """Simulate a node coming back online"""
        if node_id in self.nodes:
            self.nodes[node_id].online = True
            print(f"✅ Node {node_id} recovered")
            
            # Re-run discovery
            self.run_discovery()
    
    def report_to_dashboard(self):
        """Report node status to dashboard"""
        for node in self.nodes.values():
            status = node.get_status()
            
            try:
                response = requests.post(
                    f"{self.dashboard_url}/api/update_node",
                    json={
                        'node_id': status['node_id'],
                        'node_name': status['node_name'],
                        'peers': status['peers'],
                        'stats': status['stats']
                    },
                    timeout=2
                )
                
                if response.status_code != 200:
                    print(f"⚠️  Dashboard update failed for {node.node_id}")
            
            except requests.exceptions.RequestException as e:
                print(f"⚠️  Could not connect to dashboard: {e}")
                return False
        
        return True
    
    def print_network_stats(self):
        """Print network statistics"""
        print("\n" + "="*50)
        print("📊 Network Statistics")
        print("="*50)
        
        total_nodes = len(self.nodes)
        online_nodes = sum(1 for n in self.nodes.values() if n.online)
        total_links = sum(len(n.peers) for n in self.nodes.values()) // 2
        
        print(f"Total Nodes: {total_nodes}")
        print(f"Online Nodes: {online_nodes}")
        print(f"Total Links: {total_links}")
        print()
        
        for node in self.nodes.values():
            status = "🟢" if node.online else "🔴"
            print(f"{status} {node.node_name} ({node.node_id})")
            print(f"   Peers: {len(node.peers)}")
            print(f"   Sent: {node.stats['messages_sent']}, "
                  f"Received: {node.stats['messages_received']}, "
                  f"Forwarded: {node.stats['messages_forwarded']}")
        
        print("="*50 + "\n")
    
    def start_continuous_sim(self, interval=10):
        """Start continuous simulation with periodic dashboard updates"""
        self.running = True
        
        def sim_loop():
            while self.running:
                self.report_to_dashboard()
                time.sleep(interval)
        
        self.sim_thread = threading.Thread(target=sim_loop, daemon=True)
        self.sim_thread.start()
        print(f"🔄 Continuous simulation started (reporting every {interval}s)")
    
    def stop_continuous_sim(self):
        """Stop continuous simulation"""
        self.running = False
        if self.sim_thread:
            self.sim_thread.join()
        print("⏹️  Continuous simulation stopped")


def main():
    """Example simulation"""
    import math
    
    # Create simulator
    sim = NetworkSimulator()
    
    # Create network topology
    sim.create_topology('line', 5)
    
    # Run discovery
    sim.run_discovery()
    
    # Test direct message
    print("\n--- Test 1: Direct Message ---")
    sim.send_test_message("node_001", "node_002", "Hello, neighbor!")
    
    # Test multi-hop message
    print("\n--- Test 2: Multi-Hop Message ---")
    sim.send_test_message("node_001", "node_005", "Hello from the other side!")
    
    # Test node failure
    print("\n--- Test 3: Node Failure ---")
    sim.simulate_node_failure("node_003")
    sim.send_test_message("node_001", "node_005", "Testing with node_003 offline")
    
    # Test node recovery
    print("\n--- Test 4: Node Recovery ---")
    sim.simulate_node_recovery("node_003")
    sim.send_test_message("node_001", "node_005", "Testing after node_003 recovery")
    
    # Final stats
    sim.print_network_stats()
    
    # Start continuous reporting to dashboard
    print("\n--- Starting Dashboard Integration ---")
    print("Starting continuous simulation. Press Ctrl+C to stop.")
    sim.start_continuous_sim(interval=5)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping simulation...")
        sim.stop_continuous_sim()
        print("✅ Simulation complete")


if __name__ == '__main__':
    main()

