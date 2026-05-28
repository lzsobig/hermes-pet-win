"""Hermes Pet Win — Desktop AI Companion (tkinter)"""
import tkinter as tk
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import load_config, save_config
from ai_client import AIClient
from chat_window import ChatWindow
from pet_sprite import PetSprite
from event_engine import EventEngine
from tray import SystemTray
from hotkeys import HotkeyManager


class HermesPetApp:
    def __init__(self):
        self.config = load_config()
        self.root = tk.Tk()
        self.root.title("Hermes Pet Win")
        self.root.geometry("480x700+{}+{}".format(
            self.root.winfo_screenwidth() // 2 - 240,
            self.root.winfo_screenheight() // 2 - 350
        ))
        self.root.configure(bg="#0f0f23")
        self.root.attributes("-topmost", True)

        # Check if backend is configured
        backend = self.config["api"].get("backend", "")
        api_key = self.config["api"].get("api_key", "")
        if not backend:
            self._show_backend_select()
        elif backend == "openai" and not api_key:
            self._show_api_setup()

        self.ai_client = AIClient(self.config)
        self.event_engine = EventEngine(on_event=self._on_event)

        self.chat = ChatWindow(self.root, self.config,
                                ai_client=self.ai_client,
                                on_state_change=self._on_ai_state)

        self.pet = PetSprite(self.root, self.config)

        self.tray = SystemTray(
            on_toggle_chat=self._toggle_chat,
            on_show_status=self._show_status,
            on_quit=self._quit
        )

        self.hotkeys = HotkeyManager(self.config)
        self.hotkeys.register("toggle_chat", self._toggle_chat)
        self.hotkeys.start()

        self.tray.create()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.chat.show()

    def _show_backend_select(self):
        """Backend selection dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Select AI Backend")
        dialog.geometry("420x280")
        dialog.configure(bg="#0f0f23")
        dialog.attributes("-topmost", True)
        dialog.grab_set()

        tk.Label(dialog, text="Select AI Backend", fg="#e2e8f0",
                 bg="#0f0f23", font=("Segoe UI", 14, "bold")).pack(pady=16)

        tk.Label(dialog, text="Claude Code (recommended)", fg="#94a3b8",
                 bg="#0f0f23", font=("Segoe UI", 10)).pack(anchor="w", padx=32)

        def select_claude():
            self.config["api"]["backend"] = "claude"
            save_config(self.config)
            dialog.destroy()

        def select_api():
            self.config["api"]["backend"] = "openai"
            save_config(self.config)
            dialog.destroy()
            self._show_api_setup()

        tk.Button(dialog, text="Claude Code", fg="#0f0f23", bg="#4ade80",
                  font=("Segoe UI", 10, "bold"), relief="flat",
                  padx=24, pady=8, command=select_claude).pack(pady=12)

        tk.Label(dialog, text="OpenAI / mimo / NVIDIA API", fg="#94a3b8",
                 bg="#0f0f23", font=("Segoe UI", 10)).pack(anchor="w", padx=32, pady=(8, 0))

        tk.Button(dialog, text="API Key", fg="#0f0f23", bg="#7dd3fc",
                  font=("Segoe UI", 10, "bold"), relief="flat",
                  padx=24, pady=8, command=select_api).pack(pady=8)

    def _show_api_setup(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("API Setup")
        dialog.geometry("420x320")
        dialog.configure(bg="#0f0f23")
        dialog.attributes("-topmost", True)
        dialog.grab_set()

        tk.Label(dialog, text="API Configuration", fg="#e2e8f0",
                 bg="#0f0f23", font=("Segoe UI", 14, "bold")).pack(pady=16)

        tk.Label(dialog, text="API Key:", fg="#94a3b8",
                 bg="#0f0f23", font=("Segoe UI", 10)).pack(anchor="w", padx=32)
        key_entry = tk.Entry(dialog, show="*", bg="#2d2d44", fg="#e2e8f0",
                             font=("Consolas", 10), relief="flat", width=40)
        key_entry.pack(padx=32, pady=(4, 12), ipady=6)

        tk.Label(dialog, text="Base URL:", fg="#94a3b8",
                 bg="#0f0f23", font=("Segoe UI", 10)).pack(anchor="w", padx=32)
        url_entry = tk.Entry(dialog, bg="#2d2d44", fg="#e2e8f0",
                             font=("Consolas", 10), relief="flat", width=40)
        url_entry.insert(0, self.config["api"]["base_url"])
        url_entry.pack(padx=32, pady=(4, 12), ipady=6)

        tk.Label(dialog, text="Model:", fg="#94a3b8",
                 bg="#0f0f23", font=("Segoe UI", 10)).pack(anchor="w", padx=32)
        model_entry = tk.Entry(dialog, bg="#2d2d44", fg="#e2e8f0",
                               font=("Consolas", 10), relief="flat", width=40)
        model_entry.insert(0, self.config["api"]["model"])
        model_entry.pack(padx=32, pady=(4, 16), ipady=6)

        def save():
            self.config["api"]["api_key"] = key_entry.get().strip()
            self.config["api"]["base_url"] = url_entry.get().strip()
            self.config["api"]["model"] = model_entry.get().strip()
            save_config(self.config)
            self.ai_client.update_config(self.config)
            dialog.destroy()

        tk.Button(dialog, text="Save", fg="#0f0f23", bg="#7dd3fc",
                  font=("Segoe UI", 10, "bold"), relief="flat",
                  padx=24, pady=6, command=save).pack(pady=8)

    def _toggle_chat(self):
        self.chat.toggle()
        if self.chat.is_visible:
            self.root.deiconify()
            self.root.focus_force()

    def _show_status(self):
        summary = self.event_engine.get_job_summary()
        self.island.set_state("idle", summary)

    def _on_event(self, event_type, data):
        """事件处理 - 批量更新 UI 减少刷新"""
        state_map = {
            "job_started": "thinking", "job_finished": "done", "job_failed": "error",
        }
        state = state_map.get(event_type, "idle")
        name = data.get("name", "")
        
        # 批量更新，避免多次调用
        def update_ui():
            self.island.set_state(state, name)
            self.tray.update_state(state, name)
        
        self.root.after(0, update_ui)

    def _on_ai_state(self, state, preview=""):
        self.island.set_state(state, preview)
        self.tray.update_state(state, f"Hermes AI")

    def _on_close(self):
        self.root.withdraw()

    def _quit(self):
        self.hotkeys.stop()
        self.root.destroy()
        sys.exit(0)

    def run(self):
        self.root.mainloop()


def main():
    app = HermesPetApp()
    app.run()


if __name__ == "__main__":
    main()
