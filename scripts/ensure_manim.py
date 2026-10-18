#!/usr/bin/env python3
"""Ensure Manim is usable and prove it with a small real render."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


SCENE_SOURCE = """from manim import *

class SkillSmokeTest(Scene):
    def construct(self):
        label = Text("OK", font_size=48)
        self.play(FadeIn(label), run_time=0.1)
        self.wait(0.1)
"""


def run(command: list[str], *, cwd: Path | None = None) -> None:
    shown = " ".join(command)
    print(f"+ {shown}", flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def manim_command(candidate: Path | str) -> list[str]:
    candidate_path = Path(candidate)
    if candidate_path.name.startswith("python"):
        return [str(candidate_path), "-m", "manim"]
    return [str(candidate_path)]


def find_manim(project_root: Path) -> list[str] | None:
    candidates = [
        project_root / ".venv-manim" / "bin" / "manim",
        project_root / ".venv-manim" / "Scripts" / "manim.exe",
        project_root / ".miniforge" / "envs" / "manim" / "bin" / "manim",
    ]
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return [str(candidate)]

    system_manim = shutil.which("manim")
    if system_manim:
        return [system_manim]
    return None


def install_local_manim(project_root: Path) -> list[str]:
    venv = project_root / ".venv-manim"
    if not venv.exists():
        run([sys.executable, "-m", "venv", str(venv)])

    python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    run([str(python), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(python), "-m", "pip", "install", "manim"])
    return manim_command(python)


def smoke_render(command: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="agnes-video-manim-") as temp:
        root = Path(temp)
        scene = root / "smoke_scene.py"
        media = root / "media"
        scene.write_text(SCENE_SOURCE, encoding="utf-8")
        run(
            command
            + [
                "-ql",
                "--disable_caching",
                "--media_dir",
                str(media),
                str(scene),
                "SkillSmokeTest",
            ],
            cwd=root,
        )
        outputs = list(media.rglob("*.mp4"))
        if not outputs or all(path.stat().st_size == 0 for path in outputs):
            raise RuntimeError("Manim completed without producing a non-empty MP4")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = args.project_root.expanduser().resolve()
    project_root.mkdir(parents=True, exist_ok=True)

    command = find_manim(project_root)
    if command is None:
        print("Manim not found; installing into .venv-manim", flush=True)
        command = install_local_manim(project_root)

    try:
        run(command + ["--version"])
        smoke_render(command)
    except (OSError, subprocess.CalledProcessError, RuntimeError) as exc:
        print(f"ERROR: Manim validation failed: {exc}", file=sys.stderr)
        return 1

    print(f"MANIM_COMMAND={' '.join(command)}")
    print("Manim smoke render passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
