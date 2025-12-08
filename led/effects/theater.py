# Theater Chase effect - marquee style lights
import time

NAME = "Theater Chase"
DESCRIPTION = "Classic marquee lights"
DELAY = 0.08


def apply_brightness(color, brightness):
    factor = brightness / 100.0
    r, g, b = color
    return (int(g * factor), int(r * factor), int(b * factor))


def run(strip, num_leds, brightness, session_id, check_stop):
    colors = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green
        (0, 0, 255),    # Blue
        (255, 255, 0),  # Yellow
        (255, 255, 255) # White
    ]

    for color in colors:
        if check_stop(session_id):
            return False

        # 10 cycles per color
        for _ in range(10):
            # 3 positions in the chase pattern
            for q in range(3):
                if check_stop(session_id):
                    return False

                # Turn off all pixels
                for i in range(num_leds):
                    strip[i] = (0, 0, 0)

                # Light every 3rd pixel
                for i in range(0, num_leds, 3):
                    idx = i + q
                    if idx < num_leds:
                        strip[idx] = apply_brightness(color, brightness)

                strip.write()
                time.sleep(DELAY)

    return True
