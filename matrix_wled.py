#!/usr/bin/env python3
"""
Matrix Rain Effect for WLED
Usage: python3 matrix_wled.py [--ip IP] [--leds NUM] [--duration SEC]
"""

import socket
import time
import random
import argparse

DEFAULT_IP = "192.168.1.88"
DEFAULT_PORT = 21324
DEFAULT_NUM_LEDS = 730
CHUNK_SIZE = 480  # Max LEDs per packet to stay under MTU

# Matrix parameters
TRAIL_LENGTH = 25
MIN_SPEED = 0.1
MAX_SPEED = 2


class Drop:
    def __init__(self, num_leds):
        self.num_leds = num_leds
        self.reset()

    def reset(self):
        self.pos = random.randint(-TRAIL_LENGTH * 2, 0)
        self.speed = random.uniform(MIN_SPEED, MAX_SPEED)
        self.brightness = random.randint(150, 255)

    def update(self):
        self.pos += self.speed
        if self.pos > self.num_leds + TRAIL_LENGTH:
            self.reset()


def send_frame(sock, ip, port, buffer, num_leds):
    """Send full frame in chunks using DNRGB protocol"""
    for start in range(0, num_leds, CHUNK_SIZE):
        end = min(start + CHUNK_SIZE, num_leds)
        # DNRGB mode (4): [4, timeout, start_hi, start_lo, R, G, B, ...]
        packet = bytearray([4, 2, start >> 8, start & 0xFF])
        for i in range(start, end):
            packet.extend(buffer[i])
        sock.sendto(packet, (ip, port))


def run_matrix(ip, port, num_leds, duration, num_drops):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    buffer = [[0, 0, 0] for _ in range(num_leds)]
    drops = [Drop(num_leds) for _ in range(num_drops)]

    print(f"Matrix Rain on WLED")
    print(f"  IP: {ip}:{port}")
    print(f"  LEDs: {num_leds}")
    print(f"  Duration: {duration}s")
    print(f"  Drops: {num_drops}")
    print()
    print("Press Ctrl+C to stop")
    print()

    start_time = time.time()
    frames = 0

    try:
        while time.time() - start_time < duration:
            frame_start = time.time()

            # Fade all LEDs (slower fade for longer trails)
            for i in range(num_leds):
                buffer[i] = [int(c * 0.92) for c in buffer[i]]

            # Update and draw drops
            for drop in drops:
                drop.update()
                head = int(drop.pos)

                # Draw head (bright white-green)
                if 0 <= head < num_leds:
                    buffer[head] = [
                        drop.brightness // 3,   # R
                        drop.brightness // 4,        # G (brightest)
                        drop.brightness // 1    # B
                    ]

                # Draw trail (pure green, fading)
                for t in range(1, TRAIL_LENGTH):
                    trail_pos = head - t
                    if 0 <= trail_pos < num_leds:
                        intensity = int(drop.brightness * (1 - t / TRAIL_LENGTH) * 0.6)
                        if intensity > buffer[trail_pos][1]:
                            buffer[trail_pos] = [0, intensity, 0]

            # Send frame in chunks
            send_frame(sock, ip, port, buffer, num_leds)
            frames += 1

            # Target ~30 FPS
            elapsed = time.time() - frame_start
            if elapsed < 0.033:
                time.sleep(0.033 - elapsed)

    except KeyboardInterrupt:
        print("\nStopped")

    total_time = time.time() - start_time
    print(f"\nStats: {frames} frames, {frames/total_time:.1f} FPS")
    sock.close()


def main():
    parser = argparse.ArgumentParser(description='Matrix Rain Effect for WLED')
    parser.add_argument('--ip', default=DEFAULT_IP)
    parser.add_argument('--port', type=int, default=DEFAULT_PORT)
    parser.add_argument('--leds', type=int, default=DEFAULT_NUM_LEDS)
    parser.add_argument('--duration', type=int, default=60)
    parser.add_argument('--drops', type=int, default=80)
    args = parser.parse_args()

    run_matrix(args.ip, args.port, args.leds, args.duration, args.drops)


if __name__ == "__main__":
    main()
