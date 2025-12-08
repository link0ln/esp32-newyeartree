# Police lights effect - emergency flashers
import time

NAME = "Police"
DESCRIPTION = "Red and blue police lights"
DELAY = 0.05


def apply_brightness(color, brightness):
    factor = brightness / 100.0
    r, g, b = color
    return (int(g * factor), int(r * factor), int(b * factor))


def run(strip, num_leds, brightness, session_id, check_stop):
    red = apply_brightness((255, 0, 0), brightness)
    blue = apply_brightness((0, 0, 255), brightness)
    off = (0, 0, 0)

    half = num_leds // 2

    for _ in range(20):  # 20 cycles
        if check_stop(session_id):
            return False

        # Red side flash (3 quick flashes)
        for flash in range(3):
            if check_stop(session_id):
                return False

            # Red on left
            for i in range(half):
                strip[i] = red
            for i in range(half, num_leds):
                strip[i] = off
            strip.write()
            time.sleep(DELAY)

            # All off
            for i in range(num_leds):
                strip[i] = off
            strip.write()
            time.sleep(DELAY)

        # Blue side flash (3 quick flashes)
        for flash in range(3):
            if check_stop(session_id):
                return False

            # Blue on right
            for i in range(half):
                strip[i] = off
            for i in range(half, num_leds):
                strip[i] = blue
            strip.write()
            time.sleep(DELAY)

            # All off
            for i in range(num_leds):
                strip[i] = off
            strip.write()
            time.sleep(DELAY)

    return True
