"""
NexLattice Message Router
Implements hop-by-hop routing for mesh network
"""

import time
import json


class MessageRouter:
    def __init__(self, node_id, network_manager, crypto_manager):
        """Initialize message router"""
        self.node_id = node_id
        self.network = network_manager
        self.crypto = crypto_manager
        
        # Routing table: destination_id -> next_hop_id
        self.routing_table = {}
        
        # Message cache for loop prevention
        self.message_cache = {}  # message_id -> timestamp
        self.cache_ttl = 60  # seconds
        
        # Routing metrics
        self.max_hops = 5
        
        print(f"🗺️  Router initialized for {node_id}")
    
    def route_message(self, message):
        """Route a message to its destination"""
        dest_id = message.get('destination')
        
        # Check if destination is a direct peer
        peer = self.network.get_peer(dest_id)
        if peer and peer.get('connected'):
            # Send directly
            return self._send_message(message, peer['ip'])
        
        # Find route through routing table
        next_hop = self._find_next_hop(dest_id)
        if next_hop:
            next_hop_peer = self.network.get_peer(next_hop)
            if next_hop_peer:
                return self._send_message(message, next_hop_peer['ip'])
        
        # No route found - try flooding to all peers (simple fallback)
        print(f"⚠️  No direct route to {dest_id}, attempting flood")
        return self._flood_message(message)
    
    def forward_message(self, message):
        """Forward a received message to its destination"""
        msg_id = message.get('msg_id', f"{message['source']}_{message['timestamp']}")
        
        # Check if we've seen this message (loop prevention)
        if msg_id in self.message_cache:
            print(f"🔄 Message loop detected, dropping {msg_id}")
            return False
        
        # Check hop count
        hop_count = message.get('hop_count', 0)
        if hop_count >= self.max_hops:
            print(f"❌ Max hops reached for message {msg_id}")
            return False
        
        # Increment hop count
        message['hop_count'] = hop_count + 1
        message['msg_id'] = msg_id
        
        # Update hop distances for peers based on this message
        source_id = message.get('source')
        if source_id:
            # Update hop distance: source is (hop_count + 1) hops away
            new_hop_distance = hop_count + 1
            self.network.update_peer_hop_distance(source_id, new_hop_distance)
        
        # Cache message
        self.message_cache[msg_id] = time.time()
        self._cleanup_cache()
        
        # Route the message
        return self.route_message(message)
    
    def _send_message(self, message, dest_ip):
        """Send message to specific IP"""
        try:
            message_json = json.dumps(message)
            return self.network.send_direct(message_json, dest_ip)
        except Exception as e:
            print(f"❌ Failed to send message: {e}")
            return False
    
    def _flood_message(self, message):
        """Flood message to all connected peers (last resort)"""
        msg_id = message.get('msg_id', f"{message['source']}_{message['timestamp']}")
        
        # Mark as flooded
        message['flooded'] = True
        
        # Cache to prevent loops
        self.message_cache[msg_id] = time.time()
        
        success_count = 0
        peers = self.network.get_peer_list()
        
        for peer in peers:
            if peer['connected']:
                if self._send_message(message, peer['ip']):
                    success_count += 1
        
        return success_count > 0
    
    def _find_next_hop(self, dest_id):
        """Find next hop for destination using routing table"""
        return self.routing_table.get(dest_id)
    
    def update_routing_table(self, dest_id, next_hop_id, metric=1, hop_distance=1):
        """Update routing table entry"""
        # Simple routing: just store next hop
        # In production, implement distance-vector or link-state routing
        
        current_entry = self.routing_table.get(dest_id)
        
        # Update if no route exists or new route is better
        if not current_entry or metric < current_entry.get('metric', float('inf')):
            self.routing_table[dest_id] = {
                'next_hop': next_hop_id,
                'metric': metric,
                'hop_distance': hop_distance,
                'updated': time.time()
            }
            print(f"🗺️  Route updated: {dest_id} via {next_hop_id} (metric: {metric}, hops: {hop_distance})")
            
            # Update peer hop distance if peer exists
            peer = self.network.get_peer(dest_id)
            if peer:
                self.network.update_peer_hop_distance(dest_id, hop_distance)
            
            return True
        
        return False
    
    def build_routing_table(self):
        """Build routing table from peer information"""
        # Simple approach: all known peers are one hop away
        # In production, implement a proper routing protocol
        
        peers = self.network.get_peer_list()
        
        for peer in peers:
            if peer['connected']:
                hop_distance = peer.get('hop_distance', 1)
                self.update_routing_table(peer['id'], peer['id'], metric=1, hop_distance=hop_distance)
        
        # For multi-hop routing, would need to exchange routing info with peers
        print(f"🗺️  Routing table built: {len(self.routing_table)} routes")
    
    def _cleanup_cache(self):
        """Remove old entries from message cache"""
        current_time = time.time()
        expired = [
            msg_id for msg_id, timestamp in self.message_cache.items()
            if current_time - timestamp > self.cache_ttl
        ]
        
        for msg_id in expired:
            del self.message_cache[msg_id]
    
    def get_routing_info(self):
        """Get current routing table information"""
        return {
            'routes': len(self.routing_table),
            'cached_messages': len(self.message_cache),
            'routing_table': self.routing_table,
            'max_hops': self.max_hops
        }

