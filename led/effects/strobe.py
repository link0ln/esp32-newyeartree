# Strobe effect - fast flashing
import time
import random

NAME = "Strobe"
DESCRIPTION = "Strobe flash effect"
DELAY = 0.05


def apply_brightness(color, brightness):
    factor = brightness / 100.0
    r, g, b = color
    return (int(g * factor), int(r * factor), int(b * factor))


def run(strip, num_leds, brightness, session_id, check_stop):
    # Colors to strobe through
    colors = [
        (255, 255, 255),  # White
        (255, 0, 0),      # Red
        (0, 255, 0),      # Green
        (0, 0, 255),      # Blue
    ]

    color_idx = 0
    flash_count = 0

    for _ in range(200):
        if check_stop(session_id):
            return False

        color = colors[color_idx]

        # Flash on
        for i in range(num_leds):
            strip[i] = apply_brightness(color, brightness)
        strip.write()
        time.sleep(0.05)

        # Flash off
        for i in range(num_leds):
            strip[i] = (0, 0, 0)
        strip.write()
        time.sleep(0.05)

        flash_count += 1

        # Change color every few flashes
        if flash_count >= 5:
            flash_count = 0
            color_idx = (color_idx + 1) % len(colors)

        # Random pause sometimes
        if random.randint(0, 10) < 2:
            time.sleep(0.1)

    return True
