
# ui_config.py
# Central config for the Whisper WebUI setup GUI (PySide6)
# ASCII-only

import os

# ---------- portable bases ----------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.path.join(SCRIPT_DIR, "whisper-webui-beta")

# ---------- window ----------
WINDOW_TITLE = "Whisper WebUI Setup (Qt)"
WINDOW_WIDTH = 980
WINDOW_HEIGHT = 620

# use Fusion style + custom palette
USE_FUSION_STYLE = True

# ---------- editable colors ----------
COLOR_WINDOW_BG   = "#d3d3d3"  # main window background-
COLOR_WINDOW_FG   = "#eeff00"  # main window text
COLOR_BASE_BG     = "#ffffff"  # text areas / inputs base-
COLOR_ALT_BG      = "#eaeaea"  # alternating rows background-
COLOR_TEXT_FG     = "#000000"  # generic text color
COLOR_BUTTON_BG   = "#6c6e70cc"  # push buttons
COLOR_BUTTON_FG   = "#000000"  # push buttons text
COLOR_HILIGHT_BG  = "#2563eb"  # selection highlight
COLOR_HILIGHT_FG  = "#ffffff"  # selection text
COLOR_LINK_FG     = "#0062ff"  # tips/links text

# table row colors
COLOR_OK_BG       = "#b2ffd5"
COLOR_OK_FG       = "#000000"
COLOR_FAIL_BG     = "#4a0e0e"
COLOR_FAIL_FG     = "#ffd0d0"
COLOR_PENDING_BG  = "#1f2630"
COLOR_PENDING_FG  = "#c9d1d9"

# optional: additional css for fine tuning
EXTRA_STYLESHEET = """
QWidget { background: %(COLOR_WINDOW_BG)s; color: %(COLOR_TEXT_FG)s; }
QPushButton { background: %(COLOR_BUTTON_BG)s; color: %(COLOR_BUTTON_FG)s; border: 1px solid #2a3645; padding: 6px 10px; }
QPushButton:hover { border-color: #3a4a60; }
QLineEdit, QPlainTextEdit, QTextEdit, QTreeView, QTableView {
  background: %(COLOR_BASE_BG)s; color: %(COLOR_TEXT_FG)s; border: 1px solid #263244;
}
QHeaderView::section {
  background: %(COLOR_ALT_BG)s; color: %(COLOR_TEXT_FG)s; border: none; padding: 6px;
}
QProgressBar {
  background: %(COLOR_ALT_BG)s; color: %(COLOR_TEXT_FG)s; border: 1px solid #263244; text-align: center;
}
QProgressBar::chunk { background: %(COLOR_HILIGHT_BG)s; }
QCheckBox, QLabel { color: %(COLOR_TEXT_FG)s; }
""" % {
    "COLOR_WINDOW_BG": COLOR_WINDOW_BG,
    "COLOR_TEXT_FG": COLOR_TEXT_FG,
    "COLOR_BUTTON_BG": COLOR_BUTTON_BG,
    "COLOR_BUTTON_FG": COLOR_BUTTON_FG,
    "COLOR_BASE_BG": COLOR_BASE_BG,
    "COLOR_ALT_BG": COLOR_ALT_BG,
    "COLOR_HILIGHT_BG": COLOR_HILIGHT_BG,
}

# ---------- behavior defaults ----------
CONFIRM_ON_CLOSE_DEFAULT = False   # default state for the toolbar toggle
OPEN_EDITORS_DEFAULT     = False   # default state for the toolbar toggle

# ---------- structure ----------
DIRS = ["public", "bin", "models", "jobs"]
FILES = [
    "start.bat",
    "server.ps1",
    os.path.join("public", "index.html"),
    os.path.join("public", "style.css"),
    os.path.join("public", "app.js"),
]

# table headers
TABLE_HEADERS = ["Item", "Type", "Status", "Message"]

# tips text
TIPS = [
    '1) Put ffmpeg.exe and whisper.exe in bin\\',
    '2) Put a model (.bin) in models\\',
    '3) Edit start.bat and server.ps1 as needed',
]

# helper: build work plan
def build_steps():
    return [("dir", d) for d in DIRS] + [("file", f) for f in FILES]


#ALTERACAO_DA_BASE_VERMELHA