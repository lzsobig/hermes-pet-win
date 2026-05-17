"""Qt Signal bridge — connects AIClient/EventEngine callbacks to Qt signals"""
from PySide6.QtCore import QObject, Signal

from ai_client import AIClient
from event_engine import EventEngine


class AIBridge(QObject):
    chunk_received = Signal(str, str)   # (chunk, full_text)
    stream_done = Signal(str)           # full_text
    stream_error = Signal(str)          # error message
    state_changed = Signal(str, str)    # (state, preview)

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.ai_client = AIClient(config)
        self.event_engine = EventEngine(on_event=self._on_event)

    def update_config(self, config: dict):
        self.config = config
        self.ai_client.update_config(config)

    def send(self, messages: list):
        self.state_changed.emit("thinking", "")
        self.ai_client.chat_stream(
            messages,
            on_chunk=self._on_chunk,
            on_done=self._on_done,
            on_error=self._on_error,
        )

    def _on_chunk(self, chunk: str, full_text: str):
        self.chunk_received.emit(chunk, full_text)

    def _on_done(self, full_text: str):
        self.stream_done.emit(full_text)
        self.state_changed.emit("done", full_text[:80])

    def _on_error(self, error: str):
        self.stream_error.emit(error)
        self.state_changed.emit("error", error)

    def _on_event(self, event_type: str, data: dict):
        state_map = {
            "job_started": "thinking",
            "job_finished": "done",
            "job_failed": "error",
        }
        state = state_map.get(event_type, "idle")
        name = data.get("name", "")
        self.state_changed.emit(state, name)
