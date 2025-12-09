# Solid color effect
import time
import micropython

NAME = "Solid Color"
DESCRIPTION = "Single solid color"

PARAMS = {
    'color': {'name': 'Color', 'type': 'color', 'min': 0, 'max': 0, 'default': '#ff0000'},
}
settings = {}


def get_param(name):
    if name in settings:
        return settings[name]
    return PARAMS[name]['default']


def parse_color(hex_color):
    """Parse hex color string like '#ff0000' to (r, g, b)"""
    try:
        if hex_color.startswith('#'):
            hex_color = hex_color[1:]
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (r, g, b)
    except:
        return (255, 0, 0)  # Default red


@micropython.native
def fill_solid(buf, num, r, g, b, factor):
    idx = 0
    rf = (r * factor) >> 8
    gf = (g * factor) >> 8
    bf = (b * factor) >> 8
    for i in range(num):
        buf[idx] = rf
        buf[idx + 1] = gf
        buf[idx + 2] = bf
        idx += 3


def run(strip, num_leds, brightness, session_id, check_stop):
    color_hex = get_param('color')
    r, g, b = parse_color(color_hex)
    factor = int(brightness * 256 // 100)
    buf = strip.buf
    last_color = None

    while True:
        if check_stop(session_id):
            return False

        # Check if color changed
        current_color = get_param('color')
        if current_color != last_color:
            r, g, b = parse_color(current_color)
            last_color = current_color

        fill_solid(buf, num_leds, r, g, b, factor)
        strip.write()
        time.sleep(0.1)
