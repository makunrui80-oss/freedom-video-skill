# Kokoro Chinese Narration

Use this reference whenever a video has spoken narration.

## Source And Capability Boundary

- Requested integration: `https://github.com/ardorleo/kokoro-tts-zh`
- Verified repository revision: `261b9f78ae9861da972ad9293d6f89e1a4dd8a72`
- Runtime engine revision: `https://github.com/hexgrad/kokoro` at `dfb907a02bba8152ca444717ca5d78747ccb4bec` (version 0.9.4)
- Chinese model: `hexgrad/Kokoro-82M-v1.1-zh`
- Output: 24 kHz mono WAV

The requested repository is MIT licensed. The runtime engine and downloaded model have their own licenses; check current upstream terms before redistributing code, weights, or generated voice assets.

Kokoro supplies preset speaker voices. It is not an arbitrary reference-audio voice-cloning system. The repository mentions StableTTS cloning, but that path is a separate submodule and requires external model/vocoder weights. Do not present it as installed or verified.

## Mandatory Setup

Run once per output project and again when validation is needed:

```bash
python3 scripts/ensure_kokoro.py --project-root <OUTPUT_PROJECT>
```

The first run installs a project-local environment and downloads model assets. The script prints `KOKORO_PYTHON=...`; use that interpreter for narration. A smoke-test WAV must pass. `--skip-smoke-test` is only for static CI/packaging checks and is not allowed in a video-generation workflow.

## Narration Command

```bash
<KOKORO_PYTHON> scripts/kokoro_narrate.py \
  --text-file <NARRATION.txt> \
  --output <OUTPUT_PROJECT>/audio/narration.wav \
  --manifest <OUTPUT_PROJECT>/audio/narration.json \
  --voice zf_032 \
  --speed 0.96
```

The script splits long Chinese copy at punctuation, adds consistent short pauses, emits a 24 kHz mono PCM WAV, and records segment start/end times. Use those measured times to create subtitles and scene timings. Prefer changing scene duration over post-stretching speech.

## Voice Selection

Female voices:

`zf_001`, `zf_002`, `zf_003`, `zf_004`, `zf_005`, `zf_006`, `zf_007`, `zf_008`, `zf_017`, `zf_018`, `zf_019`, `zf_021`, `zf_022`, `zf_023`, `zf_024`, `zf_026`, `zf_027`, `zf_028`, `zf_032`, `zf_036`, `zf_038`, `zf_039`, `zf_040`, `zf_042`, `zf_043`, `zf_044`, `zf_046`, `zf_047`, `zf_048`, `zf_049`, `zf_051`, `zf_059`, `zf_060`, `zf_067`, `zf_070`, `zf_071`, `zf_072`, `zf_073`, `zf_074`, `zf_075`, `zf_076`, `zf_077`, `zf_078`, `zf_079`, `zf_083`, `zf_084`, `zf_085`, `zf_086`, `zf_087`, `zf_088`, `zf_090`, `zf_092`, `zf_093`, `zf_094`, `zf_099`

Male voices:

`zm_009`, `zm_010`, `zm_011`, `zm_012`, `zm_013`, `zm_014`, `zm_015`, `zm_016`, `zm_020`, `zm_025`, `zm_029`, `zm_030`, `zm_031`, `zm_033`, `zm_034`, `zm_035`, `zm_037`, `zm_041`, `zm_045`, `zm_050`, `zm_052`, `zm_053`, `zm_054`, `zm_055`, `zm_056`, `zm_057`, `zm_058`, `zm_061`, `zm_062`, `zm_063`, `zm_064`, `zm_065`, `zm_066`, `zm_068`, `zm_069`, `zm_080`, `zm_081`, `zm_082`, `zm_089`, `zm_091`, `zm_095`, `zm_096`, `zm_097`, `zm_098`, `zm_100`

Do not assume every voice is cached. The first use of a voice may download its voice pack. Test candidate voices with a short lesson sentence before rendering the full narration.

## Pacing And Quality

- Default to the warmer, steadier `zf_032` voice at `--speed 0.96` for teaching narration. Use `0.9` to `1.05` when the user requests a different pace.
- Keep the same voice and speed throughout one video unless different speakers are intentional.
- Rewrite long, punctuation-free copy before synthesis. Do not accelerate a crowded script until it becomes difficult to follow.
- Verify non-silence, duration, clipping, sample rate, and channel count. Keep the source WAV even when the final video uses AAC.
- System voices are prohibited as a fallback. A Kokoro failure is a blocking error.

## Optional Environment Defaults

```dotenv
AUDIO_PROVIDER=kokoro-tts-zh
KOKORO_MODEL_ID=hexgrad/Kokoro-82M-v1.1-zh
KOKORO_VOICE=zf_032
KOKORO_SPEED=0.96
KOKORO_DEVICE=auto
KOKORO_PAUSE_MS=180
```
