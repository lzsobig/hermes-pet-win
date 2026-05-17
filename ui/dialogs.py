"""Dialogs — Backend selection + API setup"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit
)
from PySide6.QtCore import Qt

from theme import BG_PRIMARY, BG_CARD, BG_CARD2, TEXT_PRIMARY, TEXT_MUTED, ACCENT, GREEN


class BackendSelectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected = None
        self.setWindowTitle("Select AI Backend")
        self.setFixedSize(420, 280)
        self.setStyleSheet(f"background-color: {BG_PRIMARY};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)

        title = QLabel("Select AI Backend")
        title.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 16px; font-weight: bold;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(16)

        # Claude Code option
        claude_desc = QLabel("Claude Code (recommended)")
        claude_desc.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(claude_desc)

        claude_btn = QPushButton("Claude Code")
        claude_btn.setStyleSheet(
            f"background-color: {GREEN}; color: {BG_PRIMARY}; font-weight: bold; "
            f"padding: 10px 24px; font-size: 13px;"
        )
        claude_btn.clicked.connect(lambda: self._select("claude"))
        layout.addWidget(claude_btn)

        layout.addSpacing(12)

        # OpenAI API option
        api_desc = QLabel("OpenAI / mimo / NVIDIA API")
        api_desc.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(api_desc)

        api_btn = QPushButton("API Key")
        api_btn.setStyleSheet(
            f"background-color: {ACCENT}; color: {BG_PRIMARY}; font-weight: bold; "
            f"padding: 10px 24px; font-size: 13px;"
        )
        api_btn.clicked.connect(lambda: self._select("openai"))
        layout.addWidget(api_btn)

        layout.addStretch()

    def _select(self, backend: str):
        self.selected = backend
        self.accept()


class APISetupDialog(QDialog):
    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("API Configuration")
        self.setFixedSize(420, 320)
        self.setStyleSheet(f"background-color: {BG_PRIMARY};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)

        title = QLabel("API Configuration")
        title.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 16px; font-weight: bold;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(12)

        # API Key
        key_label = QLabel("API Key:")
        key_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(key_label)

        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setPlaceholderText("sk-...")
        self.key_input.setStyleSheet(
            f"background-color: {BG_CARD2}; color: {TEXT_PRIMARY}; padding: 8px 12px; font-size: 13px;"
        )
        layout.addWidget(self.key_input)

        layout.addSpacing(8)

        # Base URL
        url_label = QLabel("Base URL:")
        url_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(url_label)

        self.url_input = QLineEdit()
        self.url_input.setText(config.get("api", {}).get("base_url", ""))
        self.url_input.setStyleSheet(
            f"background-color: {BG_CARD2}; color: {TEXT_PRIMARY}; padding: 8px 12px; font-size: 13px;"
        )
        layout.addWidget(self.url_input)

        layout.addSpacing(8)

        # Model
        model_label = QLabel("Model:")
        model_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(model_label)

        self.model_input = QLineEdit()
        self.model_input.setText(config.get("api", {}).get("model", ""))
        self.model_input.setStyleSheet(
            f"background-color: {BG_CARD2}; color: {TEXT_PRIMARY}; padding: 8px 12px; font-size: 13px;"
        )
        layout.addWidget(self.model_input)

        layout.addSpacing(16)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(
            f"background-color: {BG_CARD2}; color: {TEXT_MUTED}; padding: 8px 20px;"
        )
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(
            f"background-color: {ACCENT}; color: {BG_PRIMARY}; font-weight: bold; padding: 8px 20px;"
        )
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _save(self):
        self.config["api"]["api_key"] = self.key_input.text().strip()
        self.config["api"]["base_url"] = self.url_input.text().strip()
        self.config["api"]["model"] = self.model_input.text().strip()
        self.accept()
