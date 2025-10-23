# main.py
# Qt GUI (PySide6) for creating the whisper-webui-beta tree with progress and verification
# ASCII-only. No summary popups; no editors opened unless toolbar toggle is ON.

import os, sys, time, subprocess
from PySide6 import QtCore, QtGui, QtWidgets
import ui_config as cfg

# --------------------------
# Helpers (filesystem ops)
# --------------------------

def ensure_dir(full_path: str):
    try:
        os.makedirs(full_path, exist_ok=True)
        return os.path.isdir(full_path), None
    except Exception as e:
        return False, str(e)

def touch_file(full_path: str):
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        is_new = not os.path.exists(full_path)
        header = getattr(cfg, "TOUCH_HEADER", "# file created by setup script")
        if is_new:
            with open(full_path, "w", encoding="utf-8", newline="") as f:
                f.write(header)
        else:
            with open(full_path, "a", encoding="utf-8", newline="") as f:
                f.write("\n")
        ok = os.path.isfile(full_path)
        if ok and is_new:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                first = f.readline()
            if "file created by setup script" not in first:
                return False, "header check failed"
        return ok, None
    except Exception as e:
        return False, str(e)

def open_editors(root: str):
    # Opens only the files listed in cfg.FILES (no .txt involved).
    for rel in cfg.FILES:
        full = os.path.join(root, rel)
        try:
            subprocess.Popen(["notepad.exe", full])
        except Exception:
            pass

# --------------------------
# Worker (QObject in QThread)
# --------------------------

class Worker(QtCore.QObject):
    progress  = QtCore.Signal(int)                     # percent
    row_result= QtCore.Signal(str, str, str, str)      # item, type, status, msg
    log_line  = QtCore.Signal(str)                     # console line
    finished  = QtCore.Signal(int, int)                # oks, fails

    def __init__(self, root: str, open_editors_flag: bool, parent=None):
        super().__init__(parent)
        self.root = root
        self.open_editors_flag = open_editors_flag
        self.steps = cfg.build_steps()
        self.total_steps = len(self.steps)
        self._stop = False

    @QtCore.Slot()
    def run(self):
        oks = 0
        fails = 0
        step_idx = 0

        try:
            os.makedirs(self.root, exist_ok=True)
        except Exception:
            pass

        self._qlog(f"Start setup at ROOT: {self.root}")
        for kind, rel in self.steps:
            if self._stop:
                break
            step_idx += 1
            pct = int((step_idx * 100) / self.total_steps)
            full = os.path.join(self.root, rel)

            if kind == "dir":
                ok, err = ensure_dir(full)
                status, typ = ("OK", "DIR") if ok else ("FAIL", "DIR")
                msg = f"{status}: Create dir: {rel}"
            else:
                ok, err = touch_file(full)
                status, typ = ("OK", "FILE") if ok else ("FAIL", "FILE")
                msg = f"{status}: Create file: {rel}"

            if not ok and err:
                msg += f" (err: {err})"

            self._qlog(f"[{pct:3d}%] {msg}")
            self.row_result.emit(rel, typ, status, err or "")
            self.progress.emit(pct)

            if ok: oks += 1
            else:  fails += 1

            QtCore.QThread.msleep(50)

        # only open editors if toolbar toggle is ON
        if self.open_editors_flag:
            self._qlog("Opening Notepad editors for created/verified files (toolbar toggle ON)...")
            try:
                open_editors(self.root)
            except Exception as e:
                self._qlog(f"Could not open editors: {e}")

        self._qlog(f"Summary: Success={oks} Fails={fails} TotalSteps={self.total_steps}")
        self.finished.emit(oks, fails)

    def stop(self):
        self._stop = True

    def _qlog(self, msg: str):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        self.log_line.emit(f"[{ts}] {msg}")

# --------------------------
# Main Window
# --------------------------

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(cfg.WINDOW_TITLE)
        self.resize(cfg.WINDOW_WIDTH, cfg.WINDOW_HEIGHT)

        # toggles default state from config
        self.confirm_on_close = bool(getattr(cfg, "CONFIRM_ON_CLOSE_DEFAULT", False))
        self.open_editors_after_run = bool(getattr(cfg, "OPEN_EDITORS_DEFAULT", False))

        # central widget
        central = QtWidgets.QWidget(self)
        self.setCentralWidget(central)
        main_v = QtWidgets.QVBoxLayout(central)
        main_v.setContentsMargins(10, 10, 10, 10)
        main_v.setSpacing(8)

        # ===== top configuration toolbar =====
        self.toolbar = QtWidgets.QToolBar("Config")
        self.toolbar.setMovable(False)
        self.addToolBar(QtCore.Qt.ToolBarArea.TopToolBarArea, self.toolbar)

        # toggle: confirm on close
        self.act_confirm = QtGui.QAction("Confirm on close", self)
        self.act_confirm.setCheckable(True)
        self.act_confirm.setChecked(self.confirm_on_close)
        self.act_confirm.toggled.connect(self.on_toggle_confirm_close)
        self.toolbar.addAction(self.act_confirm)

        # toggle: open editors after run
        self.act_open_editors = QtGui.QAction("Open editors after run", self)
        self.act_open_editors.setCheckable(True)
        self.act_open_editors.setChecked(self.open_editors_after_run)
        self.act_open_editors.toggled.connect(self.on_toggle_open_editors)
        self.toolbar.addAction(self.act_open_editors)

        # top controls (root + browse)
        top_box = QtWidgets.QHBoxLayout()
        lbl_root = QtWidgets.QLabel("Root:")
        self.ed_root = QtWidgets.QLineEdit(cfg.DEFAULT_ROOT)
        self.btn_browse = QtWidgets.QPushButton("Browse...")

        top_box.addWidget(lbl_root)
        top_box.addWidget(self.ed_root, 1)
        top_box.addWidget(self.btn_browse)

        # run + progress
        run_box = QtWidgets.QHBoxLayout()
        self.btn_run = QtWidgets.QPushButton("Run setup")
        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 100)
        self.lbl_pct = QtWidgets.QLabel("0%")
        run_box.addWidget(self.btn_run)
        run_box.addWidget(self.progress, 1)
        run_box.addWidget(self.lbl_pct)

        # splitter: table + log
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)

        # table
        table_w = QtWidgets.QWidget()
        table_l = QtWidgets.QVBoxLayout(table_w)
        table_l.setContentsMargins(0, 0, 0, 0)
        self.table = QtWidgets.QTableWidget(0, len(cfg.TABLE_HEADERS))
        self.table.setHorizontalHeaderLabels(cfg.TABLE_HEADERS)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        splitter.addWidget(table_w)
        table_l.addWidget(self.table)

        # log + tips
        log_w = QtWidgets.QWidget()
        log_l = QtWidgets.QVBoxLayout(log_w)
        log_l.setContentsMargins(0, 0, 0, 0)
        self.txt_log = QtWidgets.QPlainTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setMaximumBlockCount(2000)
        log_l.addWidget(self.txt_log)

        tips = QtWidgets.QLabel("\n".join(cfg.TIPS))
        tips.setStyleSheet(f"color:{cfg.COLOR_LINK_FG};")
        log_l.addWidget(tips)
        splitter.addWidget(log_w)

        # assemble
        main_v.addLayout(top_box)
        main_v.addLayout(run_box)
        main_v.addWidget(splitter, 1)

        # connections
        self.btn_browse.clicked.connect(self.on_browse)
        self.btn_run.clicked.connect(self.on_run)

        self._thread = None
        self._worker = None

        # apply palette + stylesheet from config
        self.apply_theme()

    # ---- theming ----
    def apply_theme(self):
        if cfg.USE_FUSION_STYLE:
            QtWidgets.QApplication.setStyle("Fusion")
        pal = QtGui.QPalette()
        pal.setColor(QtGui.QPalette.ColorRole.Window,           QtGui.QColor(cfg.COLOR_WINDOW_BG))
        pal.setColor(QtGui.QPalette.ColorRole.WindowText,       QtGui.QColor(cfg.COLOR_WINDOW_FG))
        pal.setColor(QtGui.QPalette.ColorRole.Base,             QtGui.QColor(cfg.COLOR_BASE_BG))
        pal.setColor(QtGui.QPalette.ColorRole.AlternateBase,    QtGui.QColor(cfg.COLOR_ALT_BG))
        pal.setColor(QtGui.QPalette.ColorRole.Text,             QtGui.QColor(cfg.COLOR_TEXT_FG))
        pal.setColor(QtGui.QPalette.ColorRole.Button,           QtGui.QColor(cfg.COLOR_BUTTON_BG))
        pal.setColor(QtGui.QPalette.ColorRole.ButtonText,       QtGui.QColor(cfg.COLOR_BUTTON_FG))
        pal.setColor(QtGui.QPalette.ColorRole.Highlight,        QtGui.QColor(cfg.COLOR_HILIGHT_BG))
        pal.setColor(QtGui.QPalette.ColorRole.HighlightedText,  QtGui.QColor(cfg.COLOR_HILIGHT_FG))
        self.window().setPalette(pal)
        self.window().setStyleSheet(cfg.EXTRA_STYLESHEET)

    # ---- toolbar toggles ----
    def on_toggle_confirm_close(self, checked: bool):
        self.confirm_on_close = bool(checked)

    def on_toggle_open_editors(self, checked: bool):
        self.open_editors_after_run = bool(checked)

    # ---- actions ----
    def on_browse(self):
        d = QtWidgets.QFileDialog.getExistingDirectory(self, "Select base directory", self.ed_root.text())
        if d:
            self.ed_root.setText(d)

    def on_run(self):
        if self._thread and self._thread.isRunning():
            QtWidgets.QMessageBox.information(self, "Info", "Worker is already running.")
            return

        self.table.setRowCount(0)
        self.progress.setValue(0)
        self.lbl_pct.setText("0%")

        root = self.ed_root.text().strip()
        if not root:
            QtWidgets.QMessageBox.warning(self, "Warning", "Root path is empty.")
            return

        self._thread = QtCore.QThread(self)
        self._worker = Worker(root, self.open_editors_after_run)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self.on_progress)
        self._worker.row_result.connect(self.on_row_result)
        self._worker.log_line.connect(self.on_log_line)
        self._worker.finished.connect(self.on_finished)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self.btn_run.setEnabled(False)
        self._thread.start()

    @QtCore.Slot(int)
    def on_progress(self, pct: int):
        self.progress.setValue(pct)
        self.lbl_pct.setText(f"{pct}%")

    @QtCore.Slot(str, str, str, str)
    def on_row_result(self, item: str, typ: str, status: str, msg: str):
        r = self.table.rowCount()
        self.table.insertRow(r)

        def mk_item(text: str, bg: str, fg: str):
            it = QtWidgets.QTableWidgetItem(text)
            it.setBackground(QtGui.QColor(bg))
            it.setForeground(QtGui.QColor(fg))
            return it

        if status == "OK":
            bg, fg = cfg.COLOR_OK_BG, cfg.COLOR_OK_FG
        elif status == "FAIL":
            bg, fg = cfg.COLOR_FAIL_BG, cfg.COLOR_FAIL_FG
        else:
            bg, fg = cfg.COLOR_PENDING_BG, cfg.COLOR_PENDING_FG

        self.table.setItem(r, 0, mk_item(item, bg, fg))
        self.table.setItem(r, 1, mk_item(typ, bg, fg))
        self.table.setItem(r, 2, mk_item(status, bg, fg))
        self.table.setItem(r, 3, mk_item(msg or "", bg, fg))
        self.table.scrollToBottom()

    @QtCore.Slot(str)
    def on_log_line(self, line: str):
        self.txt_log.appendPlainText(line)
        self.txt_log.moveCursor(QtGui.QTextCursor.MoveOperation.End)

    @QtCore.Slot(int, int)
    def on_finished(self, oks: int, fails: int):
        # no popups; just log a final line
        total = len(cfg.build_steps())
        line = f"Run finished. Success={oks} Fails={fails} Total={total}"
        self.txt_log.appendPlainText(line)
        self.txt_log.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        self.btn_run.setEnabled(True)

    # close behavior controlled by toolbar toggle
    def closeEvent(self, e: QtGui.QCloseEvent):
        if self.confirm_on_close:
            res = QtWidgets.QMessageBox.question(self, "Exit", "Close the window?")
            if res != QtWidgets.QMessageBox.StandardButton.Yes:
                e.ignore()
                return
        # safe-stop worker if running
        if hasattr(self, "_worker") and self._worker:
            try: self._worker.stop()
            except: pass
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(1500)
        e.accept()

# --------------------------
# entry point  (TESTE 1234)14:56
# --------------------------

def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
