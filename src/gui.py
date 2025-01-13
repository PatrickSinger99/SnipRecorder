import tkinter as tk
import pyautogui


class TransparentSelector(tk.Toplevel):
    def __init__(self):
        super().__init__()

        # Get the screen size
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        self.overrideredirect(True)  # Remove title bar and borders
        self.config(bg="black")
        self.attributes("-alpha", 0.2)

        self.selection_canvas = tk.Canvas(self, bg=self.cget("bg"), highlightthickness=0, width=screen_width, height=screen_height)
        self.selection_canvas.pack(fill="both", expand=True)
        self.selection_canvas.bind("<Button-1>", self.on_mouse_down)
        self.selection_canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.bind("<Motion>", self.on_mouse_motion)

        self.active_draw = False
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
        self.active_draw = False

        # End selection window
        print(f"Selected Area: ({self.actual_cursor_start_x}, {self.actual_cursor_start_y}) to "
              f"({self.actual_cursor_end_x}, {self.actual_cursor_end_y})")

        self.destroy()

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
            self.selection_canvas.create_rectangle(start_x, start_y, end_x, end_y, outline="red")


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.start_selection_btn = tk.Button(self, text="Select Area", command=self.start_draw_selection)
        self.start_selection_btn.pack()

    def start_draw_selection(self):
        selector = TransparentSelector()


if __name__ == '__main__':
    app = App()
    app.mainloop()
