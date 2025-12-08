# Meteor effect - falling star with tail
import time
import random

NAME = "Meteor"
DESCRIPTION = "Falling meteor with glowing tail"
DELAY = 0.03
METEOR_SIZE = 8
TRAIL_DECAY = 64


def apply_brightness(color, brightness):
    factor = brightness / 100.0
    r, g, b = color
    return (int(g * factor), int(r * factor), int(b * factor))


def fade_pixel(strip, i, decay):
    """Fade pixel by decay amount"""
    g, r, b = strip[i]
    r = (r * decay) // 256
    g = (g * decay) // 256
    b = (b * decay) // 256
    strip[i] = (g, r, b)


def run(strip, num_leds, brightness, session_id, check_stop):
    # Meteor color (white-blue)
    meteor_color = (200, 200, 255)

    for _ in range(4):  # 4 meteors
        if check_stop(session_id):
            return False

        # Clear strip
        for i in range(num_leds):
            strip[i] = (0, 0, 0)

        # Meteor falls down
        for pos in range(num_leds + METEOR_SIZE):
            if check_stop(session_id):
                return False

            # Fade all pixels (creates tail)
            for i in range(num_leds):
                if random.randint(0, 10) > 5:  # Random fade for sparkle
                    fade_pixel(strip, i, TRAIL_DECAY)

            # Draw meteor head
            for j in range(METEOR_SIZE):
                idx = pos - j
                if 0 <= idx < num_leds:
                    scale = 255 - (255 * j // METEOR_SIZE)
                    r = meteor_color[0] * scale // 255
                    g = meteor_color[1] * scale // 255
                    b = meteor_color[2] * scale // 255
                    strip[idx] = apply_brightness((r, g, b), brightness)

            strip.write()
            time.sleep(DELAY)

    return True
