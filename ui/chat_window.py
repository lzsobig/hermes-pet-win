"""Chat window — QTextEdit + Markdown rendering + streaming display (enhanced)"""
import os
import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel,
    QFileDialog, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QTextCursor

from theme import (
    BG_DEEP, BG_PRIMARY, BG_CARD, BG_CARD2, BG_CARD3,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    ACCENT, ACCENT_BRIGHT, GREEN, RED, PURPLE, PINK, GLOW_ACCENT,
)


def _render_markdown(text: str) -> str:
    """Convert markdown to styled HTML with polished rendering."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Code blocks with language hint
    def code_block(m):
        lang = m.group(1) or ""
        code = m.group(2)
        return (
            f'<div style="background:{BG_DEEP};border:1px solid rgba(255,255,255,0.06);'
            f'border-radius:10px;margin:10px 0;overflow:hidden;">'
            f'<div style="background:{BG_CARD3};padding:6px 14px;font-size:11px;'
            f'color:{TEXT_MUTED};border-bottom:1px solid rgba(255,255,255,0.04);">'
            f'{lang if lang else "code"}</div>'
            f'<pre style="margin:0;padding:12px 16px;color:#a5f3fc;font-family:Consolas,monospace;'
            f'font-size:13px;line-height:1.5;overflow-x:auto;"><code>{code}</code></pre></div>'
        )
    text = re.sub(r"```(\w*)\n(.*?)```", code_block, text, flags=re.DOTALL)

    # Inline code
    text = re.sub(
        r"`([^`]+)`",
        f'<code style="background:{BG_CARD3};color:#a5f3fc;padding:2px 7px;border-radius:5px;'
        f'font-family:Consolas,monospace;font-size:12px;">\\1</code>',
        text,
    )

    # Bold
    text = re.sub(
        r"\*\*(.+?)\*\*",
        f'<strong style="color:{PINK};font-weight:700;">\\1</strong>',
        text,
    )

    # Italic
    text = re.sub(
        r"\*(.+?)\*",
        f'<em style="color:{TEXT_SECONDARY};">\\1</em>',
        text,
    )

    # Headings with accent line
    for level, size, margin in [("###", "15px", "10px 0 4px"), ("##", "17px", "14px 0 6px"), ("#", "20px", "18px 0 8px")]:
        text = re.sub(
            rf"^{re.escape(level)} (.+)$",
            f'<div style="color:{PURPLE};font-size:{size};font-weight:700;margin:{margin};'
            f'padding-bottom:4px;border-bottom:2px solid rgba(192,132,252,0.2);">\\1</div>',
            text, flags=re.MULTILINE,
        )

    # Bullets
    text = re.sub(
        r"^- (.+)$",
        f'<div style="margin:3px 0;padding-left:20px;"><span style="color:{ACCENT};">•</span> '
        f'<span style="color:{TEXT_PRIMARY};">\\1</span></div>',
        text, flags=re.MULTILINE,
    )

    # Numbered list
    counter = [0]
    def num_list(m):
        counter[0] += 1
        return (
            f'<div style="margin:3px 0;padding-left:20px;">'
            f'<span style="color:{ACCENT};font-weight:700;">{counter[0]}.</span> '
            f'<span style="color:{TEXT_PRIMARY};">{m.group(2)}</span></div>'
        )
    text = re.sub(r"^\d+\.\s(.+)$", num_list, text, flags=re.MULTILINE)

    # Links
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        f'<a href="\\2" style="color:{ACCENT};text-decoration:none;">\\1</a>',
        text,
    )

    # Line breaks
    text = text.replace("\n", "<br>")

    return text


CSS_BUBBLE_USER = f"""
    background: linear-gradient(135deg, {ACCENT}, {ACCENT_BRIGHT});
    background-color: {ACCENT};
    color: {BG_DEEP};
    border-radius: 16px 16px 4px 16px;
    padding: 12px 16px;
    font-size: 14px;
    line-height: 1.5;
    margin: 6px 0;
"""

CSS_BUBBLE_AI = f"""
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid rgba(255,255,255,0.04);
    border-radius: 16px 16px 16px 4px;
    padding: 14px 18px;
    font-size: 14px;
    line-height: 1.6;
    margin: 6px 0;
"""

CSS_ERROR = f"""
    background-color: rgba(248, 113, 113, 0.1);
    color: {RED};
    border: 1px solid rgba(248, 113, 113, 0.2);
    border-radius: 12px;
    padding: 12px 16px;
    font-size: 13px;
"""


class ChatWindow(QWidget):
    message_sent = Signal(list)

    def __init__(self):
        super().__init__()
        self.messages = []
        self._stream_buf = ""
        self.is_visible = False
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(f"background-color: {BG_PRIMARY};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # === Top bar ===
        top_bar = QFrame()
        top_bar.setFixedHeight(52)
        top_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border-bottom: 1px solid rgba(255,255,255,0.04);
            }}
        """)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 0, 20, 0)
        top_layout.setSpacing(12)

        # Mode indicator
        mode_dot = QLabel("✦")
        mode_dot.setStyleSheet(f"color: {ACCENT}; font-size: 18px; font-weight: bold; background: transparent;")
        top_layout.addWidget(mode_dot)

        title = QLabel("Hermes AI")
        title.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 15px; font-weight: 700; background: transparent; "
            f"letter-spacing: 0.3px;"
        )
        top_layout.addWidget(title)

        subtitle = QLabel("● online")
        subtitle.setStyleSheet(
            f"color: {GREEN}; font-size: 11px; font-weight: 500; background: transparent; "
            f"margin-top: 2px;"
        )
        top_layout.addWidget(subtitle)

        top_layout.addStretch()

        # Action buttons
        for text, callback in [("📎", self._attach_file), ("🗑", self.clear_chat), ("✕", self.hide)]:
            btn = QPushButton(text)
            btn.setFixedSize(36, 36)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {TEXT_MUTED};
                    border: none;
                    border-radius: 18px;
                    font-size: 16px;
                }}
                QPushButton:hover {{
                    background-color: rgba(255,255,255,0.06);
                    color: {TEXT_PRIMARY};
                }}
            """)
            btn.clicked.connect(callback)
            top_layout.addWidget(btn)

        layout.addWidget(top_bar)

        # === Chat display ===
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BG_PRIMARY};
                color: {TEXT_PRIMARY};
                border: none;
                padding: 20px 24px;
                font-size: 14px;
                line-height: 1.6;
            }}
        """)
        self.chat_display.setHtml(self._welcome_html())
        layout.addWidget(self.chat_display, 1)

        # === Input bar ===
        input_frame = QFrame()
        input_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border-top: 1px solid rgba(255,255,255,0.04);
            }}
        """)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(20, 14, 20, 14)
        input_layout.setSpacing(12)

        self.input_box = QTextEdit()
        self.input_box.setFixedHeight(48)
        self.input_box.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BG_CARD2};
                color: {TEXT_PRIMARY};
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 24px;
                padding: 12px 20px;
                font-size: 14px;
                selection-background-color: rgba(125, 211, 252, 0.3);
            }}
            QTextEdit:focus {{
                border-color: rgba(125, 211, 252, 0.3);
            }}
        """)
        self.input_box.setPlaceholderText("Type a message...")
        self.input_box.installEventFilter(self)
        input_layout.addWidget(self.input_box, 1)

        send_btn = QPushButton("→")
        send_btn.setFixedSize(48, 48)
        send_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {ACCENT}, stop:1 {ACCENT_BRIGHT});
                color: {BG_DEEP};
                border: none;
                border-radius: 24px;
                font-size: 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {ACCENT_BRIGHT}, stop:1 {ACCENT});
            }}
            QPushButton:pressed {{
                background: {ACCENT_BRIGHT};
            }}
        """)
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)

        layout.addWidget(input_frame)

    def _welcome_html(self) -> str:
        return f"""
        <div style="text-align:center; padding:60px 40px;">
            <div style="font-size:48px; margin-bottom:16px;">✦</div>
            <div style="color:{TEXT_PRIMARY}; font-size:20px; font-weight:700; margin-bottom:8px;">
                Hello! I'm Hermes AI
            </div>
            <div style="color:{TEXT_MUTED}; font-size:14px; line-height:1.6;">
                Your desktop AI companion. Ask me anything,<br>
                or drag a file to me to get started.
            </div>
            <div style="margin-top:24px; display:flex; justify-content:center; gap:8px;">
                <span style="background:{BG_CARD2}; color:{TEXT_MUTED}; padding:6px 14px;
                border-radius:20px; font-size:12px; border:1px solid rgba(255,255,255,0.06);">
                    Enter to send
                </span>
                <span style="background:{BG_CARD2}; color:{TEXT_MUTED}; padding:6px 14px;
                border-radius:20px; font-size:12px; border:1px solid rgba(255,255,255,0.06);">
                    Shift+Enter for newline
                </span>
            </div>
        </div>
        """

    def eventFilter(self, obj, event):
        if obj == self.input_box and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.send_message()
                return True
        return super().eventFilter(obj, event)

    def show(self):
        self.is_visible = True
        self.setVisible(True)
        self.input_box.setFocus()

    def hide(self):
        self.is_visible = False
        self.setVisible(False)

    def toggle(self):
        if self.is_visible:
            self.hide()
        else:
            self.show()

    def clear_chat(self):
        self.messages.clear()
        self.chat_display.setHtml(self._welcome_html())

    def _append_message(self, role: str, html: str):
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)
        self.chat_display.insertHtml(html)
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)

    def send_message(self):
        text = self.input_box.toPlainText().strip()
        if not text:
            return

        self.input_box.clear()

        # User bubble
        self._append_message("user",
            f'<div style="{CSS_BUBBLE_USER}">'
            f'{text.replace(chr(10), "<br>")}'
            f'</div><br>'
        )

        self.messages.append({"role": "user", "content": text})
        self._stream_buf = ""

        # AI thinking indicator
        self._append_message("ai",
            f'<div style="{CSS_BUBBLE_AI}" id="ai-stream">'
            f'<span style="color:{ACCENT};">●</span> thinking...'
            f'</div>'
        )

        self.message_sent.emit(self.messages)

    def on_chunk(self, chunk: str, full_text: str):
        self._stream_buf = full_text
        # Replace the streaming bubble with full content
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        # Select and replace the last AI bubble
        html = _render_markdown(full_text)
        # Simple: clear and rebuild all messages
        self._rebuild_display()

    def on_done(self, full_text: str):
        self.messages.append({"role": "assistant", "content": full_text})
        self._rebuild_display()

    def on_error(self, error: str):
        self._append_message("error",
            f'<div style="{CSS_ERROR}">⚠ {error}</div><br>'
        )

    def _rebuild_display(self):
        """Rebuild the entire chat display from message history."""
        html_parts = [self._welcome_html()]

        for msg in self.messages:
            role = msg["role"]
            content = msg["content"]
            if role == "user":
                bubble = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                bubble = bubble.replace("\n", "<br>")
                html_parts.append(
                    f'<div style="{CSS_BUBBLE_USER}">{bubble}</div><br>'
                )
            elif role == "assistant":
                html_parts.append(
                    f'<div style="{CSS_BUBBLE_AI}">{_render_markdown(content)}</div><br>'
                )

        # Show streaming content if in progress
        if self._stream_buf and not self.messages or (
            self.messages and self.messages[-1]["role"] != "assistant"
        ):
            html_parts.append(
                f'<div style="{CSS_BUBBLE_AI}">{_render_markdown(self._stream_buf)}</div><br>'
            )

        self.chat_display.setHtml("".join(html_parts))
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)

    def _attach_file(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select File", "",
            "Text files (*.txt *.md *.py *.json *.csv *.log);;All files (*)"
        )
        if filepath:
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(8000)
                fname = os.path.basename(filepath)
                self._append_message("user",
                    f'<div style="background:{BG_CARD3};color:{ACCENT};border-radius:12px;'
                    f'padding:10px 16px;margin:6px 0;font-size:13px;">'
                    f'📎 {fname}</div><br>'
                )
                self.messages.append({
                    "role": "user",
                    "content": f"[Attachment: {fname}]\n{content}"
                })
            except Exception as e:
                self.on_error(str(e))
