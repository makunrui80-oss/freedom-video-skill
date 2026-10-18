#!/usr/bin/env python3
"""Install and smoke-test the pinned Kokoro Chinese narration stack."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


SOURCE_REPO = "https://github.com/ardorleo/kokoro-tts-zh.git"
SOURCE_REV = "261b9f78ae9861da972ad9293d6f89e1a4dd8a72"
KOKORO_REV = "dfb907a02bba8152ca444717ca5d78747ccb4bec"
MISAKI_REV = "fba1236595f2d2bf21d414ba6e57d25256afada3"


def run(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> None:
    print("+ " + " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, env=env, check=True)


def version_supported(python: Path) -> bool:
    try:
        value = subprocess.check_output(
            [str(python), "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
            text=True,
        ).strip()
        major, minor = (int(part) for part in value.split("."))
        return major == 3 and 10 <= minor < 14
    except (OSError, subprocess.CalledProcessError, ValueError):
        return False


def select_python(project_root: Path) -> Path:
    candidates: list[Path] = []
    if os.environ.get("KOKORO_PYTHON"):
        candidates.append(Path(os.environ["KOKORO_PYTHON"]))
    candidates.extend(
        [
            project_root / ".miniforge" / "envs" / "manim" / "bin" / "python",
            project_root / ".venv-manim" / "bin" / "python",
            project_root / ".venv-manim" / "Scripts" / "python.exe",
        ]
    )
    for name in ("python3.13", "python3.12", "python3.11", "python3.10"):
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))
    candidates.append(Path(sys.executable))
    for candidate in candidates:
        if candidate.is_file() and version_supported(candidate):
            return candidate.resolve()
    raise RuntimeError(
        "Kokoro requires Python 3.10-3.13. Set KOKORO_PYTHON to a compatible interpreter."
    )


def venv_python(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def ensure_source(project_root: Path) -> Path:
    target = project_root / ".vendor" / "kokoro-tts-zh"
    if target.exists() and not (target / ".git").is_dir():
        raise RuntimeError(f"Refusing to overwrite non-Git path: {target}")
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", "--filter=blob:none", "--no-checkout", SOURCE_REPO, str(target)])
    run(["git", "-C", str(target), "fetch", "--depth", "1", "origin", SOURCE_REV])
    run(["git", "-C", str(target), "checkout", "--detach", SOURCE_REV])
    return target


def install(project_root: Path) -> Path:
    venv = project_root / ".venv-kokoro"
    python = venv_python(venv)
    if python.is_file() and not version_supported(python):
        raise RuntimeError(
            f"Existing Kokoro environment uses an unsupported Python: {python}. "
            "Move it aside and rerun setup with Python 3.10-3.13."
        )
    if not python.is_file():
        base_python = select_python(project_root)
        run([str(base_python), "-m", "venv", str(venv)])
    run([str(python), "-m", "pip", "install", "--upgrade", "pip", "wheel"])
    run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            f"misaki[zh] @ git+https://github.com/hexgrad/misaki.git@{MISAKI_REV}",
            f"kokoro @ git+https://github.com/hexgrad/kokoro.git@{KOKORO_REV}",
            "soundfile>=0.12,<1",
        ]
    )
    run(
        [
            str(python),
            "-c",
            "from kokoro import KModel, KPipeline; import misaki, soundfile; print('Kokoro imports passed')",
        ]
    )
    return python


def smoke_test(python: Path) -> None:
    narrator = Path(__file__).with_name("kokoro_narrate.py")
    download_env = os.environ.copy()
    download_env.setdefault("HF_HUB_DISABLE_XET", "1")
    download_env.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "600")
    with tempfile.TemporaryDirectory(prefix="agnes-video-kokoro-") as temp:
        output = Path(temp) / "smoke.wav"
        run(
            [
                str(python),
                str(narrator),
                "--text",
                "你好，这是语音测试。",
                "--voice",
                "zf_032",
                "--speed",
                "0.96",
                "--output",
                str(output),
            ],
            env=download_env,
        )
        run(
            [
                str(python),
                "-c",
                "import soundfile as sf,sys; d,s=sf.read(sys.argv[1]); assert s==24000 and d.ndim==1 and len(d)>2400; print(f'Kokoro smoke WAV: {len(d)/s:.2f}s')",
                str(output),
            ]
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument(
        "--skip-smoke-test",
        action="store_true",
        help="Install/import check only; not valid for a production video workflow",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = args.project_root.expanduser().resolve()
    project_root.mkdir(parents=True, exist_ok=True)
    try:
        source = ensure_source(project_root)
        python = install(project_root)
        if not args.skip_smoke_test:
            smoke_test(python)
    except (OSError, subprocess.CalledProcessError, RuntimeError) as exc:
        print(f"ERROR: Kokoro setup failed: {exc}", file=sys.stderr)
        return 1
    print(f"KOKORO_SOURCE={source}")
    print(f"KOKORO_PYTHON={python}")
    print("Kokoro narration validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
