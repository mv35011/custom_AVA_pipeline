from cvat_integration import CVATClient, get_default_labels


def test_cvat_connection():
    """Test CVAT connection and basic operations"""
    print("Testing CVAT connection...")

    # Initialize client
    client = CVATClient(host="http://localhost:8080", username="mv350", password="Amazon123")

    # Test 1: Connection
    print("\n1. Testing server connection...")
    if not client.test_connection():
        print("❌ Cannot connect to CVAT server")
        print("Make sure CVAT is running on http://localhost:8080")
        return False

    # Test 2: Authentication
    print("\n2. Testing authentication...")
    if not client.login():
        print("❌ Authentication failed")
        print("Check your username and password")
        return False

    # Test 3: Create test project
    print("\n3. Testing project creation...")
    labels = get_default_labels()
    project_id = client.create_project("Test_Project", labels)

    if project_id:
        print(f"✓ Test project created successfully (ID: {project_id})")
        return True
    else:
        print("❌ Failed to create test project")
        return False


if __name__ == "__main__":
    success = test_cvat_connection()
    if success:
        print("\n✅ CVAT connection test passed!")
        print("You can now run the assignment generator.")
    else:
        print("\n❌ CVAT connection test failed!")
        print("Fix the issues above before running the assignment generator.")