import cv2
import numpy as np
import time
import mss
import threading
import subprocess
import queue
import pyaudio


class ScreenCapture:
    def __init__(self, verbose: int = 1):
        self.coords = {"top": 0, "left": 0, "width": 1000, "height": 1000}
        self.verbose = verbose
        self.fps = 30
        self.recording_active = False
        self.video_rec_thread = None  # Thread for the recording loop
        self.audio_rec_thread = None
        self.audio_queue = queue.Queue()
        self.ffmpeg_process = None  # Subprocess for ffmpeg
        self.info_queue = queue.Queue()

        # Audio
        self.pyaudio = pyaudio.PyAudio()
        self.format = pyaudio.paInt16   # Sample format (16-bit)
        self.channels = 2  # Stereo
        self.buffer_size = 1024
        # Inital call. Get wasapi recording device, if none available, returns None
        self.audio_rec_device = self.get_wasapi_recording_device()
        self.record_audio = True if self.audio_rec_device is not None else False

    def set_coordinates(self, top: int, left: int, width: int, height: int):
        """
        Set screen recording coordinates
        :param top: top y-coordinate
        :param left: left x-coordinate
        :param width: width for x-area
        :param height: height for y-area
        """

        # height & width needs to be divisible by 2 for the ffmpeg video encoding
        if width % 2 is not 0:
            width -= 1

        if height % 2 is not 0:
            height -= 1

        self.coords = {"top": top, "left": left, "width": width, "height": height}

    def set_fps(self, fps: int):
        """Set new fps value"""
        self.fps = fps

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
        Start recording action. Initializes ffmpeg process and starts main recording thread
        """
        self.recording_active = True

        self.ffmpeg_process = subprocess.Popen(
            [
                "ffmpeg",
                "-y",  # Overwrite output file if it exists
                "-f", "rawvideo",  # Input is raw video
                "-vcodec", "rawvideo",  # No encoding on input
                "-pix_fmt", "bgra",  # Raw RGB format
                "-s", f"{self.coords["width"]}x{self.coords["height"]}",  # Frame size
                "-r", str(self.fps),  # Frame rate
                "-i", "pipe:0",  # Video input
                "-c:v", "libx264",  # Encode video using H.264
                "-preset", "fast",  # Compression speed
                "-crf", "23",  # Quality (lower is better, 17–28 typical)
                "-pix_fmt", "yuv420p",  # Output pixel format for compatibility
                "-c:a", "aac",  # Audio codec
                "-b:a", "192k",  # Audio bitrate
                "-f", "s16le",  # Raw PCM audio format
                "-ar", "44100",  # Audio sample rate
                "-ac", "2",  # Audio channels
                "-i", "pipe:1",  # Audio input
                "-loglevel", "info",  # Suppress all but errors
                "output.mp4",  # Output file
            ],
            stdin=subprocess.PIPE,
            bufsize=10 ** 8
        )

        # Start audio recording thread
        if self.record_audio:
            self.audio_rec_thread = threading.Thread(target=self._audio_capture, args=(self.audio_queue,))
            self.audio_rec_thread.start()

        # Start video recording thread
        self.video_rec_thread = threading.Thread(target=self._video_capture, args=(self.info_queue,))
        self.video_rec_thread.start()

    def stop_recording(self):
        """
        Stop recording action. Stops main recording thread
        """
        self.recording_active = False
        self.video_rec_thread.join()  # Wait for thread to finish and stop
        if self.record_audio:
            self.audio_rec_thread.join()

    def _video_capture(self, info_queue, verbose=True):
        """
        Record screen based on coordinates and fps set in class variables
        """

        # Set initial time Parameters
        time_per_frame = 1 / self.fps
        next_frame_time = time.monotonic()

        # Capture object
        capture = None

        # Statistics
        frame_skips = 0
        frames_written = 0  # Includes frame skips

        # Logging
        last_measure_time = time.monotonic()
        last_frame_count = 0
        start_time = last_measure_time
        log_frequency_sec = 1

        # Capture Loop
        while self.recording_active:

            # Calculate Time Parameters
            wait_time = next_frame_time - time.monotonic()  # Wait time before caputing next frame based on fps

            # Handle capturing screen in set intervals
            if wait_time >= 0 or capture is None:
                time.sleep(max(0, wait_time))  # Wait for next frame time
                capture = self.capture_screen()  # Capture screen
            else:
                # If last capture took to long, skip this capture and send last again
                frame_skips += 1

            # Send capture to ffmpeg process
            self.ffmpeg_process.stdin.write(capture.raw)
            frames_written += 1

            # Add Audio to stream if set and available
            if self.record_audio and not self.audio_queue.empty():
                audio_chunk = self.audio_queue.get()
                self.ffmpeg_process.stdin.write(audio_chunk)

            # Handle prints if verbose is set
            if verbose:
                current_time = time.monotonic()
                last_log_time_elapsed = current_time - last_measure_time

                # Create new print log, if logging time interval is reached
                if last_log_time_elapsed > log_frequency_sec:
                    frames_elapsed = frames_written - last_frame_count

                    # Calculate and print metrics
                    fps = round(frames_elapsed / last_log_time_elapsed, 2)
                    total_time_elapsed = round(current_time - start_time)
                    print(f"[RECORDING] Time elapsed: {total_time_elapsed}s | FPS: {fps} | Frames written: "
                          f"{frames_written} | Frame skips: {frame_skips} ({round((frame_skips/frames_written)*100)}%)")

                    # Update logging cycle based parameters
                    last_frame_count = frames_written
                    last_measure_time = current_time

                    # Update info queue
                    info_queue.put({"status": "recording", "time": total_time_elapsed, "fps": fps,
                                    "frames_written": frames_written, "frame_skips": frame_skips})

            # Schedule next frame
            next_frame_time += time_per_frame

        # Update info queue
        info_queue.put({"status": "writing"})

        # Finalize ffmpeg process
        self.ffmpeg_process.stdin.close()
        self.ffmpeg_process.wait()

        # Update info queue
        info_queue.put({"status": "done"})

    def _audio_capture(self, audio_queue):
        device_index = self.audio_rec_device["index"]
        sample_rate = int(self.audio_rec_device["defaultSampleRate"])

        stream = self.pyaudio.open(
            format=self.format,
            channels=self.channels,
            rate=sample_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=self.buffer_size
        )

        while self.recording_active:
            audio_chunk = stream.read(self.buffer_size, exception_on_overflow=False)
            audio_queue.put(audio_chunk)

        stream.stop_stream()
        stream.close()

    def get_wasapi_recording_device(self):
        # Get available host apis and find wasapi index
        wasapi_api = None
        for i in range(self.pyaudio.get_host_api_count()):
            info = self.pyaudio.get_host_api_info_by_index(i)
            if "wasapi" in info['name'].lower():
                wasapi_api = i
                if self.verbose >= 2:
                    print(f"WASAPI Host API: {wasapi_api}")
                break

        # BREAK if no WASAPI Api available
        if wasapi_api is None:
            if self.verbose >= 1:
                print("WASAPI API not found!")
                return None

        # Find all stereo mix devices and select the one with wasapi
        wasapi_device = None
        stereo_mix_devices = self.get_stereo_mix_devices()
        for device in stereo_mix_devices:
            if device["hostApi"] == wasapi_api:
                wasapi_device = device
                break

        # BREAK if no WASAPI device is available
        if wasapi_device is None:
            if self.verbose >= 1:
                print("No Stereo Mix Device with WASAPI API found")
                return None

        if self.verbose >= 1:
            print(f"WASAPI Stereo Mix Device found: Name={wasapi_device['name']}, Index={wasapi_device['index']}, "
                  f"Sample Rate={wasapi_device['defaultSampleRate']}")
        return wasapi_device

    def get_stereo_mix_devices(self):

        # Get all stereo mix devices
        stereo_mix_devices = []
        for i in range(self.pyaudio.get_device_count()):
            dev_info = self.pyaudio.get_device_info_by_index(i)
            if "stereo mix" in dev_info["name"].lower():
                stereo_mix_devices.append(dev_info)

        # Check if devices can be read from
        working_devices = []
        for device in stereo_mix_devices:
            try:
                self.pyaudio.open(format=self.format, channels=self.channels, rate=int(device["defaultSampleRate"]),
                                  input=True, input_device_index=device["index"], frames_per_buffer=self.buffer_size)
                working_devices.append(device)
            except Exception as e:
                if self.verbose >= 2:
                    print(f"(!) Could not open device {device['name']} on index {device['index']}:", e)

        if self.verbose >= 2:
            print(f"Found {len(working_devices)} readable stereo mix devices (from {len(stereo_mix_devices)} total).")
        return working_devices


if __name__ == '__main__':
    sc = ScreenCapture()
    sc.start_recording()
    time.sleep(5)
    sc.stop_recording()
