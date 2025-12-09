#!/usr/bin/env python3
"""
ESP32 Deploy Script - Upload files and manage device via HTTP

Usage:
    python deploy.py upload      # Upload all project files
    python deploy.py reset       # Restart the device
    python deploy.py upload reset # Upload and restart
    python deploy.py status      # Check device status
"""

import sys
import os
import base64
import requests
from time import sleep

# Configuration
ESP32_IP = "192.168.1.88"
ESP32_URL = f"http://{ESP32_IP}"
FILE_MANAGER_PASS = "QWEasd123rt"
CHUNK_SIZE = 256

# Files and folders to upload (relative to script directory)
UPLOAD_FILES = [
    "boot.py",
    "main.py",
    "webrepl_cfg.py",
]

UPLOAD_FOLDERS = [
    "led",
    "calibrate",
]

# Files/folders to skip
SKIP_PATTERNS = ["__pycache__", ".pyc", "deploy.py", ".git"]


def login():
    """Login to file manager"""
    try:
        r = requests.post(f"{ESP32_URL}/files",
                         data={"password": FILE_MANAGER_PASS},
                         timeout=10)
        return r.status_code == 200
    except:
        return False


def upload_file(local_path, remote_path):
    """Upload a file using chunked upload"""
    with open(local_path, "rb") as f:
        data = f.read()

    # Start upload
    r = requests.post(f"{ESP32_URL}/upload_start",
                     data={"filename": remote_path},
                     timeout=10)
    session_id = r.text

    # Upload chunks
    for i in range(0, len(data), CHUNK_SIZE):
        chunk = data[i:i+CHUNK_SIZE]
        encoded = base64.b64encode(chunk).decode()
        requests.post(f"{ESP32_URL}/upload_chunk",
                     data={"session": session_id, "data": encoded},
                     timeout=10)

    # Finish upload
    requests.post(f"{ESP32_URL}/upload_finish",
                 data={"session": session_id},
                 timeout=10)

    return True


def get_project_files(base_dir):
    """Get list of all files to upload"""
    files = []

    # Add individual files
    for f in UPLOAD_FILES:
        path = os.path.join(base_dir, f)
        if os.path.exists(path):
            files.append((path, f))

    # Add folders recursively
    for folder in UPLOAD_FOLDERS:
        folder_path = os.path.join(base_dir, folder)
        if os.path.isdir(folder_path):
            for root, dirs, filenames in os.walk(folder_path):
                # Filter out skipped patterns
                dirs[:] = [d for d in dirs if not any(p in d for p in SKIP_PATTERNS)]

                for filename in filenames:
                    if any(p in filename for p in SKIP_PATTERNS):
                        continue
                    local_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(local_path, base_dir)
                    remote_path = rel_path.replace("\\", "/")
                    files.append((local_path, remote_path))

    return files


def cmd_upload(base_dir, specific_files=None):
    """Upload files. If specific_files provided, upload only those."""
    if specific_files:
        # Upload specific files
        files = []
        for f in specific_files:
            local_path = os.path.join(base_dir, f)
            if os.path.exists(local_path):
                remote_path = f.replace("\\", "/")
                files.append((local_path, remote_path))
            else:
                print(f"File not found: {f}")
    else:
        # Upload all project files
        files = get_project_files(base_dir)

    print(f"Found {len(files)} files to upload\n")

    # Login first
    print("Logging in to file manager...")
    if not login():
        print("Login failed!")
        return False

    # Upload files
    success = 0
    for local_path, remote_path in files:
        size = os.path.getsize(local_path)
        print(f"  {remote_path} ({size} bytes)...", end=" ", flush=True)
        try:
            upload_file(local_path, remote_path)
            print("OK")
            success += 1
        except Exception as e:
            print(f"FAILED: {e}")

    print(f"\nUploaded {success}/{len(files)} files")
    return success == len(files)


def cmd_reset():
    """Reset the device"""
    print("Resetting device...")
    try:
        requests.get(f"{ESP32_URL}/reboot", timeout=3)
    except:
        pass  # Connection will be reset
    print("Reset command sent. Waiting for device...")

    # Wait for device to come back
    for i in range(20):
        sleep(1)
        try:
            r = requests.get(ESP32_URL, timeout=2)
            if r.status_code == 200:
                print(f"Device is back online!")
                return True
        except:
            print(".", end="", flush=True)

    print("\nDevice did not respond in time")
    return False


def cmd_status():
    """Show device status"""
    try:
        r = requests.get(ESP32_URL, timeout=5)
        if r.status_code == 200:
            # Parse some info from HTML
            html = r.text

            # Extract RAM info
            if "Free RAM" in html:
                import re
                ram_match = re.search(r'Free RAM</div>\s*<div[^>]*>([^<]+)', html)
                if ram_match:
                    print(f"Free RAM: {ram_match.group(1)}")

            if "Free Disk" in html:
                disk_match = re.search(r'Free Disk</div>\s*<div[^>]*>([^<]+)', html)
                if disk_match:
                    print(f"Free Disk: {disk_match.group(1)}")

            print(f"Status: Online")
            print(f"URL: {ESP32_URL}")
            return True
    except Exception as e:
        print(f"Error: {e}")

    print("Device is offline")
    return False


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    args = sys.argv[1:]
    base_dir = os.path.dirname(os.path.abspath(__file__))

    print(f"ESP32 Deploy - Target: {ESP32_URL}\n")

    i = 0
    while i < len(args):
        cmd = args[i]
        if cmd == "upload":
            # Collect file arguments until next command or end
            files = []
            i += 1
            while i < len(args) and args[i] not in ("reset", "status", "upload"):
                files.append(args[i])
                i += 1
            if not cmd_upload(base_dir, files if files else None):
                sys.exit(1)
        elif cmd == "reset":
            cmd_reset()
            i += 1
        elif cmd == "status":
            cmd_status()
            i += 1
        else:
            print(f"Unknown command: {cmd}")
            sys.exit(1)
        print()


if __name__ == "__main__":
    main()
