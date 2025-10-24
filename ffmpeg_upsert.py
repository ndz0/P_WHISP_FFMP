# ffmpeg_upsert.py
# Portable FFmpeg runner + setup helpers (UTF-8 logs)
# ASCII-only

from __future__ import annotations
import os
import sys
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional, Sequence, Union

BASE_DIR = Path(__file__).resolve().parent
BIN_DIR = BASE_DIR / "bin" / "ffmpeg"
BIN_DIR.mkdir(parents=True, exist_ok=True)

def _is_windows() -> bool:
    return os.name == "nt"

def local_ffmpeg_path() -> Optional[Path]:
    exe = "ffmpeg.exe" if _is_windows() else "ffmpeg"
    p = BIN_DIR / exe
    return p if p.exists() else None

def find_ffmpeg_in_path() -> Optional[Path]:
    exe = "ffmpeg.exe" if _is_windows() else "ffmpeg"
    found = shutil.which(exe)
    return Path(found) if found else None

def ensure_ffmpeg(prefer_local: bool = True) -> Path:
    if prefer_local:
        p = local_ffmpeg_path()
        if p:
            return p
    p = find_ffmpeg_in_path()
    if p:
        return p
    expected = BIN_DIR / ("ffmpeg.exe" if _is_windows() else "ffmpeg")
    raise FileNotFoundError(
        f"ffmpeg not found. Expected at '{expected}' or in PATH. "
        f"Run 'install_ffmpeg_portable.py' or 'install_ffmpeg_portable.bat'."
    )

def run_ffmpeg(
    args: Union[str, Sequence[str]],
    on_log: Callable[[str], None],
    cwd: Optional[Union[str, Path]] = None,
    env: Optional[dict] = None,
    prefer_local: bool = True,
    combine_stdout_stderr: bool = True,
) -> int:
    ffmpeg_exe = str(ensure_ffmpeg(prefer_local=prefer_local))
    cmd = [ffmpeg_exe] + (shlex.split(args) if isinstance(args, str) else list(args))

    creationflags = 0
    startupinfo = None
    if _is_windows():
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # type: ignore[attr-defined]
        startupinfo.wShowWindow = 0  # type: ignore[attr-defined]

    merged = subprocess.STDOUT if combine_stdout_stderr else subprocess.PIPE
    proc_env = (env or os.environ.copy())

    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=proc_env,
        stdout=subprocess.PIPE,
        stderr=merged,
        bufsize=1,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=creationflags,
        startupinfo=startupinfo,
    )

    try:
        if proc.stdout is not None:
            for line in proc.stdout:
                on_log(line.rstrip("\r\n"))
    finally:
        if proc.stdout:
            proc.stdout.close()

    code = proc.wait()
    on_log(f"[ffmpeg] exit code: {code}")
    return code

if __name__ == "__main__":
    def printer(msg: str): print(msg)
    try:
        rc = run_ffmpeg("-version", on_log=printer)
        sys.exit(rc)
    except Exception as exc:
        print(f"[error] {exc}")
        sys.exit(1)

#WHI_V3 - build 2
