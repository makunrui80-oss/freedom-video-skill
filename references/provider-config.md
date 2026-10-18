# Provider Configuration

Keep agent/script generation separate from video generation. All secrets must come from environment variables or a secret manager.

## Agent Providers

The workflow is agent-neutral. Codex, Claude, Gemini, OpenClaw, Hermes, DeepSeek, Kimi, WorkBuddy, or a local script can follow `SKILL.md`. An agent provider may generate text and Manim source through its native SDK or an OpenAI-compatible chat endpoint. Agent configuration must not be reused as video configuration unless the provider explicitly documents a video API.

Suggested optional agent variables:

```dotenv
AGENT_PROVIDER=deepseek
AGENT_BASE_URL=https://api.example/v1
AGENT_MODEL=model-id
AGENT_API_KEY=
```

## Video Providers

Supported protocol adapters:

- `agnes`: Agnes Video API adapter. Keep URLs and response paths configurable because deployments may differ.
- `openai_videos`: APIs that implement the OpenAI Videos request and retrieval contract.
- `generic_json`: arbitrary JSON-over-HTTP create and retrieve endpoints configured through field/path mappings.

Use this portable template in the output project's uncommitted `.env` file:

```dotenv
VIDEO_PROVIDER=agnes
VIDEO_PROTOCOL=generic_json
VIDEO_MODEL=agnes-video-2.5-flash
VIDEO_API_KEY=
VIDEO_CREATE_URL=https://provider.example/v1/generations
VIDEO_RETRIEVE_URL_TEMPLATE=https://provider.example/v1/tasks/{video_id}
VIDEO_AUTH_HEADER=Authorization
VIDEO_AUTH_SCHEME=Bearer
VIDEO_EXTRA_HEADERS_JSON={}
VIDEO_FIELD_MAP_JSON={"prompt":"text","seconds":"duration","aspect_ratio":"ratio","model":"model_name"}
VIDEO_STATIC_FIELDS_JSON={"resolution":"720p"}
VIDEO_ID_PATH=data.task_id
VIDEO_STATUS_PATH=data.status
VIDEO_RESULT_URL_PATH=data.output.video_url
VIDEO_ERROR_PATH=data.error.message
VIDEO_COST_PATH=data.billing.actual_cost
VIDEO_PRICE_ENDPOINT=
VIDEO_QUOTA_ENDPOINT=
VIDEO_PRICE_PER_SECOND=
VIDEO_ACCOUNT_CREDITS=
VIDEO_MAX_COST_PER_TASK=0
VIDEO_MAX_RETRIES=2
VIDEO_MAX_POLLS=180
VIDEO_POLL_INTERVAL_SECONDS=2
```

`VIDEO_MAX_COST_PER_TASK=0` means only verified zero-cost jobs are allowed. Do not interpret an empty price field as free.

## Generic JSON Mapping

`VIDEO_FIELD_MAP_JSON` maps the Skill's canonical request fields to provider request fields. `VIDEO_STATIC_FIELDS_JSON` adds provider-specific constants. Dotted response paths identify the job ID, status, output URL, error, and actual cost.

Canonical fields are `prompt`, `seconds`, `aspect_ratio`, `model`, `resolution`, `seed`, `negative_prompt`, and `reference_image`.

Normalize provider statuses into `queued`, `running`, `succeeded`, `failed`, or `cancelled`. Keep the original status in the usage ledger. If a provider needs signing, multipart upload, callbacks, or a non-JSON response, add a dedicated adapter instead of embedding provider-specific behavior into the core workflow.

## Price And Quota Verification

Preferred order:

1. Authenticated price and quota endpoints.
2. Provider SDK methods backed by documented endpoints.
3. A current official pricing page plus an authenticated account balance endpoint.

Static `VIDEO_PRICE_PER_SECOND` and `VIDEO_ACCOUNT_CREDITS` values are acceptable only when the user explicitly supplied them for a single run and their timestamp/source is recorded. Unknown price or quota blocks cloud generation.

## Switching Providers

To switch to a future free provider, change only the video variables and mappings. Test configuration with a non-billable validation endpoint when one exists. Then run one minimal-duration job after the billing preflight. Never assume API compatibility from similar model names.

## Secret Hygiene

- Put `.env` in `.gitignore`.
- Commit `.env.example` with blank secret values.
- Redact API keys and authorization headers from errors and ledgers.
- Rotate any key pasted into a chat, issue, log, or public repository before publishing the project.
