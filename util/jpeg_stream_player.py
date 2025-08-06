import threading
import cv2
import numpy as np
import time

from util.focus_calc import FocusCalc
from util.fps_counter import FPSCounter


class JpegStreamPlayer:
    def __init__(self, max_width=1280, max_height=720):
        self.running = False
        self.fps_counter = FPSCounter(alpha=0.2)
        self.max_width = max_width
        self.max_height = max_height

        self.save_next_frame = False

        self.latest_frame = None
        self.lock = threading.Lock()

    def start(self):
        self.running = True
        threading.Thread(target=self._display_loop, daemon=True).start()

    def show_next_frame(self, jpeg_buffer):
        self.fps_counter.update()

        frame = cv2.imdecode(np.frombuffer(jpeg_buffer, dtype=np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            return

        with self.lock:
            self.latest_frame = frame.copy()  # Store the latest decoded frame

        # reset save next frame flag
        self.save_next_frame = False

    def _display_loop(self):
        while self.running:
            frame = None
            with self.lock:
                if self.latest_frame is not None:
                    frame = self.latest_frame.copy()

            if frame is not None:
                # Calculate focus metrics
                h, w = frame.shape[:2]
                roi = (w // 3, h // 3, w // 3, h // 3)  # central third
                focus_calc = FocusCalc(frame, roi=roi)
                metric_laplacian = focus_calc.laplacian()
                metric_tenengrad = focus_calc.tenengrad()

                # Resize if too big
                h, w = frame.shape[:2]
                if w > self.max_width or h > self.max_height:
                    scale = min(self.max_width / w, self.max_height / h)
                    frame = cv2.resize(frame, (int(w * scale), int(h * scale)))

                # Add text
                cv2.putText(
                    frame,
                    f"FPS: {self.fps_counter.fps:.2f}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    2,
                )

                cv2.putText(
                    frame,
                    f"Focus: {metric_laplacian:.2f}, {metric_tenengrad:.2f}",
                    (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    2,
                )

                if self.save_next_frame:
                    cv2.putText(
                        frame,
                        "SAVED",
                        (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 0, 255),
                        2,
                    )

                cv2.imshow("Live Stream", frame)

                # Process key events
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    self.running = False
                    break
                elif key == ord("s") or key == ord(" "):
                    print("[INFO] Saving next frame...")
                    self.save_next_frame = True

                # Check for window being closed
                if not cv2.getWindowProperty("Live Stream", cv2.WND_PROP_VISIBLE):
                    self.running = False
                    break

            else:
                # Avoid busy loop if no frame is available
                time.sleep(0.01)

        cv2.destroyAllWindows()

    def stop(self):
        self.running = False
