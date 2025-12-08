# Bouncing balls effect - physics-based bouncing
import time
import random

NAME = "Bouncing"
DESCRIPTION = "Bouncing balls with gravity"
DELAY = 0.02


def apply_brightness(color, brightness):
    factor = brightness / 100.0
    r, g, b = color
    return (int(g * factor), int(r * factor), int(b * factor))


def run(strip, num_leds, brightness, session_id, check_stop):
    num_balls = 3
    gravity = -0.5
    start_height = 1

    # Ball colors (RGB)
    colors = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green
        (0, 0, 255),    # Blue
    ]

    # Initialize balls
    balls = []
    for i in range(num_balls):
        balls.append({
            'height': start_height,
            'impact_vel': 2.5,
            'pos': 0,
            'clock': 0,
            'damping': 0.9 - (i * 0.05),
            'color': colors[i % len(colors)]
        })

    for _ in range(500):
        if check_stop(session_id):
            return False

        # Clear strip
        for i in range(num_leds):
            strip[i] = (0, 0, 0)

        for ball in balls:
            ball['clock'] += 1

            # Calculate new height
            ball['height'] = (
                0.5 * gravity * (ball['clock'] ** 2) +
                ball['impact_vel'] * ball['clock']
            )

            # Ball hit ground?
            if ball['height'] < 0:
                ball['height'] = 0
                ball['impact_vel'] = ball['damping'] * ball['impact_vel']
                ball['clock'] = 0

                # Re-randomize if almost stopped
                if ball['impact_vel'] < 0.5:
                    ball['impact_vel'] = 2.0 + random.random()
                    ball['damping'] = 0.85 + random.random() * 0.1

            # Map height to LED position
            ball['pos'] = int(ball['height'] * (num_leds - 1))
            if ball['pos'] >= num_leds:
                ball['pos'] = num_leds - 1

            # Set LED color
            strip[ball['pos']] = apply_brightness(ball['color'], brightness)

        strip.write()
        time.sleep(DELAY)

    return True
