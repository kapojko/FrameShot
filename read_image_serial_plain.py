import argparse
import time
import serial

OUTPUT_DIR = "DCIM"


def read_image(com_port):
    ser = serial.Serial(com_port, 115200, timeout=10)  # adjust port

    current_time = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{OUTPUT_DIR}/Cam_{current_time}.jpg"

    print(f"[INFO] Image will be saved as {filename}")

    total = 0
    with open(filename, "wb") as f:
        while True:
            data = ser.read(1024)
            if not data:
                break
            f.write(data)

            total += len(data)
            if total % 10240 == 0:  # every 10 KB
                print(f"\r{total/1024:.1f} KB received", end="")

    print(f"\nDone, total {total/1024:.1f} KB")

    ser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cam serial image reader")
    parser.add_argument("-com", metavar="PORT", help="Specify COM port (e.g., COM3)")

    args = parser.parse_args()

    read_image(com_port=args.com)
