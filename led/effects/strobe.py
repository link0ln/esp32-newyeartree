# Strobe effect - direct buffer access
import time
import random
import micropython

NAME = "Strobe"
DESCRIPTION = "Strobe flash effect"

PARAMS = {
    'flash_on': {'name': 'Flash On (ms)', 'type': 'int', 'min': 20, 'max': 100, 'default': 50},
    'flash_off': {'name': 'Flash Off (ms)', 'type': 'int', 'min': 20, 'max': 100, 'default': 50},
    'flashes_per_color': {'name': 'Flashes/Color', 'type': 'int', 'min': 2, 'max': 10, 'default': 5},
}
settings = {}


def get_param(name):
    if name in settings:
        return settings[name]
    return PARAMS[name]['default']


@micropython.native
def fill_buf(buf, num, r, g, b):
    idx = 0
    for i in range(num):
        buf[idx] = r
        buf[idx + 1] = g
        buf[idx + 2] = b
        idx += 3


def run(strip, num_leds, brightness, session_id, check_stop):
    flash_on = get_param('flash_on')
    flash_off = get_param('flash_off')
    flashes_per_color = get_param('flashes_per_color')

    factor = brightness / 100.0
    colors = [(255, 255, 255), (255, 0, 0), (0, 255, 0), (0, 0, 255)]
    color_idx = 0
    flash_count = 0
    buf = strip.buf

    while True:
        if check_stop(session_id):
            return False

        c = colors[color_idx]
        fill_buf(buf, num_leds, int(c[0] * factor), int(c[1] * factor), int(c[2] * factor))
        strip.write()
        time.sleep(flash_on / 1000.0)

        fill_buf(buf, num_leds, 0, 0, 0)
        strip.write()
        time.sleep(flash_off / 1000.0)

        flash_count += 1
        if flash_count >= flashes_per_color:
            flash_count = 0
            color_idx = (color_idx + 1) % len(colors)

        if random.randint(0, 10) < 2:
            time.sleep(0.1)

    return True
