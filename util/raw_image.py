import numpy as np
import cv2


class RawImage:
    def __init__(self, buffer, width, height, interleaving=None):
        # NOTE: format is raw Bayer GRBG, 8-bit
        self.buffer = buffer
        self.width = width
        self.height = height
        self.interleaving = interleaving

    def deinterleave(bayer_interleaved, interleaving):
        height, _ = bayer_interleaved.shape
        deinterleaved = np.empty_like(bayer_interleaved)

        interleaving_height = height // interleaving
        for i in range(interleaving):
            # lines where (original_y % interleaving == i) go to lines starting from i with step 8
            deinterleaved[i::interleaving] = bayer_interleaved[i*interleaving_height:(i+1)*interleaving_height:1]

        return deinterleaved

    def convert_to_jpeg(self):
        # Convert buffer to 2D numpy array (grayscale image)
        bayer_image = np.frombuffer(self.buffer, dtype=np.uint8).reshape(
            (self.height, self.width)
        )

        # Deinterleave
        if self.interleaving:
            bayer_image = RawImage.deinterleave(bayer_image, self.interleaving)

        # Demosaic the GRBG Bayer pattern to BGR
        # OpenCV uses BGR by default
        bgr_image = cv2.cvtColor(bayer_image, cv2.COLOR_BayerBG2BGR)

        # Convert to JPEG
        _, jpeg_buffer = cv2.imencode(".jpg", bgr_image)

        return jpeg_buffer
