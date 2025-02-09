import tkinter as tk
import pyautogui
from utils import *
from ffmpeg_recorder import ScreenCapture
from PIL import Image, ImageTk
from typing import Optional
import queue


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
            """
            print(f"Selected Area: ({self.actual_cursor_start_x}, {self.actual_cursor_start_y}) to "
                  f"({self.actual_cursor_end_x}, {self.actual_cursor_end_y})")
            """
            self.selected_area = [self.actual_cursor_start_x, self.actual_cursor_start_y,
                                  self.actual_cursor_end_x, self.actual_cursor_end_y]

        else:
            """
            print("No selection was made")
            """
            self.selected_area = []

        self.destroy()


class App(tk.Tk):
    img_paths = {"select_area": "./imgs/snip.png", "record_start": "./imgs/rec_start.png",
                 "record_stop": "./imgs/rec_stop.png", "options_arrow": "./imgs/options_arrow.png"}
    icon_size = 46
    icon_color = (0, 0, 0)

    colors = {"control_bg": "#5B585B", "control_fg": "indian red", "control_txt": "light grey", "preview_bg": "#323032"}

    def __init__(self):
        super().__init__()

        self.title("Snip Recorder")
        self.resizable(False, False)

        self.recorder = ScreenCapture()

        self.control_frame = tk.Frame(self, bg=App.colors["control_bg"])
        self.control_frame.pack(side="top")

        select_area_pil_img = Image.open(App.img_paths["select_area"]).resize((App.icon_size, App.icon_size))
        self.select_area_btn_img = ImageTk.PhotoImage(change_icon_color(select_area_pil_img, App.icon_color))
        self.select_area_btn = tk.Button(self.control_frame, text="Select Area", command=self.start_draw_selection,
                                         cursor="hand2", image=self.select_area_btn_img, compound="left", bd=0,
                                         bg=self.control_frame.cget("bg"), relief="flat", fg=App.colors["control_txt"])
        self.select_area_btn.pack(side="left", fill="y", ipadx=6, ipady=6)
        self.select_area_btn.bind("<Enter>", lambda e: self.select_area_btn.configure(bg=App.colors["control_fg"]))
        self.select_area_btn.bind("<Leave>", lambda e: self.select_area_btn.configure(bg=App.colors["control_bg"]))

        # Divider
        tk.Frame(self.control_frame, bg=App.colors["preview_bg"]).pack(side="left", fill="y")

        self.select_audio_btn = tk.Button(self.control_frame, text="Audio Channel", cursor="hand2", relief="flat", bd=0,
                                          bg=self.control_frame.cget("bg"), fg=App.colors["control_txt"])
        self.select_audio_btn.pack(side="left", fill="y", ipadx=6, ipady=6)
        self.select_audio_btn.bind("<Enter>", lambda e: self.select_audio_btn.configure(bg=App.colors["control_fg"]))
        self.select_audio_btn.bind("<Leave>", lambda e: self.select_audio_btn.configure(bg=App.colors["control_bg"]))

        # Divider
        tk.Frame(self.control_frame, bg=App.colors["preview_bg"]).pack(side="left", fill="y")

        self.fps_options = [15, 24, 30, 60]
        self.selected_fps = tk.StringVar()
        self.on_fps_select(self.fps_options[0])

        self.options_arrow_down = ImageTk.PhotoImage(Image.open(App.img_paths["options_arrow"]).resize((24, 24)))

        self.select_fps_btn = tk.OptionMenu(self.control_frame, self.selected_fps, *self.fps_options,
                                            command=self.on_fps_select)
        self.select_fps_btn.configure(bg=self.control_frame.cget("bg"), fg=App.colors["control_txt"], cursor="hand2",
                                      relief="flat", bd=0, highlightthickness=0, indicatoron=0, compound="right",
                                      activeforeground=App.colors["control_txt"], image=self.options_arrow_down,
                                      activebackground=App.colors["control_fg"])
        self.select_fps_btn["menu"].configure(bg=self.control_frame.cget("bg"), fg=App.colors["control_txt"],
                                              relief="flat", bd=0, activebackground=App.colors["control_fg"])
        self.select_fps_btn.pack(side="left", fill="y", ipadx=6, ipady=6)



        # Divider
        tk.Frame(self.control_frame, bg=App.colors["preview_bg"]).pack(side="left", fill="y")

        self.record_btn_start_img = ImageTk.PhotoImage(Image.open(App.img_paths["record_start"]).resize((App.icon_size, App.icon_size)))
        self.record_btn_stop_img = ImageTk.PhotoImage(Image.open(App.img_paths["record_stop"]).resize((App.icon_size, App.icon_size)))

        self.record_btn = tk.Button(self.control_frame, text=" Start Recording", command=self.on_recording_button,
                                    cursor="hand2", relief="flat", bd=0, bg=self.control_frame.cget("bg"),
                                    image=self.record_btn_start_img, compound="left", fg=App.colors["control_txt"], state="disabled")
        self.record_btn.pack(side="left", fill="y", ipadx=6, ipady=6)
        self.record_btn.bind("<Enter>", lambda e: self.record_btn.configure(bg=App.colors["control_fg"]))
        self.record_btn.bind("<Leave>", lambda e: self.record_btn.configure(bg=App.colors["control_bg"]))

        self.area_preview_frame = tk.Frame(self, height=300, bg=App.colors["preview_bg"])
        self.area_preview_frame.pack(fill="x")
        self.area_preview_frame.pack_propagate(False)

        self.preview_img = None
        self.area_preview_img = tk.Label(self.area_preview_frame, bg=self.area_preview_frame.cget("bg"))
        self.area_preview_img.pack(anchor="center", fill="y", expand=True)

        self.info_frame = tk.Frame(self, height=40, bg=App.colors["control_bg"])
        self.info_frame.pack(side="bottom", fill="x")
        self.info_frame.pack_propagate(False)

        self.info_label = tk.Label(self.info_frame, fg=App.colors["control_txt"],
                                   bg=self.info_frame.cget("bg"))
        self.info_label.pack(side="left", fill="y")

        """INIT CALLS"""
        self.update_info_text(text="Click Define Area to set the part of the screen you want to capture")

    def on_fps_select(self, selected_value):

        self.recorder.set_fps(selected_value)
        print("[INFO] Set FPS to", selected_value)

        # Update the StringVar to show the selected value with "FPS"
        self.selected_fps.set(f"{selected_value} FPS")

    def update_info_text(self, text: Optional[str] = None, color: Optional[str] = None, image: Optional[Image] = None):

        if text is not None:
            self.info_label.configure(text=text)
        if color is not None:
            self.info_label.configure(fg=color)
        if image is not None:
            self.info_label.configure(image=image)

    def start_draw_selection(self):
        selector = TransparentSelector()
        self.wait_window(selector)

        if len(selector.selected_area) != 0:
            self.set_new_recording_area(*selector.selected_area)

    def on_recording_button(self):
        if not self.recorder.recording_active:
            # Change Button Appearance:
            self.record_btn.configure(text=" Stop Recording", image=self.record_btn_stop_img)
            self.recorder.start_recording()
            self.recording_info_update_loop()
            self.update_info_text(text="Initializing Recording")

        else:
            # Change Button Appearance:
            self.record_btn.configure(text=" Start Recording", image=self.record_btn_start_img)
            self.recorder.stop_recording()

    def recording_info_update_loop(self):
        try:
            while True:  # Check all items in the queue
                update = self.recorder.info_queue.get_nowait()

                if update["status"] == "done":
                    self.update_info_text(text="Recording finished", color=App.colors["control_txt"])
                    return  # Stop polling when listener signals completion
                elif update["status"] == "writing":
                    self.update_info_text(text="Finalizing Recording")
                else:
                    self.update_info_text(text=f"Recording active, {update['time']}s elapsed, {update['fps']}FPS,"
                                               f" {update['frames_written']} Frames", color=App.colors["control_fg"])
        except queue.Empty:
            pass  # No updates in the queue

        # Schedule the next check
        self.after(100, self.recording_info_update_loop)

    def set_new_recording_area(self, x0, y0, x1, y1):

        top, left = min(y0, y1), min(x0, x1)
        width, height = max(x0, x1) - left, max(y0, y1) - top

        self.recorder.set_coordinates(top, left, width, height)
        print(f"[INFO] Recording area set to ({x0}, {y0}) - ({x1}, {y1})")

        # Set Preview image
        capture = self.recorder.capture_screen()
        img_array = self.recorder.capture_post_processing(capture, to_rgb=True)
        resized_img = resize_image(img_array, max_width=self.area_preview_frame.winfo_width() - 8,
                                   max_height=self.area_preview_frame.winfo_height() - 8)
        self.preview_img = ImageTk.PhotoImage(Image.fromarray(resized_img))
        self.area_preview_img.configure(image=self.preview_img)

        # Set record button to normal
        self.record_btn.configure(state="normal")


if __name__ == '__main__':
    app = App()
    app.mainloop()
