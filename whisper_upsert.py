# whisper_upsert.py
# Portable Whisper runner with UTF-8 logs (ASCII-only)

from __future__ import annotations
import os
import sys
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional, Sequence, Union

BASE_DIR = Path(__file__).resolve().parent

def _is_windows() -> bool:
    return os.name == "nt"

def _python_exe() -> str:
    return sys.executable or "python"

def _module_exists(name: str) -> bool:
    try:
        __import__(name)
        return True
    except Exception:
        return False

def resolve_whisper_command(prefer_python_module: bool = True) -> list[str]:
    if prefer_python_module and _module_exists("whisper"):
        return [_python_exe(), "-m", "whisper"]
    exe = shutil.which("whisper")
    if exe:
        return [exe]
    raise FileNotFoundError(
        "whisper CLI not found. Install openai-whisper first.\n"
        "Run: python install_whisper_portable.py"
    )

def run_whisper(
    args: Union[str, Sequence[str]],
    on_log: Callable[[str], None],
    cwd: Optional[Union[str, Path]] = None,
    env: Optional[dict] = None,
    prefer_python_module: bool = True,
) -> int:
    base = resolve_whisper_command(prefer_python_module=prefer_python_module)
    cmd = base + (shlex.split(args) if isinstance(args, str) else list(args))

    creationflags = 0
    startupinfo = None
    if _is_windows():
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # type: ignore[attr-defined]
        startupinfo.wShowWindow = 0  # type: ignore[attr-defined]

    proc_env = (env or os.environ.copy())
    # Force Python CLI to emit UTF-8
    proc_env["PYTHONIOENCODING"] = "UTF-8"
    proc_env.setdefault("LC_ALL", "C.UTF-8")
    proc_env.setdefault("LANG", "C.UTF-8")

    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=proc_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
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
    on_log(f"[whisper] exit code: {code}")
    return code

def build_args_transcribe(
    input_path: Union[str, Path],
    model: str = "base",
    language: Optional[str] = None,
    output_dir: Optional[Union[str, Path]] = None,
    output_format: str = "srt",  # srt|vtt|txt|json|all
    extras: Optional[list[str]] = None,
) -> list[str]:
    args = [
        str(input_path),
        "--model", model,
        "--task", "transcribe",
        "--output_format", output_format,
    ]
    if language:
        args += ["--language", language]
    if output_dir:
        args += ["--output_dir", str(output_dir)]
    args += ["--fp16", "False"]
    if extras:
        args += extras
    return args

if __name__ == "__main__":
    def printer(s: str): print(s)
    try:
        code = run_whisper(["--help"], on_log=printer)
        sys.exit(code)
    except Exception as e:
        print(f"[error] {e}")
        sys.exit(1)

#WHI_V3 - build 2
