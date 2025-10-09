#!/usr/bin/env python3
"""
Helper script to upload NexLattice code to ESP32 boards
"""

import os
import sys
import subprocess
import argparse

def check_ampy():
    """Check if ampy is installed"""
    try:
        subprocess.run(['ampy', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def upload_file(port, local_file, remote_file):
    """Upload a single file to ESP32"""
    print(f"  Uploading {local_file} -> {remote_file}")
    try:
        subprocess.run(
            ['ampy', '--port', port, 'put', local_file, remote_file],
            check=True,
            capture_output=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Error: {e.stderr.decode()}")
        return False

def upload_nexlattice(port, node_number):
    """Upload all NexLattice files to ESP32"""
    print(f"\n🚀 Uploading NexLattice to ESP32 (Node {node_number}) on {port}...")
    
    # Define files to upload
    files = [
        ('devices/node_main.py', '/node_main.py'),
        ('devices/network_manager.py', '/network_manager.py'),
        ('devices/crypto_utils.py', '/crypto_utils.py'),
        ('devices/message_router.py', '/message_router.py'),
    ]
    
    # Use appropriate config file
    if node_number == 1:
        config_file = 'devices/config.json'
    else:
        config_file = f'devices/config_node{node_number}.json'
    
    if os.path.exists(config_file):
        files.append((config_file, '/config.json'))
    else:
        print(f"  ⚠️  Warning: Config file {config_file} not found")
        return False
    
    # Upload each file
    success_count = 0
    for local, remote in files:
        if not os.path.exists(local):
            print(f"  ❌ File not found: {local}")
            continue
        
        if upload_file(port, local, remote):
            success_count += 1
        else:
            print(f"  ❌ Failed to upload {local}")
    
    print(f"\n✅ Uploaded {success_count}/{len(files)} files successfully")
    return success_count == len(files)

def list_ports():
    """List available serial ports"""
    try:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        if ports:
            print("\n📡 Available serial ports:")
            for port in ports:
                print(f"  - {port.device}: {port.description}")
        else:
            print("\n⚠️  No serial ports found")
    except ImportError:
        print("\n⚠️  pyserial not installed. Run: pip install pyserial")

def main():
    parser = argparse.ArgumentParser(
        description='Upload NexLattice code to ESP32 boards',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload to Node 1 on COM3
  python upload_to_esp32.py COM3 1
  
  # Upload to Node 2 on /dev/ttyUSB0
  python upload_to_esp32.py /dev/ttyUSB0 2
  
  # List available ports
  python upload_to_esp32.py --list
        """
    )
    
    parser.add_argument('port', nargs='?', help='Serial port (e.g., COM3, /dev/ttyUSB0)')
    parser.add_argument('node', nargs='?', type=int, choices=[1, 2, 3, 4, 5],
                       help='Node number (1-5)')
    parser.add_argument('--list', '-l', action='store_true',
                       help='List available serial ports')
    
    args = parser.parse_args()
    
    # List ports
    if args.list:
        list_ports()
        return 0
    
    # Validate arguments
    if not args.port or not args.node:
        parser.print_help()
        print("\n❌ Error: Both port and node number are required")
        print("\nTip: Use --list to see available ports")
        return 1
    
    # Check if ampy is installed
    if not check_ampy():
        print("❌ Error: ampy is not installed")
        print("\nInstall with: pip install adafruit-ampy")
        return 1
    
    # Upload files
    if upload_nexlattice(args.port, args.node):
        print("\n🎉 Upload complete! Reset your ESP32 to start NexLattice.")
        print("\nTo monitor serial output:")
        print(f"  screen {args.port} 115200    (macOS/Linux)")
        print(f"  Use PuTTY with {args.port} at 115200 baud (Windows)")
        return 0
    else:
        print("\n❌ Upload failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())

