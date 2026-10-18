---
name: freedom-video-skill
description: Create videos with interchangeable video-model APIs, mandatory Manim rendering, Kokoro Chinese narration, subtitles, provider switching, cost safeguards, bounded retries, and usage accounting. Use across Codex, Claude, Gemini, OpenClaw, Hermes, DeepSeek, Kimi, WorkBuddy, or normal Python scripts.
---

# Freedom Video Generation Studio

Build reproducible videos from a topic, script, prompt, or Python example. Manim rendering is mandatory for deterministic scenes and code or diagram animation; a configured cloud video model can add or generate other footage. Keep the workflow portable across Codex, Claude, Gemini, OpenClaw, Hermes, DeepSeek, Kimi, WorkBuddy, or a normal Python script.

## Separate The Two Provider Layers

- Use an **agent provider** only to write the lesson plan, narration, subtitles, prompts, and Manim/Python source. OpenAI-compatible chat endpoints may be used for providers such as DeepSeek, Kimi, or Hermes.
- Use a **video provider** only to generate or enhance video clips. Never send a video job to a chat-completions endpoint.
- Treat Agnes Video 2.5 Flash as one optional default, not a hard dependency.
- Read [references/provider-config.md](references/provider-config.md) before configuring or calling any provider.

## Required Workflow

1. Create an output project directory. Keep source, audio, subtitles, renders, and logs inside it.
2. Before writing or rendering the lesson, run:

   ```bash
   python3 scripts/ensure_manim.py --project-root <OUTPUT_PROJECT>
   ```

   This step is mandatory. It finds or installs Manim in `<OUTPUT_PROJECT>/.venv-manim`, verifies the version, and performs a real smoke render. Stop if it fails. Use the Manim executable path printed by the script for later renders.
3. When narration is required, run this mandatory setup before generating it:

   ```bash
   python3 scripts/ensure_kokoro.py --project-root <OUTPUT_PROJECT>
   ```

   It installs the pinned Kokoro Chinese stack in `<OUTPUT_PROJECT>/.venv-kokoro`, preserves the requested `kokoro-tts-zh` source revision under `.vendor`, downloads the selected model/voice on first use, and synthesizes a real smoke-test WAV. Stop if any step fails. Read [references/audio-config.md](references/audio-config.md) for voices and narration commands.
4. Produce a timed lesson plan. For each scene specify narration, on-screen code, animation, subtitle text, and duration. Use Manim for code execution concepts, state changes, pointers, traces, diagrams, and deterministic educational visuals.
5. Generate the complete narration before locking scene timing. Use `scripts/kokoro_narrate.py`, default to the warm teaching voice `zf_032` at speed `0.96`, keep one voice and a steady moderate speed within a lesson, and time visuals/subtitles to the measured WAV and its manifest.
6. Render a Manim draft and verify that its measured duration, frame size, text bounds, code highlighting, and transitions match the narration plan.
7. Only call a cloud video provider when it materially improves the lesson. Run the safety preflight below before every billable job.
8. Assemble the final video, then verify audio, subtitle timing, code readability, duration, and playable output.

## Narration Source Policy

- For every narrated video, use a Chinese voice supplied by the integrated `kokoro-tts-zh` model family.
- Never use macOS `say`, Windows SAPI, browser speech synthesis, or another operating-system voice as an automatic fallback.
- If Kokoro installation, model download, voice loading, or synthesis fails, stop and report the failure. Do not silently substitute a mechanical voice.
- Kokoro provides preset voices; it does not clone an arbitrary uploaded speaker. The linked repository's cloning path depends on a separate StableTTS submodule and model weights that are not self-contained or verified by this Skill. For a cloning request, require a separately configured and validated cloning backend plus confirmation that the user has permission to use the voice.

## Mandatory Billing Preflight

Before every cloud video request:

1. Query the provider's current price endpoint or current official pricing source.
2. Query account quota/credits through the configured quota endpoint.
3. Compute the maximum expected cost using requested duration, resolution, model, and provider pricing.
4. Compare it with `VIDEO_MAX_COST_PER_TASK` and available credits.
5. Record the preflight result in `<OUTPUT_PROJECT>/usage/video-usage.jsonl`.

Do not submit the job if price or quota is unknown, the endpoint cannot be verified, credits are insufficient, or the maximum cost would be exceeded. A provider advertising a free tier does not prove that the current request is free.

## Retry And Polling Rules

- Never retry indefinitely.
- Use `VIDEO_MAX_POLLS` and `VIDEO_POLL_INTERVAL_SECONDS` for asynchronous jobs.
- Retry transient network or HTTP 429/5xx failures at most `VIDEO_MAX_RETRIES` times with capped exponential backoff.
- For queue-full, capacity-full, insufficient-credit, authentication, validation, or price-policy errors, stop immediately unless the provider explicitly supplies a short `Retry-After` and the configured retry budget permits one retry.
- Never create a replacement job merely because status polling failed; first retrieve the original job by ID.

## Usage Ledger

Append one JSON object per preflight and provider call to `<OUTPUT_PROJECT>/usage/video-usage.jsonl`. Never store API keys or authorization headers. Include:

```json
{"timestamp":"ISO-8601","provider":"name","model":"id","job_id":"id-or-null","requested_seconds":10,"actual_seconds":10,"call_count":1,"status":"succeeded","price_source":"endpoint-or-url","estimated_cost":0,"actual_cost":0,"currency":"USD","cost_known":true,"error":null}
```

If the provider does not return actual cost, set `actual_cost` to `null` and `cost_known` to `false`; do not silently record zero. Summarize total calls, generated duration, known cost, and unknown-cost calls at the end.

## Output Contract

Deliver the final video plus editable Manim source, Kokoro narration WAV and manifest, subtitle files, provider-safe configuration template, render command, and usage ledger. State the Kokoro voice/model/speed used, and state clearly when no cloud video API was called or when cost could not be verified.

Do not expose secrets in source, logs, prompts, shell history, screenshots, or committed `.env` files. Use environment variables and provide only `.env.example` templates.
