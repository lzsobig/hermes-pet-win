"""桌面像素宠物 — 漫游动画 + 鼠标交互 + 拖文件吃"""
import tkinter as tk
import random
import os
from PIL import Image, ImageTk, ImageDraw


class PetSprite:
    """桌面像素小精灵"""

    STATE_IDLE = "idle"
    STATE_WALK = "walk"
    STATE_EAT = "eat"
    STATE_HAPPY = "happy"

    def __init__(self, root: tk.Tk, config: dict, on_file_drop=None):
        self.root = root
        self.config = config
        self.on_file_drop = on_file_drop
        self.state = self.STATE_IDLE
        self.direction = 1  # 1=右, -1=左
        self.frame_idx = 0
        self.is_hovered = False
        self._walk_timer = 0

        self._create_sprites()
        self._build_ui()
        self._start_animation()

    def _create_sprites(self):
        """生成像素精灵图片"""
        self.sprites = {}
        size = 64
        bg = (0, 0, 0, 0)  # 透明

        # idle — 小猫脸
        img = Image.new("RGBA", (size, size), bg)
        d = ImageDraw.Draw(img)
        s = 2  # scale factor
        # 身体
        d.rounded_rectangle([8*s, 12*s, 24*s, 28*s], radius=4*s, fill="#ff9f43")
        # 耳朵
        d.polygon([(8*s, 12*s), (12*s, 4*s), (16*s, 12*s)], fill="#ff9f43")
        d.polygon([(16*s, 12*s), (20*s, 4*s), (24*s, 12*s)], fill="#ff9f43")
        # 眼睛
        d.ellipse([11*s, 16*s, 14*s, 19*s], fill="#1a1a2e")
        d.ellipse([18*s, 16*s, 21*s, 19*s], fill="#1a1a2e")
        # 嘴
        d.arc([13*s, 20*s, 19*s, 24*s], start=0, end=180, fill="#1a1a2e", width=2)
        self.sprites["idle"] = [ImageTk.PhotoImage(img)]

        # blink — 眨眼
        img2 = img.copy()
        d2 = ImageDraw.Draw(img2)
        d2.line([(11*s, 17*s), (14*s, 17*s)], fill="#1a1a2e", width=3)
        d2.line([(18*s, 17*s), (21*s, 17*s)], fill="#1a1a2e", width=3)
        self.sprites["blink"] = [ImageTk.PhotoImage(img2)]

        # walk — 左右走两帧
        walk1 = Image.new("RGBA", (size, size), bg)
        d = ImageDraw.Draw(walk1)
        d.rounded_rectangle([8*s, 14*s, 24*s, 28*s], radius=4*s, fill="#ff9f43")
        d.polygon([(8*s, 14*s), (12*s, 6*s), (16*s, 14*s)], fill="#ff9f43")
        d.polygon([(16*s, 14*s), (20*s, 6*s), (24*s, 14*s)], fill="#ff9f43")
        d.ellipse([11*s, 18*s, 14*s, 21*s], fill="#1a1a2e")
        d.ellipse([18*s, 18*s, 21*s, 21*s], fill="#1a1a2e")
        d.line([(6*s, 28*s), (10*s, 30*s)], fill="#ff9f43", width=3)
        d.line([(22*s, 28*s), (26*s, 30*s)], fill="#ff9f43", width=3)

        walk2 = Image.new("RGBA", (size, size), bg)
        d = ImageDraw.Draw(walk2)
        d.rounded_rectangle([8*s, 14*s, 24*s, 28*s], radius=4*s, fill="#ff9f43")
        d.polygon([(8*s, 14*s), (12*s, 6*s), (16*s, 14*s)], fill="#ff9f43")
        d.polygon([(16*s, 14*s), (20*s, 6*s), (24*s, 14*s)], fill="#ff9f43")
        d.ellipse([11*s, 18*s, 14*s, 21*s], fill="#1a1a2e")
        d.ellipse([18*s, 18*s, 21*s, 21*s], fill="#1a1a2e")
        d.line([(8*s, 28*s), (4*s, 30*s)], fill="#ff9f43", width=3)
        d.line([(24*s, 28*s), (28*s, 30*s)], fill="#ff9f43", width=3)

        self.sprites["walk"] = [ImageTk.PhotoImage(walk1),
                                 ImageTk.PhotoImage(walk2)]

        # eat — 张嘴
        eat_img = Image.new("RGBA", (size, size), bg)
        d = ImageDraw.Draw(eat_img)
        d.rounded_rectangle([8*s, 12*s, 24*s, 28*s], radius=4*s, fill="#ff9f43")
        d.polygon([(8*s, 12*s), (12*s, 4*s), (16*s, 12*s)], fill="#ff9f43")
        d.polygon([(16*s, 12*s), (20*s, 4*s), (24*s, 12*s)], fill="#ff9f43")
        d.ellipse([11*s, 16*s, 14*s, 19*s], fill="#1a1a2e")
        d.ellipse([18*s, 16*s, 21*s, 19*s], fill="#1a1a2e")
        d.ellipse([13*s, 21*s, 19*s, 26*s], fill="#1a1a2e")
        self.sprites["eat"] = [ImageTk.PhotoImage(eat_img)]

        # happy — 爱心眼
        happy_img = Image.new("RGBA", (size, size), bg)
        d = ImageDraw.Draw(happy_img)
        d.rounded_rectangle([8*s, 12*s, 24*s, 28*s], radius=4*s, fill="#ff9f43")
        d.polygon([(8*s, 12*s), (12*s, 4*s), (16*s, 12*s)], fill="#ff9f43")
        d.polygon([(16*s, 12*s), (20*s, 4*s), (24*s, 12*s)], fill="#ff9f43")
        # 爱心眼
        d.text((10*s, 14*s), "♥", fill="#ff6b6b")
        d.text((17*s, 14*s), "♥", fill="#ff6b6b")
        d.arc([13*s, 20*s, 19*s, 24*s], start=0, end=180, fill="#1a1a2e", width=2)
        self.sprites["happy"] = [ImageTk.PhotoImage(happy_img)]

    def _build_ui(self):
        """构建宠物窗口"""
        self.canvas = tk.Canvas(self.root, width=128, height=128,
                                bg="#0f0f23", highlightthickness=0)
        self.canvas.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

        self.sprite_id = self.canvas.create_image(64, 64, image=self.sprites["idle"][0])

        # 绑定事件
        self.canvas.bind("<Enter>", self._on_enter)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_drag_release)

        self._dragging = False

    def _start_animation(self):
        """启动动画循环"""
        self._last_frame_time = 0
        self._animate()

    def _animate(self):
        """动画主循环 - 基于时间戳的帧率控制"""
        import time
        current_time = int(time.time() * 1000)  # 毫秒
        
        # 限制帧率到 30 FPS (约 33ms 一帧)
        if current_time - self._last_frame_time < 33:
            self.root.after(10, self._animate)
            return
        self._last_frame_time = current_time
        
        self.frame_idx += 1

        if self.state == self.STATE_IDLE:
            if self.frame_idx % 60 == 0:  # 每3秒眨眼
                self.canvas.itemconfig(self.sprite_id,
                                       image=self.sprites["blink"][0])
            elif self.frame_idx % 60 == 5:
                self.canvas.itemconfig(self.sprite_id,
                                       image=self.sprites["idle"][0])

        elif self.state == self.STATE_WALK:
            frame = self.sprites["walk"][self.frame_idx % 2]
            self.canvas.itemconfig(self.sprite_id, image=frame)
            # 移动
            x = self.canvas.winfo_x() + self.direction * 2
            screen_w = self.root.winfo_screenwidth()
            if x < 10 or x > screen_w - 60:
                self.direction *= -1
            self.canvas.place(x=x, y=self.canvas.winfo_y())
            self._walk_timer += 1
            if self._walk_timer > 60:  # 走3秒后停下
                self.state = self.STATE_IDLE
                self._walk_timer = 0

        elif self.state == self.STATE_EAT:
            self.canvas.itemconfig(self.sprite_id,
                                   image=self.sprites["eat"][0])
            if self.frame_idx % 30 == 0:
                self.state = self.STATE_HAPPY
                self.frame_idx = 0

        elif self.state == self.STATE_HAPPY:
            self.canvas.itemconfig(self.sprite_id,
                                   image=self.sprites["happy"][0])
            if self.frame_idx % 40 == 0:
                self.state = self.STATE_IDLE

        # 随机闲逛
        if self.state == self.STATE_IDLE and random.random() < 0.003:
            self.state = self.STATE_WALK
            self.direction = random.choice([-1, 1])
            self._walk_timer = 0

        self.root.after(50, self._animate)

    def _on_enter(self, event):
        """鼠标进入 — 小跑过来"""
        self.is_hovered = True
        if self.state == self.STATE_IDLE:
            self.state = self.STATE_WALK
            self.direction = 1 if event.x > 24 else -1
            self._walk_timer = 0

    def _on_leave(self, event):
        self.is_hovered = False

    def _on_click(self, event):
        """点击开始拖拽"""
        self._dragging = True
        self._drag_offset_x = event.x
        self._drag_offset_y = event.y

    def _on_drag_motion(self, event):
        """拖拽移动"""
        if self._dragging:
            x = self.canvas.winfo_x() + event.x - self._drag_offset_x
            y = self.canvas.winfo_y() + event.y - self._drag_offset_y
            self.canvas.place(x=x, y=y)

    def _on_drag_release(self, event):
        """释放拖拽"""
        self._dragging = False

    def play_eat(self):
        """播放吃东西动画"""
        self.state = self.STATE_EAT
        self.frame_idx = 0

    def play_happy(self):
        """播放开心动画"""
        self.state = self.STATE_HAPPY
        self.frame_idx = 0
