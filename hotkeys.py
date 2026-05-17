"""全局快捷键管理"""
import keyboard
import threading


class HotkeyManager:
    """全局快捷键注册"""

    def __init__(self, config: dict):
        self.config = config
        self._handlers = {}
        self._registered = []

    def register(self, action: str, callback):
        """注册快捷键"""
        self._handlers[action] = callback

    def start(self):
        """启动所有快捷键监听"""
        hotkeys = self.config.get("hotkeys", {})

        mapping = {
            "toggle_chat": hotkeys.get("toggle_chat", "ctrl+shift+h"),
            "screenshot": hotkeys.get("screenshot", "ctrl+shift+j"),
            "quick_send": hotkeys.get("quick_send", "ctrl+shift+enter"),
        }

        for action, hotkey in mapping.items():
            if action in self._handlers:
                try:
                    keyboard.add_hotkey(hotkey, self._handlers[action])
                    self._registered.append(hotkey)
                except Exception as e:
                    print(f"[Hotkey] 注册失败 {hotkey}: {e}")

    def stop(self):
        """停止所有快捷键"""
        for hotkey in self._registered:
            try:
                keyboard.remove_hotkey(hotkey)
            except Exception:
                pass
        self._registered.clear()
