import argparse
import os
import serial
import serial.tools.list_ports
import time

from util.jpeg_stream_player import JpegStreamPlayer
from util.raw_image import RawImage

VID = 0x1A86
PID = 0xFE01

JPEG_SOI = b"\xff\xd8"  # JPEG start-of-image marker
JPEG_EOF = b"\xff\xd9"  # JPEG end-of-file marker

RAW_TIMEOUT = 1.0  # 1 second

OUTPUT_DIR = "DCIM"


def find_device_by_vid_pid(target_vid, target_pid):
    while True:
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port.vid == target_vid and port.pid == target_pid:
                print(f"[INFO] Found device: {port.device}")
                return port.device
        print("[WAIT] Waiting for USB device to be connected...")
        time.sleep(1)  # Wait before retrying


def save_image(buffer):
    # Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # filename format is "FrameCam_YYYYMMDD_HHMMSS.jpg"
    current_time = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{OUTPUT_DIR}/FrameCam_{current_time}.jpg"

    with open(filename, "wb") as f:
        f.write(buffer)

    print(f"[INFO] Image saved as {filename}")


def read_images_loop(com=None, video=False, single=False, raw=False):
    if video:
        player = JpegStreamPlayer()
        player.start()

    while True:
        try:
            if not com:
                com = find_device_by_vid_pid(VID, PID)

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
                timeout=0,  # no read timeout
            )

            if video or single:
                # Send 'S' character to request the first frame
                ser.write(b"S")
                print("[INFO] Sent 'S' to device, waiting for snapshot to be done...")

            buffer = bytearray()
            start_time = None
            last_read_time = None
            while True:
                chunk = ser.read(2048)
                if not chunk:
                    if raw and len(buffer) > 0 and last_read_time is not None and (time.time() - last_read_time) > RAW_TIMEOUT:
                        # Raw image ready by timeout
                        print(f"[INFO] Raw image ready by timeout ({len(buffer)} bytes)")

                        end_time = time.time()
                        mbps = len(buffer) * 8 / ((end_time - start_time) * 1024 * 1024)
                        print(f"[INFO] Transmission speed: {mbps:.2f}mbit/s")

                        # Debug save raw buffer
                        # with open("DCIM/image.raw", "wb") as f:
                        #     f.write(buffer)

                        # Convert to JPEG
                        raw_image = RawImage(buffer, width=1920, height=1080, interleaving=8)
                        jpeg_data = raw_image.convert_to_jpeg()

                        # Save image
                        save_image(jpeg_data)

                        buffer.clear()
                        start_time = None
                        last_read_time = None

                    continue

                last_read_time = time.time()

                if start_time is None:
                    start_time = last_read_time

                # print(f"[INFO] Received {len(chunk)} bytes, buffer size: {len(buffer)}.")

                buffer.extend(chunk)

                if raw:
                    continue

                eof_pos = buffer.find(JPEG_EOF)
                if eof_pos != -1:
                    print("[INFO] JPEG EOF detected")

                    soi_pos = buffer.find(JPEG_SOI)
                    if soi_pos != -1:
                        end_time = time.time()
                        mbps = len(buffer) * 8 / ((end_time - start_time) * 1024 * 1024)
                        print(f"[INFO] Transmission speed: {mbps:.2f}mbit/s")

                        jpeg_data = buffer[soi_pos : eof_pos + 2]
                        if not video:
                            save_image(jpeg_data)
                        else:
                            player.show_next_frame(jpeg_data)
                    else:
                        print("[WARN] JPEG SOI not found. Skipping image...")

                    buffer.clear()
                    start_time = None
                    last_read_time = None

                    if video:
                        # Send 'S' character to request the next frame
                        ser.write(b"S")
                        print("[INFO] Sent 'S' to device, waiting for snapshot to be done...")
                    elif single:
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

            if video:
                player.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FrameCam USB image reader")
    parser.add_argument("-com", metavar="PORT", help="Specify COM port (e.g., COM3)")
    parser.add_argument("-video", action="store_true", help="Play video stream")
    parser.add_argument("-single", action="store_true", help="Read single image")
    parser.add_argument("-raw", action="store_true", help="Read raw image")

    args = parser.parse_args()

    read_images_loop(**vars(args))
