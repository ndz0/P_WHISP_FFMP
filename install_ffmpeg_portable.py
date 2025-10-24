# install_ffmpeg_portable.py
# Install portable FFmpeg into ./bin/ffmpeg on Windows
# Strategy: try Chocolatey (ffmpeg.portable), else download ZIP (gyan.dev)
# ASCII-only

from __future__ import annotations
import os
import sys
import time
import glob
import shutil
import zipfile
import tempfile
import subprocess
from pathlib import Path
from urllib.request import urlopen

BASE_DIR = Path(__file__).resolve().parent
DEST_DIR = BASE_DIR / "bin" / "ffmpeg"
DEST_DIR.mkdir(parents=True, exist_ok=True)

GYAN_ZIP = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

def copy_if_exists(src: Path, dst_dir: Path):
    if src and src.exists():
        dst = dst_dir / src.name
        dst_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dst))
        print(f"OK: copied {src} -> {dst}")

def try_choco_install() -> bool:
    print("INFO: trying Chocolatey (ffmpeg.portable)...")
    choco = shutil.which("choco")
    if not choco:
        print("WARN: choco not found; skipping Chocolatey path.")
        return False

    try:
        # silent install
        cmd = [choco, "install", "ffmpeg.portable", "-y", "--no-progress"]
        print("CMD:", " ".join(cmd))
        res = subprocess.run(cmd, check=False)
        if res.returncode != 0:
            print(f"WARN: choco install returned {res.returncode}")
            # Continue anyway; maybe already installed
    except Exception as e:
        print(f"WARN: choco install error: {e}")

    # locate binaries under %ProgramData%\chocolatey\lib\ffmpeg*
    program_data = os.environ.get("ProgramData", r"C:\ProgramData")
    lib_root = Path(program_data) / "chocolatey" / "lib"
    if not lib_root.exists():
        print("WARN: Chocolatey lib folder not found.")
        return False

    candidates = list(lib_root.glob("ffmpeg*"))
    if not candidates:
        print("WARN: no ffmpeg* package under Chocolatey lib.")
        return False

    # pick newest by mtime
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    newest = candidates[0]
    exe_ffmpeg = next(newest.rglob("ffmpeg.exe"), None)
    exe_ffprobe = next(newest.rglob("ffprobe.exe"), None)

    if not exe_ffmpeg:
        print("WARN: ffmpeg.exe not found under Chocolatey package.")
        return False

    copy_if_exists(exe_ffmpeg, DEST_DIR)
    if exe_ffprobe:
        copy_if_exists(exe_ffprobe, DEST_DIR)

    print(f"OK: FFmpeg available in {DEST_DIR}")
    return True

def download_and_extract_zip(url: str, dest_dir: Path) -> bool:
    print(f"INFO: downloading ZIP from {url} ...")
    with tempfile.TemporaryDirectory() as td:
        tmp_zip = Path(td) / "ffmpeg.zip"
        with urlopen(url) as r, open(tmp_zip, "wb") as f:
            shutil.copyfileobj(r, f)

        with zipfile.ZipFile(tmp_zip) as zf:
            zf.extractall(td)

        # Find ffmpeg.exe and ffprobe.exe inside extracted tree
        ffmpeg_exe = None
        ffprobe_exe = None
        for p in Path(td).rglob("*"):
            name = p.name.lower()
            if name == "ffmpeg.exe":
                ffmpeg_exe = p
            elif name == "ffprobe.exe":
                ffprobe_exe = p

        if not ffmpeg_exe:
            print("ERR: could not find ffmpeg.exe inside ZIP.")
            return False

        copy_if_exists(ffmpeg_exe, dest_dir)
        if ffprobe_exe:
            copy_if_exists(ffprobe_exe, dest_dir)
        print(f"OK: FFmpeg available in {dest_dir}")
        return True

def main():
    # already installed?
    exe = DEST_DIR / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    if exe.exists():
        print(f"OK: already present -> {exe}")
        return 0

    # Option 1: Chocolatey
    if try_choco_install():
        return 0

    # Option 2: direct ZIP
    ok = download_and_extract_zip(GYAN_ZIP, DEST_DIR)
    if not ok:
        print("ERR: failed to install FFmpeg.")
        return 2
    return 0

if __name__ == "__main__":
    sys.exit(main())

#WHI_V3 - build 1
