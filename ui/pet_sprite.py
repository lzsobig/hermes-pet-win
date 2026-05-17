"""Pixel pet sprite — QLabel + QPixmap + QTimer animation (enhanced)"""
import math
import random
from PySide6.QtWidgets import QLabel, QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QImage, QPainter, QColor, QRadialGradient
from PIL import Image, ImageDraw, ImageFilter


class PetSprite(QLabel):
    STATE_IDLE = "idle"
    STATE_WALK = "walk"
    STATE_EAT = "eat"
    STATE_HAPPY = "happy"

    def __init__(self, on_file_drop=None):
        super().__init__()
        self.on_file_drop = on_file_drop
        self.state = self.STATE_IDLE
        self.direction = 1
        self.frame_idx = 0
        self._walk_timer = 0
        self._dragging = False
        self._drag_offset = (0, 0)
        self._bob_phase = 0

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(140, 140)

        # Generate all sprites
        self.sprites = self._create_sprites()
        self.setPixmap(self.sprites["idle"][0])

        self.setAcceptDrops(True)

        # Animation timer
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._animate)
        self._anim_timer.start(50)

        # Position at screen bottom-right
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 170, screen.height() - 200)

    def _pil_to_pixmap(self, img: Image.Image) -> QPixmap:
        # Add subtle shadow
        shadow = Image.new("RGBA", (img.width + 16, img.height + 16), (0, 0, 0, 0))
        # Create shadow circle
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.ellipse([8, img.height - 4, img.width + 8, img.height + 12], fill=(0, 0, 0, 40))
        shadow = shadow.filter(ImageFilter.GaussianBlur(4))
        # Paste sprite on top
        shadow.paste(img, (8, 0), img)

        data = shadow.tobytes("raw", "RGBA")
        qimg = QImage(data, shadow.width, shadow.height, QImage.Format.Format_RGBA8888)
        return QPixmap.fromImage(qimg)

    def _create_sprites(self) -> dict:
        sprites = {}
        size = 80
        bg = (0, 0, 0, 0)
        s = 1

        # Color palette
        BODY = "#ff9f43"
        BODY_DARK = "#e8852e"
        BODY_LIGHT = "#ffb86c"
        EAR_INNER = "#ff6b6b"
        EYE = "#1a1a2e"
        EYE_SHINE = "#ffffff"
        MOUTH = "#1a1a2e"
        CHEEK = "#ff6b6b"

        def draw_body(d, y_off=0):
            # Body shadow
            d.ellipse([18*s, (30+y_off)*s, 62*s, (38+y_off)*s], fill=(0, 0, 0, 30))
            # Main body
            d.rounded_rectangle([16*s, (14+y_off)*s, 64*s, (34+y_off)*s], radius=8*s, fill=BODY)
            # Body highlight
            d.rounded_rectangle([20*s, (16+y_off)*s, 50*s, (22+y_off)*s], radius=4*s, fill=BODY_LIGHT)

        def draw_ears(d, y_off=0):
            # Left ear
            d.polygon([(16*s, (14+y_off)*s), (24*s, (2+y_off)*s), (32*s, (14+y_off)*s)], fill=BODY)
            d.polygon([(20*s, (10+y_off)*s), (24*s, (5+y_off)*s), (28*s, (10+y_off)*s)], fill=EAR_INNER)
            # Right ear
            d.polygon([(48*s, (14+y_off)*s), (56*s, (2+y_off)*s), (64*s, (14+y_off)*s)], fill=BODY)
            d.polygon([(52*s, (10+y_off)*s), (56*s, (5+y_off)*s), (60*s, (10+y_off)*s)], fill=EAR_INNER)

        def draw_eyes(d, y_off=0, open=True):
            if open:
                # Left eye
                d.ellipse([24*s, (18+y_off)*s, 32*s, (26+y_off)*s], fill=EYE)
                d.ellipse([26*s, (19+y_off)*s, 29*s, (22+y_off)*s], fill=EYE_SHINE)
                # Right eye
                d.ellipse([48*s, (18+y_off)*s, 56*s, (26+y_off)*s], fill=EYE)
                d.ellipse([50*s, (19+y_off)*s, 53*s, (22+y_off)*s], fill=EYE_SHINE)
            else:
                # Closed eyes (lines)
                d.line([(24*s, (22+y_off)*s), (32*s, (22+y_off)*s)], fill=EYE, width=2)
                d.line([(48*s, (22+y_off)*s), (56*s, (22+y_off)*s)], fill=EYE, width=2)

        def draw_mouth(d, y_off=0, style="smile"):
            if style == "smile":
                d.arc([30*s, (24+y_off)*s, 50*s, (32+y_off)*s], start=0, end=180, fill=MOUTH, width=2)
            elif style == "open":
                d.ellipse([34*s, (25+y_off)*s, 46*s, (33+y_off)*s], fill=MOUTH)
                d.ellipse([36*s, (26+y_off)*s, 44*s, (30+y_off)*s], fill="#ff6b6b")
            elif style == "happy":
                d.arc([30*s, (22+y_off)*s, 50*s, (32+y_off)*s], start=0, end=180, fill=MOUTH, width=2)

        def draw_cheeks(d, y_off=0):
            d.ellipse([16*s, (22+y_off)*s, 22*s, (26+y_off)*s], fill=(255, 107, 107, 80))
            d.ellipse([58*s, (22+y_off)*s, 64*s, (26+y_off)*s], fill=(255, 107, 107, 80))

        def draw_tail(d, phase=0, y_off=0):
            tail_y = int(math.sin(phase) * 4)
            d.line([(64*s, (26+y_off)*s), (72*s, (22+tail_y+y_off)*s), (70*s, (16+tail_y+y_off)*s)],
                   fill=BODY, width=3)

        # === IDLE ===
        img = Image.new("RGBA", (size, size), bg)
        d = ImageDraw.Draw(img)
        draw_body(d)
        draw_ears(d)
        draw_eyes(d, open=True)
        draw_mouth(d, style="smile")
        draw_cheeks(d)
        draw_tail(d, 0)
        sprites["idle"] = [self._pil_to_pixmap(img)]

        # === BLINK ===
        img2 = Image.new("RGBA", (size, size), bg)
        d = ImageDraw.Draw(img2)
        draw_body(d)
        draw_ears(d)
        draw_eyes(d, open=False)
        draw_mouth(d, style="smile")
        draw_cheeks(d)
        draw_tail(d, 0)
        sprites["blink"] = [self._pil_to_pixmap(img2)]

        # === WALK (2 frames) ===
        for frame in range(2):
            img_w = Image.new("RGBA", (size, size), bg)
            d = ImageDraw.Draw(img_w)
            leg_off = 2 if frame == 0 else -2
            # Legs
            d.line([(28*s, 34*s), (24*s, (38+leg_off)*s)], fill=BODY_DARK, width=3)
            d.line([(52*s, 34*s), (56*s, (38-leg_off)*s)], fill=BODY_DARK, width=3)
            draw_body(d)
            draw_ears(d)
            draw_eyes(d, open=True)
            draw_mouth(d, style="smile")
            draw_cheeks(d)
            draw_tail(d, frame * math.pi)
            sprites.setdefault("walk", []).append(self._pil_to_pixmap(img_w))

        # === EAT ===
        img_e = Image.new("RGBA", (size, size), bg)
        d = ImageDraw.Draw(img_e)
        draw_body(d)
        draw_ears(d)
        draw_eyes(d, open=True)
        draw_mouth(d, style="open")
        draw_cheeks(d)
        draw_tail(d, 0.5)
        sprites["eat"] = [self._pil_to_pixmap(img_e)]

        # === HAPPY ===
        img_h = Image.new("RGBA", (size, size), bg)
        d = ImageDraw.Draw(img_h)
        draw_body(d)
        draw_ears(d)
        # Heart eyes
        d.text((24*s, 17*s), "♥", fill="#ff6b6b")
        d.text((48*s, 17*s), "♥", fill="#ff6b6b")
        draw_mouth(d, style="happy")
        draw_cheeks(d)
        draw_tail(d, 1.0)
        sprites["happy"] = [self._pil_to_pixmap(img_h)]

        return sprites

    def _animate(self):
        self.frame_idx += 1
        self._bob_phase += 0.15

        if self.state == self.STATE_IDLE:
            # Subtle bobbing
            if self.frame_idx % 80 == 0:
                self.setPixmap(self.sprites["blink"][0])
            elif self.frame_idx % 80 == 6:
                self.setPixmap(self.sprites["idle"][0])

        elif self.state == self.STATE_WALK:
            frame = self.sprites["walk"][self.frame_idx % 2]
            self.setPixmap(frame)
            x = self.x() + self.direction * 2
            screen = QApplication.primaryScreen().geometry()
            if x < 10 or x > screen.width() - 80:
                self.direction *= -1
            self.move(x, self.y())
            self._walk_timer += 1
            if self._walk_timer > 80:
                self.state = self.STATE_IDLE
                self._walk_timer = 0
                self.setPixmap(self.sprites["idle"][0])

        elif self.state == self.STATE_EAT:
            self.setPixmap(self.sprites["eat"][0])
            if self.frame_idx % 30 == 0:
                self.state = self.STATE_HAPPY
                self.frame_idx = 0

        elif self.state == self.STATE_HAPPY:
            self.setPixmap(self.sprites["happy"][0])
            if self.frame_idx % 50 == 0:
                self.state = self.STATE_IDLE
                self.setPixmap(self.sprites["idle"][0])

        # Random wander
        if self.state == self.STATE_IDLE and random.random() < 0.004:
            self.state = self.STATE_WALK
            self.direction = random.choice([-1, 1])
            self._walk_timer = 0

    def enterEvent(self, event):
        if self.state == self.STATE_IDLE:
            self.state = self.STATE_WALK
            self.direction = 1 if event.position().x() > 70 else -1
            self._walk_timer = 0

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_offset = (
                int(event.position().x()),
                int(event.position().y()),
            )

    def mouseMoveEvent(self, event):
        if self._dragging and event.buttons() & Qt.MouseButton.LeftButton:
            x = self.x() + int(event.position().x()) - self._drag_offset[0]
            y = self.y() + int(event.position().y()) - self._drag_offset[1]
            self.move(x, y)

    def mouseReleaseEvent(self, event):
        self._dragging = False

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls and self.on_file_drop:
            path = urls[0].toLocalFile()
            self.on_file_drop(path)
            self.play_eat()

    def play_eat(self):
        self.state = self.STATE_EAT
        self.frame_idx = 0

    def play_happy(self):
        self.state = self.STATE_HAPPY
        self.frame_idx = 0
