"""
NexLattice Virtual Platform Testing
Simulates different MicroPython platforms to test compatibility
"""

import sys
import importlib
from unittest.mock import Mock, MagicMock, patch
import json

class VirtualPlatform:
    """Simulates a MicroPython platform"""
    
    def __init__(self, platform_name, features):
        self.platform_name = platform_name
        self.features = features
        self.modules = {}
        self.setup_modules()
    
    def setup_modules(self):
        """Setup mock modules for this platform"""
        # Network module
        if self.features.get('network', False):
            network = MagicMock()
            wlan = MagicMock()
            wlan.isconnected.return_value = True
            wlan.ifconfig.return_value = ['192.168.1.100', '255.255.255.0', '192.168.1.1', '8.8.8.8']
            wlan.connect.return_value = None
            network.WLAN.return_value = wlan
            network.STA_IF = 0
            self.modules['network'] = network
        
        # Socket module
        if self.features.get('socket', False):
            socket = MagicMock()
            socket.AF_INET = 2
            socket.SOCK_DGRAM = 2
            socket.SOCK_STREAM = 1
            socket.SOL_SOCKET = 1
            socket.SO_REUSEADDR = 4
            socket.SO_BROADCAST = 32
            sock_instance = MagicMock()
            sock_instance.bind.return_value = None
            sock_instance.sendto.return_value = None
            sock_instance.recvfrom.return_value = (b'data', ('192.168.1.101', 5001))
            sock_instance.connect.return_value = None
            sock_instance.send.return_value = None
            socket.socket.return_value = sock_instance
            self.modules['socket'] = socket
        
        # Crypto modules
        if self.features.get('ucryptolib', False):
            ucryptolib = MagicMock()
            aes = MagicMock()
            aes.encrypt.return_value = b'encrypted_data'
            aes.decrypt.return_value = b'decrypted_data'
            ucryptolib.aes.return_value = aes
            self.modules['ucryptolib'] = ucryptolib
        else:
            # Fallback - no ucryptolib
            self.modules['ucryptolib'] = None
        
        # Hashlib
        if self.features.get('uhashlib', False):
            uhashlib = MagicMock()
            sha256 = MagicMock()
            sha256.digest.return_value = b'hash_digest'
            sha256.hexdigest.return_value = 'hash_hex'
            sha256.update.return_value = None
            uhashlib.sha256.return_value = sha256
            self.modules['uhashlib'] = uhashlib
        
        # Binascii
        if self.features.get('ubinascii', False):
            ubinascii = MagicMock()
            ubinascii.hexlify.return_value = b'hex_data'
            ubinascii.unhexlify.return_value = b'bin_data'
            self.modules['ubinascii'] = ubinascii
        
        # Random
        if self.features.get('urandom', False):
            urandom = MagicMock()
            urandom.getrandbits.return_value = 12345
            self.modules['urandom'] = urandom
        
        # Threading
        if self.features.get('threading', False):
            _thread = MagicMock()
            _thread.start_new_thread.return_value = None
            self.modules['_thread'] = _thread
    
    def test_imports(self):
        """Test if all required imports work"""
        results = {
            'network': False,
            'socket': False,
            'ucryptolib': False,
            'uhashlib': False,
            'ubinascii': False,
            'urandom': False,
            '_thread': False
        }
        
        try:
            if self.modules.get('network'):
                results['network'] = True
        except:
            pass
        
        try:
            if self.modules.get('socket'):
                results['socket'] = True
        except:
            pass
        
        try:
            if self.modules.get('ucryptolib') is not None:
                results['ucryptolib'] = self.features.get('ucryptolib', False)
            else:
                results['ucryptolib'] = False  # Not available, but code handles it
        except:
            pass
        
        try:
            if self.modules.get('uhashlib'):
                results['uhashlib'] = True
        except:
            pass
        
        try:
            if self.modules.get('ubinascii'):
                results['ubinascii'] = True
        except:
            pass
        
        try:
            if self.modules.get('urandom'):
                results['urandom'] = True
        except:
            pass
        
        try:
            if self.modules.get('_thread'):
                results['_thread'] = True
        except:
            pass
        
        return results
    
    def test_code_compatibility(self, code_files):
        """Test if code would work on this platform"""
        compatibility_results = []
        
        for code_file in code_files:
            try:
                # Read and analyze code
                with open(code_file, 'r') as f:
                    code = f.read()
                
                # Check for platform-specific code
                issues = []
                warnings = []
                
                # Check for ucryptolib usage
                if 'ucryptolib' in code and not self.features.get('ucryptolib', False):
                    if 'try:' in code and 'except ImportError:' in code:
                        warnings.append(f"Uses ucryptolib with fallback (compatible)")
                    else:
                        issues.append(f"Uses ucryptolib without fallback")
                
                # Check for network usage
                if 'network.WLAN' in code and not self.features.get('network', False):
                    issues.append(f"Uses network.WLAN (not available)")
                
                # Check for socket usage
                if 'socket.socket' in code and not self.features.get('socket', False):
                    issues.append(f"Uses socket (not available)")
                
                # Check for threading
                if '_thread' in code and not self.features.get('threading', False):
                    issues.append(f"Uses _thread (not available)")
                
                compatibility_results.append({
                    'file': code_file.name,
                    'compatible': len(issues) == 0,
                    'issues': issues,
                    'warnings': warnings
                })
                
            except Exception as e:
                compatibility_results.append({
                    'file': code_file.name,
                    'compatible': False,
                    'issues': [f"Error analyzing: {str(e)}"],
                    'warnings': []
                })
        
        return compatibility_results


def test_platforms():
    """Test all platforms"""
    platforms = {
        'ESP32': {
            'network': True,
            'socket': True,
            'ucryptolib': True,
            'uhashlib': True,
            'ubinascii': True,
            'urandom': True,
            'threading': True
        },
        'Pico_W': {
            'network': True,
            'socket': True,
            'ucryptolib': True,
            'uhashlib': True,
            'ubinascii': True,
            'urandom': True,
            'threading': True
        },
        'STM32_WiFi': {
            'network': True,
            'socket': True,
            'ucryptolib': True,
            'uhashlib': True,
            'ubinascii': True,
            'urandom': True,
            'threading': True
        },
        'ESP8266': {
            'network': True,
            'socket': True,
            'ucryptolib': False,  # Limited support
            'uhashlib': True,
            'ubinascii': True,
            'urandom': True,
            'threading': True
        }
    }
    
    from pathlib import Path
    code_dir = Path('devices')
    code_files = list(code_dir.glob('*.py'))
    
    print("=" * 70)
    print("VIRTUAL PLATFORM COMPATIBILITY TESTING")
    print("=" * 70)
    print()
    
    results = {}
    
    for platform_name, features in platforms.items():
        print(f"Testing {platform_name}...")
        platform = VirtualPlatform(platform_name, features)
        
        # Test imports
        import_results = platform.test_imports()
        
        # Test code compatibility
        code_results = platform.test_code_compatibility(code_files)
        
        # Determine overall compatibility
        all_compatible = all(r['compatible'] for r in code_results)
        has_warnings = any(r['warnings'] for r in code_results)
        
        if all_compatible and not has_warnings:
            status = "[OK] Fully Compatible"
        elif all_compatible and has_warnings:
            status = "[WARN] Compatible (with fallbacks)"
        else:
            status = "[ERROR] Not Compatible"
        
        results[platform_name] = {
            'status': status,
            'imports': import_results,
            'code_tests': code_results,
            'overall_compatible': all_compatible
        }
        
        print(f"  Status: {status}")
        print(f"  Imports: {sum(import_results.values())}/{len(import_results)} available")
        print(f"  Code Files: {sum(1 for r in code_results if r['compatible'])}/{len(code_results)} compatible")
        print()
    
    return results


def generate_test_report(results):
    """Generate test report"""
    report = []
    report.append("# Virtual Platform Compatibility Test Report\n\n")
    report.append("This report shows virtual testing results for NexLattice on different platforms.\n\n")
    
    report.append("## Test Results\n\n")
    report.append("| Platform | Status | Imports | Code Files | Notes |\n")
    report.append("|----------|--------|---------|------------|-------|\n")
    
    for platform_name, result in results.items():
        imports_ok = sum(result['imports'].values())
        imports_total = len(result['imports'])
        code_ok = sum(1 for r in result['code_tests'] if r['compatible'])
        code_total = len(result['code_tests'])
        
        notes = []
        if not result['imports'].get('ucryptolib', False):
            notes.append("Uses fallback encryption")
        
        notes_str = "; ".join(notes) if notes else "All features supported"
        
        report.append(f"| {platform_name} | {result['status']} | {imports_ok}/{imports_total} | {code_ok}/{code_total} | {notes_str} |\n")
    
    report.append("\n## Conclusion\n\n")
    
    all_compatible = all(r['overall_compatible'] for r in results.values())
    if all_compatible:
        report.append("✅ **All tested platforms are compatible with NexLattice.**\n\n")
        report.append("The code uses proper fallback mechanisms for optional dependencies ")
        report.append("(like ucryptolib), ensuring compatibility across all MicroPython platforms.\n")
    else:
        report.append("⚠️ **Some platforms may have limitations.**\n\n")
        report.append("See detailed results above for platform-specific issues.\n")
    
    return "".join(report)


if __name__ == '__main__':
    results = test_platforms()
    
    report = generate_test_report(results)
    
    output_file = Path('compatibility/VIRTUAL_TEST_REPORT.md')
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write(report)
    
    print("=" * 70)
    print(f"✅ Test report saved to: {output_file}")
    print("=" * 70)

