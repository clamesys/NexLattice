"""
NexLattice Platform Compatibility Analyzer
Tests code compatibility across different MicroPython platforms
"""

import ast
import os
import re
from pathlib import Path

class PlatformCompatibilityAnalyzer:
    """Analyze NexLattice code for platform compatibility"""
    
    def __init__(self, code_dir='devices'):
        self.code_dir = Path(code_dir)
        self.platforms = {
            'ESP32': {
                'name': 'ESP32 (WROOM-32, WROVER)',
                'micropython': True,
                'network': True,
                'socket': True,
                'ucryptolib': True,
                'uhashlib': True,
                'ubinascii': True,
                'urandom': True,
                'threading': True,
                'status': 'tested'
            },
            'Pico_W': {
                'name': 'Raspberry Pi Pico W',
                'micropython': True,
                'network': True,
                'socket': True,
                'ucryptolib': True,
                'uhashlib': True,
                'ubinascii': True,
                'urandom': True,
                'threading': True,
                'status': 'compatible'
            },
            'STM32_WiFi': {
                'name': 'STM32 with WiFi (e.g., STM32F4 with ESP8266/ESP32)',
                'micropython': True,
                'network': True,
                'socket': True,
                'ucryptolib': True,
                'uhashlib': True,
                'ubinascii': True,
                'urandom': True,
                'threading': True,
                'status': 'compatible'
            },
            'ESP8266': {
                'name': 'ESP8266',
                'micropython': True,
                'network': True,
                'socket': True,
                'ucryptolib': False,  # Limited crypto support
                'uhashlib': True,
                'ubinascii': True,
                'urandom': True,
                'threading': True,
                'status': 'compatible_with_fallback'
            }
        }
        
        self.imports_found = set()
        self.files_analyzed = []
        
    def analyze_file(self, filepath):
        """Analyze a Python file for imports and dependencies"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            
            # Find all imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.imports_found.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self.imports_found.add(node.module)
            
            self.files_analyzed.append(str(filepath))
            return True
        except Exception as e:
            print(f"❌ Error analyzing {filepath}: {e}")
            return False
    
    def analyze_codebase(self):
        """Analyze all Python files in code directory"""
        print("Analyzing NexLattice codebase for platform compatibility...\n")
        
        python_files = list(self.code_dir.glob('*.py'))
        
        for py_file in python_files:
            print(f"  Analyzing {py_file.name}...")
            self.analyze_file(py_file)
        
        print(f"\n[OK] Analyzed {len(self.files_analyzed)} files")
        print(f"[OK] Found {len(self.imports_found)} unique imports\n")
        
        return self.imports_found
    
    def check_platform_compatibility(self, platform_name):
        """Check if code is compatible with a specific platform"""
        platform = self.platforms.get(platform_name)
        if not platform:
            return None
        
        issues = []
        warnings = []
        
        # Check standard library imports
        standard_imports = {
            'network', 'socket', 'time', 'json', '_thread'
        }
        
        # Check MicroPython-specific imports
        micropython_imports = {
            'ubinascii', 'uhashlib', 'urandom', 'ucryptolib'
        }
        
        # Check each import
        for imp in self.imports_found:
            # Skip standard Python modules that work everywhere
            if imp in ['time', 'json']:
                continue
            
            # Check MicroPython-specific modules
            if imp == 'network':
                if not platform['network']:
                    issues.append(f"[ERROR] {imp} not available on {platform['name']}")
            elif imp == 'socket':
                if not platform['socket']:
                    issues.append(f"[ERROR] {imp} not available on {platform['name']}")
            elif imp == '_thread':
                if not platform['threading']:
                    issues.append(f"[ERROR] {imp} not available on {platform['name']}")
            elif imp == 'ucryptolib':
                if not platform['ucryptolib']:
                    warnings.append(f"[WARN] {imp} not available on {platform['name']} (fallback encryption will be used)")
            elif imp == 'uhashlib':
                if not platform['uhashlib']:
                    issues.append(f"[ERROR] {imp} not available on {platform['name']}")
            elif imp == 'ubinascii':
                if not platform['ubinascii']:
                    issues.append(f"[ERROR] {imp} not available on {platform['name']}")
            elif imp == 'urandom':
                if not platform['urandom']:
                    issues.append(f"[ERROR] {imp} not available on {platform['name']}")
        
        return {
            'platform': platform,
            'compatible': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'status': platform['status']
        }
    
    def generate_compatibility_report(self):
        """Generate comprehensive compatibility report"""
        print("=" * 70)
        print("NEXLATTICE PLATFORM COMPATIBILITY REPORT")
        print("=" * 70)
        print()
        
        # Analyze codebase
        imports = self.analyze_codebase()
        
        print("IMPORTS DETECTED:")
        print("-" * 70)
        for imp in sorted(imports):
            print(f"  • {imp}")
        print()
        
        print("PLATFORM COMPATIBILITY ANALYSIS:")
        print("=" * 70)
        print()
        
        results = {}
        
        for platform_name in self.platforms.keys():
            result = self.check_platform_compatibility(platform_name)
            if result:
                results[platform_name] = result
                
                status_icon = "[OK]" if result['compatible'] else "[ERROR]"
                if result['warnings']:
                    status_icon = "[WARN]"
                
                print(f"{status_icon} {result['platform']['name']}")
                print(f"   Status: {result['status']}")
                
                if result['issues']:
                    print("   Issues:")
                    for issue in result['issues']:
                        print(f"     {issue}")
                
                if result['warnings']:
                    print("   Warnings:")
                    for warning in result['warnings']:
                        print(f"     {warning}")
                
                if result['compatible'] and not result['warnings']:
                    print("   [OK] Fully compatible - All dependencies available")
                elif result['compatible'] and result['warnings']:
                    print("   [WARN] Compatible with fallbacks - Some features may use alternatives")
                else:
                    print("   [ERROR] Not compatible - Missing critical dependencies")
                
                print()
        
        return results
    
    def generate_compatibility_matrix(self, results):
        """Generate compatibility matrix markdown"""
        matrix = []
        matrix.append("# NexLattice Platform Compatibility Matrix\n")
        matrix.append("**Generated:** Platform Compatibility Analysis\n\n")
        matrix.append("| Platform | Status | Compatibility | Notes |\n")
        matrix.append("|----------|--------|---------------|-------|\n")
        
        for platform_name, result in results.items():
            platform = result['platform']
            
            if result['compatible'] and not result['warnings']:
                status = "✅ Fully Compatible"
                notes = "All features supported"
            elif result['compatible'] and result['warnings']:
                status = "⚠️ Compatible (Fallbacks)"
                notes = "Uses fallback encryption"
            else:
                status = "❌ Not Compatible"
                notes = "; ".join(result['issues'][:2])
            
            matrix.append(f"| {platform['name']} | {result['status']} | {status} | {notes} |\n")
        
        return "".join(matrix)


def main():
    """Main entry point"""
    analyzer = PlatformCompatibilityAnalyzer()
    results = analyzer.generate_compatibility_report()
    
    # Generate markdown report
    matrix = analyzer.generate_compatibility_matrix(results)
    
    # Save to file
    output_file = Path('compatibility/COMPATIBILITY_REPORT.md')
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(matrix)
        f.write("\n\n## Detailed Analysis\n\n")
        f.write("### Dependencies Required\n\n")
        f.write("All platforms require MicroPython with the following modules:\n\n")
        f.write("- `network` - WiFi connectivity\n")
        f.write("- `socket` - UDP/TCP communication\n")
        f.write("- `uhashlib` - Cryptographic hashing\n")
        f.write("- `ubinascii` - Binary/hex encoding\n")
        f.write("- `urandom` - Random number generation\n")
        f.write("- `_thread` - Threading support\n")
        f.write("- `ucryptolib` - AES encryption (optional, fallback available)\n\n")
        
        f.write("### Platform-Specific Notes\n\n")
        for platform_name, result in results.items():
            platform = result['platform']
            f.write(f"#### {platform['name']}\n\n")
            f.write(f"- **Status**: {result['status']}\n")
            f.write(f"- **Compatibility**: {'✅ Compatible' if result['compatible'] else '❌ Not Compatible'}\n")
            if result['warnings']:
                warning_texts = []
                for w in result['warnings']:
                    if ':' in w:
                        warning_texts.append(w.split(':', 1)[1].strip())
                    else:
                        warning_texts.append(w)
                f.write(f"- **Warnings**: {', '.join(warning_texts)}\n")
            f.write("\n")
    
    print("=" * 70)
    print(f"[OK] Compatibility report saved to: {output_file}")
    print("=" * 70)


if __name__ == '__main__':
    main()

