#!/usr/bin/env python3
"""
Complete System Test for ZUS Coffee Chatbot
==========================================

This script tests the entire ZUS Coffee chatbot system:
1. Environment setup (API keys, dependencies)
2. Database connectivity (outlets.db)
3. Vector store (FAISS)
4. All API endpoints
5. Agent functionality
6. End-to-end workflows

Run this to verify everything is working properly.
"""

import os
import sys
import sqlite3
import json
import requests
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ZUSSystemTester:
    """Complete system tester for ZUS Coffee chatbot."""
    
    def __init__(self):
        self.results = {}
        self.errors = []
        self.warnings = []
        
        # API endpoints to test
        self.api_ports = {
            'main': 8000,
        }
        
        self.test_apis = [
            'http://127.0.0.1:8000'
        ]
    
    def run_all_tests(self):
        """Run all system tests."""
        print("ZUS Coffee Chatbot - Complete System Test")
        print("=" * 60)
        
        # 1. Environment checks
        self.test_environment()
        
        # 2. File structure checks  
        self.test_file_structure()
        
        # 3. Database checks
        self.test_database()
        
        # 4. Vector store checks
        self.test_vector_store()
        
        # 5. Dependencies check
        self.test_dependencies()
        
        # 6. API server tests (if running)
        self.test_api_servers()
        
        # 7. Agent functionality
        self.test_agent()
        
        # Print final report
        self.print_final_report()
    
    def test_environment(self):
        """Test environment setup."""
        print("\nTesting Environment Setup")
        print("-" * 40)
        
        # Check API keys
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key:
            print("PASS: GEMINI_API_KEY found")
            self.results['gemini_key'] = True
        else:
            print("FAIL: GEMINI_API_KEY not found")
            self.errors.append("Missing GEMINI_API_KEY in .env file")
            self.results['gemini_key'] = False
        
        # Check Python version
        python_version = sys.version_info
        if python_version >= (3, 8):
            print(f"PASS: Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
            self.results['python_version'] = True
        else:
            print(f"FAIL: Python version too old: {python_version}")
            self.errors.append("Python 3.8+ required")
            self.results['python_version'] = False
    
    def test_file_structure(self):
        """Test if all required files exist."""
        print("\nTesting File Structure")
        print("-" * 40)
        
        required_files = [
            'api/main.py',
            'api/calculator.py', 
            'api/outlets.py',
            'api/products.py',
            'chatbot/main_agent.py',
            'scripts/scrape_outlets.py',
            'scripts/scrape_products.py',
            'scripts/load_products.py',
            'requirements.txt',
            'README.md'
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = Path(file_path)
            if full_path.exists():
                print(f"PASS: {file_path}")
            else:
                print(f"FAIL: {file_path}")
                missing_files.append(file_path)
        
        self.results['file_structure'] = len(missing_files) == 0
        if missing_files:
            self.errors.extend([f"Missing file: {f}" for f in missing_files])
    
    def test_database(self):
        """Test database connectivity and data."""
        print("\nTesting Database")
        print("-" * 40)
        
        db_path = Path("data/outlets.db")
        
        if not db_path.exists():
            print("FAIL: Database file not found")
            self.errors.append("outlets.db not found - run scripts/load_outlets.py")
            self.results['database'] = False
            return
        
        try:
            # Connect to database
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Check outlets table
            cursor.execute("SELECT COUNT(*) FROM outlets")
            outlet_count = cursor.fetchone()[0]
            
            if outlet_count > 0:
                print(f"PASS: Database connected - {outlet_count} outlets found")
                
                # Sample some data
                cursor.execute("SELECT name, address, area FROM outlets LIMIT 3")
                samples = cursor.fetchall()
                print("Sample outlets:")
                for i, (name, address, area) in enumerate(samples, 1):
                    print(f"   {i}. {name} - {address}, {area}")
                
                self.results['database'] = True
            else:
                print("FAIL: Database empty")
                self.errors.append("Database has no outlets data")
                self.results['database'] = False
            
            conn.close()
            
        except Exception as e:
            print(f"FAIL: Database error: {e}")
            self.errors.append(f"Database error: {e}")
            self.results['database'] = False
    
    def test_vector_store(self):
        """Test vector store files."""
        print("\nTesting Vector Store")
        print("-" * 40)
        
        vector_dir = Path("data/vector_store")
        
        if not vector_dir.exists():
            print("FAIL: Vector store directory not found")
            self.errors.append("Vector store not found - run scripts/load_products.py")
            self.results['vector_store'] = False
            return
        
        required_files = ['products.index', 'products.pkl', 'metadata.json']
        missing = []
        
        for file in required_files:
            file_path = vector_dir / file
            if file_path.exists():
                print(f"PASS: {file}")
            else:
                print(f"FAIL: {file}")
                missing.append(file)
        
        if not missing:
            # Try to load metadata
            try:
                with open(vector_dir / 'metadata.json', 'r') as f:
                    metadata = json.load(f)
                
                product_count = metadata.get('num_products', metadata.get('total_products', 0))
                print(f"PASS: Vector store loaded - {product_count} products")
                self.results['vector_store'] = True
                
            except Exception as e:
                print(f"FAIL: Vector store metadata error: {e}")
                self.errors.append(f"Vector store error: {e}")
                self.results['vector_store'] = False
        else:
            self.errors.extend([f"Missing vector file: {f}" for f in missing])
            self.results['vector_store'] = False
    
    def test_dependencies(self):
        """Test if all required Python packages are installed."""
        print("\nTesting Dependencies")
        print("-" * 40)
        
        required_packages = [
            'fastapi',
            'uvicorn',
            'requests',
            'sqlalchemy',
            'faiss-cpu',
            'sentence-transformers',
            'langchain',
            'langchain-community',
            'google-generativeai',
            'python-dotenv',
            'beautifulsoup4',
            'pandas'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                if package == 'faiss-cpu':
                    import faiss
                    print("PASS: faiss-cpu")
                elif package == 'sentence-transformers':
                    import sentence_transformers
                    print("PASS: sentence-transformers")
                elif package == 'langchain-community':
                    import langchain_community
                    print("PASS: langchain-community")
                elif package == 'google-generativeai':
                    import google.generativeai
                    print("PASS: google-generativeai")
                elif package == 'python-dotenv':
                    import dotenv
                    print("PASS: python-dotenv")
                elif package == 'beautifulsoup4':
                    import bs4
                    print("PASS: beautifulsoup4")
                else:
                    __import__(package)
                    print(f"PASS: {package}")
                    
            except ImportError:
                print(f"FAIL: {package}")
                missing_packages.append(package)
        
        self.results['dependencies'] = len(missing_packages) == 0
        if missing_packages:
            self.errors.append(f"Missing packages: {', '.join(missing_packages)}")
            print(f"\nTo install missing packages: pip install {' '.join(missing_packages)}")
    
    def test_api_servers(self):
        """Test if API servers are running and responsive."""
        print("\nTesting API Servers")
        print("-" * 40)
        
        api_results = {}
        
        for name, port in self.api_ports.items():
            url = f"http://127.0.0.1:{port}"
            
            try:
                # Test health/root endpoint
                response = requests.get(f"{url}/", timeout=5)
                if response.status_code == 200:
                    print(f"PASS: {name} API ({port}) - Running")
                    api_results[name] = True
                else:
                    print(f"WARN: {name} API ({port}) - Responding but error {response.status_code}")
                    api_results[name] = False
                    
            except requests.ConnectionError:
                print(f"FAIL: {name} API ({port}) - Not running")
                api_results[name] = False
                
            except Exception as e:
                print(f"FAIL: {name} API ({port}) - Error: {e}")
                api_results[name] = False
        
        self.results['api_servers'] = api_results
        
        # Test specific endpoints if main API is running
        if api_results.get('main', False):
            self.test_api_endpoints()
    
    def test_api_endpoints(self):
        """Test specific API endpoints."""
        print("\nTesting API Endpoints")
        print("-" * 40)
        
        base_url = "http://127.0.0.1:8000"
        
        # Test calculator
        try:
            response = requests.get(f"{base_url}/calculator/?expression=2%2B2", timeout=10)
            if response.status_code == 200:
                data = response.json()
                result = data.get('result')
                print(f"PASS: Calculator API - Result: {result}")
            else:
                print(f"FAIL: Calculator API - Error {response.status_code}")
        except Exception as e:
            print(f"FAIL: Calculator API - Exception: {e}")
        
        # Test outlets
        try:
            response = requests.get(f"{base_url}/outlets?query=all outlets", timeout=15)
            if response.status_code == 200:
                data = response.json()
                count = data.get('count', 0)
                print(f"PASS: Outlets API - {count} outlets found")
            else:
                print(f"FAIL: Outlets API - Error {response.status_code}")
        except Exception as e:
            print(f"FAIL: Outlets API - Exception: {e}")
        
        # Test products
        try:
            response = requests.get(f"{base_url}/products?query=mugs", timeout=15)
            if response.status_code == 200:
                data = response.json()
                count = data.get('total_results', 0)
                print(f"PASS: Products API - {count} products found")
            else:
                print(f"FAIL: Products API - Error {response.status_code}")
        except Exception as e:
            print(f"FAIL: Products API - Exception: {e}")
    
    def test_agent(self):
        """Test the LangChain agent functionality."""
        print("\nTesting Agent")
        print("-" * 40)
        
        try:
            # Try to import and create agent
            sys.path.append(str(Path.cwd()))
            from chatbot.main_agent import create_agent
            
            print("PASS: Agent import successful")
            
            # Try to create agent (this tests all dependencies)
            agent = create_agent()
            print("PASS: Agent creation successful")
            
            # Simple test
            test_input = "What is 2 + 2?"
            response = agent.invoke({"input": test_input}, config={"configurable": {"session_id": "test_agent"}})
            output = response.get('output', '')
            
            if '4' in output:
                print("PASS: Agent calculation test passed")
                self.results['agent'] = True
            else:
                print(f"FAIL: Agent test failed - Output: {output}")
                self.results['agent'] = False
                
        except ImportError as e:
            print(f"FAIL: Agent import failed: {e}")
            self.errors.append(f"Agent import error: {e}")
            self.results['agent'] = False
            
        except Exception as e:
            print(f"FAIL: Agent error: {e}")
            self.errors.append(f"Agent error: {e}")
            self.results['agent'] = False
    
    
    def print_final_report(self):
        """Print comprehensive test report."""
        print("\n" + "=" * 60)
        print("FINAL SYSTEM TEST REPORT")
        print("=" * 60)
        
        # Count passed/failed tests
        total_tests = 0
        passed_tests = 0
        
        # Core system tests
        core_tests = ['gemini_key', 'python_version', 'file_structure', 'database', 'vector_store', 'dependencies']
        
        print("\nCore System:")
        for test in core_tests:
            result = self.results.get(test, False)
            status = "PASS" if result else "FAIL"
            print(f"  {test.replace('_', ' ').title()}: {status}")
            total_tests += 1
            if result:
                passed_tests += 1
        
        # API tests
        if 'api_servers' in self.results:
            print("\nAPI Server:")
            for name, result in self.results['api_servers'].items():
                status = "PASS" if result else "FAIL"
                description = "Unified API (calculator, outlets, products)" if name == 'main' else f"{name.title()} API"
                print(f"  {description}: {status}")
                total_tests += 1
                if result:
                    passed_tests += 1
        
        # Agent test
        if 'agent' in self.results:
            print(f"\nAgent: {'PASS' if self.results['agent'] else 'FAIL'}")
            total_tests += 1
            if self.results['agent']:
                passed_tests += 1
        
        # Errors and warnings
        if self.errors:
            print("\nCritical Issues:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print("\nWarnings:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        # Recommendations
        print(self.get_recommendations())
    
    def get_recommendations(self) -> str:
        """Get recommendations based on test results."""
        recommendations = ["\nRecommendations:"]
        
        if not self.results.get('gemini_key', False):
            recommendations.append("  - Set up GEMINI_API_KEY in .env file")
        
        if not self.results.get('database', False):
            recommendations.append("  - Run: python scripts/load_outlets.py")
        
        if not self.results.get('vector_store', False):
            recommendations.append("  - Run: python scripts/load_products.py")
        
        if not self.results.get('dependencies', False):
            recommendations.append("  - Install missing packages: pip install -r requirements.txt")
        
        api_running = any(self.results.get('api_servers', {}).values())
        if not api_running:
            recommendations.append("  - Start API server: python -m uvicorn api.main:app --port 8000")
            recommendations.append("  - Or run directly: python api/main.py")
        
        if not self.results.get('agent', False):
            recommendations.append("  - Check LangChain dependencies and GEMINI_API_KEY")
        
        if len(recommendations) == 1:
            recommendations.append("  - System looks good! Try running: python zus_chatbot.py")
        
        return "\n".join(recommendations)

# Quick setup check function
def quick_check():
    """Quick system health check."""
    print("ZUS Coffee Chatbot - Quick Health Check")
    print("=" * 50)
    
    # Check files
    critical_files = ['data/outlets.db', 'data/vector_store/products.index', '.env']
    all_good = True
    
    for file in critical_files:
        if Path(file).exists():
            print(f"PASS: {file}")
        else:
            print(f"FAIL: {file}")
            all_good = False
    
    # Check environment
    if os.getenv('GEMINI_API_KEY'):
        print("PASS: GEMINI_API_KEY")
    else:
        print("FAIL: GEMINI_API_KEY")
        all_good = False
    
    if all_good:
        print("\nQuick check passed! System should work.")
        return True
    else:
        print("\nIssues found. Run full test for details.")
        return False

def main():
    """Main function to run tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description='ZUS Coffee Chatbot System Tester')
    parser.add_argument('--quick', action='store_true', help='Run quick health check only')
    parser.add_argument('--setup', action='store_true', help='Run setup mode (install dependencies)')
    
    args = parser.parse_args()
    
    if args.quick:
        quick_check()
    elif args.setup:
        print("Setting up ZUS Coffee Chatbot...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("Dependencies installed. Run test again.")
    else:
        tester = ZUSSystemTester()
        tester.run_all_tests()

if __name__ == "__main__":
    main()
