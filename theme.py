"""Design tokens + QSS stylesheet for Hermes Pet Win (PySide6)"""

# Background layers
BG_DEEP = "#080816"
BG_PRIMARY = "#0f0f23"
BG_CARD = "#161630"
BG_CARD2 = "#1e1e42"
BG_CARD3 = "#282855"

# Text
TEXT_PRIMARY = "#f0f0ff"
TEXT_SECONDARY = "#c0c0e0"
TEXT_MUTED = "#7070a0"

# Accents
ACCENT = "#7dd3fc"
ACCENT_BRIGHT = "#38bdf8"
GREEN = "#4ade80"
GREEN_DIM = "#22c55e"
RED = "#f87171"
AMBER = "#fbbf24"
PURPLE = "#c084fc"
PINK = "#f472b6"
ORANGE = "#fb923c"

# Glow / effects
GLOW_ACCENT = "rgba(125, 211, 252, 0.15)"
GLOW_GREEN = "rgba(74, 222, 128, 0.15)"
GLOW_PURPLE = "rgba(192, 132, 252, 0.15)"


def get_stylesheet() -> str:
    return f"""
    * {{
        font-family: 'Segoe UI', 'SF Pro Display', system-ui, -apple-system, sans-serif;
    }}

    QWidget {{
        background-color: {BG_PRIMARY};
        color: {TEXT_PRIMARY};
        font-size: 13px;
    }}

    /* ===== Buttons ===== */
    QPushButton {{
        background-color: {BG_CARD2};
        color: {TEXT_SECONDARY};
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 10px;
        padding: 8px 18px;
        font-weight: 600;
        font-size: 13px;
    }}
    QPushButton:hover {{
        background-color: {ACCENT};
        color: {BG_DEEP};
        border-color: transparent;
    }}
    QPushButton:pressed {{
        background-color: {ACCENT_BRIGHT};
    }}

    /* ===== Text Edit ===== */
    QTextEdit {{
        background-color: {BG_CARD};
        color: {TEXT_PRIMARY};
        border: 1px solid rgba(255,255,255,0.04);
        border-radius: 12px;
        padding: 12px 16px;
        font-size: 14px;
        selection-background-color: rgba(125, 211, 252, 0.3);
    }}

    /* ===== Line Edit ===== */
    QLineEdit {{
        background-color: {BG_CARD};
        color: {TEXT_PRIMARY};
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 10px;
        padding: 10px 14px;
        font-size: 13px;
        selection-background-color: rgba(125, 211, 252, 0.3);
    }}
    QLineEdit:focus {{
        border-color: {ACCENT};
    }}

    /* ===== Labels ===== */
    QLabel {{
        color: {TEXT_PRIMARY};
        background: transparent;
    }}

    /* ===== Frames ===== */
    QFrame {{
        background: transparent;
    }}

    /* ===== Scrollbar ===== */
    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {BG_CARD3};
        border-radius: 3px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {TEXT_MUTED};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}

    /* ===== Menu ===== */
    QMenu {{
        background-color: {BG_CARD};
        color: {TEXT_PRIMARY};
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px;
        padding: 6px 0;
    }}
    QMenu::item {{
        padding: 8px 24px;
        border-radius: 6px;
        margin: 2px 6px;
    }}
    QMenu::item:selected {{
        background-color: {ACCENT};
        color: {BG_DEEP};
    }}
    QMenu::separator {{
        height: 1px;
        background: rgba(255,255,255,0.06);
        margin: 4px 12px;
    }}

    /* ===== Dialog ===== */
    QDialog {{
        background-color: {BG_PRIMARY};
    }}
    """
