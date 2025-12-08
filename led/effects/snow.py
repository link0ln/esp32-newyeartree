# Falling snow effect - direct buffer access for speed
import time
import random
import micropython

NAME = "Falling Snow"
DESCRIPTION = "Gentle falling snowflakes with trails"

PARAMS = {
    'num_flakes': {'name': 'Snowflakes', 'type': 'int', 'min': 1, 'max': 15, 'default': 5},
    'trail_len': {'name': 'Trail Length', 'type': 'int', 'min': 1, 'max': 6, 'default': 2},
    'fade_speed': {'name': 'Fade Speed', 'type': 'int', 'min': 10, 'max': 80, 'default': 35},
    'speed_min': {'name': 'Min Speed', 'type': 'float', 'min': 0.2, 'max': 1.5, 'default': 0.6},
    'speed_max': {'name': 'Max Speed', 'type': 'float', 'min': 0.5, 'max': 3.0, 'default': 1.4},
    'spawn_rate': {'name': 'Spawn Rate', 'type': 'int', 'min': 5, 'max': 50, 'default': 25},
}
settings = {}


def get_param(name):
    if name in settings:
        return settings[name]
    return PARAMS[name]['default']


@micropython.native
def fade_and_render(buf, leds_r, leds_g, leds_b, num, fade, bg_b, factor):
    """Fade LEDs and write directly to NeoPixel buffer"""
    idx = 0
    for i in range(num):
        # Fade R
        vr = leds_r[i]
        if vr > fade:
            vr -= fade
        else:
            vr = 0
        leds_r[i] = vr

        # Fade G
        vg = leds_g[i]
        if vg > fade:
            vg -= fade
        else:
            vg = 0
        leds_g[i] = vg

        # Fade B
        vb = leds_b[i]
        if vb > bg_b + fade:
            vb -= fade
        elif vb > bg_b:
            vb = bg_b
        leds_b[i] = vb

        # Write to NeoPixel buffer (RGB order)
        buf[idx] = (vr * factor) >> 8      # R
        buf[idx + 1] = (vg * factor) >> 8  # G
        buf[idx + 2] = (vb * factor) >> 8  # B
        idx += 3


def run(strip, num_leds, brightness, session_id, check_stop):
    num_flakes = get_param('num_flakes')
    trail_len = get_param('trail_len')
    fade_speed = get_param('fade_speed')
    speed_min = get_param('speed_min')
    speed_max = get_param('speed_max')
    spawn_rate = get_param('spawn_rate')

    # Scale for large strips
    if num_leds > 100:
        num_flakes = max(num_flakes, num_leds // 30)
        speed_max = speed_max * (num_leds / 50)
        speed_min = speed_min * (num_leds / 50)

    leds_r = bytearray(num_leds)
    leds_g = bytearray(num_leds)
    leds_b = bytearray(num_leds)
    bg_b = 15
    factor = int(brightness * 256 // 100)

    # Direct access to NeoPixel buffer
    buf = strip.buf

    flakes = []
    sleep_time = 0.005 if num_leds > 300 else 0.015

    while True:
        if check_stop(session_id):
            return False

        # Spawn
        if random.randint(0, 100) < spawn_rate and len(flakes) < num_flakes:
            flakes.append([0.0, random.uniform(speed_min, speed_max), random.randint(180, 255)])

        # Update flakes - draw to LED buffers
        new_flakes = []
        for f in flakes:
            f[0] += f[1]
            p = int(f[0])
            if p < num_leds:
                if 0 <= p:
                    leds_r[p] = f[2]
                    leds_g[p] = f[2]
                    leds_b[p] = f[2]
                for t in range(1, trail_len):
                    tp = p - t
                    if 0 <= tp < num_leds:
                        lv = f[2] >> t
                        if leds_r[tp] < lv:
                            leds_r[tp] = lv
                        if leds_g[tp] < lv:
                            leds_g[tp] = lv
                        if leds_b[tp] < lv:
                            leds_b[tp] = lv
                new_flakes.append(f)
        flakes = new_flakes

        # Fade and render directly to buffer (native optimized)
        fade_and_render(buf, leds_r, leds_g, leds_b, num_leds, fade_speed, bg_b, factor)
        strip.write()
        time.sleep(sleep_time)

    return True
