#!/usr/bin/env python3
"""
Improved CVAT Test Script
Tests the fixed CVAT integration with better error handling and diagnostics.
"""

import sys
import os
from pathlib import Path

# Add the current directory to the path so we can import the fixed module
sys.path.insert(0, str(Path(__file__).parent))

try:
    from cvat_integration_fixed import CVATClient, get_default_labels
    print("✓ Using fixed CVAT integration module")
except ImportError:
    try:
        from cvat_integration import CVATClient, get_default_labels
        print("⚠ Using original CVAT integration module")
    except ImportError as e:
        print(f"✗ Could not import CVAT integration: {e}")
        sys.exit(1)

def run_connection_test():
    """Test CVAT connection"""
    print("=== CVAT Connection Test ===")
    
    # Test 1: Basic connection
    print("\n1. Testing basic connection...")
    client = CVATClient()
    
    if not client.test_connection():
        print("❌ Cannot connect to CVAT server")
        print("\nTroubleshooting steps:")
        print("1. Check if CVAT is running:")
        print("   curl -I http://localhost:8080")
        print("2. If not running, start CVAT:")
        print("   python setup_cvat.py")
        print("3. If still failing, check Docker:")
        print("   docker ps | grep cvat")
        return False
    
    print("✓ Basic connection successful")
    return True

def run_authentication_test():
    """Test CVAT authentication"""
    print("\n=== CVAT Authentication Test ===")
    
    # Test 2: Authentication
    print("\n2. Testing authentication...")
    client = CVATClient(username="mv350", password="Amazon123")
    
    if not client.authenticated:
        print("❌ Authentication failed")
        print("\nTroubleshooting steps:")
        print("1. Check if user exists:")
        print("   python setup_cvat.py")
        print("2. Try admin credentials:")
        print("   Username: admin, Password: admin123")
        print("3. Create user manually in CVAT web interface")
        return False
    
    print("✓ Authentication successful")
    return client

def run_project_test(client):
    """Test project creation"""
    print("\n=== CVAT Project Creation Test ===")
    
    # Test 3: Project creation
    print("\n3. Testing project creation...")
    labels = get_default_labels()
    project_id = client.create_project("Test_Project_AVA", labels)
    
    if not project_id:
        print("❌ Project creation failed")
        print("\nTroubleshooting steps:")
        print("1. Check CVAT logs:")
        print("   docker compose logs cvat_server")
        print("2. Check user permissions in CVAT")
        print("3. Try creating project manually in web interface")
        return False
    
    print(f"✓ Project created successfully (ID: {project_id})")
    return project_id

def run_comprehensive_test():
    """Run comprehensive CVAT integration test"""
    print("=== Comprehensive CVAT Integration Test ===")
    
    # Step 1: Connection test
    if not run_connection_test():
        return False
    
    # Step 2: Authentication test
    client = run_authentication_test()
    if not client:
        return False
    
    # Step 3: Project creation test
    project_id = run_project_test(client)
    if not project_id:
        return False
    
    print("\n=== All Tests Passed ===")
    print("✅ CVAT integration is working correctly!")
    print(f"✅ Project ID: {project_id}")
    print("\nNext steps:")
    print("1. You can now run the annotation pipeline:")
    print("   python single_annotator_assignment.py")
    print("2. Or run the multi-annotator assignment:")
    print("   python assignment_generator.py")
    
    return True

def main():
    """Main test function"""
    print("CVAT Integration Test Script")
    print("=" * 40)
    
    success = run_comprehensive_test()
    
    if success:
        print("\n🎉 All tests passed! CVAT integration is working.")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
