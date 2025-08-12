import argparse
import os

import cv2
import numpy as np
import serial
import time

from util.buffer_image import BufferImage
from util.device import find_device_by_vid_pid
from util.jpeg_stream_player import JpegStreamPlayer
from util.raw_image import RawImage
from util.snapshot_header import SnapshotHeader

RESET_CMD = b"R"
SNAPSHOT_CMD = b"S"
TRANSFER_CMD = b"T"


def read_images_loop(com=None, format="jpeg", vflip=False, hflip=False):
    player = None

    while True:
        try:
            if not com:
                com = find_device_by_vid_pid()

                if not com:
                    print("[ERROR] No FrameCam device found")
                    time.sleep(1)
                    continue

            print(f"[INFO] Opening serial port {com}...")
            ser = serial.Serial(
                port=com,
                baudrate=460800,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0,  # 1 sec
            )

            # Start video player
            if not player:
                player = JpegStreamPlayer()
                player.start()

            # Send reset command
            ser.write(RESET_CMD)
            print(f"[INFO] Sent '{RESET_CMD.decode()}' to device, waiting for reset data...")

            # Wait for 1 sec
            time.sleep(1)

            # Read data loop
            buffer = bytearray()
            while True:
                # Send snapshot command
                ser.write(SNAPSHOT_CMD)
                print(f"[INFO] Sent '{SNAPSHOT_CMD.decode()}' to device, waiting for snapshot to be done...")

                # Read snapshot header (16 byte)
                header_data = ser.read(16)
                if not header_data:
                    print("[ERROR] Could not read snapshot header")
                    time.sleep(1)
                    continue

                # Parse snapshot
                snapshot_header = SnapshotHeader(header_data)
                if not snapshot_header.valid():
                    print("[ERROR] Invalid snapshot header")
                    time.sleep(1)
                    continue

                # Start image transfer
                ser.write(TRANSFER_CMD)
                print(f"[INFO] Sent '{TRANSFER_CMD.decode()}' to device, waiting for image...")

                # Read image
                start_time = time.time()
                image_data = ser.read(snapshot_header.image_size)
                if not image_data:
                    print("[ERROR] Could not read image")
                    time.sleep(1)
                    continue

                # Calculate transmission time
                end_time = time.time()
                kb = len(image_data) / 1024
                mbps = len(image_data) * 8 / ((end_time - start_time) * 1024 * 1024)
                print(f"[INFO] Transfer done, {kb:.1f}kb, speed: {mbps:.2f}mbit/s")

                buffer_image = BufferImage(image_data)

                # Flip image
                if hflip or vflip:
                    buffer_image.flip(hflip, vflip)

                # Save image
                if player.save_next_frame:
                    buffer_image.save(format)

                # Show image
                player.show_next_frame(image_data)

                # Check for video to be closed
                if not player.running:
                    print("[INFO] Video closed by user. Exiting...")
                    return

        except KeyboardInterrupt:
            print("[INFO] Exiting...")
            return
        except Exception as e:
            print(f"[ERROR] {e}. Restarting in 1 second...")
            time.sleep(1)
        finally:
            try:
                if "ser" in locals() and ser.is_open:
                    ser.close()
                    buffer.clear()
                    print(f"[INFO] Serial port {com} closed.")
            except Exception as e:
                print(f"[WARN] Could not close serial port cleanly: {e}")
            com = None  # Re-trigger device search on next loop

            player.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FrameCam USB image reader")
    parser.add_argument("-com", metavar="PORT", help="Specify COM port (e.g., COM3)")
    parser.add_argument("-format", metavar="FORMAT", default="jpeg", help="Raw image save format")
    parser.add_argument("-vflip", action="store_true", help="Horizontal flip")
    parser.add_argument("-hflip", action="store_true", help="Vertical flip")

    args = parser.parse_args()

    read_images_loop(**vars(args))
