import argparse
import serial
import os
import sys
import time

JPEG_EOF = b"\xff\xd9"  # JPEG end-of-file marker

OUTPUT_DIR = "DCIM"


def find_device():
    ports = serial.tools.list_ports.comports()
    if len(ports) == 0:
        print("[ERROR] No COM port found")
        sys.exit(1)

    return ports[0].device


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


def read_image(com_port=None):
    try:
        # Find device
        if not com_port:
            com_port = find_device()

        # Open serial port with the specified settings
        ser = serial.Serial(
            port=com_port,
            baudrate=460800,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0,  # no read timeout
        )
    except serial.SerialException as e:
        print(f"[ERROR] Could not open COM4: {e}")
        sys.exit(1)

    try:
        # Send 'S' character (start snapshot)
        ser.write(b"S")
        print("[INFO] Sent 'S' to device, waiting for snapshot to be done...")

        # Wait for 1 sec
        time.sleep(1)

        # Send 'T' character (transfer image)
        ser.write(b"T")
        print("[INFO] Sent 'T' to device, waiting for image...")

        # Read data until JPEG EOF marker
        buffer = bytearray()
        while True:
            chunk = ser.read(1024)
            if not chunk:
                print("[ERROR] Timeout or no data received.")
                break
            buffer.extend(chunk)
            if JPEG_EOF in buffer[-2:]:  # Efficient tail check
                print("[INFO] JPEG EOF detected.")
                break

        if JPEG_EOF not in buffer:
            print("[ERROR] JPEG EOF marker not found. Incomplete image.")
            sys.exit(1)

        # Trim buffer on JPEG EOF
        eof_pos = buffer.find(JPEG_EOF) + 2
        buffer = buffer[:eof_pos]

        # Save to image file
        save_image(buffer)

    except Exception as e:
        print(f"[ERROR] Communication failed: {e}")
        sys.exit(1)
    finally:
        ser.close()

    # 4. Open image with default Windows viewer
    try:
        os.startfile("image.jpg")
        print("[INFO] Opening image viewer...")
    except Exception as e:
        print(f"[ERROR] Failed to open image viewer: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FrameCam serial image reader")
    parser.add_argument("-com", metavar="PORT", help="Specify COM port (e.g., COM3)")

    args = parser.parse_args()

    read_image(com_port=args.com)
