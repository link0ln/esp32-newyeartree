# Twinkle stars effect - direct buffer access
import time
import random
import micropython

NAME = "Twinkle Stars"
DESCRIPTION = "Random twinkling stars"

PARAMS = {
    'num_stars': {'name': 'Stars Count', 'type': 'int', 'min': 1, 'max': 15, 'default': 5},
    'fade_speed': {'name': 'Fade Speed', 'type': 'int', 'min': 5, 'max': 40, 'default': 15},
    'speed': {'name': 'Speed', 'type': 'int', 'min': 20, 'max': 100, 'default': 50},
}
settings = {}


def get_param(name):
    if name in settings:
        return settings[name]
    return PARAMS[name]['default']


@micropython.native
def update_and_render(buf, bright, direction, colors_r, colors_g, colors_b, num, fade, factor):
    idx = 0
    for i in range(num):
        d = direction[i]
        b = bright[i]
        if d == 1:
            b += fade
            if b >= 100:
                b = 100
                direction[i] = 2
            bright[i] = b
        elif d == 2:
            if b > fade:
                b -= fade
            else:
                b = 0
                direction[i] = 0
            bright[i] = b

        if b > 0:
            f = (b * factor) >> 8
            buf[idx] = (colors_r[i] * f) >> 8
            buf[idx + 1] = (colors_g[i] * f) >> 8
            buf[idx + 2] = (colors_b[i] * f) >> 8
        else:
            buf[idx] = 0
            buf[idx + 1] = 0
            buf[idx + 2] = 0
        idx += 3


def run(strip, num_leds, brightness, session_id, check_stop):
    num_stars = get_param('num_stars')
    fade_speed = get_param('fade_speed')
    delay = get_param('speed') / 1000.0

    colors = [(255, 200, 100), (200, 220, 255), (255, 180, 0), (180, 180, 200), (255, 0, 0), (0, 255, 0)]

    star_brightness = bytearray(num_leds)
    star_direction = bytearray(num_leds)
    colors_r = bytearray(num_leds)
    colors_g = bytearray(num_leds)
    colors_b = bytearray(num_leds)

    factor = int(brightness * 256 // 100)
    buf = strip.buf

    while True:
        if check_stop(session_id):
            return False

        for _ in range(num_stars):
            if random.random() < 0.1:
                pos = random.randint(0, num_leds - 1)
                if star_brightness[pos] == 0:
                    c = random.choice(colors)
                    colors_r[pos] = c[0]
                    colors_g[pos] = c[1]
                    colors_b[pos] = c[2]
                    star_direction[pos] = 1

        update_and_render(buf, star_brightness, star_direction, colors_r, colors_g, colors_b, num_leds, fade_speed, factor)
        strip.write()
        time.sleep(delay)
    return True
