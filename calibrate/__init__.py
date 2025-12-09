# LED Calibration Module - minimal version
# HTML served from separate file to save RAM
import json
import time

MODULE_NAME = "Calibrate"
MODULE_ROUTE = "/calibrate"
MODULE_ICON = ""

current_pixel = 0
calibration_active = False
detect_color = 'w'  # w=white, r=red, g=green, b=blue
COORDS_FILE = '/coords.json'

# Color values for detection (GRB order for WS2815)
COLORS = {
    'w': (255, 255, 255),
    'r': (0, 255, 0),   # GRB: G=0, R=255, B=0
    'g': (255, 0, 0),   # GRB: G=255, R=0, B=0
    'b': (0, 0, 255),
}


def init():
    print("[CAL] Init")
    return True


def get_led():
    try:
        import led
        return led.strip, led.NUM_LEDS
    except:
        return None, 0


def light_pixel(px, on=True):
    global detect_color
    strip, num = get_led()
    if not strip:
        return
    for i in range(num):
        strip[i] = (0, 0, 0)
    if on and 0 <= px < num:
        strip[px] = COLORS.get(detect_color, (255, 255, 255))
    strip.write()


def handle_request(path, method, params):
    global current_pixel, calibration_active, detect_color
    strip, num = get_led()

    if path == MODULE_ROUTE or path == MODULE_ROUTE + "/":
        try:
            with open('/calibrate/index.html', 'r') as f:
                html = f.read().replace('{{NUM}}', str(num))
            return (html, "text/html", "200 OK")
        except Exception as e:
            return ("HTML not found: " + str(e), "text/plain", "500 Error")

    if path.startswith(MODULE_ROUTE + "/start"):
        # Parse color from ?c=r/g/b/w
        if 'c=' in path:
            c = path.split('c=')[1].split('&')[0]
            if c in COLORS:
                detect_color = c
        current_pixel = 0
        calibration_active = True
        light_pixel(0)
        return (json.dumps({'status': 'started', 'pixel': 0, 'total': num, 'color': detect_color}), "application/json", "200 OK")

    # Set detection color
    if path.startswith(MODULE_ROUTE + "/color"):
        c = path.split('c=')[1].split('&')[0] if 'c=' in path else 'w'
        if c in COLORS:
            detect_color = c
            light_pixel(current_pixel)  # Re-light with new color
        return (json.dumps({'status': 'ok', 'color': detect_color}), "application/json", "200 OK")

    if path == MODULE_ROUTE + "/status":
        return (json.dumps({'active': calibration_active, 'pixel': current_pixel, 'total': num}), "application/json", "200 OK")

    if path == MODULE_ROUTE + "/next":
        if not calibration_active or current_pixel >= num - 1:
            calibration_active = False
            light_pixel(-1)
            return (json.dumps({'status': 'complete', 'pixel': current_pixel, 'total': num}), "application/json", "200 OK")
        current_pixel += 1
        light_pixel(current_pixel)
        return (json.dumps({'status': 'next', 'pixel': current_pixel, 'total': num}), "application/json", "200 OK")

    if path == MODULE_ROUTE + "/prev":
        if calibration_active and current_pixel > 0:
            current_pixel -= 1
            light_pixel(current_pixel)
        return (json.dumps({'status': 'prev', 'pixel': current_pixel, 'total': num}), "application/json", "200 OK")

    # Set specific pixel: /goto?p=123
    if path.startswith(MODULE_ROUTE + "/goto"):
        p = int(path.split('p=')[1].split('&')[0]) if 'p=' in path else 0
        if 0 <= p < num:
            current_pixel = p
            calibration_active = True
            light_pixel(current_pixel)
        return (json.dumps({'status': 'goto', 'pixel': current_pixel, 'total': num}), "application/json", "200 OK")

    if path == MODULE_ROUTE + "/stop":
        calibration_active = False
        light_pixel(-1)
        return (json.dumps({'status': 'stopped'}), "application/json", "200 OK")

    if path == MODULE_ROUTE + "/blink":
        light_pixel(current_pixel)
        time.sleep(0.3)
        light_pixel(-1)
        time.sleep(0.2)
        light_pixel(current_pixel)
        return (json.dumps({'status': 'ok'}), "application/json", "200 OK")

    if path == MODULE_ROUTE + "/upload" and method == "POST":
        try:
            data = params.get('data', '{}')
            with open(COORDS_FILE, 'w') as f:
                f.write(data)
            return (json.dumps({'status': 'saved', 'size': len(data)}), "application/json", "200 OK")
        except Exception as e:
            return (json.dumps({'error': str(e)}), "application/json", "500 Error")

    if path == MODULE_ROUTE + "/download":
        try:
            with open(COORDS_FILE, 'r') as f:
                return (f.read(), "application/json", "200 OK")
        except:
            return ('{}', "application/json", "200 OK")

    return ("Not Found", "text/plain", "404 Not Found")
