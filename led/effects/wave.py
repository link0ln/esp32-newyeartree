# Color Wave effect - flowing wave of color
import time
import math

NAME = "Color Wave"
DESCRIPTION = "Flowing wave of colors"
DELAY = 0.03


def apply_brightness(color, brightness):
    factor = brightness / 100.0
    r, g, b = color
    return (int(g * factor), int(r * factor), int(b * factor))


def run(strip, num_leds, brightness, session_id, check_stop):
    # Precompute sine table (0-255 values)
    sine_table = []
    for i in range(256):
        val = int((math.sin(i * 3.14159 * 2 / 256) + 1) * 127.5)
        sine_table.append(val)

    colors = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green
        (0, 0, 255),    # Blue
        (255, 128, 0),  # Orange
    ]

    for base_color in colors:
        if check_stop(session_id):
            return False

        for offset in range(256):
            if check_stop(session_id):
                return False

            for i in range(num_leds):
                # Calculate wave position
                wave_pos = (i * 256 // num_leds + offset) & 255
                wave_val = sine_table[wave_pos]

                # Apply wave to color
                r = base_color[0] * wave_val // 255
                g = base_color[1] * wave_val // 255
                b = base_color[2] * wave_val // 255

                strip[i] = apply_brightness((r, g, b), brightness)

            strip.write()
            time.sleep(DELAY)

    return True
