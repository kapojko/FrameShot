import numpy as np
import cv2

from util.image_proc import ImageProc
from util.snapshot_header import SnapshotFormat


class RawImage:
    def __init__(self, buffer, format, width, height, interleaving=None):
        # NOTE: format is raw Bayer GRBG, 8-bit
        self.buffer = buffer
        self.format = format
        self.width = width
        self.height = height
        self.interleaving = interleaving

    def deinterleave(bayer_interleaved, interleaving):
        height, _ = bayer_interleaved.shape
        deinterleaved = np.empty_like(bayer_interleaved)

        interleaving_height = height // interleaving
        for i in range(interleaving):
            # lines where (original_y % interleaving == i) go to lines starting from i with step 8
            deinterleaved[i::interleaving] = bayer_interleaved[i * interleaving_height : (i + 1) * interleaving_height : 1]

        return deinterleaved

    def horizontal_flip(self):
        flipped_buffer = bytearray(len(self.buffer))
        for y in range(self.height):
            for x in range(self.width):
                flipped_buffer[y * self.width + (self.width - 1 - x)] = self.buffer[y * self.width + x]
        return RawImage(flipped_buffer, self.width, self.height, self.interleaving)

    def vertical_flip(self):
        flipped_buffer = bytearray(len(self.buffer))
        for y in range(self.height):
            for x in range(self.width):
                flipped_buffer[(self.height - 1 - y) * self.width + x] = self.buffer[y * self.width + x]
        return RawImage(flipped_buffer, self.width, self.height, self.interleaving)

    def to_image(self):
        # Convert buffer to 2D numpy array (grayscale image)
        bayer_image = np.frombuffer(self.buffer, dtype=np.uint8).reshape((self.height, self.width))

        # Deinterleave
        if self.interleaving:
            bayer_image = RawImage.deinterleave(bayer_image, self.interleaving)

        # Demosaic the GRBG Bayer pattern to BGR
        # OpenCV uses BGR by default
        # see: https://docs.opencv.org/4.x/de/d25/imgproc_color_conversions.html#color_convert_bayer
        if self.format == SnapshotFormat.RAW_GRBG8:
            bgr_image = cv2.cvtColor(bayer_image, cv2.COLOR_BayerRGGB2BGR)
        elif self.format == SnapshotFormat.RAW_BGGR8:
            bgr_image = cv2.cvtColor(bayer_image, cv2.COLOR_BayerBGGR2BGR)
        else:
            raise ValueError(f"Unsupported raw image format: {self.format}")

        # Apply AWB and gamma-correction
        # image_proc = ImageProc(bgr_image)
        # image_proc.auto_white_balance()
        # image_proc.gamma_correction()
        # proc_image = image_proc.img

        proc_image = bgr_image

        return proc_image

    def to_jpeg(self):
        bgr_image = self.to_image()

        # Convert to JPEG
        _, jpeg_buffer = cv2.imencode(".jpg", bgr_image)

        return jpeg_buffer

    def to_png(self):
        bgr_image = self.to_image()

        # Convert to PNG
        _, png_buffer = cv2.imencode(".png", bgr_image)

        return png_buffer
