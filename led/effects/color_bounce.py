# Color bounce effect - direct buffer access
import time
import micropython

NAME = "Color Bounce"
DESCRIPTION = "Bouncing LED with trail"

PARAMS = {
    'speed': {'name': 'Speed', 'type': 'int', 'min': 15, 'max': 60, 'default': 30},
    'fade_speed': {'name': 'Fade Speed', 'type': 'int', 'min': 15, 'max': 60, 'default': 30},
}
settings = {}


def get_param(name):
    if name in settings:
        return settings[name]
    return PARAMS[name]['default']


@micropython.native
def fade_and_render(buf, r, g, b, num, fade, factor):
    idx = 0
    for i in range(num):
        vr = r[i]
        vg = g[i]
        vb = b[i]
        r[i] = vr - fade if vr > fade else 0
        g[i] = vg - fade if vg > fade else 0
        b[i] = vb - fade if vb > fade else 0
        buf[idx] = (r[i] * factor) >> 8
        buf[idx + 1] = (g[i] * factor) >> 8
        buf[idx + 2] = (b[i] * factor) >> 8
        idx += 3


def run(strip, num_leds, brightness, session_id, check_stop):
    speed = get_param('speed')
    fade_speed = get_param('fade_speed')

    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
    color_idx = 0
    position = 0
    direction = 1 if num_leds < 200 else num_leds // 100

    leds_r = bytearray(num_leds)
    leds_g = bytearray(num_leds)
    leds_b = bytearray(num_leds)
    factor = int(brightness * 256 // 100)
    buf = strip.buf

    while True:
        if check_stop(session_id):
            return False

        color = colors[color_idx]
        leds_r[position] = color[0]
        leds_g[position] = color[1]
        leds_b[position] = color[2]

        fade_and_render(buf, leds_r, leds_g, leds_b, num_leds, fade_speed, factor)
        strip.write()

        position += direction
        if position >= num_leds - 1:
            position = num_leds - 1
            direction = -abs(direction)
            color_idx = (color_idx + 1) % len(colors)
        elif position <= 0:
            position = 0
            direction = abs(direction)
            color_idx = (color_idx + 1) % len(colors)

        time.sleep(speed / 1000.0)

    return True
