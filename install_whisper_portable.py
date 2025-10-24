# install_whisper_portable.py
# Install openai-whisper into current Python env (prefer venv)
# ASCII-only

from __future__ import annotations
import os
import sys
import subprocess

def run(cmd: list[str]) -> int:
    print("CMD:", " ".join(cmd))
    return subprocess.call(cmd)

def main() -> int:
    py = sys.executable or "python"
    print(f"INFO: using python: {py}")

    # upgrade pip (optional but helps)
    run([py, "-m", "pip", "install", "--upgrade", "pip"])

    # install torch first is optional; openai-whisper will pull a compatible build.
    # If you want CPU-only torch explicitly, uncomment below:
    # run([py, "-m", "pip", "install", "torch", "--index-url", "https://download.pytorch.org/whl/cpu"])

    # install openai-whisper
    rc = run([py, "-m", "pip", "install", "-U", "openai-whisper"])
    if rc != 0:
        print("ERR: failed to install openai-whisper")
        return rc

    # quick smoke test
    print("INFO: validating whisper CLI...")
    rc = run([py, "-m", "whisper", "--help"])
    if rc != 0:
        print("WARN: whisper CLI returned non-zero (may still be ok to run).")
    else:
        print("OK: whisper CLI is available.")

    print("DONE.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

#WHI_V3 - build 1
