"""System tray — QSystemTrayIcon with state-aware icon"""
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, QImage, QPainter, QColor
from PIL import Image, ImageDraw


def _create_icon(state: str = "idle") -> QIcon:
    colors = {
        "idle": "#4ade80",
        "thinking": "#60a5fa",
        "done": "#4ade80",
        "error": "#f59e0b",
    }
    color = colors.get(state, "#4ade80")

    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([6, 8, 26, 26], radius=6, fill=color)
    d.polygon([(6, 8), (10, 2), (16, 8)], fill=color)
    d.polygon([(16, 8), (22, 2), (26, 8)], fill=color)
    d.ellipse([10, 14, 14, 18], fill="#1a1a2e")
    d.ellipse([18, 14, 22, 18], fill="#1a1a2e")

    data = img.tobytes("raw", "RGBA")
    qimg = QImage(data, 32, 32, QImage.Format.Format_RGBA8888)
    return QIcon(QPixmap.fromImage(qimg))


class SystemTray:
    def __init__(self, on_toggle_chat=None, on_show_status=None, on_quit=None):
        self.on_toggle_chat = on_toggle_chat
        self.on_show_status = on_show_status
        self.on_quit = on_quit

        self.icon = QSystemTrayIcon()
        self.icon.setIcon(_create_icon("idle"))
        self.icon.setToolTip("Hermes AI — ready")

        menu = QMenu()
        menu.addAction("Open Chat", self._toggle_chat)
        menu.addAction("View Status", self._show_status)
        menu.addSeparator()
        menu.addAction("Quit", self._quit)
        self.icon.setContextMenu(menu)
        self.icon.activated.connect(self._on_activated)

    def show(self):
        self.icon.show()

    def update_state(self, state: str, title: str = ""):
        self.icon.setIcon(_create_icon(state))
        if title:
            self.icon.setToolTip(title)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._toggle_chat()

    def _toggle_chat(self):
        if self.on_toggle_chat:
            self.on_toggle_chat()

    def _show_status(self):
        if self.on_show_status:
            self.on_show_status()

    def _quit(self):
        if self.on_quit:
            self.on_quit()
