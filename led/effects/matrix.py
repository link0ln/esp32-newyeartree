# Matrix effect - falling dots like The Matrix movie
import time
import random

NAME = "Matrix"
DESCRIPTION = "Matrix movie falling dots"
DELAY = 0.05


def apply_brightness(color, brightness):
    factor = brightness / 100.0
    r, g, b = color
    return (int(g * factor), int(r * factor), int(b * factor))


def run(strip, num_leds, brightness, session_id, check_stop):
    # Matrix green color
    matrix_color = (0, 255, 0)

    # Fade buffer for trails
    leds = [(0, 0, 0)] * num_leds

    # Active drops (position, speed, brightness)
    drops = []

    for _ in range(300):
        if check_stop(session_id):
            return False

        # Randomly spawn new drops
        if random.randint(0, 100) < 20 and len(drops) < num_leds // 3:
            drops.append({
                'pos': 0,
                'speed': random.randint(1, 3),
                'bright': random.randint(180, 255)
            })

        # Fade all LEDs
        new_leds = []
        for r, g, b in leds:
            new_leds.append((
                max(0, r - 20),
                max(0, g - 20),
                max(0, b - 20)
            ))
        leds = new_leds

        # Update drops
        active_drops = []
        for drop in drops:
            pos = int(drop['pos'])
            if pos < num_leds:
                # Set the drop pixel (bright green)
                leds[pos] = (0, drop['bright'], 0)
                drop['pos'] += drop['speed']
                if drop['pos'] < num_leds + 5:
                    active_drops.append(drop)
        drops = active_drops

        # Write to strip
        for i in range(num_leds):
            strip[i] = apply_brightness(leds[i], brightness)
        strip.write()

        time.sleep(DELAY)

    return True
