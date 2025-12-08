# Falling snow effect with smooth trails
import time
import random

NAME = "Falling Snow"
DESCRIPTION = "Gentle falling snowflakes with trails"
DELAY = 0.04
NUM_FLAKES = 5


def apply_brightness(color, brightness):
    factor = brightness / 100.0
    r, g, b = color
    return (int(g * factor), int(r * factor), int(b * factor))


def run(strip, num_leds, brightness, session_id, check_stop):
    # Snowflakes list: pos (float), speed, intensity
    flakes = []

    # LED buffer for smooth fading trails
    leds = [[0, 0, 0] for _ in range(num_leds)]

    # Dark blue background
    bg_r, bg_g, bg_b = 0, 0, 15

    for _ in range(300):
        if check_stop(session_id):
            return False

        # Fade all LEDs towards background (creates trail effect)
        fade_speed = 35  # Faster fade = shorter trail
        for i in range(num_leds):
            # Fade R
            if leds[i][0] > bg_r:
                leds[i][0] = max(bg_r, leds[i][0] - fade_speed)
            # Fade G
            if leds[i][1] > bg_g:
                leds[i][1] = max(bg_g, leds[i][1] - fade_speed)
            # Fade B
            if leds[i][2] > bg_b:
                leds[i][2] = max(bg_b, leds[i][2] - fade_speed)

        # Spawn new flakes randomly
        if random.random() < 0.25 and len(flakes) < NUM_FLAKES:
            flakes.append({
                'pos': 0.0,
                'speed': random.uniform(0.6, 1.4),  # Faster movement
                'intensity': random.randint(180, 255)
            })

        # Update and draw snowflakes
        new_flakes = []
        for flake in flakes:
            flake['pos'] += flake['speed']
            pos = flake['pos']
            intensity = flake['intensity']

            # Calculate sub-pixel position for smooth movement
            pos_int = int(pos)
            pos_frac = pos - pos_int  # 0.0 to 1.0

            if pos_int < num_leds:
                # Draw gradient trail behind the snowflake
                trail_len = 2

                for t in range(trail_len):
                    trail_pos = pos_int - t
                    if 0 <= trail_pos < num_leds:
                        # Gradient falloff: brighter at head, dimmer at tail
                        if t == 0:
                            # Head pixel - blend based on fractional position
                            level = int(intensity * (1.0 - pos_frac * 0.3))
                        else:
                            # Trail pixels - exponential falloff
                            level = int(intensity * (0.7 ** t))

                        # Add to LED buffer (don't replace, add for overlapping flakes)
                        leds[trail_pos][0] = min(255, max(leds[trail_pos][0], level))
                        leds[trail_pos][1] = min(255, max(leds[trail_pos][1], level))
                        leds[trail_pos][2] = min(255, max(leds[trail_pos][2], level + 20))

                # Sub-pixel: light up next pixel partially
                next_pos = pos_int + 1
                if next_pos < num_leds:
                    next_level = int(intensity * pos_frac * 0.8)
                    leds[next_pos][0] = min(255, max(leds[next_pos][0], next_level))
                    leds[next_pos][1] = min(255, max(leds[next_pos][1], next_level))
                    leds[next_pos][2] = min(255, max(leds[next_pos][2], next_level + 10))

                new_flakes.append(flake)

        flakes = new_flakes

        # Write to strip
        for i in range(num_leds):
            strip[i] = apply_brightness(tuple(leds[i]), brightness)

        strip.write()
        time.sleep(DELAY)

    return True
