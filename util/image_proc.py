import numpy as np
import cv2


class ImageProc:
    def __init__(self, img):
        self.img = img

    def auto_white_balance(self):
        """
        Applies simple gray-world assumption white balance.
        img: np.ndarray (BGR image)
        Returns: white-balanced image (uint8)
        """
        img_proc = self.img.astype(np.float32)

        # Calculate average per channel
        avg_b = np.mean(img_proc[:, :, 0])
        avg_g = np.mean(img_proc[:, :, 1])
        avg_r = np.mean(img_proc[:, :, 2])

        # Calculate global average
        avg_gray = (avg_r + avg_g + avg_b) / 3

        # Compute gains
        gain_b = avg_gray / avg_b
        gain_g = avg_gray / avg_g
        gain_r = avg_gray / avg_r

        # Apply gains
        img_proc[:, :, 0] *= gain_b
        img_proc[:, :, 1] *= gain_g
        img_proc[:, :, 2] *= gain_r

        # Clip to valid range
        img_proc = np.clip(img_proc, 0, 255).astype(np.uint8)

        self.img = img_proc
        return img_proc

    def gamma_correction(self, gamma=2.2):
        """
        Applies gamma correction to a BGR image.
        gamma: gamma value (default = 2.2)
        Returns: gamma-corrected image (uint8)
        """
        inv_gamma = 1.0 / gamma
        # Build lookup table
        table = np.array([(i / 255.0) ** inv_gamma * 255 for i in range(256)]).astype(np.uint8)
        # Apply to all channels
        self.img = cv2.LUT(self.img, table)

        return self.img
