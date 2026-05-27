"""
NexLattice Message Router
Implements dynamic Ad-Hoc On-Demand Distance Vector (AODV) routing for the mesh network
"""

import time
import json


class MessageRouter:
    def __init__(self, node_id, network_manager, crypto_manager):
        """Initialize dynamic AODV router"""
        self.node_id = node_id
        self.network = network_manager
        self.crypto = crypto_manager
        
        # Routing table: destination_id -> {next_hop, hop_distance, active, updated}
        self.routing_table = {}
        
        # Message cache for loop prevention
        self.message_cache = {}  # message_id -> timestamp
        self.cache_ttl = 60  # seconds
        
        # AODV buffers and parameters
        self.message_buffer = {}  # dest_id -> list of messages waiting for route
        self.rreq_seq_num = 0
        self.seen_rreqs = {}  # (source_id, rreq_id) -> timestamp
        self.max_hops = 5
        
        print(f"🗺️  Dynamic AODV Router initialized for {node_id}")
    
    def route_message(self, message):
        """Route a message to its destination using AODV routing"""
        dest_id = message.get('destination')
        
        # Check if destination is a direct peer
        peer = self.network.get_peer(dest_id)
        if peer and peer.get('connected'):
            # Send directly
            return self._send_message(message, peer['ip'])
        
        # Find active route in our routing table
        route = self.routing_table.get(dest_id)
        if route and route.get('active'):
            next_hop = route['next_hop']
            next_hop_peer = self.network.get_peer(next_hop)
            if next_hop_peer and next_hop_peer.get('connected'):
                # Forward to next hop
                return self._send_message(message, next_hop_peer['ip'])
            else:
                # Route is broken
                route['active'] = False
                print(f"⚠️  Route to {dest_id} is broken (next hop {next_hop} disconnected)")
        
        # No active route - initiate AODV Route Discovery
        print(f"🔍 No route to {dest_id}, initiating AODV Route Request (RREQ)")
        self.buffer_message(dest_id, message)
        self.send_rreq(dest_id)
        return True
    
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
        
        # Cache message
        self.message_cache[msg_id] = time.time()
        self._cleanup_cache()
        
        # Route the message using our AODV router
        return self.route_message(message)
    
    def buffer_message(self, dest_id, message):
        """Buffer a message waiting for route discovery"""
        if dest_id not in self.message_buffer:
            self.message_buffer[dest_id] = []
        self.message_buffer[dest_id].append(message)
        print(f"📥 Buffered message for {dest_id} (total buffered: {len(self.message_buffer[dest_id])})")
    
    def send_rreq(self, dest_id):
        """Broadcast AODV Route Request (RREQ)"""
        self.rreq_seq_num += 1
        
        rreq = {
            'type': 'AODV_RREQ',
            'rreq_id': self.rreq_seq_num,
            'source': self.node_id,
            'destination': dest_id,
            'hop_count': 0,
            'timestamp': time.time()
        }
        
        # Sign the RREQ
        rreq['signature'] = self.crypto.sign_message(rreq)
        
        # Broadcast RREQ to subnet
        try:
            broadcast_ip = self.network._get_broadcast_ip()
            rreq_json = json.dumps(rreq)
            self.network.send_direct(rreq_json, broadcast_ip)
            print(f"📢 Broadcasted AODV RREQ #{self.rreq_seq_num} for destination {dest_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to broadcast RREQ: {e}")
            return False
    
    def handle_rreq(self, rreq_data, sender_ip):
        """Process received AODV Route Request (RREQ)"""
        source = rreq_data.get('source')
        rreq_id = rreq_data.get('rreq_id')
        dest = rreq_data.get('destination')
        hop_count = rreq_data.get('hop_count', 0)
        
        # Prevent self-routing loops
        if source == self.node_id:
            return False
        
        # Check if we have already seen this RREQ
        rreq_key = (source, rreq_id)
        if rreq_key in self.seen_rreqs:
            return False
        
        # Record this RREQ as seen
        self.seen_rreqs[rreq_key] = time.time()
        
        print(f"📥 Received AODV RREQ #{rreq_id} from {source} for {dest} via {sender_ip}")
        
        # Identify node ID for sender_ip to build routing entry
        sender_id = None
        for p_id, p_info in self.network.peers.items():
            if p_info.get('ip') == sender_ip:
                sender_id = p_id
                break
        
        if not sender_id:
            sender_id = source  # Fallback placeholder
        
        # Update reverse route back to RREQ source
        self.routing_table[source] = {
            'next_hop': sender_id,
            'hop_distance': hop_count + 1,
            'active': True,
            'updated': time.time()
        }
        print(f"🗺️  Reverse route established: {source} via {sender_id} (hops: {hop_count + 1})")
        
        # Update network peer hop distance for visual topology
        self.network.update_peer_hop_distance(source, hop_count + 1)
        
        # Check if we are the destination of the RREQ
        if dest == self.node_id:
            print(f"🎯 We are the destination! Generating AODV Route Reply (RREP)")
            self.send_rrep(source, dest, hop_count + 1)
            return True
        
        # Check if we have an active route to the destination
        dest_route = self.routing_table.get(dest)
        if dest_route and dest_route.get('active'):
            print(f"🎯 We have an active route to destination {dest}! Generating intermediate AODV RREP")
            self.send_rrep(source, dest, dest_route['hop_distance'])
            return True
            
        # Re-broadcast RREQ if max hops not reached
        if hop_count < self.max_hops:
            rreq_data['hop_count'] = hop_count + 1
            rreq_data['signature'] = self.crypto.sign_message(rreq_data)
            
            try:
                broadcast_ip = self.network._get_broadcast_ip()
                rreq_json = json.dumps(rreq_data)
                self.network.send_direct(rreq_json, broadcast_ip)
                print(f"📢 Forwarded RREQ #{rreq_id} from {source} (hop: {hop_count + 1})")
                return True
            except Exception as e:
                print(f"❌ Failed to forward RREQ: {e}")
        
        return False
    
    def send_rrep(self, source, dest, hop_distance):
        """Send AODV Route Reply (RREP) unicast back to the source"""
        reverse_route = self.routing_table.get(source)
        if not reverse_route or not reverse_route.get('active'):
            print(f"❌ Cannot send RREP: No reverse route back to RREQ source {source}")
            return False
            
        next_hop = reverse_route['next_hop']
        next_hop_peer = self.network.get_peer(next_hop)
        if not next_hop_peer:
            print(f"❌ Cannot send RREP: Next hop {next_hop} peer info not found")
            return False
            
        rrep = {
            'type': 'AODV_RREP',
            'source': source,
            'destination': dest,
            'hop_count': 0,
            'total_hop_distance': hop_distance,
            'timestamp': time.time()
        }
        
        rrep['signature'] = self.crypto.sign_message(rrep)
        
        rrep_json = json.dumps(rrep)
        self.network.send_direct(rrep_json, next_hop_peer['ip'])
        print(f"📤 Sent AODV RREP back to {source} via next hop {next_hop} ({next_hop_peer['ip']})")
        return True
    
    def handle_rrep(self, rrep_data, sender_ip):
        """Process received AODV Route Reply (RREP)"""
        source = rrep_data.get('source')
        dest = rrep_data.get('destination')
        hop_count = rrep_data.get('hop_count', 0)
        
        sender_id = None
        for p_id, p_info in self.network.peers.items():
            if p_info.get('ip') == sender_ip:
                sender_id = p_id
                break
                
        if not sender_id:
            sender_id = dest  # Fallback
            
        # Update forward route to destination (dest)
        self.routing_table[dest] = {
            'next_hop': sender_id,
            'hop_distance': hop_count + 1,
            'active': True,
            'updated': time.time()
        }
        print(f"🗺️  Forward route established: {dest} via {sender_id} (hops: {hop_count + 1})")
        
        self.network.update_peer_hop_distance(dest, hop_count + 1)
        
        # Check if we are the destination of the RREP
        if source == self.node_id:
            print(f"🎯 RREP reached the initiator {self.node_id}! Route search successful.")
            self.flush_buffer(dest)
            return True
            
        # Otherwise, propagate the RREP back towards the source
        reverse_route = self.routing_table.get(source)
        if reverse_route and reverse_route.get('active'):
            next_hop = reverse_route['next_hop']
            next_hop_peer = self.network.get_peer(next_hop)
            if next_hop_peer:
                rrep_data['hop_count'] = hop_count + 1
                rrep_data['signature'] = self.crypto.sign_message(rrep_data)
                
                rrep_json = json.dumps(rrep_data)
                self.network.send_direct(rrep_json, next_hop_peer['ip'])
                print(f"📤 Forwarded RREP for {dest} to {source} via {next_hop} ({next_hop_peer['ip']})")
                return True
                
        print(f"❌ Failed to forward RREP: No reverse route back to {source}")
        return False
    
    def flush_buffer(self, dest_id):
        """Flush buffered messages for destination now that a route is found"""
        messages = self.message_buffer.pop(dest_id, [])
        if not messages:
            return
            
        print(f"🚀 Flushing {len(messages)} buffered messages to {dest_id}...")
        
        route = self.routing_table.get(dest_id)
        if route and route.get('active'):
            next_hop = route['next_hop']
            next_hop_peer = self.network.get_peer(next_hop)
            if next_hop_peer:
                for msg in messages:
                    msg['timestamp'] = time.time()
                    msg['signature'] = self.crypto.sign_message(msg)
                    
                    msg_json = json.dumps(msg)
                    self.network.send_direct(msg_json, next_hop_peer['ip'])
                print(f"✅ Successfully sent all buffered messages to {dest_id} via {next_hop}")
    
    def _send_message(self, message, dest_ip):
        """Send message directly to specific IP"""
        try:
            message_json = json.dumps(message)
            return self.network.send_direct(message_json, dest_ip)
        except Exception as e:
            print(f"❌ Failed to send message: {e}")
            return False
            
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
