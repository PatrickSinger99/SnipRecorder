import tkinter as tk
import pyautogui


class TransparentSelector(tk.Toplevel):
    def __init__(self):
        super().__init__()

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
        else:
            print("No selection was made")

        self.destroy()




class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Snip Recorder")
        self.resizable(False, False)

        self.control_frame = tk.Frame(self)
        self.control_frame.pack(side="top")

        self.select_area_btn = tk.Button(self.control_frame, text="Select Area", command=self.start_draw_selection)
        self.select_area_btn.pack(side="left")

        self.select_audio_btn = tk.Button(self.control_frame, text="Audio Channel")
        self.select_audio_btn.pack(side="left")

        self.record_btn = tk.Button(self.control_frame, text="Start Recording")
        self.record_btn.pack(side="left")

        self.area_preview_frame = tk.Frame(self, height=300)
        self.area_preview_frame.pack(side="bottom", fill="x")
        self.area_preview_frame.pack_propagate(False)

        self.area_preview_img = tk.Label(self.area_preview_frame, bg="green")
        self.area_preview_img.pack(anchor="center")

    def start_draw_selection(self):
        selector = TransparentSelector()


if __name__ == '__main__':
    app = App()
    app.mainloop()
