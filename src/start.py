#!/usr/bin/env python3
"""
start_step.py  –  truly interactive wrapper around test_executor.py

• runs ONE LLM / Docker attempt at a time (loops=1)
• after every run:
      – looks for a new/updated output_data_*.yml
      – shows a 1‑line plain‑English summary of the result
      – asks the user whether to continue
• stops as soon as the last error_type is not a dependency error
  (None, SyntaxError, NonZeroCode are considered SUCCESS)
"""

from __future__ import annotations
import os, sys, subprocess, pathlib, time, glob, yaml, textwrap, itertools
import requests, json, uuid

SRC       = pathlib.Path(__file__).resolve().parent
EXECUTOR  = SRC / "test_executor.py"
DEFAULT_PY = SRC.parent / "local-test-gists/5780127/snippet.py"
OLLAMA_URL = "http://localhost:11434"
DOCKER_TAG = "test/pllm"

def snippet_dir(pyfile: str | pathlib.Path) -> pathlib.Path:
    return pathlib.Path(pyfile).expanduser().resolve().parent

def ask(q: str, default: str | None = None) -> str:
    prompt = f"{q} [{default}]: " if default else f"{q}: "
    ans = input(prompt).strip()
    return ans or (default or "")

def list_models() -> list[str]:
    try:
        out = subprocess.check_output(["ollama", "list"], text=True)
        return [ln.split()[0] for ln in out.splitlines() if ln and not ln.startswith("NAME")]
    except Exception:
        return []

# ── main interactive loop ──────────────────────────────────────────────
def main() -> None:

    # ------------------------------------------------------------------
    pyfile = ask("Path to Python snippet", str(DEFAULT_PY))
    if not pathlib.Path(pyfile).is_file():
        sys.exit(f"❌  File not found: {pyfile}")

    models = list_models()
    if not models:
        sys.exit("❌  Could not contact Ollama – is `ollama serve` running?")
    for i, m in enumerate(models, 1):
        print(f"  {i}. {m}")
    model = models[int(ask("Pick model #", "1")) - 1]

    rng = int(ask("Python‑version range (0 = only guessed)", "0"))
    max_outer_loops = int(ask("Maximum total attempts", "10"))
    print()

    # ------------------------------------------------------------------
    # Fire up test_executor **once** in real interactive mode (‑i) and
    # hand control over to it.  When the executor finishes we simply quit.
    cmd = [
        sys.executable, str(EXECUTOR),
        "-f", str(pyfile),
        "-m", model,
        "-b", OLLAMA_URL,
        "-t", "0.1",                 # or keep your preferred temp
        "-l", str(max_outer_loops),  # let executor own the inner loop
        "-r", str(rng),
        "-i",                        # <‑‑ new flag = interactive
    ]
    print("▶  Handing over to test_executor.py – press Ctrl‑C inside it "
          "to abort.\n")
    subprocess.call(cmd, cwd=str(SRC))
    return


# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹  Aborted by user.")
