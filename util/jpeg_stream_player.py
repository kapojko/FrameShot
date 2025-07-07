from util.fps_counter import FPSCounter
import cv2
import numpy as np
import time


class JpegStreamPlayer:
    def __init__(self, max_width=1280, max_height=720):
        self.running = False
        self.fps_counter = FPSCounter(alpha=0.2)
        self.max_width = max_width
        self.max_height = max_height

    def start(self):
        self.running = True
        self.start_time = time.time()
        self.frame_count = 0
        self.fps = 0

    def show_next_frame(self, jpeg_buffer):
        if not self.running:
            return

        # Load JPEG
        frame = cv2.imdecode(
            np.frombuffer(jpeg_buffer, dtype=np.uint8), cv2.IMREAD_COLOR
        )

        if frame is None:
            return

        # Update FPS
        fps = self.fps_counter.update()

        # Display FPS in top-right corner
        cv2.putText(
            frame,
            f"FPS: {fps:.2f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2,
        )

        # Resize to fit inside the max window
        h, w = frame.shape[:2]
        if w > self.max_width or h > self.max_height:
            scale = min(self.max_width / w, self.max_height / h)
            frame = cv2.resize(
                frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA
            )

        # Display frame
        cv2.imshow("Live Stream", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            return

    def stop(self):
        self.running = False
        cv2.destroyAllWindows()
