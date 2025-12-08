# LED Strip Module for ESP32
# This module handles WS2815 RGB LED strip control

import machine
import neopixel
import os
import time
import _thread

# ============================================================================
# MODULE INTERFACE (required by main.py)
# ============================================================================

MODULE_NAME = "LED Control"
MODULE_ROUTE = "/led"
MODULE_ICON = ""

# ============================================================================
# CONFIGURATION
# ============================================================================

LED_PIN = 3
NUM_LEDS = 50

# ============================================================================
# STATE
# ============================================================================

strip = None
current_effect = None
effect_running = False
effect_session = 0
brightness = 100
current_color = (255, 0, 0)
loaded_effects = {}
initialized = False

# ============================================================================
# INITIALIZATION
# ============================================================================

def init():
    """Initialize the LED strip module"""
    global strip, initialized
    try:
        strip = neopixel.NeoPixel(machine.Pin(LED_PIN), NUM_LEDS)
        clear()
        load_effects()
        initialized = True
        print("[LED] Initialized: {} LEDs on pin {}".format(NUM_LEDS, LED_PIN))
        return True
    except Exception as e:
        print("[LED] Init error:", e)
        initialized = False
        return False


def load_effects():
    """Load effects from /led/effects folder"""
    global loaded_effects
    loaded_effects = {}

    effects_path = '/led/effects'
    try:
        effect_files = os.listdir(effects_path)
    except:
        print("[LED] No effects folder")
        return

    for filename in effect_files:
        if filename.endswith('.py') and not filename.startswith('_'):
            effect_name = filename[:-3]
            try:
                module = __import__('led.effects.' + effect_name)
                effect_module = getattr(getattr(module, 'effects'), effect_name)
                loaded_effects[effect_name] = {
                    'name': getattr(effect_module, 'NAME', effect_name),
                    'description': getattr(effect_module, 'DESCRIPTION', ''),
                    'run': effect_module.run
                }
                print("[LED] Loaded effect:", effect_name)
            except Exception as e:
                print("[LED] Failed to load effect {}: {}".format(effect_name, e))

# ============================================================================
# LED CONTROL FUNCTIONS
# ============================================================================

def apply_brightness(r, g, b):
    """Apply brightness, output in GRB order for WS2815"""
    factor = brightness / 100.0
    return (int(g * factor), int(r * factor), int(b * factor))


def set_all(r, g, b):
    """Set all pixels to same color"""
    global current_color
    current_color = (r, g, b)
    if strip:
        color = apply_brightness(r, g, b)
        for i in range(NUM_LEDS):
            strip[i] = color
        strip.write()


def clear():
    """Turn off all LEDs"""
    if strip:
        for i in range(NUM_LEDS):
            strip[i] = (0, 0, 0)
        strip.write()


def set_brightness(level):
    """Set brightness 0-100"""
    global brightness
    brightness = max(0, min(100, level))


def check_stop(session_id):
    """Check if effect should stop"""
    return effect_session != session_id or not effect_running


def stop_effect():
    """Stop current effect"""
    global effect_running, current_effect, effect_session
    effect_running = False
    current_effect = None
    effect_session += 1
    time.sleep(0.2)


def run_effect(effect_name):
    """Run effect by name"""
    global effect_running, current_effect, effect_session

    if effect_name not in loaded_effects:
        return False

    stop_effect()
    current_effect = effect_name
    effect_running = True
    my_session = effect_session

    def effect_thread():
        global effect_running, current_effect
        try:
            effect = loaded_effects[effect_name]
            while effect_running and effect_session == my_session:
                result = effect['run'](strip, NUM_LEDS, brightness, my_session, check_stop)
                if result == False or effect_session != my_session:
                    break
        except Exception as e:
            print("[LED] Effect error:", e)
        finally:
            if effect_session == my_session:
                effect_running = False
                current_effect = None

    try:
        _thread.start_new_thread(effect_thread, ())
    except:
        pass

    return True


def get_status():
    """Get current status"""
    return {
        'initialized': initialized,
        'num_leds': NUM_LEDS,
        'brightness': brightness,
        'current_color': current_color,
        'current_effect': current_effect,
        'effect_running': effect_running,
        'effects_count': len(loaded_effects)
    }


def get_effects():
    """Get available effects"""
    return {k: {'name': v['name'], 'description': v['description']} for k, v in loaded_effects.items()}

# ============================================================================
# HTTP INTERFACE (required by main.py)
# ============================================================================

def handle_request(path, method, params):
    """Handle HTTP request, return (response_body, content_type, status)"""

    if not initialized:
        return ("Module not initialized", "text/plain", "503 Service Unavailable")

    # /led - main page
    if path == MODULE_ROUTE or path == MODULE_ROUTE + "/":
        return (get_html(), "text/html", "200 OK")

    # /led/effect?name=xxx
    if path.startswith(MODULE_ROUTE + "/effect"):
        try:
            effect_name = path.split("name=")[1] if "name=" in path else ""
            if effect_name:
                run_effect(effect_name)
        except:
            pass
        return ("OK", "text/plain", "200 OK")

    # /led/brightness?value=xxx
    if path.startswith(MODULE_ROUTE + "/brightness"):
        try:
            value = int(path.split("value=")[1]) if "value=" in path else 100
            set_brightness(value)
        except:
            pass
        return ("OK", "text/plain", "200 OK")

    # /led/color?r=x&g=x&b=x
    if path.startswith(MODULE_ROUTE + "/color"):
        try:
            r = int(path.split("r=")[1].split("&")[0]) if "r=" in path else 0
            g = int(path.split("g=")[1].split("&")[0]) if "g=" in path else 0
            b = int(path.split("b=")[1].split("&")[0]) if "b=" in path else 0
            stop_effect()
            set_all(r, g, b)
        except:
            pass
        return ("OK", "text/plain", "200 OK")

    # /led/stop
    if path == MODULE_ROUTE + "/stop":
        stop_effect()
        return ("OK", "text/plain", "200 OK")

    # /led/off
    if path == MODULE_ROUTE + "/off":
        stop_effect()
        clear()
        return ("OK", "text/plain", "200 OK")

    return ("Not Found", "text/plain", "404 Not Found")


def get_html():
    """Generate module HTML page"""
    status = get_status()
    effs = get_effects()

    effects_html = ""
    for effect_id, effect_info in effs.items():
        active = " active" if status['current_effect'] == effect_id else ""
        effects_html += '<button class="effect-btn' + active + '" onclick="runEffect(\'' + effect_id + '\')">' + effect_info['name'] + '</button>'

    r, g, b = status['current_color']
    color_hex = "#{:02x}{:02x}{:02x}".format(r, g, b)

    return """<!DOCTYPE html>
<html>
<head>
    <title>LED Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial; margin: 20px; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; color: white; }
        .container { max-width: 600px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 20px; border-radius: 15px; }
        h2 { text-align: center; color: #00ff88; text-shadow: 0 0 10px #00ff88; }
        .nav { text-align: center; margin-bottom: 20px; }
        .nav a { color: #00ff88; text-decoration: none; margin: 0 15px; }
        .section { background: rgba(0,0,0,0.3); padding: 15px; border-radius: 10px; margin: 15px 0; }
        .section h3 { margin-top: 0; color: #ff6b6b; }
        .status { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        .status-item { background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; text-align: center; }
        .status-value { font-size: 1.5em; color: #00ff88; }
        .effects-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
        .effect-btn { padding: 15px; background: linear-gradient(45deg, #667eea, #764ba2); color: white; border: none; border-radius: 10px; cursor: pointer; font-size: 14px; }
        .effect-btn.active { background: linear-gradient(45deg, #00ff88, #00cc6a); }
        .control-btn { padding: 15px 30px; margin: 5px; border: none; border-radius: 10px; cursor: pointer; font-size: 16px; }
        .btn-stop { background: #ff4757; color: white; }
        .btn-off { background: #2f3542; color: white; }
        .slider { width: 100%; height: 20px; border-radius: 10px; background: linear-gradient(90deg, #2f3542, #00ff88); -webkit-appearance: none; }
        .slider::-webkit-slider-thumb { -webkit-appearance: none; width: 30px; height: 30px; border-radius: 50%; background: white; cursor: pointer; }
        .brightness-value { text-align: center; font-size: 2em; color: #00ff88; margin: 10px 0; }
        .color-picker input { width: 100%; height: 50px; border: none; border-radius: 10px; cursor: pointer; }
        .btn-color { width: 100%; padding: 15px; background: linear-gradient(45deg, #f093fb, #f5576c); color: white; border: none; border-radius: 10px; cursor: pointer; font-size: 16px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="nav"><a href="/">Home</a> | <a href="/led">LED Control</a> | <a href="/files">Files</a></div>
        <h2>Christmas Tree LED</h2>
        <div class="section">
            <h3>Status</h3>
            <div class="status">
                <div class="status-item"><div>LEDs</div><div class="status-value">""" + str(status['num_leds']) + """</div></div>
                <div class="status-item"><div>Effect</div><div class="status-value">""" + (status['current_effect'] or 'None') + """</div></div>
            </div>
        </div>
        <div class="section">
            <h3>Brightness</h3>
            <div class="brightness-value" id="brightnessValue">""" + str(status['brightness']) + """%</div>
            <input type="range" class="slider" id="brightness" min="0" max="100" value=\"""" + str(status['brightness']) + """" onchange="setBrightness(this.value)">
        </div>
        <div class="section">
            <h3>Effects</h3>
            <div class="effects-grid">""" + effects_html + """</div>
        </div>
        <div class="section">
            <h3>Solid Color</h3>
            <div class="color-picker"><input type="color" id="colorPicker" value=\"""" + color_hex + """\"></div>
            <button class="btn-color" onclick="setColor()">Set Color</button>
        </div>
        <div class="section" style="text-align: center;">
            <button class="control-btn btn-stop" onclick="stopEffect()">Stop Effect</button>
            <button class="control-btn btn-off" onclick="turnOff()">Turn Off</button>
        </div>
    </div>
    <script>
        function runEffect(name) { fetch('/led/effect?name=' + name).then(() => location.reload()); }
        function stopEffect() { fetch('/led/stop').then(() => location.reload()); }
        function turnOff() { fetch('/led/off').then(() => location.reload()); }
        function setBrightness(v) { document.getElementById('brightnessValue').textContent = v + '%'; fetch('/led/brightness?value=' + v); }
        function setColor() {
            const c = document.getElementById('colorPicker').value;
            fetch('/led/color?r=' + parseInt(c.substr(1,2),16) + '&g=' + parseInt(c.substr(3,2),16) + '&b=' + parseInt(c.substr(5,2),16)).then(() => location.reload());
        }
    </script>
</body>
</html>"""
