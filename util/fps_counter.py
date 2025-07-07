import time


class FPSCounter:
    def __init__(self, alpha=0.1):
        self.last_time = time.time()
        self.fps = 0
        self.alpha = alpha  # 0.1 is a good starting point

    def update(self):
        current_time = time.time()
        delta = current_time - self.last_time
        if delta > 0:
            current_fps = 1.0 / delta
            if self.fps == 0:
                self.fps = current_fps  # Initial seed
            else:
                self.fps = self.alpha * current_fps + (1 - self.alpha) * self.fps
        self.last_time = current_time
        return self.fps
