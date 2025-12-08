# Breathing effect - smooth pulsing light
import time
import math

NAME = "Breathing"
DESCRIPTION = "Smooth breathing pulse"
DELAY = 0.02


def apply_brightness(color, brightness):
    factor = brightness / 100.0
    r, g, b = color
    return (int(g * factor), int(r * factor), int(b * factor))


def run(strip, num_leds, brightness, session_id, check_stop):
    # Colors to breathe through
    colors = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green
        (0, 0, 255),    # Blue
        (255, 0, 255),  # Purple
        (0, 255, 255),  # Cyan
    ]

    for color in colors:
        if check_stop(session_id):
            return False

        # Breathe in (0 to 100)
        for level in range(0, 101, 2):
            if check_stop(session_id):
                return False

            factor = level / 100.0
            r = int(color[0] * factor)
            g = int(color[1] * factor)
            b = int(color[2] * factor)
            c = apply_brightness((r, g, b), brightness)

            for i in range(num_leds):
                strip[i] = c
            strip.write()
            time.sleep(DELAY)

        # Breathe out (100 to 0)
        for level in range(100, -1, -2):
            if check_stop(session_id):
                return False

            factor = level / 100.0
            r = int(color[0] * factor)
            g = int(color[1] * factor)
            b = int(color[2] * factor)
            c = apply_brightness((r, g, b), brightness)

            for i in range(num_leds):
                strip[i] = c
            strip.write()
            time.sleep(DELAY)

    return True
