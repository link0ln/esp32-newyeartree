# Sparkle effect - random glittering stars
import time
import random

NAME = "Sparkle"
DESCRIPTION = "Random glittering sparkles"
DELAY = 0.02
SPARKLE_COUNT = 3
FADE_SPEED = 25


def apply_brightness(color, brightness):
    factor = brightness / 100.0
    r, g, b = color
    return (int(g * factor), int(r * factor), int(b * factor))


def run(strip, num_leds, brightness, session_id, check_stop):
    # Background color (dark blue)
    bg = apply_brightness((0, 0, 30), brightness)

    # Pixel brightness levels
    pixel_bright = [0] * num_leds

    for _ in range(150):
        if check_stop(session_id):
            return False

        # Add new sparkles
        for _ in range(SPARKLE_COUNT):
            if random.randint(0, 100) < 15:
                idx = random.randint(0, num_leds - 1)
                pixel_bright[idx] = 255

        # Update all pixels
        for i in range(num_leds):
            if pixel_bright[i] > 0:
                # Sparkle color (white/silver)
                level = pixel_bright[i]
                r = level
                g = level
                b = level
                strip[i] = apply_brightness((r, g, b), brightness)
                pixel_bright[i] = max(0, pixel_bright[i] - FADE_SPEED)
            else:
                strip[i] = bg

        strip.write()
        time.sleep(DELAY)

    return True
