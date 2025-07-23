import cv2
import numpy as np


class FocusCalc:
    def __init__(self, image, roi):
        self.image = image
        self.roi = roi

    def laplacian(self):
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        if self.roi is not None:
            x, y, w, h = self.roi
            gray = gray[y : y + h, x : x + w]
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        return laplacian.var()

    def tenengrad(self):
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        if self.roi is not None:
            x, y, w, h = self.roi
            gray = gray[y : y + h, x : x + w]
        gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        magnitude = np.sqrt(gx**2 + gy**2)
        return np.mean(magnitude)
