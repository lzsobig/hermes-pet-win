"""灵动岛 — 独立浮动窗口，显示 AI 状态 + 最近回复预览"""
import tkinter as tk


class DynamicIsland:
    """独立浮动灵动岛窗口"""

    STATE_IDLE = "idle"
    STATE_THINKING = "thinking"
    STATE_DONE = "done"
    STATE_ERROR = "error"

    def __init__(self, root: tk.Tk, config: dict, on_click=None):
        self.root = root
        self.config = config
        self.on_click = on_click
        self.state = self.STATE_IDLE
        self.preview_text = ""
        self.is_expanded = False
        self._drag_data = {"x": 0, "y": 0}

        self._build_ui()
        self._bind_events()
        self._start_animation()

    def _build_ui(self):
        """构建独立浮动灵动岛窗口"""
        self.win = tk.Toplevel(self.root)
        self.win.overrideredirect(True)  # 无标题栏
        self.win.attributes("-topmost", True)
        self.win.configure(bg="#1a1a2e")

        # 屏幕顶部居中
        sw = self.win.winfo_screenwidth()
        self.win.geometry(f"300x40+{sw//2-150}+8")

        # 胶囊容器
        self.capsule = tk.Frame(self.win, bg="#2d2d44", padx=12, pady=6)
        self.capsule.pack(fill="both", expand=True)

        # 状态圆点
        self.status_dot = tk.Canvas(self.capsule, width=14, height=14,
                                    bg="#2d2d44", highlightthickness=0)
        self.status_dot.pack(side="left", padx=(0, 8))
        self._draw_dot("#4ade80")

        # 模式标签
        self.mode_label = tk.Label(self.capsule, text="✦ mimo",
                                   fg="#e2e8f0", bg="#2d2d44",
                                   font=("Segoe UI", 10, "bold"))
        self.mode_label.pack(side="left")

        # 状态文字
        self.status_label = tk.Label(self.capsule, text="ready",
                                     fg="#94a3b8", bg="#2d2d44",
                                     font=("Segoe UI", 9))
        self.status_label.pack(side="right", padx=(0, 8))

        # 关闭按钮
        self.close_btn = tk.Label(self.capsule, text="x", fg="#94a3b8",
                                  bg="#2d2d44", font=("Segoe UI", 10, "bold"),
                                  cursor="hand2")
        self.close_btn.pack(side="right")
        self.close_btn.bind("<Button-1>", self._on_close)

    def _on_close(self, event=None):
        """关闭灵动岛"""
        self.hide()
        return "break"

        # 展开预览区
        self.preview_frame = tk.Frame(self.win, bg="#2d2d2e", padx=12, pady=8)
        self.preview_label = tk.Label(self.preview_frame, text="",
                                      fg="#cbd5e1", bg="#2d2d2e",
                                      font=("Segoe UI", 9),
                                      wraplength=300, justify="left")
        self.preview_label.pack()

    def _bind_events(self):
        self.capsule.bind("<Enter>", self._on_hover_enter)
        self.capsule.bind("<Leave>", self._on_hover_leave)
        self.capsule.bind("<Button-1>", self._on_click)
        self.capsule.bind("<ButtonPress-3>", self._on_drag_start)
        self.capsule.bind("<B3-Motion>", self._on_drag_motion)
        # 关闭按钮阻止事件传播到 capsule
        self.close_btn.bind("<Enter>", lambda e: self.close_btn.config(fg="#f87171"))
        self.close_btn.bind("<Leave>", lambda e: self.close_btn.config(fg="#94a3b8"))
        # 整个窗口也能拖
        self.win.bind("<ButtonPress-3>", self._on_drag_start)
        self.win.bind("<B3-Motion>", self._on_drag_motion)

    def _draw_dot(self, color):
        self.status_dot.delete("all")
        self.status_dot.create_oval(2, 2, 12, 12, fill=color, outline="")

    def _start_animation(self):
        self._pulse_phase = 0
        self._animate()

    def _animate(self):
        if self.state == self.STATE_THINKING:
            self._pulse_phase = (self._pulse_phase + 1) % 20
            intensity = int(128 + 127 * abs((self._pulse_phase / 10) - 1))
            color = f"#{intensity:02x}{intensity:02x}ff"
            self._draw_dot(color)
            self.status_label.config(text="thinking...")
        elif self.state == self.STATE_DONE:
            self._draw_dot("#4ade80")
            self.status_label.config(text="done", fg="#4ade80")
        elif self.state == self.STATE_ERROR:
            self._draw_dot("#f59e0b")
            self.status_label.config(text="error", fg="#f59e0b")
        else:
            self._draw_dot("#4ade80")
            self.status_label.config(text="ready", fg="#94a3b8")

        self.root.after(200, self._animate)

    def set_state(self, state, preview=""):
        self.state = state
        if preview:
            self.preview_text = preview
            self.preview_label.config(text=preview[:80] + ("..." if len(preview) > 80 else ""))

    def show(self):
        self.win.deiconify()

    def hide(self):
        self.win.withdraw()

    def _on_hover_enter(self, event):
        if not self.is_expanded and self.preview_text:
            self.is_expanded = True
            self.preview_frame.pack(fill="x")

    def _on_hover_leave(self, event):
        if self.is_expanded:
            self.is_expanded = False
            self.preview_frame.pack_forget()

    def _on_click(self, event):
        # 点击关闭按钮时不触发 on_click
        if event.widget == self.close_btn:
            return
        if self.on_click:
            self.on_click()

    def _on_drag_start(self, event):
        self._drag_data["x"] = event.x_root - self.win.winfo_x()
        self._drag_data["y"] = event.y_root - self.win.winfo_y()

    def _on_drag_motion(self, event):
        x = event.x_root - self._drag_data["x"]
        y = event.y_root - self._drag_data["y"]
        self.win.geometry(f"+{x}+{y}")
