import tkinter as tk
import pyautogui
from utils import *
from recorder import ScreenCapture
from PIL import Image, ImageTk


class TransparentSelector(tk.Toplevel):
    def __init__(self):
        super().__init__()

        # Variable for returning selected area
        self.selected_area = []

        # Get the screen size
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        self.overrideredirect(True)  # Remove title bar and borders
        self.config(bg="white")
        self.attributes("-alpha", 0.15)

        self.selection_canvas = tk.Canvas(self, bg=self.cget("bg"), highlightthickness=0, width=screen_width,
                                          height=screen_height, cursor="tcross")
        self.selection_canvas.pack(fill="both", expand=True)
        self.selection_canvas.bind("<Button-1>", self.on_mouse_down)
        self.selection_canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.selection_canvas.bind("<Button-3>", self.on_right_mouse_btn)
        self.selection_canvas.bind("<Motion>", self.on_mouse_motion)
        # self.selection_canvas.bind("<Escape>", self.end_selection)

        self.active_draw = False  # Currently in progress of drawing the area
        self.selection_made = False  # Was a full area selection made
        self.start_pos_x = 0
        self.start_pos_y = 0

        # Actual cursor coordinates differ between canvas and windows
        self.actual_cursor_start_x = 0
        self.actual_cursor_start_y = 0
        self.actual_cursor_end_x = 0
        self.actual_cursor_end_y = 0

    def on_mouse_down(self, event):
        self.start_pos_x = event.x
        self.start_pos_y = event.y
        self.active_draw = True

        self.actual_cursor_start_x, self.actual_cursor_start_y = pyautogui.position()

    def on_mouse_up(self, event):
        if self.active_draw:
            self.active_draw = False
            self.selection_made = True
            self.end_selection()

    def on_mouse_motion(self, event):
        self.actual_cursor_end_x, self.actual_cursor_end_y = pyautogui.position()
        if self.start_pos_x <= event.x:
            start_x, end_x = self.start_pos_x, event.x
        else:
            start_x, end_x = event.x, self.start_pos_x

        if self.start_pos_y <= event.y:
            start_y, end_y = self.start_pos_y, event.y
        else:
            start_y, end_y = event.y, self.start_pos_y

        if self.active_draw:
            self.selection_canvas.delete("all")
            self.selection_canvas.create_rectangle(start_x, start_y, end_x, end_y, outline="red", width=3, fill="black")

    def on_right_mouse_btn(self, event):
        if not self.active_draw:
            self.end_selection()

        else:
            self.reset_selection()

    def reset_selection(self):
        # Delete canvas drawings
        self.selection_canvas.delete("all")

        # Reset draw variables
        self.active_draw = False  # Currently in progress of drawing the area
        self.selection_made = False
        self.start_pos_x = 0
        self.start_pos_y = 0

        # Reset actual cursor variables
        self.actual_cursor_start_x = 0
        self.actual_cursor_start_y = 0
        self.actual_cursor_end_x = 0
        self.actual_cursor_end_y = 0

    def end_selection(self):
        if self.selection_made:
            print(f"Selected Area: ({self.actual_cursor_start_x}, {self.actual_cursor_start_y}) to "
                  f"({self.actual_cursor_end_x}, {self.actual_cursor_end_y})")

            self.selected_area = [self.actual_cursor_start_x, self.actual_cursor_start_y,
                                  self.actual_cursor_end_x, self.actual_cursor_end_y]

        else:
            print("No selection was made")
            self.selected_area = []

        self.destroy()


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Snip Recorder")
        self.resizable(False, False)

        self.recorder = ScreenCapture()

        self.control_frame = tk.Frame(self)
        self.control_frame.pack(side="top")

        self.select_area_btn = tk.Button(self.control_frame, text="Select Area", command=self.start_draw_selection,
                                         cursor="hand2")
        self.select_area_btn.pack(side="left")

        self.select_audio_btn = tk.Button(self.control_frame, text="Audio Channel", cursor="hand2")
        self.select_audio_btn.pack(side="left")

        self.fast_rec_mode_check_var = tk.BooleanVar(value=False)
        self.fast_rec_mode_check = tk.Checkbutton(self.control_frame, text="Performance Mode", cursor="hand2",
                                                  variable=self.fast_rec_mode_check_var)
        self.fast_rec_mode_check.pack(side="left")

        self.record_btn = tk.Button(self.control_frame, text="Start Recording", command=self.on_recording_button,
                                    cursor="hand2")
        self.record_btn.pack(side="left")

        self.area_preview_frame = tk.Frame(self, height=300)
        self.area_preview_frame.pack(side="bottom", fill="x")
        self.area_preview_frame.pack_propagate(False)

        self.preview_img = None
        self.area_preview_img = tk.Label(self.area_preview_frame, bg=self.area_preview_frame.cget("bg"))
        self.area_preview_img.pack(anchor="center", fill="y", expand=True)

    def start_draw_selection(self):
        selector = TransparentSelector()
        self.wait_window(selector)

        if len(selector.selected_area) != 0:
            self.set_new_recording_area(*selector.selected_area)

    def on_recording_button(self):
        if not self.recorder.recording_active:
            # Change Button Appearance:
            self.record_btn.configure(text="Stop Recording")

            self.recorder.set_fast_capture(self.fast_rec_mode_check_var.get())
            self.recorder.start_recording()

        else:
            # Change Button Appearance:
            self.record_btn.configure(text="Start Recording")

            self.recorder.stop_recording()

    def set_new_recording_area(self, x0, y0, x1, y1):
        print(f"Setting recording area to ({x0}, {y0}) - ({x1}, {y1})")

        top, left = min(y0, y1), min(x0, x1)
        width, height = max(x0, x1) - left, max(y0, y1) - top

        self.recorder.set_coordinates(top, left, width, height)

        # Set Preview image
        capture = self.recorder.capture_screen()
        img_array = self.recorder.capture_post_processing(capture, to_rgb=True)
        resized_img = resize_image(img_array, max_width=self.area_preview_frame.winfo_width() - 8,
                                   max_height=self.area_preview_frame.winfo_height() - 8)
        self.preview_img = ImageTk.PhotoImage(Image.fromarray(resized_img))
        self.area_preview_img.configure(image=self.preview_img)


if __name__ == '__main__':
    app = App()
    app.mainloop()
