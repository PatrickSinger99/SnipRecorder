import cv2
import numpy as np
import time
import mss
import threading


class ScreenCapture:
    def __init__(self):
        self.coords = {"top": 0, "left": 0, "width": 2000, "height": 2000}
        self.fps = 30
        self.recording_active = False
        self.capture_thread = None

    def set_coordinates(self, top: int, left: int, width: int, height: int):
        """
        Set screen recording coordinates
        :param top: top y-coordinate
        :param left: left x-coordinate
        :param width: width for x-area
        :param height: height for y-area
        """
        self.coords = {"top": top, "left": left, "width": width, "height": height}

    def capture_screen(self):
        """
        Capture one screenshot on the class defined screen coordinates
        :return: Image as Numpy Array
        """

        with mss.mss() as sct:
            capture = sct.grab(self.coords)
            img_array = np.array(capture)
            img_array = cv2.cvtColor(img_array, cv2.COLOR_BGRA2BGR)

        return img_array

    def start_recording(self):
        """
        Start recording action. Starts main recording thread
        """
        self.recording_active = True
        self.capture_thread = threading.Thread(target=self.recording_thread)
        self.capture_thread.start()

    def stop_recording(self):
        """
        Stop recording action. Stops main recording thread
        """
        self.recording_active = False
        self.capture_thread.join()  # Wait for thread to finish and stop

    def recording_thread(self):
        """
        Record screen based on coordinates and fps set in class variables
        """

        # Set initial time Parameters
        time_per_frame = 1 / self.fps
        next_frame_time = time.time()

        # Initialize Video Writer
        fourcc = cv2.VideoWriter_fourcc(*"DIVX")
        writer = cv2.VideoWriter("output.avi", fourcc, self.fps, (self.coords["width"], self.coords["height"]))

        # Initialize FPS tracking
        last_time = time.time()

        # Capture Loop
        while self.recording_active:

            # Calculate Time Parameters
            wait_time = next_frame_time - time.time()  # Wait time before caputing next frame based on fps

            # Wait for next frame time (for stable fps)
            time.sleep(max(0, wait_time))

            # Capture screen and write to video writer
            img_array = self.capture_screen()
            writer.write(img_array)

            # Get actual fps
            now = time.time()
            actual_fps = 1 / (now - last_time)  # Reciprocal of frame duration
            print(f"Actual FPS: {actual_fps:.2f}")
            last_time = now

            # Schedule next frame
            next_frame_time += time_per_frame

        # Finalize Video
        writer.release()


if __name__ == '__main__':
    sc = ScreenCapture()
    sc.start_recording()
    time.sleep(5)
    sc.stop_recording()
