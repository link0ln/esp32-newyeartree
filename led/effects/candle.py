# Candle effect - direct buffer access
import time
import random
import micropython

NAME = "Candle"
DESCRIPTION = "Realistic candle flicker"

PARAMS = {
    'flicker_min': {'name': 'Min Brightness', 'type': 'int', 'min': 100, 'max': 200, 'default': 150},
    'flicker_max': {'name': 'Max Brightness', 'type': 'int', 'min': 200, 'max': 255, 'default': 255},
    'gust_chance': {'name': 'Gust Chance', 'type': 'int', 'min': 0, 'max': 30, 'default': 10},
    'variation': {'name': 'LED Variation', 'type': 'int', 'min': 0, 'max': 50, 'default': 20},
}
settings = {}


def get_param(name):
    if name in settings:
        return settings[name]
    return PARAMS[name]['default']


@micropython.native
def render_candle(buf, num, base_r, base_g, factor, variation):
    idx = 0
    for i in range(num):
        var = ((i * 13 + base_r) % (variation * 2 + 1)) - variation
        pr = base_r + var
        pg = base_g + (var >> 1)
        if pr < 0: pr = 0
        if pr > 255: pr = 255
        if pg < 0: pg = 0
        if pg > 255: pg = 255
        buf[idx] = (pr * factor) >> 8
        buf[idx + 1] = (pg * factor) >> 8
        buf[idx + 2] = 0
        idx += 3


def run(strip, num_leds, brightness, session_id, check_stop):
    flicker_min = get_param('flicker_min')
    flicker_max = get_param('flicker_max')
    gust_chance = get_param('gust_chance')
    variation = get_param('variation')

    factor = int(brightness * 256 // 100)
    buf = strip.buf

    while True:
        if check_stop(session_id):
            return False

        random_bright = random.randint(flicker_min, flicker_max)
        if random.randint(0, 100) < gust_chance:
            random_bright = random.randint(50, 120)

        r = random_bright
        g = int(random_bright * 0.4)

        render_candle(buf, num_leds, r, g, factor, variation)
        strip.write()
        time.sleep(random.randint(10, 80) / 1000.0)

    return True
