import serial.tools.list_ports
import time

VID_LIST = [0x1A86, 12619]
PID_LIST = [0xFE01]


def find_device_by_vid_pid(target_vid_list=VID_LIST, target_pid_list=PID_LIST):
    while True:
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port.vid in target_vid_list and port.pid in target_pid_list:
                print(f"[INFO] Found device: {port.device}")
                return port.device
        print("[WAIT] Waiting for USB device to be connected...")
        time.sleep(1)  # Wait before retrying
