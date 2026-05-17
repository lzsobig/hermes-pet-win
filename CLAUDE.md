# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Hermes Pet Win** — a Windows desktop AI companion built with Python (PySide6). Inspired by macOS [HermesPet](https://github.com/basionwang-bot/HermesPet). Combines a Dynamic Island status bar, a pixel pet sprite, an AI chat window, a system tray icon, and global hotkeys.

## Running the App

```bash
pip install PySide6 requests Pillow keyboard
python main_pyside6.py
```

Or use `launch.py`. Requires Python 3.10+.

## Architecture

```
main_pyside6.py        Entry point. QApplication + HermesPetApp coordinator.
                       Creates all components, wires Qt signals, handles lifecycle.

config.py              Config management. Reads/writes JSON at ~/.hermes_pet_win/config.json.

ai_client.py           Dual-backend AI client (OpenAI API streaming + Claude CLI subprocess).
                       Callback model: on_chunk, on_done, on_error. Runs in daemon threads.

bridge.py              AIBridge(QObject). Wraps AIClient/EventEngine callbacks as Qt Signals.
                       Thread-safe: queued connections handle cross-thread dispatch.

event_engine.py        Command wrapper. Runs shell commands in threads, records job status
                       to jobs.json, emits events via callback.

hotkeys.py             Global hotkey registration via the `keyboard` package.

theme.py               Color constants (BG_PRIMARY, ACCENT, etc.) + get_stylesheet() QSS.

ui/
  dynamic_island.py    Floating capsule at screen top. Qt.FramelessWindowHint + pulse animation.
  pet_sprite.py        Pixel cat sprite. QLabel + QPixmap + QTimer animation loop.
  chat_window.py       Chat UI. QTextEdit + Markdown→HTML rendering + streaming display.
  system_tray.py       QSystemTrayIcon (replaces pystray). No daemon thread needed.
  dialogs.py           BackendSelectDialog + APISetupDialog.
```

## Signal Flow

```
AIClient (daemon thread)
  → AIBridge.chunk_received Signal  → ChatWindow.on_chunk()
  → AIBridge.stream_done Signal     → ChatWindow.on_done()
  → AIBridge.stream_error Signal    → ChatWindow.on_error()
  → AIBridge.state_changed Signal   → DynamicIsland.set_state()
                                   → SystemTray.update_state()

ChatWindow.message_sent Signal → AIBridge.send() → AIClient.chat_stream()

HotkeyManager → toggle_chat callback → ChatWindow.toggle()
```

## AI Backend Configuration

Two backends, selected at first launch:

| Backend | How it works |
|---------|-------------|
| **Claude Code** | Spawns local `claude -p <prompt>` subprocess. Zero config needed. |
| **OpenAI API** | HTTP streaming to any OpenAI-compatible endpoint (mimo, NVIDIA, DeepSeek, etc.) |

Config is stored at `~/.hermes_pet_win/config.json`. Default API endpoint: `http://model.mify.ai.srv/v1`, default model: `mimo-v2.5-pro`.

## Key Patterns

- **Qt Signals replace callbacks**: AIBridge wraps AIClient's thread callbacks into Qt Signals, enabling thread-safe UI updates without `root.after()`.
- **Reusable backend modules**: `config.py`, `ai_client.py`, `event_engine.py`, `hotkeys.py` have zero UI dependency and are shared between the tkinter and PySide6 versions.
- **Pillow for sprite generation**: Pixel sprites are drawn with PIL ImageDraw, converted to QPixmap via QImage for display.
- **Config deep-merge**: User config is merged over defaults with `_deep_merge` so partial configs work correctly.

## Legacy Files

The original tkinter version files remain for reference: `main.py`, `chat_window.py`, `pet_sprite.py`, `dynamic_island.py`, `tray.py`. The PySide6 version in `main_pyside6.py` + `ui/` is the active codebase.
