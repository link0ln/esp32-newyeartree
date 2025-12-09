# LED Strip Module for ESP32
# This module handles WS2815 RGB LED strip control

import machine
import neopixel
import os
import time
import _thread
import json

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
NUM_LEDS = 700
SETTINGS_DIR = '/led/effects'

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


def load_effect_settings(effect_name):
    """Load settings for effect from JSON file"""
    settings_file = SETTINGS_DIR + '/' + effect_name + '_settings.json'
    try:
        with open(settings_file, 'r') as f:
            return json.load(f)
    except:
        return {}


def save_effect_settings(effect_name, settings):
    """Save settings for effect to JSON file"""
    settings_file = SETTINGS_DIR + '/' + effect_name + '_settings.json'
    try:
        with open(settings_file, 'w') as f:
            json.dump(settings, f)
        return True
    except Exception as e:
        print("[LED] Save settings error:", e)
        return False


def load_effects():
    """Load effects from /led/effects folder"""
    import gc
    global loaded_effects
    loaded_effects = {}

    effects_path = '/led/effects'
    try:
        effect_files = os.listdir(effects_path)
    except:
        print("[LED] No effects folder")
        return

    gc.collect()
    for filename in effect_files:
        if filename.endswith('.py') and not filename.startswith('_'):
            effect_name = filename[:-3]
            try:
                module = __import__('led.effects.' + effect_name)
                effect_module = getattr(getattr(module, 'effects'), effect_name)

                # Get PARAMS if available
                params = getattr(effect_module, 'PARAMS', {})

                # Load saved settings and apply to module
                saved_settings = load_effect_settings(effect_name)
                if hasattr(effect_module, 'settings'):
                    effect_module.settings = saved_settings

                loaded_effects[effect_name] = {
                    'name': getattr(effect_module, 'NAME', effect_name),
                    'description': getattr(effect_module, 'DESCRIPTION', ''),
                    'params': params,
                    'settings': saved_settings,
                    'run': effect_module.run,
                    'module': effect_module
                }
                print("[LED] Loaded effect:", effect_name)
                gc.collect()
            except Exception as e:
                print("[LED] Failed to load effect {}: {}".format(effect_name, e))
                gc.collect()

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
    import gc
    effect_running = False
    current_effect = None
    effect_session += 1
    time.sleep(0.3)  # Wait for thread to finish
    gc.collect()  # Free memory from old thread


def run_effect(effect_name):
    """Run effect by name"""
    global effect_running, current_effect, effect_session
    import gc

    if effect_name not in loaded_effects:
        return False

    stop_effect()
    gc.collect()  # Clean before starting

    current_effect = effect_name
    effect_running = True
    my_session = effect_session

    def effect_thread():
        global effect_running, current_effect
        import gc
        try:
            effect = loaded_effects[effect_name]
            loop_count = 0
            while effect_running and effect_session == my_session:
                effect['run'](strip, NUM_LEDS, brightness, my_session, check_stop)
                if not effect_running or effect_session != my_session:
                    break
                # Periodic GC every 5 loops
                loop_count += 1
                if loop_count % 5 == 0:
                    gc.collect()
        except Exception as e:
            print("[LED] Effect error:", e)
        finally:
            if effect_session == my_session:
                effect_running = False
                current_effect = None
            gc.collect()

    try:
        _thread.start_new_thread(effect_thread, ())
    except Exception as e:
        print("[LED] Thread error:", e)

    return True


def set_effect_param(effect_name, param_name, value):
    """Set parameter for effect"""
    if effect_name not in loaded_effects:
        return False

    effect = loaded_effects[effect_name]
    params = effect.get('params', {})

    if param_name not in params:
        return False

    # Convert value to correct type
    param_info = params[param_name]
    try:
        if param_info['type'] == 'int':
            value = int(float(value))
            value = max(param_info['min'], min(param_info['max'], value))
        elif param_info['type'] == 'float':
            value = float(value)
            value = max(param_info['min'], min(param_info['max'], value))
        elif param_info['type'] == 'color':
            # Color is stored as hex string like "#ff0000"
            value = str(value)
    except:
        return False

    # Update settings
    if 'settings' not in effect:
        effect['settings'] = {}
    effect['settings'][param_name] = value

    # Update module's settings
    if hasattr(effect['module'], 'settings'):
        effect['module'].settings[param_name] = value

    # Save to file
    save_effect_settings(effect_name, effect['settings'])

    return True


def get_effect_params(effect_name):
    """Get parameters with current values for effect"""
    if effect_name not in loaded_effects:
        return {}

    effect = loaded_effects[effect_name]
    params = effect.get('params', {})
    settings = effect.get('settings', {})

    result = {}
    for key, info in params.items():
        result[key] = {
            'name': info['name'],
            'type': info['type'],
            'min': info['min'],
            'max': info['max'],
            'default': info['default'],
            'value': settings.get(key, info['default'])
        }
    return result


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
    return {k: {'name': v['name'], 'description': v['description'], 'has_params': len(v.get('params', {})) > 0} for k, v in loaded_effects.items()}

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

    # /led/params?effect=xxx - get effect parameters as JSON
    if path.startswith(MODULE_ROUTE + "/params"):
        try:
            effect_name = path.split("effect=")[1].split("&")[0] if "effect=" in path else ""
            if effect_name:
                params_data = get_effect_params(effect_name)
                return (json.dumps(params_data), "application/json", "200 OK")
        except:
            pass
        return ("{}", "application/json", "200 OK")

    # /led/setparam?effect=xxx&param=yyy&value=zzz
    if path.startswith(MODULE_ROUTE + "/setparam"):
        try:
            effect_name = path.split("effect=")[1].split("&")[0] if "effect=" in path else ""
            param_name = path.split("param=")[1].split("&")[0] if "param=" in path else ""
            value = path.split("value=")[1].split("&")[0] if "value=" in path else ""
            # URL decode for color values (%23 -> #)
            value = value.replace("%23", "#")
            if effect_name and param_name:
                set_effect_param(effect_name, param_name, value)
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
    """Generate module HTML page - minified for memory efficiency"""
    import gc
    gc.collect()

    status = get_status()
    effs = get_effects()

    # Build effects list
    el = ""
    for eid, ei in sorted(effs.items(), key=lambda x: x[1]['name']):
        a = " active" if status['current_effect'] == eid else ""
        el += '<div class="e' + a + '" data-e="' + eid + '" onclick="S(\'' + eid + '\')">' + ei['name'] + '</div>'

    ce = status['current_effect'] or ''
    br = str(status['brightness'])
    nl = str(status['num_leds'])

    gc.collect()

    return """<!DOCTYPE html><html><head><title>LED</title><meta name="viewport" content="width=device-width,initial-scale=1">
<style>*{box-sizing:border-box}body{font-family:Arial;margin:0;background:#1a1a2e;min-height:100vh;color:#fff}.n{text-align:center;padding:10px;background:rgba(0,0,0,.3)}.n a{color:#0f8;text-decoration:none;margin:0 15px}.m{display:flex;min-height:calc(100vh - 50px)}.l{width:180px;background:rgba(0,0,0,.4);padding:10px;overflow-y:auto}.l h3{margin:0 0 10px;color:#0f8;font-size:14px}.e{padding:10px;margin:4px 0;background:rgba(255,255,255,.1);border-radius:8px;cursor:pointer;font-size:13px}.e:hover{background:rgba(255,255,255,.2)}.e.active{background:#0f8;color:#000}.e.sel{border:2px solid #0f8}.r{flex:1;padding:15px}.r h2{margin:0 0 15px;color:#0f8}.g{background:rgba(0,0,0,.3);padding:12px;border-radius:10px;margin:10px 0}.pr{display:flex;align-items:center;margin:8px 0}.pl{width:110px;font-size:13px;color:#ccc}.pi{flex:1;display:flex;align-items:center;gap:8px}.pi input{flex:1;height:8px}.pi input[type=color]{height:32px;padding:0;border:none;cursor:pointer}.pv{width:50px;text-align:center;background:rgba(255,255,255,.1);padding:4px;border-radius:4px;font-size:13px}.np{color:#888;font-style:italic}.c{background:rgba(0,0,0,.3);padding:12px;border-radius:10px;margin:15px 0}.c h3{margin:0 0 12px;color:#f66;font-size:14px}.br{display:flex;align-items:center;gap:12px;margin:8px 0}.bv{font-size:1.3em;color:#0f8;min-width:50px}.bs{flex:1;height:10px}.b{padding:10px 16px;border:none;border-radius:6px;cursor:pointer;font-size:14px}.bn{background:#764ba2;color:#fff;width:100%;margin-top:12px;padding:12px}.bt{background:#ff4757;color:#fff}.bo{background:#2f3542;color:#fff}.bw{display:flex;gap:8px;margin-top:12px}.bw .b{flex:1}.sb{display:flex;gap:15px;padding:8px;background:rgba(0,0,0,.3);border-radius:6px;margin-bottom:15px;font-size:12px}.si{display:flex;gap:6px}.sl{color:#888}.sv{color:#0f8}</style></head>
<body><div class="n"><a href="/">Home</a>|<a href="/led">LED</a>|<a href="/files">Files</a></div>
<div class="m"><div class="l"><h3>EFFECTS</h3>""" + el + """</div>
<div class="r"><div class="sb"><div class="si"><span class="sl">LEDs:</span><span class="sv">""" + nl + """</span></div><div class="si"><span class="sl">Effect:</span><span class="sv" id="ce">""" + (ce or 'None') + """</span></div></div>
<h2 id="et">Select effect</h2><div id="pc" class="g"><div class="np">Select an effect</div></div>
<button class="b bn" id="rb" onclick="R()" style="display:none">Run</button>
<div class="c"><h3>CONTROLS</h3><div class="br"><span>Bright</span><input type="range" class="bs" id="br" min="0" max="100" value=\"""" + br + """" oninput="U(this.value)" onchange="B(this.value)"><span class="bv" id="bv">""" + br + """%</span></div>
<div class="bw"><button class="b bt" onclick="X()">Stop</button><button class="b bo" onclick="O()">Off</button></div></div></div></div>
<script>let se=null,P={};function S(n){se=n;document.querySelectorAll('.e').forEach(e=>e.classList.remove('sel'));document.querySelector('[data-e="'+n+'"]').classList.add('sel');document.getElementById('et').textContent=document.querySelector('[data-e="'+n+'"]').textContent;document.getElementById('rb').style.display='block';fetch('/led/params?effect='+n).then(r=>r.json()).then(p=>{P=p;let c=document.getElementById('pc');if(!Object.keys(p).length){c.innerHTML='<div class="np">No parameters</div>';return}let h='';for(let[k,i]of Object.entries(p).sort()){if(i.type==='color'){h+='<div class="pr"><span class="pl">'+i.name+'</span><div class="pi"><input type="color" value="'+(i.value||'#00ff00')+'" data-p="'+k+'" onchange="T(this)"></div></div>'}else{let s=i.type==='float'?'0.1':'1';h+='<div class="pr"><span class="pl">'+i.name+'</span><div class="pi"><input type="range" min="'+i.min+'" max="'+i.max+'" step="'+s+'" value="'+i.value+'" data-p="'+k+'" oninput="V(this)" onchange="T(this)"><span class="pv" id="v_'+k+'">'+i.value+'</span></div></div>'}}c.innerHTML=h})}function V(e){document.getElementById('v_'+e.dataset.p).textContent=e.value}function T(e){fetch('/led/setparam?effect='+se+'&param='+e.dataset.p+'&value='+encodeURIComponent(e.value))}function R(){if(!se)return;fetch('/led/effect?name='+se).then(()=>{document.getElementById('ce').textContent=se;document.querySelectorAll('.e').forEach(e=>e.classList.remove('active'));document.querySelector('[data-e="'+se+'"]').classList.add('active')})}function X(){fetch('/led/stop').then(()=>{document.getElementById('ce').textContent='None';document.querySelectorAll('.e').forEach(e=>e.classList.remove('active'))})}function O(){fetch('/led/off').then(()=>{document.getElementById('ce').textContent='None';document.querySelectorAll('.e').forEach(e=>e.classList.remove('active'))})}function U(v){document.getElementById('bv').textContent=v+'%'}function B(v){U(v);fetch('/led/brightness?value='+v)}let ce='""" + ce + """';if(ce)S(ce);</script></body></html>"""
