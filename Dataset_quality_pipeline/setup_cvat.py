#!/usr/bin/env python3
"""
CVAT Setup Script for AVA Dataset Pipeline
This script sets up CVAT for the AVA dataset annotation pipeline.
"""

import os
import subprocess
import sys
import time
import requests
from pathlib import Path

class CVATSetup:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.cvat_dir = self.base_dir / "cvat"
        self.cvat_host = "http://localhost:8080"
        
    def check_docker(self):
        """Check if Docker is installed and running"""
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, check=True)
            print(f"✓ Docker version: {result.stdout.strip()}")
            
            # Check if Docker daemon is running
            result = subprocess.run(['docker', 'info'], 
                                  capture_output=True, text=True, check=True)
            print("✓ Docker daemon is running")
            return True
        except subprocess.CalledProcessError:
            print("✗ Docker is not installed or not running")
            print("Please install Docker Desktop and ensure it's running")
            return False
    
    def check_docker_compose(self):
        """Check if Docker Compose is available"""
        try:
            result = subprocess.run(['docker', 'compose', '--version'], 
                                  capture_output=True, text=True, check=True)
            print(f"✓ Docker Compose version: {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError:
            print("✗ Docker Compose is not available")
            return False
    
    def clone_cvat(self):
        """Clone CVAT repository"""
        if self.cvat_dir.exists():
            print(f"✓ CVAT directory already exists at {self.cvat_dir}")
            return True
        
        try:
            print("Cloning CVAT repository...")
            subprocess.run(['git', 'clone', 'https://github.com/opencv/cvat.git', str(self.cvat_dir)], 
                          check=True)
            print("✓ CVAT repository cloned successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to clone CVAT: {e}")
            return False
    
    def setup_cvat_environment(self):
        """Set up CVAT environment variables"""
        env_file = self.cvat_dir / ".env"
        if env_file.exists():
            print("✓ CVAT environment file already exists")
            return True
        
        try:
            # Create basic .env file
            env_content = """# Basic CVAT configuration
CVAT_HOST=localhost
CVAT_PORT=8080
CVAT_SUPERUSER_USERNAME=admin
CVAT_SUPERUSER_EMAIL=admin@example.com
CVAT_SUPERUSER_PASSWORD=admin123
DJANGO_LOG_LEVEL=INFO
"""
            with open(env_file, 'w') as f:
                f.write(env_content)
            print("✓ CVAT environment file created")
            return True
        except Exception as e:
            print(f"✗ Failed to create environment file: {e}")
            return False
    
    def start_cvat(self):
        """Start CVAT using Docker Compose"""
        if not self.cvat_dir.exists():
            print("✗ CVAT directory not found")
            return False
        
        try:
            print("Starting CVAT services...")
            os.chdir(self.cvat_dir)
            
            # Pull latest images
            subprocess.run(['docker', 'compose', 'pull'], check=True)
            
            # Start services
            subprocess.run(['docker', 'compose', 'up', '-d'], check=True)
            print("✓ CVAT services started")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to start CVAT: {e}")
            return False
    
    def wait_for_cvat(self, timeout=120):
        """Wait for CVAT to be ready"""
        print(f"Waiting for CVAT to be ready at {self.cvat_host}...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.cvat_host}/api/server/about", timeout=5)
                if response.status_code == 200:
                    print("✓ CVAT is ready!")
                    return True
            except:
                pass
            
            print(".", end="", flush=True)
            time.sleep(5)
        
        print(f"\n✗ CVAT did not become ready within {timeout} seconds")
        return False
    
    def create_superuser(self):
        """Create CVAT superuser"""
        try:
            print("Creating CVAT superuser...")
            result = subprocess.run([
                'docker', 'compose', 'exec', '-T', 'cvat_server',
                'python3', 'manage.py', 'createsuperuser',
                '--noinput',
                '--username', 'admin',
                '--email', 'admin@example.com'
            ], capture_output=True, text=True, check=True)
            
            # Set password
            subprocess.run([
                'docker', 'compose', 'exec', '-T', 'cvat_server',
                'python3', 'manage.py', 'shell', '-c',
                "from django.contrib.auth import get_user_model; User = get_user_model(); user = User.objects.get(username='admin'); user.set_password('admin123'); user.save()"
            ], check=True)
            
            print("✓ Superuser created (admin/admin123)")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✓ Superuser might already exist or creation failed: {e}")
            return True  # Continue anyway
    
    def create_project_user(self):
        """Create the project user (mv350)"""
        try:
            print("Creating project user...")
            subprocess.run([
                'docker', 'compose', 'exec', '-T', 'cvat_server',
                'python3', 'manage.py', 'shell', '-c',
                """
from django.contrib.auth import get_user_model
User = get_user_model()
try:
    user = User.objects.create_user(username='mv350', email='mv350@example.com', password='Amazon123')
    user.is_staff = True
    user.save()
    print('User mv350 created successfully')
except:
    print('User mv350 already exists')
"""
            ], check=True)
            print("✓ Project user created (mv350/Amazon123)")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✓ Project user might already exist: {e}")
            return True
    
    def test_connection(self):
        """Test CVAT connection"""
        try:
            response = requests.get(f"{self.cvat_host}/api/server/about", timeout=10)
            if response.status_code == 200:
                server_info = response.json()
                print(f"✓ CVAT server info: {server_info}")
                return True
            else:
                print(f"✗ CVAT server returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Failed to connect to CVAT: {e}")
            return False
    
    def run_setup(self):
        """Run the complete CVAT setup"""
        print("=== CVAT Setup for AVA Dataset Pipeline ===\n")
        
        # Check prerequisites
        if not self.check_docker():
            return False
        
        if not self.check_docker_compose():
            return False
        
        # Clone and setup CVAT
        if not self.clone_cvat():
            return False
        
        if not self.setup_cvat_environment():
            return False
        
        # Start CVAT
        if not self.start_cvat():
            return False
        
        # Wait for CVAT to be ready
        if not self.wait_for_cvat():
            return False
        
        # Create users
        if not self.create_superuser():
            return False
        
        if not self.create_project_user():
            return False
        
        # Test connection
        if not self.test_connection():
            return False
        
        print("\n=== CVAT Setup Complete ===")
        print(f"CVAT is running at: {self.cvat_host}")
        print("Admin user: admin/admin123")
        print("Project user: mv350/Amazon123")
        print("\nYou can now run the CVAT integration tests:")
        print("python src/annotation_management/cvat_test.py")
        
        return True

def main():
    setup = CVATSetup()
    success = setup.run_setup()
    
    if success:
        print("\n✅ CVAT setup completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ CVAT setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
