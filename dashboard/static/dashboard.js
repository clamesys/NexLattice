// NexLattice Dashboard Client-Side JavaScript

// Initialize Socket.IO connection
const socket = io();

// Global state
let networkData = {
    nodes: [],
    links: [],
    messages: []
};

// D3 visualization variables
let svg, simulation, linkElements, nodeElements, textElements;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 NexLattice Dashboard Initializing...');
    initializeVisualization();
    setupSocketHandlers();
    fetchInitialData();
});

// Socket.IO event handlers
function setupSocketHandlers() {
    socket.on('connect', () => {
        console.log('✅ Connected to dashboard server');
        updateConnectionStatus(true);
    });

    socket.on('disconnect', () => {
        console.log('❌ Disconnected from dashboard server');
        updateConnectionStatus(false);
    });

    socket.on('initial_state', (data) => {
        console.log('📊 Received initial state', data);
        updateNetworkData(data);
    });

    socket.on('node_update', (data) => {
        console.log('🔄 Node update received', data);
        if (data.topology) {
            updateNetworkData({ topology: data.topology });
        }
        fetchStats();
    });

    socket.on('node_status', (data) => {
        console.log('⚠️  Node status change', data);
        updateNodeStatus(data.node_id, data.status);
    });

    socket.on('new_message', (data) => {
        console.log('📨 New message', data);
        addMessage(data);
    });
}

// Fetch initial data
async function fetchInitialData() {
    try {
        const response = await fetch('/api/network_state');
        const data = await response.json();
        updateNetworkData(data);
        fetchStats();
    } catch (error) {
        console.error('❌ Error fetching initial data:', error);
    }
}

// Fetch and update statistics
async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        document.getElementById('totalNodes').textContent = stats.total_nodes;
        document.getElementById('activeNodes').textContent = stats.active_nodes;
        document.getElementById('totalLinks').textContent = stats.total_links;
        document.getElementById('messagesSent').textContent = stats.messages_sent;
        document.getElementById('messagesForwarded').textContent = stats.messages_forwarded;
    } catch (error) {
        console.error('❌ Error fetching stats:', error);
    }
}

// Update network data and visualization
function updateNetworkData(data) {
    if (data.topology) {
        networkData.nodes = data.topology.nodes || [];
        networkData.links = data.topology.links || [];
        updateVisualization();
    }
    
    if (data.nodes) {
        updateNodeList(data.nodes);
    }
    
    if (data.messages) {
        networkData.messages = data.messages;
        updateMessageLog();
    }
}

// Initialize D3.js network visualization
function initializeVisualization() {
    const container = document.getElementById('network-viz');
    const width = container.clientWidth;
    const height = container.clientHeight;

    svg = d3.select('#network-viz')
        .append('svg')
        .attr('width', width)
        .attr('height', height);

    // Create simulation
    simulation = d3.forceSimulation()
        .force('link', d3.forceLink().id(d => d.id).distance(150))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(50));

    // Create arrow markers for directed links
    svg.append('defs').selectAll('marker')
        .data(['active', 'inactive'])
        .enter().append('marker')
        .attr('id', d => `arrow-${d}`)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 25)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', d => d === 'active' ? '#10b981' : '#64748b');

    // Initialize empty groups
    linkElements = svg.append('g').selectAll('line');
    nodeElements = svg.append('g').selectAll('circle');
    textElements = svg.append('g').selectAll('text');
}

// Update D3 visualization
function updateVisualization() {
    if (!svg || networkData.nodes.length === 0) return;

    // Update links
    linkElements = linkElements.data(networkData.links, d => `${d.source.id || d.source}-${d.target.id || d.target}`);
    linkElements.exit().remove();
    
    const linkEnter = linkElements.enter().append('line')
        .attr('stroke-width', 2)
        .attr('marker-end', d => `url(#arrow-${d.status})`);
    
    linkElements = linkEnter.merge(linkElements)
        .attr('stroke', d => d.status === 'active' ? '#10b981' : '#64748b')
        .attr('stroke-opacity', d => d.status === 'active' ? 0.8 : 0.3);

    // Update nodes
    nodeElements = nodeElements.data(networkData.nodes, d => d.id);
    nodeElements.exit().remove();
    
    const nodeEnter = nodeElements.enter().append('circle')
        .attr('r', 20)
        .call(d3.drag()
            .on('start', dragStarted)
            .on('drag', dragged)
            .on('end', dragEnded));
    
    nodeElements = nodeEnter.merge(nodeElements)
        .attr('fill', d => d.status === 'online' ? '#10b981' : '#ef4444')
        .attr('stroke', '#34d399')
        .attr('stroke-width', 3);

    // Update text labels
    textElements = textElements.data(networkData.nodes, d => d.id);
    textElements.exit().remove();
    
    const textEnter = textElements.enter().append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', 35)
        .attr('font-size', '12px')
        .attr('font-weight', 'bold');
    
    textElements = textEnter.merge(textElements)
        .text(d => d.name)
        .attr('fill', '#e2e8f0');

    // Update simulation
    simulation.nodes(networkData.nodes).on('tick', ticked);
    simulation.force('link').links(networkData.links);
    simulation.alpha(1).restart();
}

// D3 tick function
function ticked() {
    linkElements
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

    nodeElements
        .attr('cx', d => d.x)
        .attr('cy', d => d.y);

    textElements
        .attr('x', d => d.x)
        .attr('y', d => d.y);
}

// Drag functions
function dragStarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
}

function dragEnded(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
}

// Update node list panel
function updateNodeList(nodes) {
    const nodeList = document.getElementById('nodeList');
    
    if (nodes.length === 0) {
        nodeList.innerHTML = '<p style="color: #64748b; text-align: center;">No nodes connected...</p>';
        return;
    }
    
    nodeList.innerHTML = nodes.map(node => {
        const stats = node.stats || {};
        const isOnline = node.status === 'online';
        
        return `
            <div class="node-item ${isOnline ? '' : 'offline'}">
                <div class="node-name">
                    <span class="status-indicator ${isOnline ? '' : 'offline'}"></span>
                    ${node.node_name}
                </div>
                <div class="node-id">${node.node_id}</div>
                <div class="node-stats">
                    <span>👥 ${node.peers ? node.peers.length : 0} peers</span>
                    <span>📤 ${stats.messages_sent || 0} sent</span>
                    <span>📥 ${stats.messages_received || 0} received</span>
                    <span>🔄 ${stats.messages_forwarded || 0} forwarded</span>
                </div>
                <div style="margin-top: 0.5rem; font-size: 0.8rem; color: #64748b;">
                    Uptime: ${formatUptime(stats.uptime || 0)}
                </div>
            </div>
        `;
    }).join('');
}

// Update message log
function updateMessageLog() {
    const messageLog = document.getElementById('messageLog');
    
    if (networkData.messages.length === 0) {
        messageLog.innerHTML = '<p style="color: #64748b; text-align: center;">No messages yet...</p>';
        return;
    }
    
    messageLog.innerHTML = networkData.messages.slice(-20).reverse().map(msg => `
        <div class="message-item">
            <div class="msg-header">
                <span>${msg.source} → ${msg.destination}</span>
                <span>${formatTimestamp(msg.timestamp)}</span>
            </div>
            <div class="msg-content">${msg.message}</div>
        </div>
    `).join('');
}

// Add new message to log
function addMessage(message) {
    networkData.messages.push(message);
    updateMessageLog();
}

// Update node status
function updateNodeStatus(nodeId, status) {
    const node = networkData.nodes.find(n => n.id === nodeId);
    if (node) {
        node.status = status;
        updateVisualization();
        fetchInitialData();
    }
}

// Update connection status indicator
function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connectionStatus');
    if (connected) {
        statusEl.classList.remove('disconnected');
        statusEl.innerHTML = '<span class="status-indicator"></span><span>Connected</span>';
    } else {
        statusEl.classList.add('disconnected');
        statusEl.innerHTML = '<span class="status-indicator offline"></span><span>Disconnected</span>';
    }
}

// Utility functions
function formatUptime(seconds) {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
}

function formatTimestamp(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString();
}

// Auto-refresh stats
setInterval(fetchStats, 5000);

