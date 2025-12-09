# Snow sparkle - direct buffer access
import time
import random
import micropython

NAME = "Snow Sparkle"
DESCRIPTION = "Sparkling snow effect"

PARAMS = {
    'color': {'name': 'Background', 'type': 'color', 'min': 0, 'max': 0, 'default': '#101040'},
    'sparkle_min': {'name': 'Min Sparkles', 'type': 'int', 'min': 1, 'max': 5, 'default': 1},
    'sparkle_max': {'name': 'Max Sparkles', 'type': 'int', 'min': 2, 'max': 10, 'default': 5},
    'delay_min': {'name': 'Min Delay (ms)', 'type': 'int', 'min': 10, 'max': 80, 'default': 20},
    'delay_max': {'name': 'Max Delay (ms)', 'type': 'int', 'min': 50, 'max': 150, 'default': 100},
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
        return (16, 16, 64)  # Default bluish


@micropython.native
def fill_bg(buf, num, bg_r, bg_g, bg_b):
    idx = 0
    for i in range(num):
        buf[idx] = bg_r
        buf[idx + 1] = bg_g
        buf[idx + 2] = bg_b
        idx += 3


def run(strip, num_leds, brightness, session_id, check_stop):
    color_hex = get_param('color')
    sparkle_min = get_param('sparkle_min')
    sparkle_max = get_param('sparkle_max')
    delay_min = get_param('delay_min')
    delay_max = get_param('delay_max')

    cr, cg, cb = parse_color(color_hex)
    factor = brightness / 100.0
    bg_r = int(cr * factor)
    bg_g = int(cg * factor)
    bg_b = int(cb * factor)
    sparkle_v = int(255 * factor)
    buf = strip.buf

    while True:
        if check_stop(session_id):
            return False

        fill_bg(buf, num_leds, bg_r, bg_g, bg_b)

        sparkle_positions = []
        for _ in range(random.randint(sparkle_min, sparkle_max)):
            pos = random.randint(0, num_leds - 1)
            sparkle_positions.append(pos)
            idx = pos * 3
            buf[idx] = sparkle_v
            buf[idx + 1] = sparkle_v
            buf[idx + 2] = sparkle_v

        strip.write()
        time.sleep(random.randint(delay_min, delay_max) / 1000.0)

        for pos in sparkle_positions:
            idx = pos * 3
            buf[idx] = bg_r
            buf[idx + 1] = bg_g
            buf[idx + 2] = bg_b

        strip.write()
        time.sleep(0.02)

    return True
