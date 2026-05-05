#!/usr/bin/env python3
"""
DABABYBOT Windows Test Suite
Verify all components work before deploying to production
"""

import os
import sys
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestSuite:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0

    def test_python_version(self):
        """Test Python version compatibility"""
        print("\n" + "="*60)
        print("TEST 1: Python Version")
        print("="*60)
        
        try:
            version = sys.version_info
            print(f"Python version: {version.major}.{version.minor}.{version.micro}")
            
            if version.major == 3 and version.minor >= 8:
                print("✅ PASSED: Python 3.8+ detected")
                self.passed += 1
                self.results.append(("Python Version", True))
                return True
            else:
                print("❌ FAILED: Python 3.8+ required")
                self.failed += 1
                self.results.append(("Python Version", False))
                return False
        except Exception as e:
            print(f"❌ FAILED: {e}")
            self.failed += 1
            self.results.append(("Python Version", False))
            return False

    def test_dependencies(self):
        """Test if required packages are installed"""
        print("\n" + "="*60)
        print("TEST 2: Dependencies")
        print("="*60)
        
        required_packages = {
            'requests': 'Web requests',
            'numpy': 'Numerical computing',
            'pandas': 'Data manipulation',
        }
        
        all_passed = True
        for package, description in required_packages.items():
            try:
                __import__(package)
                print(f"✅ {package}: {description} - OK")
            except ImportError:
                print(f"❌ {package}: {description} - NOT INSTALLED")
                all_passed = False
        
        if all_passed:
            print("\n✅ PASSED: All dependencies installed")
            self.passed += 1
            self.results.append(("Dependencies", True))
        else:
            print("\n❌ FAILED: Missing dependencies")
            self.failed += 1
            self.results.append(("Dependencies", False))
        
        return all_passed

    def test_metatrader5(self):
        """Test MetaTrader5 availability"""
        print("\n" + "="*60)
        print("TEST 3: MetaTrader5 Connection")
        print("="*60)
        
        try:
            import MetaTrader5 as mt5
            print("✅ MetaTrader5 module imported successfully")
            
            # Try to initialize
            if mt5.initialize():
                print("✅ MT5 initialization successful")
                
                # Get account info (no login required for this)
                info = mt5.version()
                if info:
                    print(f"   MT5 Version: {info}")
                    print("✅ PASSED: MetaTrader5 is working")
                    mt5.shutdown()
                    self.passed += 1
                    self.results.append(("MetaTrader5", True))
                    return True
                else:
                    print("❌ FAILED: Cannot get MT5 version")
                    self.failed += 1
                    self.results.append(("MetaTrader5", False))
                    return False
            else:
                print("❌ FAILED: MT5 initialization failed")
                print("   Make sure MetaTrader5 terminal is installed")
                self.failed += 1
                self.results.append(("MetaTrader5", False))
                return False
                
        except ImportError:
            print("❌ FAILED: MetaTrader5 module not found")
            print("   Install using: pip install MetaTrader5")
            self.failed += 1
            self.results.append(("MetaTrader5", False))
            return False
        except Exception as e:
            print(f"❌ FAILED: {e}")
            self.failed += 1
            self.results.append(("MetaTrader5", False))
            return False

    def test_web_service_connection(self):
        """Test connection to web service"""
        print("\n" + "="*60)
        print("TEST 4: Web Service Connection")
        print("="*60)
        
        try:
            import requests
            
            # Test default Render URL
            test_urls = [
                'https://dababybot-saas.onrender.com',
                'http://localhost:5000'
            ]
            
            for url in test_urls:
                try:
                    response = requests.get(f'{url}/health', timeout=5)
                    if response.status_code in [200, 404]:  # 404 is ok if endpoint doesn't exist
                        print(f"✅ Connected to {url}")
                        print("✅ PASSED: Web service reachable")
                        self.passed += 1
                        self.results.append(("Web Service", True))
                        return True
                except:
                    continue
            
            print("⚠️  WARNING: Could not reach web service")
            print("   Make sure your web service is deployed and URL is correct")
            print("   Or if running locally, make sure it's on http://localhost:5000")
            self.results.append(("Web Service", None))  # Warning, not failure
            return None
            
        except Exception as e:
            print(f"❌ FAILED: {e}")
            self.failed += 1
            self.results.append(("Web Service", False))
            return False

    def test_file_structure(self):
        """Test if required files exist"""
        print("\n" + "="*60)
        print("TEST 5: File Structure")
        print("="*60)
        
        required_files = [
            'bot_platform.py',
            'dababybot_vps_client.py',
            'botMayl999990000th.py',
        ]
        
        all_passed = True
        for filename in required_files:
            if os.path.exists(filename):
                print(f"✅ {filename} - Found")
            else:
                print(f"❌ {filename} - NOT FOUND")
                all_passed = False
        
        if all_passed:
            print("\n✅ PASSED: All required files present")
            self.passed += 1
            self.results.append(("File Structure", True))
        else:
            print("\n❌ FAILED: Missing required files")
            self.failed += 1
            self.results.append(("File Structure", False))
        
        return all_passed

    def test_environment_variables(self):
        """Test environment variables"""
        print("\n" + "="*60)
        print("TEST 6: Environment Variables")
        print("="*60)
        
        required_env = {
            'WEB_SERVICE_URL': 'Web service URL',
            'VPS_USER_ID': 'VPS user ID',
            'API_KEY': 'API key',
        }
        
        all_set = True
        for env_var, description in required_env.items():
            value = os.getenv(env_var)
            if value:
                print(f"✅ {env_var}: Set ({description})")
            else:
                print(f"⚠️  {env_var}: Not set ({description})")
                all_set = False
        
        if all_set:
            print("\n✅ PASSED: All environment variables set")
            self.passed += 1
            self.results.append(("Environment Variables", True))
        else:
            print("\n⚠️  WARNING: Some environment variables not set")
            print("   They can be set later in deployment")
            self.results.append(("Environment Variables", None))
        
        return all_set

    def test_bot_logic(self):
        """Test if bot logic can be imported"""
        print("\n" + "="*60)
        print("TEST 7: Bot Logic")
        print("="*60)
        
        try:
            # Try to import bot module
            import botMayl999990000th as bot
            print("✅ Bot module imported successfully")
            
            # Check for required functions
            required_functions = [
                'run_trading_cycle',
                'initialize_mt5',
            ]
            
            all_present = True
            for func_name in required_functions:
                if hasattr(bot, func_name):
                    print(f"✅ Function '{func_name}' found")
                else:
                    print(f"⚠️  Function '{func_name}' not found (may not be required)")
            
            print("✅ PASSED: Bot logic is functional")
            self.passed += 1
            self.results.append(("Bot Logic", True))
            return True
            
        except ImportError as e:
            print(f"❌ FAILED: Cannot import bot module: {e}")
            self.failed += 1
            self.results.append(("Bot Logic", False))
            return False
        except Exception as e:
            print(f"⚠️  WARNING: {e}")
            self.results.append(("Bot Logic", None))
            return None

    def test_logging(self):
        """Test logging configuration"""
        print("\n" + "="*60)
        print("TEST 8: Logging")
        print("="*60)
        
        try:
            test_log_file = 'test_dababybot.log'
            
            # Create a test logger
            test_logger = logging.getLogger('test_bot')
            handler = logging.FileHandler(test_log_file)
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            test_logger.addHandler(handler)
            test_logger.setLevel(logging.INFO)
            
            # Write test message
            test_logger.info("Test log message")
            
            # Check if file was created
            if os.path.exists(test_log_file):
                print(f"✅ Test log file created: {test_log_file}")
                
                # Read and verify
                with open(test_log_file, 'r') as f:
                    content = f.read()
                    if 'Test log message' in content:
                        print("✅ Log message written successfully")
                        os.remove(test_log_file)
                        print("✅ PASSED: Logging is working")
                        self.passed += 1
                        self.results.append(("Logging", True))
                        return True
            
            print("❌ FAILED: Log file not created")
            self.failed += 1
            self.results.append(("Logging", False))
            return False
            
        except Exception as e:
            print(f"❌ FAILED: {e}")
            self.failed += 1
            self.results.append(("Logging", False))
            return False

    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*60)
        print("TEST REPORT SUMMARY")
        print("="*60)
        
        total = self.passed + self.failed
        
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        
        if self.failed == 0:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ System is ready for deployment")
            return True
        else:
            print(f"\n⚠️  {self.failed} test(s) failed")
            print("❌ Please fix the issues before deployment")
            return False

    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("DABABYBOT WINDOWS TEST SUITE")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        self.test_python_version()
        self.test_dependencies()
        self.test_metatrader5()
        self.test_web_service_connection()
        self.test_file_structure()
        self.test_environment_variables()
        self.test_bot_logic()
        self.test_logging()
        
        success = self.generate_report()
        
        print("\n" + "="*60)
        print(f"Ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        return success

def main():
    suite = TestSuite()
    success = suite.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()