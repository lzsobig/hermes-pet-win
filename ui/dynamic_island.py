"""Dynamic Island — floating capsule at screen top showing AI state"""
from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout, QVBoxLayout, QApplication
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QSize
from PySide6.QtGui import QPixmap, QPainter, QColor, QLinearGradient, QFont

from theme import (
    BG_CARD, BG_CARD2, BG_CARD3, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    GREEN, RED, AMBER, ACCENT, ACCENT_BRIGHT, GLOW_ACCENT,
)


def _draw_dot(color: str, size: int = 12, glow: bool = False) -> QPixmap:
    pixmap = QPixmap(size + 8, size + 8)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    if glow:
        # Outer glow
        for i in range(4):
            alpha = 60 - i * 15
            c = QColor(color)
            c.setAlpha(alpha)
            painter.setBrush(c)
            painter.setPen(Qt.PenStyle.NoPen)
            offset = i * 2
            painter.drawEllipse(4 - offset, 4 - offset, size + offset * 2, size + offset * 2)

    # Core dot
    painter.setBrush(QColor(color))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(4, 4, size, size)

    # Inner highlight
    highlight = QColor(255, 255, 255, 120)
    painter.setBrush(highlight)
    painter.drawEllipse(6, 5, size // 3, size // 3)

    painter.end()
    return pixmap


class DynamicIsland(QFrame):
    STATE_IDLE = "idle"
    STATE_THINKING = "thinking"
    STATE_DONE = "done"
    STATE_ERROR = "error"

    def __init__(self, on_click=None):
        super().__init__()
        self.on_click = on_click
        self.state = self.STATE_IDLE
        self.preview_text = ""
        self.is_expanded = False
        self._pulse_phase = 0

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Outer container with shadow effect
        self.outer = QFrame(self)
        self.outer.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD2};
                border-radius: 22px;
                border: 1px solid rgba(255,255,255,0.08);
            }}
        """)

        # Main capsule row
        main_layout = QHBoxLayout(self.outer)
        main_layout.setContentsMargins(16, 0, 16, 0)
        main_layout.setSpacing(12)

        # Status dot with glow
        self.dot_container = QLabel()
        self.dot_container.setFixedSize(28, 28)
        self.dot_container.setStyleSheet("background: transparent;")
        self._update_dot(GREEN, glow=False)
        main_layout.addWidget(self.dot_container)

        # Mode icon + label
        self.mode_icon = QLabel("✦")
        self.mode_icon.setStyleSheet(f"color: {ACCENT}; font-size: 16px; font-weight: bold; background: transparent;")
        main_layout.addWidget(self.mode_icon)

        self.mode_label = QLabel("mimo")
        self.mode_label.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-weight: 700; font-size: 13px; "
            f"letter-spacing: 0.5px; background: transparent;"
        )
        main_layout.addWidget(self.mode_label)

        main_layout.addSpacing(4)

        # Status text
        self.status_label = QLabel("ready")
        self.status_label.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 12px; font-weight: 500; background: transparent;"
        )
        main_layout.addWidget(self.status_label)

        main_layout.addStretch()

        # Close button
        self.close_btn = QLabel("×")
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.close_btn.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_MUTED};
                font-size: 16px;
                font-weight: bold;
                background: transparent;
                border-radius: 12px;
            }}
            QLabel:hover {{
                background-color: rgba(255,255,255,0.1);
                color: {RED};
            }}
        """)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.mousePressEvent = lambda e: self.hide()
        main_layout.addWidget(self.close_btn)

        # Preview area (always created)
        self.preview_container = QFrame()
        self.preview_container.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD3};
                border-radius: 0 0 20px 20px;
                border-top: 1px solid rgba(255,255,255,0.04);
            }}
        """)
        preview_layout = QVBoxLayout(self.preview_container)
        preview_layout.setContentsMargins(16, 10, 16, 12)
        preview_layout.setSpacing(4)

        self.preview_label = QLabel()
        self.preview_label.setWordWrap(True)
        self.preview_label.setStyleSheet(f"""
            color: {TEXT_SECONDARY};
            font-size: 12px;
            line-height: 1.5;
            background: transparent;
        """)
        preview_layout.addWidget(self.preview_label)
        self.preview_container.hide()

        # Outer layout
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        outer_layout.addWidget(self.outer)
        outer_layout.addWidget(self.preview_container)

        self.setFixedWidth(320)

        # Pulse timer
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._pulse_tick)
        self._pulse_timer.start(150)

        # Hover events
        self.outer.enterEvent = self._on_hover_enter
        self.outer.leaveEvent = self._on_hover_leave

        # Click + Drag
        self._drag_pos = None
        self._press_pos = None
        self.outer.mousePressEvent = self._on_press
        self.outer.mouseMoveEvent = self._on_move
        self.outer.mouseReleaseEvent = self._on_release

        self._center_on_screen()

    def _update_dot(self, color: str, glow: bool = False):
        self.dot_container.setPixmap(_draw_dot(color, glow=glow))

    def _center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        w = self.width() or 320
        self.setGeometry(screen.width() // 2 - w // 2, 10, w, 44)

    def _on_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.pos()
            self._press_pos = event.globalPosition().toPoint()

    def _on_move(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self._press_pos
            if abs(delta.x()) > 5 or abs(delta.y()) > 5:
                self.move(event.globalPosition().toPoint() - self._drag_pos)

    def _on_release(self, event):
        if self._drag_pos and self.on_click:
            delta = event.globalPosition().toPoint() - self._press_pos
            if abs(delta.x()) < 5 and abs(delta.y()) < 5:
                self.on_click()
        self._drag_pos = None
        self._press_pos = None

    def _on_hover_enter(self, event):
        if self.preview_text and not self.is_expanded:
            self.is_expanded = True
            text = self.preview_text[:120]
            if len(self.preview_text) > 120:
                text += "..."
            self.preview_label.setText(text)
            self.preview_container.show()
            h = 44 + max(50, self.preview_label.sizeHint().height() + 20)
            self.setFixedHeight(h)
            # Glow effect on hover
            self.outer.setStyleSheet(f"""
                QFrame {{
                    background-color: {BG_CARD2};
                    border-radius: 22px;
                    border: 1px solid rgba(125, 211, 252, 0.2);
                }}
            """)

    def _on_hover_leave(self, event):
        if self.is_expanded:
            self.is_expanded = False
            self.preview_container.hide()
            self.setFixedHeight(44)
            self.outer.setStyleSheet(f"""
                QFrame {{
                    background-color: {BG_CARD2};
                    border-radius: 22px;
                    border: 1px solid rgba(255,255,255,0.08);
                }}
            """)

    def _pulse_tick(self):
        if self.state == self.STATE_THINKING:
            self._pulse_phase = (self._pulse_phase + 1) % 20
            t = self._pulse_phase / 20.0
            # Smooth sine wave
            import math
            intensity = int(100 + 100 * abs(math.sin(t * math.pi)))
            color = f"#{intensity:02x}{intensity:02x}ff"
            self._update_dot(color, glow=True)
            self.status_label.setText("thinking...")
            self.status_label.setStyleSheet(
                f"color: {ACCENT}; font-size: 12px; font-weight: 600; background: transparent;"
            )
            self.mode_icon.setStyleSheet(
                f"color: {ACCENT}; font-size: 16px; font-weight: bold; background: transparent;"
            )
        elif self.state == self.STATE_DONE:
            self._update_dot(GREEN, glow=True)
            self.status_label.setText("done")
            self.status_label.setStyleSheet(
                f"color: {GREEN}; font-size: 12px; font-weight: 600; background: transparent;"
            )
            self.mode_icon.setStyleSheet(
                f"color: {GREEN}; font-size: 16px; font-weight: bold; background: transparent;"
            )
        elif self.state == self.STATE_ERROR:
            self._update_dot(AMBER, glow=True)
            self.status_label.setText("error")
            self.status_label.setStyleSheet(
                f"color: {AMBER}; font-size: 12px; font-weight: 600; background: transparent;"
            )
            self.mode_icon.setStyleSheet(
                f"color: {AMBER}; font-size: 16px; font-weight: bold; background: transparent;"
            )
        else:
            self._update_dot(GREEN, glow=False)
            self.status_label.setText("ready")
            self.status_label.setStyleSheet(
                f"color: {TEXT_MUTED}; font-size: 12px; font-weight: 500; background: transparent;"
            )
            self.mode_icon.setStyleSheet(
                f"color: {ACCENT}; font-size: 16px; font-weight: bold; background: transparent;"
            )

    def set_state(self, state: str, preview: str = ""):
        self.state = state
        if preview:
            self.preview_text = preview

    def showEvent(self, event):
        self._center_on_screen()
        super().showEvent(event)
