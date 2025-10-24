# main.py
# UI PySide6: convert to WAV (FFmpeg) and auto-transcribe with Whisper
# No "Transcribe" button; UTF-8 end-to-end; reads final file to show accents correctly
# ASCII-only

from __future__ import annotations
import sys
from pathlib import Path
from PySide6 import QtCore, QtWidgets, QtGui

import ffmpeg_upsert
from whisper_upsert import run_whisper, build_args_transcribe

BASE_DIR = Path(__file__).resolve().parent

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Whisper WAV Converter + Transcriber (Auto)")
        self.resize(980, 620)

        # toolbar toggle
        self.toolbar = self.addToolBar("Main")
        self.toolbar.setMovable(False)
        self.act_confirm_exit = QtGui.QAction("Confirm exit?", self)
        self.act_confirm_exit.setCheckable(True)
        self.toolbar.addAction(self.act_confirm_exit)

        # status
        self.status = self.statusBar()

        # widgets
        self.in_edit = QtWidgets.QLineEdit()
        self.in_btn  = QtWidgets.QPushButton("Browse...")
        self.out_edit = QtWidgets.QLineEdit()
        self.out_btn  = QtWidgets.QPushButton("Browse...")
        self.over_cb  = QtWidgets.QCheckBox("Overwrite (-y)")
        self.over_cb.setChecked(True)

        self.convert_btn = QtWidgets.QPushButton("Convert to WAV (mono 16k)")

        # whisper controls (sem botao)
        self.model_cb = QtWidgets.QComboBox()
        self.model_cb.addItems(["tiny", "tiny.en", "base", "base.en", "small", "small.en", "medium", "large-v3"])
        self.lang_edit = QtWidgets.QLineEdit()
        self.lang_edit.setPlaceholderText("auto or ISO code (e.g. pt)")
        self.format_cb = QtWidgets.QComboBox()
        self.format_cb.addItems(["srt", "vtt", "txt", "json"])

        self.log_view = QtWidgets.QPlainTextEdit(); self.log_view.setReadOnly(True)

        # layout
        form = QtWidgets.QFormLayout()
        r1 = QtWidgets.QHBoxLayout(); r1.addWidget(self.in_edit, 1); r1.addWidget(self.in_btn)
        r2 = QtWidgets.QHBoxLayout(); r2.addWidget(self.out_edit, 1); r2.addWidget(self.out_btn)
        form.addRow("Input:", r1)
        form.addRow("Output WAV:", r2)

        opts = QtWidgets.QHBoxLayout()
        opts.addWidget(self.over_cb); opts.addStretch(1)

        whisper_row1 = QtWidgets.QHBoxLayout()
        whisper_row1.addWidget(QtWidgets.QLabel("Model:")); whisper_row1.addWidget(self.model_cb)
        whisper_row1.addWidget(QtWidgets.QLabel("Lang:"));  whisper_row1.addWidget(self.lang_edit)
        whisper_row1.addWidget(QtWidgets.QLabel("Format:")); whisper_row1.addWidget(self.format_cb)
        whisper_row1.addStretch(1)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(form)
        vbox.addLayout(opts)
        vbox.addWidget(self.convert_btn)
        vbox.addSpacing(8)
        vbox.addLayout(whisper_row1)
        vbox.addWidget(self.log_view, 1)

        central = QtWidgets.QWidget(); central.setLayout(vbox)
        self.setCentralWidget(central)

        # connections
        self.in_btn.clicked.connect(self.pick_input)
        self.out_btn.clicked.connect(self.pick_output)
        self.convert_btn.clicked.connect(self.on_convert_clicked)

        self._ff_worker = None
        self._whisper_worker = None
        self._last_wav = None
        self._last_fmt = None

        # ffmpeg status
        try:
            p = ffmpeg_upsert.ensure_ffmpeg()
            self.status.showMessage(f"ffmpeg OK: {p}")
        except Exception:
            self.status.showMessage("ffmpeg not found. Run install_ffmpeg_portable.py")

        # remember toggle
        self.settings = QtCore.QSettings("P_WHISP_FFMP", "WAVConverter")
        # QSettings.value may be typed as 'object' by type checkers, coerce to bool explicitly
        self.act_confirm_exit.setChecked(bool(self.settings.value("confirm_exit", False, type=bool)))
        self.act_confirm_exit.toggled.connect(lambda v: self.settings.setValue("confirm_exit", v))

    # helpers
    def pick_input(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Choose input media", str(BASE_DIR), "Media files (*.*)")
        if not path: return
        self.in_edit.setText(path)
        self.out_edit.setText(str(self._suggest_wav(Path(path))))

    def pick_output(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Choose output WAV", str(BASE_DIR / "output.wav"), "WAV (*.wav)")
        if not path: return
        if not path.lower().endswith(".wav"): path += ".wav"
        self.out_edit.setText(path)

    def _suggest_wav(self, src: Path) -> Path:
        return src.with_name(f"{src.stem}.wav")

    def _set_busy(self, busy: bool):
        for w in (self.convert_btn, self.in_btn, self.out_btn, self.in_edit, self.out_edit,
                  self.over_cb, self.model_cb, self.lang_edit, self.format_cb):
            w.setEnabled(not busy)  # keep ascii logic simple
        self.setCursor(QtCore.Qt.CursorShape.BusyCursor if busy else QtCore.Qt.CursorShape.ArrowCursor)

    def _log(self, text: str):
        self.log_view.appendPlainText(text)

    # convert (FFmpeg)
    def on_convert_clicked(self):
        src = self.in_edit.text().strip()
        dst = self.out_edit.text().strip()
        if not src:
            QtWidgets.QMessageBox.warning(self, "Warn", "Select an input file"); return
        if not Path(src).exists():
            QtWidgets.QMessageBox.critical(self, "Error", "Input file not found"); return
        if not dst:
            dst = str(self._suggest_wav(Path(src))); self.out_edit.setText(dst)

        try:
            p = ffmpeg_upsert.ensure_ffmpeg()
            self._log(f"[ffmpeg] using: {p}")
        except Exception:
            QtWidgets.QMessageBox.critical(self, "FFmpeg missing", "ffmpeg not found.\nRun: python install_ffmpeg_portable.py")
            return

        args = []
        if self.over_cb.isChecked(): args += ["-y"]
        args += ["-i", src, "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", dst]

        self._last_wav = dst
        self.log_view.clear()
        self._set_busy(True)
        # Use internal FFmpeg thread wrapper instead of missing FFmpegWorker from ffmpeg_upsert
        self._ff_worker = _FFmpegThread(args)
        self._ff_worker.log.connect(self._log)
        self._ff_worker.finished_with_code.connect(self._on_ffmpeg_finished)
        self._ff_worker.start()
        self.status.showMessage("Converting...")

    @QtCore.Slot(int)
    def _on_ffmpeg_finished(self, code: int):
        self._set_busy(False)
        self.status.showMessage(f"FFmpeg done. Exit code: {code}")
        if code != 0:
            QtWidgets.QMessageBox.warning(self, "Warn", f"ffmpeg returned code {code}")
            return
        wav = self._last_wav
        if not wav or not Path(wav).exists():
            self._log("[auto] output WAV not found; skipping whisper")
            return
        self._log("-----")
        self._log("[auto] starting Whisper transcription...")
        self._start_whisper(wav)

    # whisper (auto)
    def _start_whisper(self, wav_path: str):
        model = self.model_cb.currentText().strip()
        lang  = self.lang_edit.text().strip() or None
        fmt   = self.format_cb.currentText().strip()
        self._last_fmt = fmt
        out_dir = str(Path(wav_path).resolve().parent)

        args = build_args_transcribe(
            input_path=wav_path,
            model=model,
            language=lang,
            output_dir=out_dir,
            output_format=fmt
        )

        self._set_busy(True)
        self._log(f"[whisper] model={model} lang={lang or 'auto'} format={fmt}")
        self.status.showMessage("Transcribing...")

        worker = _WhisperThread(args)
        worker.log.connect(self._log)
        worker.finished_with_code.connect(self._on_whisper_finished)
        self._whisper_worker = worker
        worker.start()

    @QtCore.Slot(int)
    def _on_whisper_finished(self, code: int):
        self._set_busy(False)
        self.status.showMessage(f"Whisper done. Exit code: {code}")
        if code == 0:
            # read final file in UTF-8 and append to log
            try:
                wav = self._last_wav or ""
                fmt = self._last_fmt or "srt"
                out_dir = Path(wav).resolve().parent if wav else BASE_DIR
                out_file = out_dir / (Path(wav).stem + f".{fmt}")
                if out_file.exists():
                    with open(out_file, "r", encoding="utf-8", errors="replace") as f:
                        self._log("-----")
                        self._log(f"[result] {out_file.name}")
                        self._log(f.read())
                    QtWidgets.QMessageBox.information(self, "OK", f"Transcription completed: {out_file.name}")
                else:
                    QtWidgets.QMessageBox.information(self, "OK", "Transcription completed.")
            except Exception as e:
                self._log(f"[read-result][error] {e}")
        else:
            QtWidgets.QMessageBox.warning(self, "Warn", f"whisper returned code {code}. If missing, run install_whisper_portable.py")

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        if self.act_confirm_exit.isChecked():
            r = QtWidgets.QMessageBox.question(
                self,
                "Confirm",
                "Close the app?",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
            )
            if r != QtWidgets.QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        super().closeEvent(event)
class _FFmpegThread(QtCore.QThread):
    log = QtCore.Signal(str)
    finished_with_code = QtCore.Signal(int)
    def __init__(self, args: list[str]):
        super().__init__()
        self.args = args
        self._exit = -1
    def run(self):
        import subprocess
        try:
            # ensure_ffmpeg() returns the ffmpeg binary path (str or Path)
            ffbin = ffmpeg_upsert.ensure_ffmpeg()
            cmd = [str(ffbin)] + list(self.args)
            # spawn ffmpeg and emit its combined stdout/stderr lines to the UI
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            if proc.stdout is not None:
                for line in proc.stdout:
                    self.log.emit(line.rstrip())
            proc.wait()
            self._exit = proc.returncode
        except Exception as e:
            self.log.emit(f"[ffmpeg][error] {e}")
            self._exit = -1
        finally:
            self.finished_with_code.emit(self._exit)

class _WhisperThread(QtCore.QThread):
    log = QtCore.Signal(str)
    finished_with_code = QtCore.Signal(int)
    def __init__(self, args: list[str]):
        super().__init__()
        self.args = args
        self._exit = -1
    def run(self):
        def _emit(s: str): self.log.emit(s)
        try:
            code = run_whisper(self.args, on_log=_emit, prefer_python_module=True)
            self._exit = code
        except Exception as e:
            self.log.emit(f"[whisper][error] {e}")
            self._exit = -1
        finally:
            self.finished_with_code.emit(self._exit)
            self.finished_with_code.emit(self._exit)

def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

#WHI_V3 - build 6
