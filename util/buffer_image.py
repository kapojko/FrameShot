import os
import time

import cv2
import numpy as np

OUTPUT_DIR = "DCIM"


class BufferImage:
    def __init__(self, buffer, output_dir=OUTPUT_DIR):
        self.buffer = buffer
        self.output_dir = output_dir

    def save(self, format="jpeg"):
        # Create output directory if it doesn't exist
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)

        # Select file extension
        if format == "jpeg":
            ext = "jpg"
        else:
            ext = format

        # filename format is "FrameCam_YYYYMMDD_HHMMSS.EXT"
        current_time = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/FrameCam_{current_time}.{ext}"

        with open(filename, "wb") as f:
            f.write(self.buffer)

        print(f"[INFO] Image saved as {filename}")
        return filename

    def flip(self, hflip=False, vflip=False):
        image_array = cv2.imdecode(np.frombuffer(self.buffer, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image_array is not None:
            if hflip:
                image_array = cv2.flip(image_array, 1)
            if vflip:
                image_array = cv2.flip(image_array, 0)
            _, encoded_image = cv2.imencode(".jpg", image_array)
            self.buffer = encoded_image.tobytes()

        return self.buffer
