"""Hermes Pet Win — Desktop AI Companion (PySide6)"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt

from config import load_config, save_config
from bridge import AIBridge
from hotkeys import HotkeyManager
from ui.dynamic_island import DynamicIsland
from ui.pet_sprite import PetSprite
from ui.chat_window import ChatWindow
from ui.system_tray import SystemTray
from ui.dialogs import BackendSelectDialog, APISetupDialog
from theme import get_stylesheet


class HermesPetApp:
    def __init__(self):
        self.config = load_config()
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.app.setStyleSheet(get_stylesheet())

        # Hidden main window (owns all components)
        self.main_window = QWidget()
        self.main_window.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.main_window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.main_window.resize(0, 0)

        # Check backend config
        backend = self.config["api"].get("backend", "")
        api_key = self.config["api"].get("api_key", "")
        if not backend:
            self._show_backend_select()
        elif backend == "openai" and not api_key:
            self._show_api_setup()

        # Bridge (AI + Event engine)
        self.bridge = AIBridge(self.config)

        # UI components
        self.island = DynamicIsland(on_click=self._toggle_chat)
        self.pet = PetSprite(on_file_drop=self._on_file_drop)
        self.chat = ChatWindow()

        # System tray
        self.tray = SystemTray(
            on_toggle_chat=self._toggle_chat,
            on_show_status=self._show_status,
            on_quit=self._quit,
        )

        # Hotkeys
        self.hotkeys = HotkeyManager(self.config)
        self.hotkeys.register("toggle_chat", self._toggle_chat)
        self.hotkeys.start()

        # Wire signals
        self.bridge.state_changed.connect(self._on_ai_state)
        self.bridge.chunk_received.connect(self.chat.on_chunk)
        self.bridge.stream_done.connect(self.chat.on_done)
        self.bridge.stream_error.connect(self.chat.on_error)
        self.chat.message_sent.connect(self.bridge.send)

        # Show
        self.island.show()
        self.pet.show()
        self.tray.show()

    def _show_backend_select(self):
        dialog = BackendSelectDialog()
        if dialog.exec():
            self.config["api"]["backend"] = dialog.selected
            save_config(self.config)
            if dialog.selected == "openai":
                self._show_api_setup()

    def _show_api_setup(self):
        dialog = APISetupDialog(self.config)
        if dialog.exec():
            save_config(self.config)
            if hasattr(self, "bridge"):
                self.bridge.update_config(self.config)

    def _toggle_chat(self):
        self.chat.toggle()
        if self.chat.is_visible:
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()

    def _show_status(self):
        summary = self.bridge.event_engine.get_job_summary()
        self.island.set_state("idle", summary)

    def _on_ai_state(self, state: str, preview: str = ""):
        self.island.set_state(state, preview)
        self.tray.update_state(state, "Hermes AI")

    def _on_file_drop(self, filepath: str):
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(8000)
            fname = os.path.basename(filepath)
            self.chat._append_html(
                f'<p style="color:#7dd3fc;font-weight:bold;">📎 Attached: {fname}</p>'
            )
            self.chat.messages.append({
                "role": "user",
                "content": f"[Attachment: {fname}]\n{content}"
            })
        except Exception as e:
            self.chat.on_error(str(e))

    def _quit(self):
        self.hotkeys.stop()
        self.app.quit()

    def run(self):
        sys.exit(self.app.exec())


def main():
    app = HermesPetApp()
    app.run()


if __name__ == "__main__":
    main()
