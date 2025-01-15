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

        self.fast_capture = False  # Mode for better capturing performance: Does img processing after recording
        self.capture_objs = []

    def set_coordinates(self, top: int, left: int, width: int, height: int):
        """
        Set screen recording coordinates
        :param top: top y-coordinate
        :param left: left x-coordinate
        :param width: width for x-area
        :param height: height for y-area
        """
        self.coords = {"top": top, "left": left, "width": width, "height": height}

    def set_fast_capture(self, value: bool):
        self.fast_capture = value

    def capture_screen(self):
        """
        Capture one screenshot on the class defined screen coordinates
        :return: capture object
        """
        with mss.mss() as sct:
            capture = sct.grab(self.coords)

        return capture

    @staticmethod
    def capture_post_processing(capture, to_rgb=False):
        """
        Convert capture object to numpy array and convert color BGR required by Video writer
        :param capture: Capture object
        :param to_rgb: return as RGB and not as BGR by default
        :return: Image as numpy array in BGR (if to_rgb set to false)
        """
        img_array = np.array(capture)
        img_array = cv2.cvtColor(img_array, cv2.COLOR_BGRA2BGR)
        if to_rgb:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)

        return img_array

    def start_recording(self):
        """
        Start recording action. Starts main recording thread
        """
        self.recording_active = True
        self.capture_thread = threading.Thread(target=self.recording_thread, args=(self.fast_capture, ))
        self.capture_thread.start()

    def stop_recording(self):
        """
        Stop recording action. Stops main recording thread
        """
        self.recording_active = False
        self.capture_thread.join()  # Wait for thread to finish and stop

    def recording_thread(self, fast_capture=False):
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
            capture = self.capture_screen()
            if fast_capture:
                # If fast capture active, only save raw capture in class list
                self.capture_objs.append(capture)
            else:
                # If fast capture not active, do post processing for image and write to video
                img_array = self.capture_post_processing(capture)
                writer.write(img_array)

            # Get actual fps
            now = time.time()
            actual_fps = int(1 / (now - last_time))  # Reciprocal of frame duration
            print(f"Actual FPS: {actual_fps}")
            last_time = now

            # Schedule next frame
            next_frame_time += time_per_frame

        # If fast capture active, do post processing of images and write to video
        if fast_capture:
            # Write to video
            for capture_obj in self.capture_objs:
                img_array = np.array(capture_obj)
                img_array = cv2.cvtColor(img_array, cv2.COLOR_BGRA2BGR)
                writer.write(img_array)

            # Reset capture object list
            self.capture_objs = []

        # Finalize Video
        writer.release()


if __name__ == '__main__':
    sc = ScreenCapture()
    sc.fast_capture = True
    sc.start_recording()
    time.sleep(5)
    sc.stop_recording()
