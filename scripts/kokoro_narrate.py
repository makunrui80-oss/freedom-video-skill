#!/usr/bin/env python3
"""Generate steady Chinese narration with Kokoro preset voices."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
import time

os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "600")

MODEL_ID = "hexgrad/Kokoro-82M-v1.1-zh"
SAMPLE_RATE = 24_000
DEFAULT_VOICE = "zf_032"
DEFAULT_SPEED = 0.96

FEMALE_VOICES = """
zf_001 zf_002 zf_003 zf_004 zf_005 zf_006 zf_007 zf_008 zf_017 zf_018
zf_019 zf_021 zf_022 zf_023 zf_024 zf_026 zf_027 zf_028 zf_032 zf_036
zf_038 zf_039 zf_040 zf_042 zf_043 zf_044 zf_046 zf_047 zf_048 zf_049
zf_051 zf_059 zf_060 zf_067 zf_070 zf_071 zf_072 zf_073 zf_074 zf_075
zf_076 zf_077 zf_078 zf_079 zf_083 zf_084 zf_085 zf_086 zf_087 zf_088
zf_090 zf_092 zf_093 zf_094 zf_099
""".split()

MALE_VOICES = """
zm_009 zm_010 zm_011 zm_012 zm_013 zm_014 zm_015 zm_016 zm_020 zm_025
zm_029 zm_030 zm_031 zm_033 zm_034 zm_035 zm_037 zm_041 zm_045 zm_050
zm_052 zm_053 zm_054 zm_055 zm_056 zm_057 zm_058 zm_061 zm_062 zm_063
zm_064 zm_065 zm_066 zm_068 zm_069 zm_080 zm_081 zm_082 zm_089 zm_091
zm_095 zm_096 zm_097 zm_098 zm_100
""".split()

CHINESE_VOICES = frozenset(FEMALE_VOICES + MALE_VOICES)


def split_text(text: str, max_chars: int) -> list[str]:
    cleaned = re.sub(r"[ \t]+", " ", text.replace("\r", "\n"))
    cleaned = re.sub(r"\n{2,}", "\n", cleaned).strip()
    if not cleaned:
        return []

    sentences = [part.strip() for part in re.findall(r"[^。！？!?；;\n]+[。！？!?；;]?", cleaned)]
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if len(sentence) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(sentence[i : i + max_chars] for i in range(0, len(sentence), max_chars))
        elif current and len(current) + len(sentence) > max_chars:
            chunks.append(current)
            current = sentence
        else:
            current += sentence
    if current:
        chunks.append(current)
    return chunks


def choose_device(requested: str) -> str:
    import torch

    if requested == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if requested == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is not available")
    return requested


def synthesize(args: argparse.Namespace) -> dict[str, object]:
    import numpy as np
    import soundfile as sf
    import torch
    from kokoro import KModel, KPipeline

    if args.voice not in CHINESE_VOICES:
        raise ValueError(f"Unsupported Chinese voice: {args.voice}. Use --list-voices.")
    if not 0.75 <= args.speed <= 1.25:
        raise ValueError("--speed must be between 0.75 and 1.25")
    if not 0 <= args.pause_ms <= 2_000:
        raise ValueError("--pause-ms must be between 0 and 2000")

    text = args.text
    if args.text_file:
        text = args.text_file.read_text(encoding="utf-8")
    chunks = split_text(text or "", args.max_chars)
    if not chunks:
        raise ValueError("Narration text is empty")

    device = choose_device(args.device)
    torch.manual_seed(0)
    started = time.monotonic()

    model = KModel(repo_id=args.model_id).to(device).eval()
    en_pipeline = KPipeline(lang_code="a", repo_id=args.model_id, model=False)

    def english_phonemes(value: str) -> str:
        result = next(en_pipeline(value))
        return result.phonemes

    pipeline = KPipeline(
        lang_code="z",
        repo_id=args.model_id,
        model=model,
        en_callable=english_phonemes,
    )

    pause = np.zeros(round(SAMPLE_RATE * args.pause_ms / 1000), dtype=np.float32)
    pieces: list[np.ndarray] = []
    segment_records: list[dict[str, object]] = []
    cursor_samples = 0

    for chunk_index, chunk in enumerate(chunks):
        results = list(pipeline(chunk, voice=args.voice, speed=args.speed))
        if not results:
            raise RuntimeError(f"Kokoro returned no audio for segment {chunk_index + 1}")
        for result in results:
            if result.audio is None:
                raise RuntimeError(f"Kokoro returned empty audio for segment {chunk_index + 1}")
            audio = result.audio.detach().cpu().numpy().astype(np.float32).reshape(-1)
            if audio.size == 0 or not np.isfinite(audio).all():
                raise RuntimeError(f"Invalid audio for segment {chunk_index + 1}")
            start = cursor_samples / SAMPLE_RATE
            pieces.append(audio)
            cursor_samples += audio.size
            end = cursor_samples / SAMPLE_RATE
            segment_records.append(
                {
                    "text": result.graphemes or chunk,
                    "start_seconds": round(start, 3),
                    "end_seconds": round(end, 3),
                }
            )
            if pause.size:
                pieces.append(pause)
                cursor_samples += pause.size

    if pause.size and pieces:
        pieces.pop()
        cursor_samples -= pause.size
    narration = np.concatenate(pieces)
    peak = float(np.max(np.abs(narration)))
    if peak <= 1e-5:
        raise RuntimeError("Generated narration is silent")
    if peak > 0.98:
        narration = narration * (0.98 / peak)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    sf.write(args.output, narration, SAMPLE_RATE, subtype="PCM_16")
    duration = narration.size / SAMPLE_RATE
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "provider": "kokoro-tts-zh",
        "model": args.model_id,
        "voice": args.voice,
        "speed": args.speed,
        "device": device,
        "sample_rate": SAMPLE_RATE,
        "channels": 1,
        "duration_seconds": round(duration, 3),
        "generation_seconds": round(time.monotonic() - started, 3),
        "pause_ms": args.pause_ms,
        "segments": segment_records,
    }
    manifest_path = args.manifest or args.output.with_suffix(".json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--text")
    source.add_argument("--text-file", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--voice", default=os.environ.get("KOKORO_VOICE", DEFAULT_VOICE))
    parser.add_argument("--speed", type=float, default=float(os.environ.get("KOKORO_SPEED", str(DEFAULT_SPEED))))
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default=os.environ.get("KOKORO_DEVICE", "auto"))
    parser.add_argument("--pause-ms", type=int, default=int(os.environ.get("KOKORO_PAUSE_MS", "180")))
    parser.add_argument("--max-chars", type=int, default=110)
    parser.add_argument("--model-id", default=os.environ.get("KOKORO_MODEL_ID", MODEL_ID))
    parser.add_argument("--list-voices", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.list_voices:
        print("Female:", " ".join(FEMALE_VOICES))
        print("Male:", " ".join(MALE_VOICES))
        return 0
    if not (args.text or args.text_file) or not args.output:
        print("ERROR: provide --text or --text-file and --output", file=sys.stderr)
        return 2
    try:
        manifest = synthesize(args)
    except Exception as exc:
        print(f"ERROR: Kokoro narration failed: {exc}", file=sys.stderr)
        return 1
    print(f"KOKORO_WAV={args.output.resolve()}")
    print(f"KOKORO_MANIFEST={(args.manifest or args.output.with_suffix('.json')).resolve()}")
    print(f"KOKORO_DURATION={manifest['duration_seconds']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
