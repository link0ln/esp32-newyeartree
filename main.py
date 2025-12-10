# main.py - Universal ESP32 Module Manager
# Automatically discovers and loads modules from root folders
# This file should NEVER crash - all errors are caught

import os
import gc

# ============================================================================
# CHECK FOR UDP MODE (before loading anything else!)
# ============================================================================
def check_udp_mode():
    try:
        os.stat('/udp_mode')
        print("[Boot] UDP mode flag found, starting UDP receiver...")
        gc.collect()
        import udp_mode
        udp_mode.run()  # This will reboot when done
        return True
    except OSError:
        return False  # Flag doesn't exist, normal boot

if check_udp_mode():
    import machine
    machine.reset()  # Should not reach here, but just in case

# Normal imports (only loaded if NOT in UDP mode)
import time
import machine
import neopixel
import socket
import ubinascii

# ============================================================================
# STATUS LED (Pin 8 - built-in WS LED on ESP32-C3)
# ============================================================================

STATUS_LED_PIN = 8
status_led = None


def init_status_led():
    global status_led
    try:
        status_led = neopixel.NeoPixel(machine.Pin(STATUS_LED_PIN), 1)
        status_red()
    except:
        pass


def set_status(r, g, b):
    try:
        if status_led:
            status_led[0] = (r, g, b)  # RGB
            status_led.write()
    except:
        pass


def status_red():
    set_status(255, 0, 0)


def status_blue():
    set_status(0, 0, 255)


def status_green():
    set_status(0, 255, 0)


# ============================================================================
# WIFI
# ============================================================================

WIFI_SSID = 'wgnet'
WIFI_PASSWORD = 'bomba1235'


def connect_wifi():
    import network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        print("[WiFi] Already connected")
        status_blue()
        return True

    print("[WiFi] Connecting to", WIFI_SSID)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    timeout = 30
    start = time.time()
    while not wlan.isconnected():
        set_status(0, 0, 255)
        time.sleep(0.2)
        set_status(0, 0, 50)
        time.sleep(0.2)
        if time.time() - start > timeout:
            print("[WiFi] Timeout!")
            return False

    print("[WiFi] Connected:", wlan.ifconfig())
    status_blue()
    return True


# ============================================================================
# MODULE MANAGER
# ============================================================================

modules = {}  # {route: module}


def discover_modules():
    """Find and load modules from root folders"""
    global modules
    modules = {}

    # System folders to skip
    skip_folders = ['lib', 'sys', 'boot', '__pycache__']

    try:
        items = os.listdir('/')
    except:
        return

    for item in items:
        if item.startswith('.') or item.startswith('_') or item in skip_folders:
            continue

        try:
            stat = os.stat('/' + item)
            is_dir = stat[0] & 0x4000
            if not is_dir:
                continue

            # Check if folder has __init__.py
            try:
                os.stat('/' + item + '/__init__.py')
            except:
                continue

            # Try to import module
            try:
                module = __import__(item)

                # Check required interface
                if not hasattr(module, 'MODULE_NAME') or not hasattr(module, 'MODULE_ROUTE'):
                    print("[Modules] Skipping {}: missing interface".format(item))
                    continue

                # Initialize module
                if hasattr(module, 'init'):
                    try:
                        module.init()
                    except Exception as e:
                        print("[Modules] Init error for {}: {}".format(item, e))

                modules[module.MODULE_ROUTE] = {
                    'name': module.MODULE_NAME,
                    'route': module.MODULE_ROUTE,
                    'icon': getattr(module, 'MODULE_ICON', ''),
                    'handle_request': getattr(module, 'handle_request', None),
                    'module': module
                }
                print("[Modules] Loaded:", item, "->", module.MODULE_ROUTE)

            except Exception as e:
                print("[Modules] Failed to load {}: {}".format(item, e))

        except:
            continue


def get_module_for_path(path):
    """Find module that handles this path"""
    for route, mod in modules.items():
        if path == route or path.startswith(route + '/') or path.startswith(route + '?'):
            return mod
    return None


# ============================================================================
# FILE MANAGER (built-in)
# ============================================================================

FILE_MANAGER_PASSWORD = "QWEasd123rt"
logged_in = False
upload_sessions = {}


def format_file_size(size):
    if size < 1024:
        return str(size) + " B"
    elif size < 1024 * 1024:
        return str(round(size / 1024, 1)) + " KB"
    return str(round(size / (1024 * 1024), 1)) + " MB"


def rmtree(path):
    """Recursively delete a directory and all its contents"""
    try:
        for item in os.listdir(path):
            item_path = path + "/" + item
            try:
                stat = os.stat(item_path)
                if stat[0] & 0x4000:  # is directory
                    rmtree(item_path)
                else:
                    os.remove(item_path)
            except:
                pass
        os.rmdir(path)
        return True
    except:
        return False


def list_files(path="/"):
    try:
        files = []
        for item in os.listdir(path):
            full_path = path + "/" + item if path != "/" else "/" + item
            try:
                stat = os.stat(full_path)
                is_dir = stat[0] & 0x4000
                if is_dir:
                    files.append({"name": item, "type": "dir", "size": "-"})
                else:
                    files.append({"name": item, "type": "file", "size": format_file_size(stat[6])})
            except:
                files.append({"name": item, "type": "unknown", "size": "-"})
        return files
    except:
        return []


def url_decode(s):
    """Proper URL decoding"""
    result = []
    i = 0
    while i < len(s):
        if s[i] == '%' and i + 2 < len(s):
            try:
                result.append(chr(int(s[i+1:i+3], 16)))
                i += 3
                continue
            except:
                pass
        elif s[i] == '+':
            result.append(' ')
            i += 1
            continue
        result.append(s[i])
        i += 1
    return ''.join(result)


def parse_post_data(data):
    params = {}
    try:
        body = data.split('\r\n\r\n')[1]
        for pair in body.split('&'):
            if '=' in pair:
                key, value = pair.split('=', 1)
                params[key] = url_decode(value)
    except:
        pass
    return params


def base64_decode(s):
    try:
        return ubinascii.a2b_base64(s)
    except:
        return b''


# ============================================================================
# HTML PAGES
# ============================================================================

def get_nav_html():
    """Generate navigation with all modules"""
    nav = '<a href="/">Home</a>'
    for route, mod in modules.items():
        icon = mod['icon'] + ' ' if mod['icon'] else ''
        nav += ' | <a href="' + route + '">' + icon + mod['name'] + '</a>'
    nav += ' | <a href="/files">Files</a>'
    return nav


def get_home_html():
    """Home page with system info and modules"""
    import network
    wlan = network.WLAN(network.STA_IF)
    ip = wlan.ifconfig()[0] if wlan.isconnected() else "Not connected"

    # RAM info
    ram_free = gc.mem_free() // 1024
    ram_total = (gc.mem_free() + gc.mem_alloc()) // 1024
    ram_str = "{}KB/{}KB".format(ram_free, ram_total)

    # Disk info
    try:
        stat = os.statvfs('/')
        disk_free = (stat[0] * stat[3]) // 1024
        disk_total = (stat[0] * stat[2]) // 1024
        disk_str = "{}KB/{}KB".format(disk_free, disk_total)
    except:
        disk_str = "N/A"

    modules_html = ""
    for route, mod in modules.items():
        icon = mod['icon'] if mod['icon'] else '[M]'
        modules_html += '<a href="' + route + '" class="module-card"><div class="module-icon">' + icon + '</div><div class="module-name">' + mod['name'] + '</div></a>'

    return """<!DOCTYPE html>
<html>
<head>
    <title>ESP32 Control Panel</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial; margin: 0; padding: 20px; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; color: white; }
        .container { max-width: 600px; margin: 0 auto; }
        h1 { text-align: center; color: #00ff88; text-shadow: 0 0 10px #00ff88; }
        .nav { text-align: center; margin-bottom: 20px; background: rgba(0,0,0,0.3); padding: 10px; border-radius: 10px; }
        .nav a { color: #00ff88; text-decoration: none; margin: 0 10px; }
        .section { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 15px; margin: 20px 0; }
        .section h2 { margin-top: 0; color: #ff6b6b; font-size: 1.2em; }
        .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        .info-item { background: rgba(0,0,0,0.3); padding: 15px; border-radius: 10px; text-align: center; }
        .info-label { font-size: 0.8em; color: #aaa; }
        .info-value { font-size: 1.3em; color: #00ff88; margin-top: 5px; }
        .modules-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
        .module-card { display: block; background: linear-gradient(45deg, #667eea, #764ba2); padding: 20px; border-radius: 15px; text-decoration: none; color: white; text-align: center; transition: transform 0.2s; }
        .module-card:hover { transform: scale(1.05); }
        .module-icon { font-size: 2em; margin-bottom: 10px; }
        .module-name { font-size: 1.1em; }
        .btn-reboot { display: block; width: 100%; padding: 15px; background: linear-gradient(45deg, #ff9500, #ff5e3a); color: white; border: none; border-radius: 10px; font-size: 16px; cursor: pointer; margin-top: 10px; }
        .btn-reboot:hover { opacity: 0.9; }
    </style>
</head>
<body>
    <div class="container">
        <h1>ESP32 Control Panel</h1>
        <div class="nav">""" + get_nav_html() + """</div>

        <div class="section">
            <h2>System Info</h2>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">IP Address</div>
                    <div class="info-value">""" + ip + """</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Modules</div>
                    <div class="info-value">""" + str(len(modules)) + """</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Free RAM</div>
                    <div class="info-value">""" + ram_str + """</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Free Disk</div>
                    <div class="info-value">""" + disk_str + """</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Modules</h2>
            <div class="modules-grid">
                """ + modules_html + """
                <a href="/files" class="module-card" style="background: linear-gradient(45deg, #11998e, #38ef7d);">
                    <div class="module-icon">[F]</div>
                    <div class="module-name">File Manager</div>
                </a>
            </div>
        </div>

        <div class="section">
            <h2>System</h2>
            <button class="btn-reboot" onclick="reboot()">Reboot Device</button>
        </div>
    </div>
    <script>
        function reboot() {
            if (confirm('Reboot the device?')) {
                fetch('/reboot').catch(() => {});
                alert('Rebooting... Page will reload in 10 seconds.');
                setTimeout(() => location.reload(), 10000);
            }
        }
    </script>
</body>
</html>"""


def get_login_html():
    return """<!DOCTYPE html>
<html>
<head>
    <title>File Manager Login</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial; margin: 20px; background: #f0f0f0; }
        .container { max-width: 400px; margin: 50px auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h2 { text-align: center; color: #333; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        button { width: 100%; padding: 15px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
        button:hover { background: #45a049; }
        .back { text-align: center; margin-top: 15px; }
        .back a { color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <h2>File Manager</h2>
        <form method="post" action="/files">
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        <div class="back"><a href="/">Back to Home</a></div>
    </div>
</body>
</html>"""


def get_files_html(files, current_path="/"):
    files_html = ""
    for file in files:
        icon = "[D]" if file["type"] == "dir" else "[F]"
        file_path = ("/" + file["name"]) if current_path == "/" else (current_path + "/" + file["name"])

        if file["type"] == "dir":
            files_html += '<tr><td><a href="/files?path=' + file_path + '">' + icon + ' ' + file["name"] + '</a></td><td>' + file["size"] + '</td><td><a href="/delete?file=' + file_path + '" onclick="return confirm(\'Delete folder and all contents?\')">Delete</a></td></tr>'
        else:
            files_html += '<tr><td>' + icon + ' ' + file["name"] + '</td><td>' + file["size"] + '</td><td><a href="/download?file=' + file_path + '">Download</a> | <a href="/delete?file=' + file_path + '" onclick="return confirm(\'Delete?\')">Delete</a></td></tr>'

    return """<!DOCTYPE html>
<html>
<head>
    <title>File Manager</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial; margin: 20px; background: #f0f0f0; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
        .nav { background: #333; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
        .nav a { color: white; text-decoration: none; margin: 0 10px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f8f8f8; }
        .upload { margin: 20px 0; padding: 15px; background: #f9f9f9; border-radius: 5px; }
        input, textarea { width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        button { padding: 10px 20px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background: #45a049; }
        .logout { background: #f44336; }
        .progress { display: none; background: #f0f0f0; border-radius: 5px; margin: 10px 0; }
        .progress-bar { height: 20px; background: #4CAF50; border-radius: 5px; text-align: center; color: white; line-height: 20px; }
    </style>
    <script>
        const CHUNK_SIZE = 256;
        async function uploadFile() {
            const file = document.getElementById('fileInput').files[0];
            if (!file) { alert('Select a file'); return; }
            const btn = document.getElementById('uploadBtn');
            const progress = document.getElementById('progress');
            const bar = document.getElementById('progressBar');
            btn.disabled = true;
            progress.style.display = 'block';
            try {
                const start = await fetch('/upload_start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: 'filename=' + encodeURIComponent(file.name)
                });
                const sessionId = await start.text();
                for (let offset = 0; offset < file.size; offset += CHUNK_SIZE) {
                    const chunk = file.slice(offset, Math.min(offset + CHUNK_SIZE, file.size));
                    const data = await new Promise(r => {
                        const reader = new FileReader();
                        reader.onload = () => r(new Uint8Array(reader.result));
                        reader.readAsArrayBuffer(chunk);
                    });
                    await fetch('/upload_chunk', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                        body: 'session=' + sessionId + '&data=' + encodeURIComponent(btoa(String.fromCharCode.apply(null, data)))
                    });
                    const pct = Math.round((Math.min(offset + CHUNK_SIZE, file.size) / file.size) * 100);
                    bar.style.width = pct + '%';
                    bar.textContent = pct + '%';
                }
                await fetch('/upload_finish', {method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'}, body: 'session=' + sessionId});
                location.reload();
            } catch (e) { alert('Upload failed'); }
            btn.disabled = false;
        }
        function createFile() {
            const name = document.getElementById('fileName').value;
            const content = document.getElementById('fileContent').value;
            if (!name) { alert('Enter filename'); return; }
            fetch('/upload_simple', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: 'filename=' + encodeURIComponent(name) + '&content=' + encodeURIComponent(content)
            }).then(() => location.reload());
        }
    </script>
</head>
<body>
    <div class="container">
        <div class="nav">
            <a href="/">Home</a> | <a href="/files">Files</a> | <a href="/logout" class="logout" style="float:right">Logout</a>
        </div>
        <h2>File Manager</h2>
        <p>Path: """ + current_path + """</p>
        <div class="upload">
            <h3>Upload File</h3>
            <input type="file" id="fileInput">
            <button id="uploadBtn" onclick="uploadFile()">Upload</button>
            <div id="progress" class="progress"><div id="progressBar" class="progress-bar">0%</div></div>
        </div>
        <div class="upload">
            <h3>Create Text File</h3>
            <input type="text" id="fileName" placeholder="Filename">
            <textarea id="fileContent" placeholder="Content..." rows="3"></textarea>
            <button onclick="createFile()">Create</button>
        </div>
        <table>
            <tr><th>Name</th><th>Size</th><th>Actions</th></tr>
            """ + files_html + """
        </table>
    </div>
</body>
</html>"""


# ============================================================================
# HTTP SERVER
# ============================================================================

def http_server():
    global logged_in, upload_sessions

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', 80))
    s.listen(5)
    print("[HTTP] Server started on port 80")

    while True:
        conn = None
        try:
            conn, addr = s.accept()
            conn.settimeout(30)

            # Read request (up to 4KB should be enough for chunk uploads)
            request = conn.recv(4096).decode()

            lines = request.split('\r\n')
            method, path, _ = lines[0].split()

            response_body = ""
            status = "200 OK"
            content_type = "text/html"
            headers = ""

            # Check if module handles this path
            mod = get_module_for_path(path)
            if mod and mod['handle_request']:
                try:
                    params = parse_post_data(request) if 'POST' in method else {}
                    result = mod['handle_request'](path, method, params)
                    if isinstance(result, tuple):
                        response_body, content_type, status = result
                    else:
                        response_body = result
                except Exception as e:
                    import sys
                    sys.print_exception(e)
                    response_body = "Module error: " + str(e)
                    status = "500 Internal Server Error"

            # Home page
            elif path == "/":
                response_body = get_home_html()

            # Reboot
            elif path == "/reboot":
                try:
                    conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 2\r\n\r\nOK".encode())
                    conn.close()
                except:
                    pass
                print("[System] Rebooting...")
                time.sleep(1)
                machine.reset()

            # File Manager routes
            elif path == "/files" or path.startswith("/files?"):
                if not logged_in:
                    if 'POST' in method:
                        params = parse_post_data(request)
                        if params.get('password') == FILE_MANAGER_PASSWORD:
                            logged_in = True
                            response_body = get_files_html(list_files("/"), "/")
                        else:
                            response_body = get_login_html()
                    else:
                        response_body = get_login_html()
                else:
                    current_path = path.split("path=")[1] if "path=" in path else "/"
                    response_body = get_files_html(list_files(current_path), current_path)

            elif path == "/logout":
                logged_in = False
                response_body = get_login_html()

            elif path.startswith("/download?file=") and logged_in:
                filename = path.split("file=")[1]
                if filename.startswith("/"):
                    filename = filename[1:]
                try:
                    with open("/" + filename, 'rb') as f:
                        response_body = f.read()
                    content_type = "application/octet-stream"
                    headers = 'Content-Disposition: attachment; filename="' + filename.split("/")[-1] + '"\r\n'
                except:
                    response_body = "Not found"
                    status = "404 Not Found"

            elif path.startswith("/delete?file=") and logged_in:
                filename = path.split("file=")[1]
                if filename.startswith("/"):
                    filename = filename[1:]
                full_path = "/" + filename
                try:
                    stat = os.stat(full_path)
                    if stat[0] & 0x4000:  # is directory
                        rmtree(full_path)
                    else:
                        os.remove(full_path)
                except:
                    pass
                # Go back to parent folder after delete
                parent = "/" + "/".join(filename.split("/")[:-1]) if "/" in filename else "/"
                response_body = get_files_html(list_files(parent), parent)

            elif path == "/upload_simple" and logged_in:
                params = parse_post_data(request)
                filename = params.get('filename', '')
                content = params.get('content', '')
                if filename:
                    try:
                        with open("/" + filename, 'w') as f:
                            f.write(content)
                    except:
                        pass
                response_body = "OK"
                content_type = "text/plain"

            elif path == "/upload_start" and logged_in:
                params = parse_post_data(request)
                filename = params.get('filename', '')
                if filename:
                    session_id = str(len(upload_sessions))
                    upload_sessions[session_id] = {'filename': "/" + filename}
                    # Create parent directories if needed
                    full_path = "/" + filename
                    if "/" in filename:
                        parts = filename.split("/")
                        path_so_far = ""
                        for part in parts[:-1]:
                            path_so_far += "/" + part
                            try:
                                os.mkdir(path_so_far)
                            except:
                                pass
                    try:
                        with open(full_path, 'wb') as f:
                            pass
                    except:
                        pass
                    response_body = session_id
                content_type = "text/plain"

            elif path == "/upload_chunk" and logged_in:
                params = parse_post_data(request)
                session_id = params.get('session', '')
                chunk_data = params.get('data', '')
                if session_id in upload_sessions:
                    try:
                        with open(upload_sessions[session_id]['filename'], 'ab') as f:
                            f.write(base64_decode(chunk_data))
                    except:
                        pass
                response_body = "OK"
                content_type = "text/plain"

            elif path == "/upload_finish" and logged_in:
                params = parse_post_data(request)
                session_id = params.get('session', '')
                if session_id in upload_sessions:
                    del upload_sessions[session_id]
                response_body = "OK"
                content_type = "text/plain"

            else:
                response_body = "404 Not Found"
                status = "404 Not Found"

            # Send response
            if isinstance(response_body, str):
                response_body = response_body.encode()

            response = "HTTP/1.1 {}\r\nContent-Type: {}\r\n{}Content-Length: {}\r\nConnection: close\r\n\r\n".format(
                status, content_type, headers, len(response_body))
            conn.send(response.encode())
            conn.send(response_body)
            conn.close()
            gc.collect()

        except Exception as e:
            print("[HTTP] Error:", e)
            try:
                if conn:
                    conn.close()
            except:
                pass


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 40)
    print("ESP32 Module Manager Starting...")
    print("=" * 40)

    init_status_led()
    status_red()
    print("[Status] RED - Starting")

    if not connect_wifi():
        print("[WiFi] Failed, continuing...")

    # WebREPL is started in boot.py

    status_blue()
    print("[Status] BLUE - WiFi OK")
    time.sleep(0.3)

    print("[Modules] Discovering modules...")
    discover_modules()
    print("[Modules] Found:", len(modules), "modules")

    status_green()
    print("[Status] GREEN - Ready")
    print("=" * 40)

    http_server()


# Run with error recovery
while True:
    try:
        main()
    except Exception as e:
        print("=" * 40)
        print("CRITICAL ERROR:", e)
        print("=" * 40)
        try:
            init_status_led()
            for _ in range(10):
                set_status(255, 0, 0)
                time.sleep(0.3)
                set_status(50, 0, 0)
                time.sleep(0.3)
        except:
            pass
        print("Restarting in 3 seconds...")
        time.sleep(3)
        gc.collect()
