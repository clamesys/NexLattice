#!/usr/bin/env python3
"""
Quick test script for NexLattice simulator
"""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from simulator.network_simulator import NetworkSimulator
import math

def run_basic_test():
    """Run basic simulator test"""
    print("\n" + "="*60)
    print("  NexLattice Simulator - Basic Test")
    print("="*60 + "\n")
    
    # Create simulator
    sim = NetworkSimulator(dashboard_url="http://localhost:8080")
    
    # Test 1: Line topology
    print("📐 Test 1: Line Topology")
    print("-" * 40)
    sim.create_topology('line', 5)
    sim.run_discovery()
    
    # Send messages
    print("\n📤 Sending test messages...")
    sim.send_test_message("node_001", "node_002", "Hello, neighbor!")
    time.sleep(1)
    sim.send_test_message("node_001", "node_005", "Multi-hop message!")
    time.sleep(1)
    
    # Stats
    sim.print_network_stats()
    
    # Test 2: Node failure
    print("\n💥 Test 2: Node Failure Simulation")
    print("-" * 40)
    sim.simulate_node_failure("node_003")
    time.sleep(1)
    sim.send_test_message("node_001", "node_005", "Testing with failure")
    time.sleep(1)
    
    # Test 3: Node recovery
    print("\n✅ Test 3: Node Recovery")
    print("-" * 40)
    sim.simulate_node_recovery("node_003")
    time.sleep(1)
    sim.send_test_message("node_001", "node_005", "Testing after recovery")
    time.sleep(1)
    
    # Final stats
    sim.print_network_stats()
    
    print("\n✅ Basic test complete!\n")
    
    # Ask about dashboard integration
    print("Would you like to start continuous dashboard integration?")
    print("This will send updates to http://localhost:8080 every 5 seconds.")
    print("Make sure the dashboard is running first!")
    response = input("Start dashboard integration? (y/n): ").lower().strip()
    
    if response == 'y':
        print("\n🔄 Starting continuous simulation...")
        print("Press Ctrl+C to stop\n")
        
        sim.start_continuous_sim(interval=5)
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nStopping simulation...")
            sim.stop_continuous_sim()
            print("✅ Simulation stopped\n")
    else:
        print("\n👋 Test complete. Exiting.\n")

def run_advanced_test():
    """Run advanced simulator tests"""
    print("\n" + "="*60)
    print("  NexLattice Simulator - Advanced Test")
    print("="*60 + "\n")
    
    sim = NetworkSimulator()
    
    # Test different topologies
    topologies = ['line', 'mesh', 'random']
    
    for topology in topologies:
        print(f"\n📐 Testing {topology.upper()} topology")
        print("-" * 40)
        
        # Clear previous nodes
        sim.nodes.clear()
        
        # Create topology
        sim.create_topology(topology, 5)
        sim.run_discovery()
        
        # Send messages
        sim.send_test_message("node_001", "node_005", f"Test on {topology} topology")
        time.sleep(0.5)
        
        # Stats
        sim.print_network_stats()
        time.sleep(1)
    
    print("\n✅ Advanced test complete!\n")

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == '--advanced':
        run_advanced_test()
    else:
        run_basic_test()

if __name__ == '__main__':
    main()

