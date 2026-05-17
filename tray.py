"""系统托盘 — 菜单栏图标 + 状态指示"""
import pystray
from PIL import Image, ImageDraw
import threading


def create_tray_icon(state: str = "idle") -> Image.Image:
    """创建托盘图标"""
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    colors = {
        "idle": "#4ade80",
        "thinking": "#60a5fa",
        "done": "#4ade80",
        "error": "#f59e0b",
    }
    color = colors.get(state, "#4ade80")

    # 简化小猫图标
    d.rounded_rectangle([6, 8, 26, 26], radius=6, fill=color)
    d.polygon([(6, 8), (10, 2), (16, 8)], fill=color)
    d.polygon([(16, 8), (22, 2), (26, 8)], fill=color)
    d.ellipse([10, 14, 14, 18], fill="#1a1a2e")
    d.ellipse([18, 14, 22, 18], fill="#1a1a2e")

    return img


class SystemTray:
    """系统托盘管理"""

    def __init__(self, on_toggle_chat=None, on_show_status=None,
                 on_settings=None, on_quit=None):
        self.on_toggle_chat = on_toggle_chat
        self.on_show_status = on_show_status
        self.on_settings = on_settings
        self.on_quit = on_quit
        self.icon = None
        self._state = "idle"

    def create(self):
        """创建并启动托盘"""
        menu = pystray.Menu(
            pystray.MenuItem("打开聊天", self._toggle_chat, default=True),
            pystray.MenuItem("查看状态", self._show_status),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("设置", self._settings),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self._quit),
        )

        self.icon = pystray.Icon(
            name="HermesPet",
            icon=create_tray_icon("idle"),
            title="Hermes AI — 就绪",
            menu=menu
        )

        thread = threading.Thread(target=self.icon.run, daemon=True)
        thread.start()
        return thread

    def update_state(self, state: str, title: str = ""):
        """更新托盘状态"""
        self._state = state
        if self.icon:
            self.icon.icon = create_tray_icon(state)
            if title:
                self.icon.title = title

    def _toggle_chat(self, icon=None, item=None):
        if self.on_toggle_chat:
            self.on_toggle_chat()

    def _show_status(self, icon=None, item=None):
        if self.on_show_status:
            self.on_show_status()

    def _settings(self, icon=None, item=None):
        if self.on_settings:
            self.on_settings()

    def _quit(self, icon=None, item=None):
        if self.icon:
            self.icon.stop()
        if self.on_quit:
            self.on_quit()
