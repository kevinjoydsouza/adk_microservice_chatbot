#!/usr/bin/env python3
"""
ADK Server Startup Script for IntelliSurf Research Agent
"""

import subprocess
import sys
import os
import time
import requests
from pathlib import Path

def check_adk_server(port=8000, timeout=5):
    """Check if ADK server is running"""
    try:
        response = requests.get(f"http://localhost:{port}/list-apps", timeout=timeout)
        return response.status_code == 200
    except:
        return False

def start_adk_server(app_name="academic-research", port=8000):
    """Start the ADK server"""
    print(f"Starting ADK server for app '{app_name}' on port {port}...")
    
    # Change to the project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Start the server
    cmd = [
        sys.executable, "-m", "google.adk.agents.server",
        "--app", app_name,
        "--port", str(port),
        "--host", "0.0.0.0"
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Check if server is running
        if check_adk_server(port):
            print(f"✅ ADK server started successfully on port {port}")
            print(f"📊 Process ID: {process.pid}")
            return process
        else:
            print("❌ ADK server failed to start")
            stdout, stderr = process.communicate(timeout=5)
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting ADK server: {e}")
        return None

def main():
    """Main function"""
    print("🚀 IntelliSurf ADK Server Startup")
    print("=" * 40)
    
    # Check if server is already running
    if check_adk_server():
        print("✅ ADK server is already running on port 8000")
        return
    
    # Start the server
    process = start_adk_server()
    
    if process:
        try:
            print("🔄 ADK server is running. Press Ctrl+C to stop.")
            process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping ADK server...")
            process.terminate()
            process.wait()
            print("✅ ADK server stopped")
    else:
        print("❌ Failed to start ADK server")
        sys.exit(1)

if __name__ == "__main__":
    main()
