# GPT Context — 2025-10-24 12:48:10 UTC

**Repo:** ndz0/P_WHISP_FFMP  |  **Branch:** ffmpeg_whisper  |  **SHA:** a39443f515c822e4ea9aa9ba4e05ec6c93608ffe

## Ultimos 20 commits
- a39443f 2025-10-24 CKP_1 (vbndz)
- 44df586 2025-10-23 test(gpt): trigger workflow (vbndz)
- 6c2bed5 2025-10-23 test(gpt): trigger workflow (vbndz)
- 1079d66 2025-10-23 ALTERACAO_DA_BASE_VERMELHA (vbndz)
- 552395f 2025-10-23 KAUAI_14_59 (vbndz)
- a6f5184 2025-10-23 14_56 (vbndz)
- 629c2fd 2025-10-23 chore: update (vbndz)
- 4def455 2025-10-22 ALTERACOES_POPUP_DE_FECHAMENTO (vbndz)
## Arquivos alterados neste push
A	.github/workflows/gpt-context.yml
A	.gitignore
A	__pycache__/ffmpeg_upsert.cpython-313.pyc
M	__pycache__/ui_config.cpython-313.pyc
A	__pycache__/whisper_upsert.cpython-313.pyc
A	ffmpeg_upsert.py
A	install_ffmpeg_portable.py
A	install_whisper_portable.py
M	main.py
M	ui_config.py
M	whisper-webui-beta/public/app.js
M	whisper-webui-beta/public/index.html
M	whisper-webui-beta/public/style.css
M	whisper-webui-beta/server.ps1
M	whisper-webui-beta/start.bat
A	whisper_upsert.py

## Diff (trechos)
diff --git a/.github/workflows/gpt-context.yml b/.github/workflows/gpt-context.yml
new file mode 100644
index 0000000..7460cf9
--- /dev/null
+++ b/.github/workflows/gpt-context.yml
@@ -0,0 +1,47 @@
+name: GPT context (no-API)
+
+on:
+  push:
+    branches: [ "**" ]  # roda em qualquer branch
+
+permissions:
+  contents: write
+
+jobs:
+  build:
+    runs-on: ubuntu-latest
+    steps:
+      - uses: actions/checkout@v4
+        with:
+          fetch-depth: 0
+
+      - name: Generate context file
+        run: |
+          mkdir -p docs
+          BEFORE="${{ github.event.before || 'HEAD^' }}"
+          AFTER="${{ github.sha }}"
+          {
+            echo "# GPT Context — $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
+            echo
+            echo "**Repo:** ${{ github.repository }}  |  **Branch:** ${{ github.ref_name }}  |  **SHA:** $AFTER"
+            echo
+            echo "## Ultimos 20 commits"
+            git log --pretty=format:'- %h %ad %s (%an)' --date=short -n 20
+            echo
+            echo "## Arquivos alterados neste push"
+            git diff --name-status "$BEFORE" "$AFTER" || true
+            echo
+            echo "## Diff (trechos)"
+            git diff --unified=3 --no-color "$BEFORE" "$AFTER" | sed -n '1,2000p' || true
+            echo
+            echo "## Mapa do repo (top 200)"
+            git ls-files | head -n 200
+          } > docs/gpt-context.md
+
+      - name: Commit context
+        run: |
+          git config user.name  "github-actions[bot]"
+          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
+          git add docs/gpt-context.md
+          git commit -m "chore: update docs/gpt-context.md [skip ci]" || exit 0
+          git push
diff --git a/.gitignore b/.gitignore
new file mode 100644
index 0000000..4a04253
--- /dev/null
+++ b/.gitignore
@@ -0,0 +1,5 @@
+/bin/ffmpeg/
+/OUTPUT/
+/SLAVE/
+/SLAVE/
+/slave/
diff --git a/__pycache__/ffmpeg_upsert.cpython-313.pyc b/__pycache__/ffmpeg_upsert.cpython-313.pyc
new file mode 100644
index 0000000..e388fee
Binary files /dev/null and b/__pycache__/ffmpeg_upsert.cpython-313.pyc differ
diff --git a/__pycache__/ui_config.cpython-313.pyc b/__pycache__/ui_config.cpython-313.pyc
index f462f0a..66db675 100644
Binary files a/__pycache__/ui_config.cpython-313.pyc and b/__pycache__/ui_config.cpython-313.pyc differ
diff --git a/__pycache__/whisper_upsert.cpython-313.pyc b/__pycache__/whisper_upsert.cpython-313.pyc
new file mode 100644
index 0000000..48e6477
Binary files /dev/null and b/__pycache__/whisper_upsert.cpython-313.pyc differ
diff --git a/ffmpeg_upsert.py b/ffmpeg_upsert.py
new file mode 100644
index 0000000..32c0c02
--- /dev/null
+++ b/ffmpeg_upsert.py
@@ -0,0 +1,102 @@
+# ffmpeg_upsert.py
+# Portable FFmpeg runner + setup helpers (UTF-8 logs)
+# ASCII-only
+
+from __future__ import annotations
+import os
+import sys
+import shlex
+import shutil
+import subprocess
+from pathlib import Path
+from typing import Callable, Optional, Sequence, Union
+
+BASE_DIR = Path(__file__).resolve().parent
+BIN_DIR = BASE_DIR / "bin" / "ffmpeg"
+BIN_DIR.mkdir(parents=True, exist_ok=True)
+
+def _is_windows() -> bool:
+    return os.name == "nt"
+
+def local_ffmpeg_path() -> Optional[Path]:
+    exe = "ffmpeg.exe" if _is_windows() else "ffmpeg"
+    p = BIN_DIR / exe
+    return p if p.exists() else None
+
+def find_ffmpeg_in_path() -> Optional[Path]:
+    exe = "ffmpeg.exe" if _is_windows() else "ffmpeg"
+    found = shutil.which(exe)
+    return Path(found) if found else None
+
+def ensure_ffmpeg(prefer_local: bool = True) -> Path:
+    if prefer_local:
+        p = local_ffmpeg_path()
+        if p:
+            return p
+    p = find_ffmpeg_in_path()
+    if p:
+        return p
+    expected = BIN_DIR / ("ffmpeg.exe" if _is_windows() else "ffmpeg")
+    raise FileNotFoundError(
+        f"ffmpeg not found. Expected at '{expected}' or in PATH. "
+        f"Run 'install_ffmpeg_portable.py' or 'install_ffmpeg_portable.bat'."
+    )
+
+def run_ffmpeg(
+    args: Union[str, Sequence[str]],
+    on_log: Callable[[str], None],
+    cwd: Optional[Union[str, Path]] = None,
+    env: Optional[dict] = None,
+    prefer_local: bool = True,
+    combine_stdout_stderr: bool = True,
+) -> int:
+    ffmpeg_exe = str(ensure_ffmpeg(prefer_local=prefer_local))
+    cmd = [ffmpeg_exe] + (shlex.split(args) if isinstance(args, str) else list(args))
+
+    creationflags = 0
+    startupinfo = None
+    if _is_windows():
+        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
+        startupinfo = subprocess.STARTUPINFO()
+        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # type: ignore[attr-defined]
+        startupinfo.wShowWindow = 0  # type: ignore[attr-defined]
+
+    merged = subprocess.STDOUT if combine_stdout_stderr else subprocess.PIPE
+    proc_env = (env or os.environ.copy())
+
+    proc = subprocess.Popen(
+        cmd,
+        cwd=str(cwd) if cwd else None,
+        env=proc_env,
+        stdout=subprocess.PIPE,
+        stderr=merged,
+        bufsize=1,
+        text=True,
+        encoding="utf-8",
+        errors="replace",
+        creationflags=creationflags,
+        startupinfo=startupinfo,
+    )
+
+    try:
+        if proc.stdout is not None:
+            for line in proc.stdout:
+                on_log(line.rstrip("\r\n"))
+    finally:
+        if proc.stdout:
+            proc.stdout.close()
+
+    code = proc.wait()
+    on_log(f"[ffmpeg] exit code: {code}")
+    return code
+
+if __name__ == "__main__":
+    def printer(msg: str): print(msg)
+    try:
+        rc = run_ffmpeg("-version", on_log=printer)
+        sys.exit(rc)
+    except Exception as exc:
+        print(f"[error] {exc}")
+        sys.exit(1)
+
+#WHI_V3 - build 2
diff --git a/install_ffmpeg_portable.py b/install_ffmpeg_portable.py
new file mode 100644
index 0000000..f6ecf3a
--- /dev/null
+++ b/install_ffmpeg_portable.py
@@ -0,0 +1,129 @@
+# install_ffmpeg_portable.py
+# Install portable FFmpeg into ./bin/ffmpeg on Windows
+# Strategy: try Chocolatey (ffmpeg.portable), else download ZIP (gyan.dev)
+# ASCII-only
+
+from __future__ import annotations
+import os
+import sys
+import time
+import glob
+import shutil
+import zipfile
+import tempfile
+import subprocess
+from pathlib import Path
+from urllib.request import urlopen
+
+BASE_DIR = Path(__file__).resolve().parent
+DEST_DIR = BASE_DIR / "bin" / "ffmpeg"
+DEST_DIR.mkdir(parents=True, exist_ok=True)
+
+GYAN_ZIP = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
+
+def copy_if_exists(src: Path, dst_dir: Path):
+    if src and src.exists():
+        dst = dst_dir / src.name
+        dst_dir.mkdir(parents=True, exist_ok=True)
+        shutil.copy2(str(src), str(dst))
+        print(f"OK: copied {src} -> {dst}")
+
+def try_choco_install() -> bool:
+    print("INFO: trying Chocolatey (ffmpeg.portable)...")
+    choco = shutil.which("choco")
+    if not choco:
+        print("WARN: choco not found; skipping Chocolatey path.")
+        return False
+
+    try:
+        # silent install
+        cmd = [choco, "install", "ffmpeg.portable", "-y", "--no-progress"]
+        print("CMD:", " ".join(cmd))
+        res = subprocess.run(cmd, check=False)
+        if res.returncode != 0:
+            print(f"WARN: choco install returned {res.returncode}")
+            # Continue anyway; maybe already installed
+    except Exception as e:
+        print(f"WARN: choco install error: {e}")
+
+    # locate binaries under %ProgramData%\chocolatey\lib\ffmpeg*
+    program_data = os.environ.get("ProgramData", r"C:\ProgramData")
+    lib_root = Path(program_data) / "chocolatey" / "lib"
+    if not lib_root.exists():
+        print("WARN: Chocolatey lib folder not found.")
+        return False
+
+    candidates = list(lib_root.glob("ffmpeg*"))
+    if not candidates:
+        print("WARN: no ffmpeg* package under Chocolatey lib.")
+        return False
+
+    # pick newest by mtime
+    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
+    newest = candidates[0]
+    exe_ffmpeg = next(newest.rglob("ffmpeg.exe"), None)
+    exe_ffprobe = next(newest.rglob("ffprobe.exe"), None)
+
+    if not exe_ffmpeg:
+        print("WARN: ffmpeg.exe not found under Chocolatey package.")
+        return False
+
+    copy_if_exists(exe_ffmpeg, DEST_DIR)
+    if exe_ffprobe:
+        copy_if_exists(exe_ffprobe, DEST_DIR)
+
+    print(f"OK: FFmpeg available in {DEST_DIR}")
+    return True
+
+def download_and_extract_zip(url: str, dest_dir: Path) -> bool:
+    print(f"INFO: downloading ZIP from {url} ...")
+    with tempfile.TemporaryDirectory() as td:
+        tmp_zip = Path(td) / "ffmpeg.zip"
+        with urlopen(url) as r, open(tmp_zip, "wb") as f:
+            shutil.copyfileobj(r, f)
+
+        with zipfile.ZipFile(tmp_zip) as zf:
+            zf.extractall(td)
+
+        # Find ffmpeg.exe and ffprobe.exe inside extracted tree
+        ffmpeg_exe = None
+        ffprobe_exe = None
+        for p in Path(td).rglob("*"):
+            name = p.name.lower()
+            if name == "ffmpeg.exe":
+                ffmpeg_exe = p
+            elif name == "ffprobe.exe":
+                ffprobe_exe = p
+
+        if not ffmpeg_exe:
+            print("ERR: could not find ffmpeg.exe inside ZIP.")
+            return False
+
+        copy_if_exists(ffmpeg_exe, dest_dir)
+        if ffprobe_exe:
+            copy_if_exists(ffprobe_exe, dest_dir)
+        print(f"OK: FFmpeg available in {dest_dir}")
+        return True
+
+def main():
+    # already installed?
+    exe = DEST_DIR / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
+    if exe.exists():
+        print(f"OK: already present -> {exe}")
+        return 0
+
+    # Option 1: Chocolatey
+    if try_choco_install():
+        return 0
+
+    # Option 2: direct ZIP
+    ok = download_and_extract_zip(GYAN_ZIP, DEST_DIR)
+    if not ok:
+        print("ERR: failed to install FFmpeg.")
+        return 2
+    return 0
+
+if __name__ == "__main__":
+    sys.exit(main())
+
+#WHI_V3 - build 1
diff --git a/install_whisper_portable.py b/install_whisper_portable.py
new file mode 100644
index 0000000..082b36a
--- /dev/null
+++ b/install_whisper_portable.py
@@ -0,0 +1,45 @@
+# install_whisper_portable.py
+# Install openai-whisper into current Python env (prefer venv)
+# ASCII-only
+
+from __future__ import annotations
+import os
+import sys
+import subprocess
+
+def run(cmd: list[str]) -> int:
+    print("CMD:", " ".join(cmd))
+    return subprocess.call(cmd)
+
+def main() -> int:
+    py = sys.executable or "python"
+    print(f"INFO: using python: {py}")
+
+    # upgrade pip (optional but helps)
+    run([py, "-m", "pip", "install", "--upgrade", "pip"])
+
+    # install torch first is optional; openai-whisper will pull a compatible build.
+    # If you want CPU-only torch explicitly, uncomment below:
+    # run([py, "-m", "pip", "install", "torch", "--index-url", "https://download.pytorch.org/whl/cpu"])
+
+    # install openai-whisper
+    rc = run([py, "-m", "pip", "install", "-U", "openai-whisper"])
+    if rc != 0:
+        print("ERR: failed to install openai-whisper")
+        return rc
+
+    # quick smoke test
+    print("INFO: validating whisper CLI...")
+    rc = run([py, "-m", "whisper", "--help"])
+    if rc != 0:
+        print("WARN: whisper CLI returned non-zero (may still be ok to run).")
+    else:
+        print("OK: whisper CLI is available.")
+
+    print("DONE.")
+    return 0
+
+if __name__ == "__main__":
+    sys.exit(main())
+
+#WHI_V3 - build 1
diff --git a/main.py b/main.py
index 3627fd1..1c25e32 100644
--- a/main.py
+++ b/main.py
@@ -1,363 +1,290 @@
 # main.py
-# Qt GUI (PySide6) for creating the whisper-webui-beta tree with progress and verification
-# ASCII-only. No summary popups; no editors opened unless toolbar toggle is ON.
-
-import os, sys, time, subprocess
-from PySide6 import QtCore, QtGui, QtWidgets
-import ui_config as cfg
-
-# --------------------------
-# Helpers (filesystem ops)
-# --------------------------
-
-def ensure_dir(full_path: str):
-    try:
-        os.makedirs(full_path, exist_ok=True)
-        return os.path.isdir(full_path), None
-    except Exception as e:
-        return False, str(e)
-
-def touch_file(full_path: str):
-    try:
-        os.makedirs(os.path.dirname(full_path), exist_ok=True)
-        is_new = not os.path.exists(full_path)
-        header = getattr(cfg, "TOUCH_HEADER", "# file created by setup script")
-        if is_new:
-            with open(full_path, "w", encoding="utf-8", newline="") as f:
-                f.write(header)
-        else:
-            with open(full_path, "a", encoding="utf-8", newline="") as f:
-                f.write("\n")
-        ok = os.path.isfile(full_path)
-        if ok and is_new:
-            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
-                first = f.readline()
-            if "file created by setup script" not in first:
-                return False, "header check failed"
-        return ok, None
-    except Exception as e:
-        return False, str(e)
-
-def open_editors(root: str):
-    # Opens only the files listed in cfg.FILES (no .txt involved).
-    for rel in cfg.FILES:
-        full = os.path.join(root, rel)
-        try:
-            subprocess.Popen(["notepad.exe", full])
-        except Exception:
-            pass
-
-# --------------------------
-# Worker (QObject in QThread)
-# --------------------------
-
-class Worker(QtCore.QObject):
-    progress  = QtCore.Signal(int)                     # percent
-    row_result= QtCore.Signal(str, str, str, str)      # item, type, status, msg
-    log_line  = QtCore.Signal(str)                     # console line
-    finished  = QtCore.Signal(int, int)                # oks, fails
-
-    def __init__(self, root: str, open_editors_flag: bool, parent=None):
-        super().__init__(parent)
-        self.root = root
-        self.open_editors_flag = open_editors_flag
-        self.steps = cfg.build_steps()
-        self.total_steps = len(self.steps)
-        self._stop = False
-
-    @QtCore.Slot()
-    def run(self):
-        oks = 0
-        fails = 0
-        step_idx = 0
-
-        try:
-            os.makedirs(self.root, exist_ok=True)
-        except Exception:
-            pass
-
-        self._qlog(f"Start setup at ROOT: {self.root}")
-        for kind, rel in self.steps:
-            if self._stop:
-                break
-            step_idx += 1
-            pct = int((step_idx * 100) / self.total_steps)
-            full = os.path.join(self.root, rel)
-
-            if kind == "dir":
-                ok, err = ensure_dir(full)
-                status, typ = ("OK", "DIR") if ok else ("FAIL", "DIR")
-                msg = f"{status}: Create dir: {rel}"
-            else:
-                ok, err = touch_file(full)
-                status, typ = ("OK", "FILE") if ok else ("FAIL", "FILE")
-                msg = f"{status}: Create file: {rel}"
-
-            if not ok and err:
-                msg += f" (err: {err})"
-
-            self._qlog(f"[{pct:3d}%] {msg}")
-            self.row_result.emit(rel, typ, status, err or "")
-            self.progress.emit(pct)
-
-            if ok: oks += 1
-            else:  fails += 1
-
-            QtCore.QThread.msleep(50)
-
-        # only open editors if toolbar toggle is ON
-        if self.open_editors_flag:
-            self._qlog("Opening Notepad editors for created/verified files (toolbar toggle ON)...")
-            try:
-                open_editors(self.root)
-            except Exception as e:
-                self._qlog(f"Could not open editors: {e}")
-
-        self._qlog(f"Summary: Success={oks} Fails={fails} TotalSteps={self.total_steps}")
-        self.finished.emit(oks, fails)
+# UI PySide6: convert to WAV (FFmpeg) and auto-transcribe with Whisper
+# No "Transcribe" button; UTF-8 end-to-end; reads final file to show accents correctly
+# ASCII-only
 
-    def stop(self):
-        self._stop = True
+from __future__ import annotations
+import sys
+from pathlib import Path
+from PySide6 import QtCore, QtWidgets, QtGui
 
-    def _qlog(self, msg: str):
-        ts = time.strftime("%Y-%m-%d %H:%M:%S")
-        self.log_line.emit(f"[{ts}] {msg}")
+import ffmpeg_upsert
+from whisper_upsert import run_whisper, build_args_transcribe
 
-# --------------------------
-# Main Window
-# --------------------------
+BASE_DIR = Path(__file__).resolve().parent
 
 class MainWindow(QtWidgets.QMainWindow):
     def __init__(self):
         super().__init__()
-        self.setWindowTitle(cfg.WINDOW_TITLE)
-        self.resize(cfg.WINDOW_WIDTH, cfg.WINDOW_HEIGHT)
-
-        # toggles default state from config
-        self.confirm_on_close = bool(getattr(cfg, "CONFIRM_ON_CLOSE_DEFAULT", False))
-        self.open_editors_after_run = bool(getattr(cfg, "OPEN_EDITORS_DEFAULT", False))
-
-        # central widget
-        central = QtWidgets.QWidget(self)
-        self.setCentralWidget(central)
-        main_v = QtWidgets.QVBoxLayout(central)
-        main_v.setContentsMargins(10, 10, 10, 10)
-        main_v.setSpacing(8)
+        self.setWindowTitle("Whisper WAV Converter + Transcriber (Auto)")
+        self.resize(980, 620)
 
-        # ===== top configuration toolbar =====
-        self.toolbar = QtWidgets.QToolBar("Config")
+        # toolbar toggle
+        self.toolbar = self.addToolBar("Main")
         self.toolbar.setMovable(False)
-        self.addToolBar(QtCore.Qt.ToolBarArea.TopToolBarArea, self.toolbar)
-
-        # toggle: confirm on close
-        self.act_confirm = QtGui.QAction("Confirm on close", self)
-        self.act_confirm.setCheckable(True)
-        self.act_confirm.setChecked(self.confirm_on_close)
-        self.act_confirm.toggled.connect(self.on_toggle_confirm_close)
-        self.toolbar.addAction(self.act_confirm)
-
-        # toggle: open editors after run
-        self.act_open_editors = QtGui.QAction("Open editors after run", self)
-        self.act_open_editors.setCheckable(True)
-        self.act_open_editors.setChecked(self.open_editors_after_run)
-        self.act_open_editors.toggled.connect(self.on_toggle_open_editors)
-        self.toolbar.addAction(self.act_open_editors)
-
-        # top controls (root + browse)
-        top_box = QtWidgets.QHBoxLayout()
-        lbl_root = QtWidgets.QLabel("Root:")
-        self.ed_root = QtWidgets.QLineEdit(cfg.DEFAULT_ROOT)
-        self.btn_browse = QtWidgets.QPushButton("Browse...")
-
-        top_box.addWidget(lbl_root)
-        top_box.addWidget(self.ed_root, 1)
-        top_box.addWidget(self.btn_browse)
-
-        # run + progress
-        run_box = QtWidgets.QHBoxLayout()
-        self.btn_run = QtWidgets.QPushButton("Run setup")
-        self.progress = QtWidgets.QProgressBar()
-        self.progress.setRange(0, 100)
-        self.lbl_pct = QtWidgets.QLabel("0%")
-        run_box.addWidget(self.btn_run)
-        run_box.addWidget(self.progress, 1)
-        run_box.addWidget(self.lbl_pct)
-
-        # splitter: table + log
-        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
-
-        # table
-        table_w = QtWidgets.QWidget()
-        table_l = QtWidgets.QVBoxLayout(table_w)
-        table_l.setContentsMargins(0, 0, 0, 0)
-        self.table = QtWidgets.QTableWidget(0, len(cfg.TABLE_HEADERS))
-        self.table.setHorizontalHeaderLabels(cfg.TABLE_HEADERS)
-        hh = self.table.horizontalHeader()
-        hh.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
-        hh.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
-        hh.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
-        hh.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Stretch)
-        self.table.setAlternatingRowColors(True)
-        splitter.addWidget(table_w)
-        table_l.addWidget(self.table)
-
-        # log + tips
-        log_w = QtWidgets.QWidget()
-        log_l = QtWidgets.QVBoxLayout(log_w)
-        log_l.setContentsMargins(0, 0, 0, 0)
-        self.txt_log = QtWidgets.QPlainTextEdit()
-        self.txt_log.setReadOnly(True)
-        self.txt_log.setMaximumBlockCount(2000)
-        log_l.addWidget(self.txt_log)
-
-        tips = QtWidgets.QLabel("\n".join(cfg.TIPS))
-        tips.setStyleSheet(f"color:{cfg.COLOR_LINK_FG};")
-        log_l.addWidget(tips)
-        splitter.addWidget(log_w)
-
-        # assemble
-        main_v.addLayout(top_box)
-        main_v.addLayout(run_box)
-        main_v.addWidget(splitter, 1)
+        self.act_confirm_exit = QtGui.QAction("Confirm exit?", self)
+        self.act_confirm_exit.setCheckable(True)
+        self.toolbar.addAction(self.act_confirm_exit)
+
+        # status
+        self.status = self.statusBar()
+
+        # widgets
+        self.in_edit = QtWidgets.QLineEdit()
+        self.in_btn  = QtWidgets.QPushButton("Browse...")
+        self.out_edit = QtWidgets.QLineEdit()
+        self.out_btn  = QtWidgets.QPushButton("Browse...")
+        self.over_cb  = QtWidgets.QCheckBox("Overwrite (-y)")
+        self.over_cb.setChecked(True)
+
+        self.convert_btn = QtWidgets.QPushButton("Convert to WAV (mono 16k)")
+
+        # whisper controls (sem botao)
+        self.model_cb = QtWidgets.QComboBox()
+        self.model_cb.addItems(["tiny", "tiny.en", "base", "base.en", "small", "small.en", "medium", "large-v3"])
+        self.lang_edit = QtWidgets.QLineEdit()
+        self.lang_edit.setPlaceholderText("auto or ISO code (e.g. pt)")
+        self.format_cb = QtWidgets.QComboBox()
+        self.format_cb.addItems(["srt", "vtt", "txt", "json"])
+
+        self.log_view = QtWidgets.QPlainTextEdit(); self.log_view.setReadOnly(True)
+
+        # layout
+        form = QtWidgets.QFormLayout()
+        r1 = QtWidgets.QHBoxLayout(); r1.addWidget(self.in_edit, 1); r1.addWidget(self.in_btn)
+        r2 = QtWidgets.QHBoxLayout(); r2.addWidget(self.out_edit, 1); r2.addWidget(self.out_btn)
+        form.addRow("Input:", r1)
+        form.addRow("Output WAV:", r2)
+
+        opts = QtWidgets.QHBoxLayout()
+        opts.addWidget(self.over_cb); opts.addStretch(1)
+
+        whisper_row1 = QtWidgets.QHBoxLayout()
+        whisper_row1.addWidget(QtWidgets.QLabel("Model:")); whisper_row1.addWidget(self.model_cb)
+        whisper_row1.addWidget(QtWidgets.QLabel("Lang:"));  whisper_row1.addWidget(self.lang_edit)
+        whisper_row1.addWidget(QtWidgets.QLabel("Format:")); whisper_row1.addWidget(self.format_cb)
+        whisper_row1.addStretch(1)
+
+        vbox = QtWidgets.QVBoxLayout()
+        vbox.addLayout(form)
+        vbox.addLayout(opts)
+        vbox.addWidget(self.convert_btn)
+        vbox.addSpacing(8)
+        vbox.addLayout(whisper_row1)
+        vbox.addWidget(self.log_view, 1)
+
+        central = QtWidgets.QWidget(); central.setLayout(vbox)
+        self.setCentralWidget(central)
 
         # connections
-        self.btn_browse.clicked.connect(self.on_browse)
-        self.btn_run.clicked.connect(self.on_run)
-
-        self._thread = None
-        self._worker = None
-
-        # apply palette + stylesheet from config
-        self.apply_theme()
-
-    # ---- theming ----
-    def apply_theme(self):
-        if cfg.USE_FUSION_STYLE:
-            QtWidgets.QApplication.setStyle("Fusion")
-        pal = QtGui.QPalette()
-        pal.setColor(QtGui.QPalette.ColorRole.Window,           QtGui.QColor(cfg.COLOR_WINDOW_BG))
-        pal.setColor(QtGui.QPalette.ColorRole.WindowText,       QtGui.QColor(cfg.COLOR_WINDOW_FG))
-        pal.setColor(QtGui.QPalette.ColorRole.Base,             QtGui.QColor(cfg.COLOR_BASE_BG))
-        pal.setColor(QtGui.QPalette.ColorRole.AlternateBase,    QtGui.QColor(cfg.COLOR_ALT_BG))
-        pal.setColor(QtGui.QPalette.ColorRole.Text,             QtGui.QColor(cfg.COLOR_TEXT_FG))
-        pal.setColor(QtGui.QPalette.ColorRole.Button,           QtGui.QColor(cfg.COLOR_BUTTON_BG))
-        pal.setColor(QtGui.QPalette.ColorRole.ButtonText,       QtGui.QColor(cfg.COLOR_BUTTON_FG))
-        pal.setColor(QtGui.QPalette.ColorRole.Highlight,        QtGui.QColor(cfg.COLOR_HILIGHT_BG))
-        pal.setColor(QtGui.QPalette.ColorRole.HighlightedText,  QtGui.QColor(cfg.COLOR_HILIGHT_FG))
-        self.window().setPalette(pal)
-        self.window().setStyleSheet(cfg.EXTRA_STYLESHEET)
-
-    # ---- toolbar toggles ----
-    def on_toggle_confirm_close(self, checked: bool):
-        self.confirm_on_close = bool(checked)
-
-    def on_toggle_open_editors(self, checked: bool):
-        self.open_editors_after_run = bool(checked)
-
-    # ---- actions ----
-    def on_browse(self):
-        d = QtWidgets.QFileDialog.getExistingDirectory(self, "Select base directory", self.ed_root.text())
-        if d:
-            self.ed_root.setText(d)
-
-    def on_run(self):
-        if self._thread and self._thread.isRunning():
-            QtWidgets.QMessageBox.information(self, "Info", "Worker is already running.")
-            return
+        self.in_btn.clicked.connect(self.pick_input)
+        self.out_btn.clicked.connect(self.pick_output)
+        self.convert_btn.clicked.connect(self.on_convert_clicked)
+
+        self._ff_worker = None
+        self._whisper_worker = None
+        self._last_wav = None
+        self._last_fmt = None
 
-        self.table.setRowCount(0)
-        self.progress.setValue(0)
-        self.lbl_pct.setText("0%")
+        # ffmpeg status
+        try:
+            p = ffmpeg_upsert.ensure_ffmpeg()
+            self.status.showMessage(f"ffmpeg OK: {p}")
+        except Exception:
+            self.status.showMessage("ffmpeg not found. Run install_ffmpeg_portable.py")
+
+        # remember toggle
+        self.settings = QtCore.QSettings("P_WHISP_FFMP", "WAVConverter")
+        # QSettings.value may be typed as 'object' by type checkers, coerce to bool explicitly
+        self.act_confirm_exit.setChecked(bool(self.settings.value("confirm_exit", False, type=bool)))
+        self.act_confirm_exit.toggled.connect(lambda v: self.settings.setValue("confirm_exit", v))
+
+    # helpers
+    def pick_input(self):
+        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Choose input media", str(BASE_DIR), "Media files (*.*)")
+        if not path: return
+        self.in_edit.setText(path)
+        self.out_edit.setText(str(self._suggest_wav(Path(path))))
+
+    def pick_output(self):
+        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Choose output WAV", str(BASE_DIR / "output.wav"), "WAV (*.wav)")
+        if not path: return
+        if not path.lower().endswith(".wav"): path += ".wav"
+        self.out_edit.setText(path)
+
+    def _suggest_wav(self, src: Path) -> Path:
+        return src.with_name(f"{src.stem}.wav")
+
+    def _set_busy(self, busy: bool):
+        for w in (self.convert_btn, self.in_btn, self.out_btn, self.in_edit, self.out_edit,
+                  self.over_cb, self.model_cb, self.lang_edit, self.format_cb):
+            w.setEnabled(not busy)  # keep ascii logic simple
+        self.setCursor(QtCore.Qt.CursorShape.BusyCursor if busy else QtCore.Qt.CursorShape.ArrowCursor)
+
+    def _log(self, text: str):
+        self.log_view.appendPlainText(text)
+
+    # convert (FFmpeg)
+    def on_convert_clicked(self):
+        src = self.in_edit.text().strip()
+        dst = self.out_edit.text().strip()
+        if not src:
+            QtWidgets.QMessageBox.warning(self, "Warn", "Select an input file"); return
+        if not Path(src).exists():
+            QtWidgets.QMessageBox.critical(self, "Error", "Input file not found"); return
+        if not dst:
+            dst = str(self._suggest_wav(Path(src))); self.out_edit.setText(dst)
 
-        root = self.ed_root.text().strip()
-        if not root:
-            QtWidgets.QMessageBox.warning(self, "Warning", "Root path is empty.")
+        try:
+            p = ffmpeg_upsert.ensure_ffmpeg()
+            self._log(f"[ffmpeg] using: {p}")
+        except Exception:
+            QtWidgets.QMessageBox.critical(self, "FFmpeg missing", "ffmpeg not found.\nRun: python install_ffmpeg_portable.py")
             return
 
-        self._thread = QtCore.QThread(self)
-        self._worker = Worker(root, self.open_editors_after_run)
-        self._worker.moveToThread(self._thread)
+        args = []
+        if self.over_cb.isChecked(): args += ["-y"]
+        args += ["-i", src, "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", dst]
 
-        self._thread.started.connect(self._worker.run)
-        self._worker.progress.connect(self.on_progress)
-        self._worker.row_result.connect(self.on_row_result)
-        self._worker.log_line.connect(self.on_log_line)
-        self._worker.finished.connect(self.on_finished)
-        self._worker.finished.connect(self._thread.quit)
-        self._worker.finished.connect(self._worker.deleteLater)
-        self._thread.finished.connect(self._thread.deleteLater)
+        self._last_wav = dst
+        self.log_view.clear()
+        self._set_busy(True)
+        # Use internal FFmpeg thread wrapper instead of missing FFmpegWorker from ffmpeg_upsert
+        self._ff_worker = _FFmpegThread(args)
+        self._ff_worker.log.connect(self._log)
+        self._ff_worker.finished_with_code.connect(self._on_ffmpeg_finished)
+        self._ff_worker.start()
+        self.status.showMessage("Converting...")
 
-        self.btn_run.setEnabled(False)
-        self._thread.start()
+    @QtCore.Slot(int)
+    def _on_ffmpeg_finished(self, code: int):
+        self._set_busy(False)
+        self.status.showMessage(f"FFmpeg done. Exit code: {code}")
+        if code != 0:
+            QtWidgets.QMessageBox.warning(self, "Warn", f"ffmpeg returned code {code}")
+            return
+        wav = self._last_wav
+        if not wav or not Path(wav).exists():
+            self._log("[auto] output WAV not found; skipping whisper")
+            return
+        self._log("-----")
+        self._log("[auto] starting Whisper transcription...")
+        self._start_whisper(wav)
+
+    # whisper (auto)
+    def _start_whisper(self, wav_path: str):
+        model = self.model_cb.currentText().strip()
+        lang  = self.lang_edit.text().strip() or None
+        fmt   = self.format_cb.currentText().strip()
+        self._last_fmt = fmt
+        out_dir = str(Path(wav_path).resolve().parent)
+
+        args = build_args_transcribe(
+            input_path=wav_path,
+            model=model,
+            language=lang,
+            output_dir=out_dir,
+            output_format=fmt
+        )
+
+        self._set_busy(True)
+        self._log(f"[whisper] model={model} lang={lang or 'auto'} format={fmt}")
+        self.status.showMessage("Transcribing...")
+
+        worker = _WhisperThread(args)
+        worker.log.connect(self._log)
+        worker.finished_with_code.connect(self._on_whisper_finished)
+        self._whisper_worker = worker
+        worker.start()
 
     @QtCore.Slot(int)
-    def on_progress(self, pct: int):
-        self.progress.setValue(pct)
-        self.lbl_pct.setText(f"{pct}%")
-
-    @QtCore.Slot(str, str, str, str)
-    def on_row_result(self, item: str, typ: str, status: str, msg: str):
-        r = self.table.rowCount()
-        self.table.insertRow(r)
-
-        def mk_item(text: str, bg: str, fg: str):
-            it = QtWidgets.QTableWidgetItem(text)
-            it.setBackground(QtGui.QColor(bg))
-            it.setForeground(QtGui.QColor(fg))
-            return it
-
-        if status == "OK":
-            bg, fg = cfg.COLOR_OK_BG, cfg.COLOR_OK_FG
-        elif status == "FAIL":
-            bg, fg = cfg.COLOR_FAIL_BG, cfg.COLOR_FAIL_FG
+    def _on_whisper_finished(self, code: int):
+        self._set_busy(False)
+        self.status.showMessage(f"Whisper done. Exit code: {code}")
+        if code == 0:
+            # read final file in UTF-8 and append to log
+            try:
+                wav = self._last_wav or ""
+                fmt = self._last_fmt or "srt"
+                out_dir = Path(wav).resolve().parent if wav else BASE_DIR
+                out_file = out_dir / (Path(wav).stem + f".{fmt}")
+                if out_file.exists():
+                    with open(out_file, "r", encoding="utf-8", errors="replace") as f:
+                        self._log("-----")
+                        self._log(f"[result] {out_file.name}")
+                        self._log(f.read())
+                    QtWidgets.QMessageBox.information(self, "OK", f"Transcription completed: {out_file.name}")
+                else:
+                    QtWidgets.QMessageBox.information(self, "OK", "Transcription completed.")
+            except Exception as e:
+                self._log(f"[read-result][error] {e}")
         else:
-            bg, fg = cfg.COLOR_PENDING_BG, cfg.COLOR_PENDING_FG
-
-        self.table.setItem(r, 0, mk_item(item, bg, fg))
-        self.table.setItem(r, 1, mk_item(typ, bg, fg))
-        self.table.setItem(r, 2, mk_item(status, bg, fg))
-        self.table.setItem(r, 3, mk_item(msg or "", bg, fg))
-        self.table.scrollToBottom()
-
-    @QtCore.Slot(str)
-    def on_log_line(self, line: str):
-        self.txt_log.appendPlainText(line)
-        self.txt_log.moveCursor(QtGui.QTextCursor.MoveOperation.End)
-
-    @QtCore.Slot(int, int)
-    def on_finished(self, oks: int, fails: int):
-        # no popups; just log a final line
-        total = len(cfg.build_steps())
-        line = f"Run finished. Success={oks} Fails={fails} Total={total}"
-        self.txt_log.appendPlainText(line)
-        self.txt_log.moveCursor(QtGui.QTextCursor.MoveOperation.End)
-        self.btn_run.setEnabled(True)
-
-    # close behavior controlled by toolbar toggle
-    def closeEvent(self, e: QtGui.QCloseEvent):
-        if self.confirm_on_close:
-            res = QtWidgets.QMessageBox.question(self, "Exit", "Close the window?")
-            if res != QtWidgets.QMessageBox.StandardButton.Yes:
-                e.ignore()
+            QtWidgets.QMessageBox.warning(self, "Warn", f"whisper returned code {code}. If missing, run install_whisper_portable.py")
+
+    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
+        if self.act_confirm_exit.isChecked():
+            r = QtWidgets.QMessageBox.question(
+                self,
+                "Confirm",
+                "Close the app?",
+                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
+            )
+            if r != QtWidgets.QMessageBox.StandardButton.Yes:
+                event.ignore()
                 return
-        # safe-stop worker if running
-        if hasattr(self, "_worker") and self._worker:
-            try: self._worker.stop()
-            except: pass
-        if self._thread and self._thread.isRunning():
-            self._thread.quit()
-            self._thread.wait(1500)
-        e.accept()
-
-# --------------------------
-# entry point  KAUAI 14_59
-# --------------------------
+        super().closeEvent(event)
+class _FFmpegThread(QtCore.QThread):
+    log = QtCore.Signal(str)
+    finished_with_code = QtCore.Signal(int)
+    def __init__(self, args: list[str]):
+        super().__init__()
+        self.args = args
+        self._exit = -1
+    def run(self):
+        import subprocess
+        try:
+            # ensure_ffmpeg() returns the ffmpeg binary path (str or Path)
+            ffbin = ffmpeg_upsert.ensure_ffmpeg()
+            cmd = [str(ffbin)] + list(self.args)
+            # spawn ffmpeg and emit its combined stdout/stderr lines to the UI
+            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
+            if proc.stdout is not None:
+                for line in proc.stdout:
+                    self.log.emit(line.rstrip())
+            proc.wait()
+            self._exit = proc.returncode
+        except Exception as e:
+            self.log.emit(f"[ffmpeg][error] {e}")
+            self._exit = -1
+        finally:
+            self.finished_with_code.emit(self._exit)
+
+class _WhisperThread(QtCore.QThread):
+    log = QtCore.Signal(str)
+    finished_with_code = QtCore.Signal(int)
+    def __init__(self, args: list[str]):
+        super().__init__()
+        self.args = args
+        self._exit = -1
+    def run(self):
+        def _emit(s: str): self.log.emit(s)
+        try:
+            code = run_whisper(self.args, on_log=_emit, prefer_python_module=True)
+            self._exit = code
+        except Exception as e:
+            self.log.emit(f"[whisper][error] {e}")
+            self._exit = -1
+        finally:
+            self.finished_with_code.emit(self._exit)
+            self.finished_with_code.emit(self._exit)
 
 def main():
     app = QtWidgets.QApplication(sys.argv)
-    w = MainWindow()
-    w.show()
+    win = MainWindow()
+    win.show()
     sys.exit(app.exec())
 
 if __name__ == "__main__":
     main()
+
+#WHI_V3 - build 6
diff --git a/ui_config.py b/ui_config.py
index 5aea384..87ad45f 100644
--- a/ui_config.py
+++ b/ui_config.py
@@ -18,7 +18,7 @@ WINDOW_HEIGHT = 620
 USE_FUSION_STYLE = True
 
 # ---------- editable colors ----------
-COLOR_WINDOW_BG   = "#ff0000"  # main window background-
+COLOR_WINDOW_BG   = "#d3d3d3"  # main window background-
 COLOR_WINDOW_FG   = "#eeff00"  # main window text
 COLOR_BASE_BG     = "#ffffff"  # text areas / inputs base-
 COLOR_ALT_BG      = "#eaeaea"  # alternating rows background-
@@ -27,11 +27,11 @@ COLOR_BUTTON_BG   = "#6c6e70cc"  # push buttons
 COLOR_BUTTON_FG   = "#000000"  # push buttons text
 COLOR_HILIGHT_BG  = "#2563eb"  # selection highlight
 COLOR_HILIGHT_FG  = "#ffffff"  # selection text
-COLOR_LINK_FG     = "#8ab4f8"  # tips/links text
+COLOR_LINK_FG     = "#0062ff"  # tips/links text
 
 # table row colors
 COLOR_OK_BG       = "#b2ffd5"
-COLOR_OK_FG       = "#a8ffc8"
+COLOR_OK_FG       = "#000000"
 COLOR_FAIL_BG     = "#4a0e0e"
 COLOR_FAIL_FG     = "#ffd0d0"
 COLOR_PENDING_BG  = "#1f2630"
diff --git a/whisper-webui-beta/public/app.js b/whisper-webui-beta/public/app.js
index e49bd6f..b21c80c 100644
--- a/whisper-webui-beta/public/app.js
+++ b/whisper-webui-beta/public/app.js
@@ -11,3 +11,5 @@
 
 
 
+
+
diff --git a/whisper-webui-beta/public/index.html b/whisper-webui-beta/public/index.html
index e49bd6f..b21c80c 100644
--- a/whisper-webui-beta/public/index.html
+++ b/whisper-webui-beta/public/index.html
@@ -11,3 +11,5 @@
 
 
 
+
+
diff --git a/whisper-webui-beta/public/style.css b/whisper-webui-beta/public/style.css
index e49bd6f..b21c80c 100644
--- a/whisper-webui-beta/public/style.css
+++ b/whisper-webui-beta/public/style.css
@@ -11,3 +11,5 @@
 
 
 
+
+
diff --git a/whisper-webui-beta/server.ps1 b/whisper-webui-beta/server.ps1
index e49bd6f..b21c80c 100644
--- a/whisper-webui-beta/server.ps1
+++ b/whisper-webui-beta/server.ps1
@@ -11,3 +11,5 @@
 
 
 
+
+
diff --git a/whisper-webui-beta/start.bat b/whisper-webui-beta/start.bat
index e49bd6f..b21c80c 100644
--- a/whisper-webui-beta/start.bat
+++ b/whisper-webui-beta/start.bat
@@ -11,3 +11,5 @@
 
 
 
+
+
diff --git a/whisper_upsert.py b/whisper_upsert.py
new file mode 100644
index 0000000..3d41745
--- /dev/null
+++ b/whisper_upsert.py
@@ -0,0 +1,121 @@
+# whisper_upsert.py
+# Portable Whisper runner with UTF-8 logs (ASCII-only)
+
+from __future__ import annotations
+import os
+import sys
+import shlex
+import shutil
+import subprocess
+from pathlib import Path
+from typing import Callable, Optional, Sequence, Union
+
+BASE_DIR = Path(__file__).resolve().parent
+
+def _is_windows() -> bool:
+    return os.name == "nt"
+
+def _python_exe() -> str:
+    return sys.executable or "python"
+
+def _module_exists(name: str) -> bool:
+    try:
+        __import__(name)
+        return True
+    except Exception:
+        return False
+
+def resolve_whisper_command(prefer_python_module: bool = True) -> list[str]:
+    if prefer_python_module and _module_exists("whisper"):
+        return [_python_exe(), "-m", "whisper"]
+    exe = shutil.which("whisper")
+    if exe:
+        return [exe]
+    raise FileNotFoundError(
+        "whisper CLI not found. Install openai-whisper first.\n"
+        "Run: python install_whisper_portable.py"
+    )
+
+def run_whisper(
+    args: Union[str, Sequence[str]],
+    on_log: Callable[[str], None],
+    cwd: Optional[Union[str, Path]] = None,
+    env: Optional[dict] = None,
+    prefer_python_module: bool = True,
+) -> int:
+    base = resolve_whisper_command(prefer_python_module=prefer_python_module)
+    cmd = base + (shlex.split(args) if isinstance(args, str) else list(args))
+
+    creationflags = 0
+    startupinfo = None
+    if _is_windows():
+        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
+        startupinfo = subprocess.STARTUPINFO()
+        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # type: ignore[attr-defined]
+        startupinfo.wShowWindow = 0  # type: ignore[attr-defined]
+
+    proc_env = (env or os.environ.copy())
+    # Force Python CLI to emit UTF-8
+    proc_env["PYTHONIOENCODING"] = "UTF-8"
+    proc_env.setdefault("LC_ALL", "C.UTF-8")
+    proc_env.setdefault("LANG", "C.UTF-8")
+
+    proc = subprocess.Popen(
+        cmd,
+        cwd=str(cwd) if cwd else None,
+        env=proc_env,
+        stdout=subprocess.PIPE,
+        stderr=subprocess.STDOUT,
+        bufsize=1,
+        text=True,
+        encoding="utf-8",
+        errors="replace",
+        creationflags=creationflags,
+        startupinfo=startupinfo,
+    )
+
+    try:
+        if proc.stdout is not None:
+            for line in proc.stdout:
+                on_log(line.rstrip("\r\n"))
+    finally:
+        if proc.stdout:
+            proc.stdout.close()
+
+    code = proc.wait()
+    on_log(f"[whisper] exit code: {code}")
+    return code
+
+def build_args_transcribe(
+    input_path: Union[str, Path],
+    model: str = "base",
+    language: Optional[str] = None,
+    output_dir: Optional[Union[str, Path]] = None,
+    output_format: str = "srt",  # srt|vtt|txt|json|all
+    extras: Optional[list[str]] = None,
+) -> list[str]:
+    args = [
+        str(input_path),
+        "--model", model,
+        "--task", "transcribe",
+        "--output_format", output_format,
+    ]
+    if language:
+        args += ["--language", language]
+    if output_dir:
+        args += ["--output_dir", str(output_dir)]
+    args += ["--fp16", "False"]
+    if extras:
+        args += extras
+    return args
+
+if __name__ == "__main__":
+    def printer(s: str): print(s)
+    try:
+        code = run_whisper(["--help"], on_log=printer)
+        sys.exit(code)
+    except Exception as e:
+        print(f"[error] {e}")
+        sys.exit(1)
+
+#WHI_V3 - build 2

## Mapa do repo (top 200)
.github/workflows/gpt-context.yml
.gitignore
__pycache__/ffmpeg_upsert.cpython-313.pyc
__pycache__/ui_config.cpython-313.pyc
__pycache__/whisper_upsert.cpython-313.pyc
ffmpeg_upsert.py
install_ffmpeg_portable.py
install_whisper_portable.py
main.py
ui_config.py
whisper-webui-beta/public/app.js
whisper-webui-beta/public/index.html
whisper-webui-beta/public/style.css
whisper-webui-beta/server.ps1
whisper-webui-beta/start.bat
whisper_upsert.py
