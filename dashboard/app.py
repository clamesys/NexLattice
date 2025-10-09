"""
NexLattice Dashboard - Main Application
Real-time visualization of mesh network status
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
import time
from datetime import datetime
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'nexlattice-secret-key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Network state
network_state = {
    'nodes': {},  # node_id: {info, stats, last_update}
    'messages': [],  # Recent messages
    'topology': {
        'nodes': [],
        'links': []
    }
}

# Lock for thread-safe updates
state_lock = threading.Lock()


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/api/network_state')
def get_network_state():
    """Get current network state"""
    with state_lock:
        return jsonify({
            'nodes': list(network_state['nodes'].values()),
            'topology': network_state['topology'],
            'messages': network_state['messages'][-50:],  # Last 50 messages
            'timestamp': time.time()
        })


@app.route('/api/update_node', methods=['POST'])
def update_node():
    """Receive status updates from nodes"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        node_id = data.get('node_id')
        if not node_id:
            return jsonify({'error': 'No node_id provided'}), 400
        
        with state_lock:
            # Update node info
            network_state['nodes'][node_id] = {
                'node_id': node_id,
                'node_name': data.get('node_name'),
                'peers': data.get('peers', []),
                'stats': data.get('stats', {}),
                'last_update': time.time(),
                'status': 'online'
            }
            
            # Update topology
            update_topology()
        
        # Broadcast update to all connected clients
        socketio.emit('node_update', {
            'node_id': node_id,
            'data': network_state['nodes'][node_id],
            'topology': network_state['topology']
        })
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error updating node: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/send_message', methods=['POST'])
def send_message():
    """API endpoint to send test message through network"""
    try:
        data = request.get_json()
        source = data.get('source')
        destination = data.get('destination')
        message = data.get('message')
        
        if not all([source, destination, message]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Log message
        message_entry = {
            'id': f"msg_{int(time.time() * 1000)}",
            'source': source,
            'destination': destination,
            'message': message,
            'timestamp': time.time(),
            'status': 'sent'
        }
        
        with state_lock:
            network_state['messages'].append(message_entry)
            # Keep only last 100 messages
            if len(network_state['messages']) > 100:
                network_state['messages'] = network_state['messages'][-100:]
        
        # Broadcast to clients
        socketio.emit('new_message', message_entry)
        
        return jsonify({'success': True, 'message_id': message_entry['id']})
        
    except Exception as e:
        print(f"Error sending message: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/nodes')
def get_nodes():
    """Get list of all nodes"""
    with state_lock:
        nodes = list(network_state['nodes'].values())
    return jsonify({'nodes': nodes})


@app.route('/api/node/<node_id>')
def get_node_details(node_id):
    """Get detailed information about specific node"""
    with state_lock:
        node = network_state['nodes'].get(node_id)
    
    if node:
        return jsonify(node)
    else:
        return jsonify({'error': 'Node not found'}), 404


@app.route('/api/stats')
def get_stats():
    """Get overall network statistics"""
    with state_lock:
        total_nodes = len(network_state['nodes'])
        active_nodes = sum(1 for n in network_state['nodes'].values() 
                          if time.time() - n['last_update'] < 120)
        total_links = len(network_state['topology']['links'])
        total_messages = len(network_state['messages'])
        
        # Calculate total stats
        total_sent = sum(n['stats'].get('messages_sent', 0) 
                        for n in network_state['nodes'].values())
        total_received = sum(n['stats'].get('messages_received', 0) 
                            for n in network_state['nodes'].values())
        total_forwarded = sum(n['stats'].get('messages_forwarded', 0) 
                             for n in network_state['nodes'].values())
    
    return jsonify({
        'total_nodes': total_nodes,
        'active_nodes': active_nodes,
        'total_links': total_links,
        'total_messages': total_messages,
        'messages_sent': total_sent,
        'messages_received': total_received,
        'messages_forwarded': total_forwarded,
        'timestamp': time.time()
    })


def update_topology():
    """Update network topology from node peer information"""
    nodes_list = []
    links_list = []
    link_set = set()  # To avoid duplicates
    
    for node_id, node_info in network_state['nodes'].items():
        # Add node
        nodes_list.append({
            'id': node_id,
            'name': node_info['node_name'],
            'status': node_info['status'],
            'peers': len(node_info.get('peers', [])),
            'uptime': node_info['stats'].get('uptime', 0)
        })
        
        # Add links to peers
        for peer in node_info.get('peers', []):
            peer_id = peer.get('id')
            if peer_id:
                # Create link (ensure no duplicates)
                link_key = tuple(sorted([node_id, peer_id]))
                if link_key not in link_set:
                    link_set.add(link_key)
                    links_list.append({
                        'source': node_id,
                        'target': peer_id,
                        'latency': peer.get('latency'),
                        'status': 'active' if peer.get('connected') else 'inactive'
                    })
    
    network_state['topology'] = {
        'nodes': nodes_list,
        'links': links_list
    }


def check_node_timeouts():
    """Background task to check for inactive nodes"""
    while True:
        time.sleep(30)  # Check every 30 seconds
        
        current_time = time.time()
        timeout = 120  # 2 minutes
        
        with state_lock:
            for node_id, node_info in network_state['nodes'].items():
                if current_time - node_info['last_update'] > timeout:
                    if node_info['status'] != 'offline':
                        node_info['status'] = 'offline'
                        
                        # Notify clients
                        socketio.emit('node_status', {
                            'node_id': node_id,
                            'status': 'offline'
                        })


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Client connected: {request.sid}")
    
    # Send current state to new client
    with state_lock:
        emit('initial_state', {
            'nodes': list(network_state['nodes'].values()),
            'topology': network_state['topology'],
            'messages': network_state['messages'][-50:]
        })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"Client disconnected: {request.sid}")


@socketio.on('request_update')
def handle_update_request():
    """Handle manual update request from client"""
    with state_lock:
        emit('node_update', {
            'topology': network_state['topology'],
            'timestamp': time.time()
        })


def init_app():
    """Initialize application"""
    print("🚀 NexLattice Dashboard Starting...")
    print("=" * 50)
    
    # Start background thread for timeout checking
    timeout_thread = threading.Thread(target=check_node_timeouts, daemon=True)
    timeout_thread.start()
    
    print("✅ Dashboard initialized")
    print("📊 Access dashboard at: http://localhost:8080")
    print("=" * 50)


if __name__ == '__main__':
    init_app()
    socketio.run(app, host='0.0.0.0', port=8080, debug=True)

