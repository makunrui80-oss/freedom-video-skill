# Freedom Video Skill

`freedom-video-skill` 是一个通用、可移植的视频生成 Skill。它把视频模型 API、旁白、字幕、Manim 动画和费用保护组合在一起，让你可以自由切换不同的视频模型，并在 Codex、Claude、Gemini、OpenClaw、Hermes、DeepSeek、Kimi、WorkBuddy 或普通 Python 脚本中使用。Python 教学视频只是其中一个典型应用。

## 能做什么

- 强制验证并使用 Manim，把代码步骤、流程图、数学概念和确定性场景制作成动画。
- 使用集成的 `kokoro-tts-zh` 生成中文旁白，默认音色是 `zf_032`，默认语速是 `0.96`。
- 生成旁白时间轴，并按时间轴制作字幕。
- 调用已配置的视频模型生成视频，也可以只使用本地 Manim 完成视频。
- 每次云调用前检查价格和账户额度，限制轮询和重试，并记录时长、调用次数和实际费用。
- 支持切换视频提供商，避免绑定某一个模型或平台。

## 兼容哪些模型和工具

Agent 层支持国内外大模型平台：Codex、Claude、Gemini、OpenClaw、Hermes、DeepSeek、Kimi、WorkBuddy，以及其他本地或云端脚本。Agent 可以使用原生 SDK 或 OpenAI 兼容聊天接口，因此不绑定 OpenAI。

视频层支持三类协议：Agnes Video API、OpenAI Videos 兼容接口、任意 JSON over HTTP 接口（通过字段路径映射配置）。模型名称相似不代表 API 兼容；其他平台应根据官方文档配置 URL、请求字段、状态字段、结果字段、价格接口和额度接口。

## 安装和使用

将仓库克隆到 Codex 的 Skill 目录：

```bash
git clone https://github.com/<你的用户名>/freedom-video-skill.git ~/.codex/skills/freedom-video-skill
```

然后用 `$freedom-video-skill` 调用：

```text
$freedom-video-skill 制作一个 30 秒的 Python while 循环原理动画，使用温和中文旁白。
```

也可以把仓库作为普通 Python 项目使用；核心脚本在 `scripts/`，详细约束在 `SKILL.md`。

## 接入 Agent API

实际项目中用 `.env` 或系统环境变量保存配置：

```dotenv
AGENT_PROVIDER=deepseek
AGENT_BASE_URL=https://api.deepseek.com/v1
AGENT_MODEL=deepseek-chat
AGENT_API_KEY=只在本机环境变量中设置
```

密钥只放在本机环境变量、密钥管理器或 CI Secret 中，不要写入 README、源码、日志或 GitHub。

## 接入视频模型 API

在项目的 `.env` 中配置通用 JSON 接口：

```dotenv
VIDEO_PROVIDER=my-provider
VIDEO_PROTOCOL=generic_json
VIDEO_MODEL=provider-video-model
VIDEO_API_KEY=只在本机设置
VIDEO_CREATE_URL=https://provider.example/v1/generations
VIDEO_RETRIEVE_URL_TEMPLATE=https://provider.example/v1/tasks/{video_id}
VIDEO_AUTH_HEADER=Authorization
VIDEO_AUTH_SCHEME=Bearer
VIDEO_FIELD_MAP_JSON={"prompt":"text","seconds":"duration","aspect_ratio":"ratio","model":"model_name"}
VIDEO_ID_PATH=data.task_id
VIDEO_STATUS_PATH=data.status
VIDEO_RESULT_URL_PATH=data.output.video_url
VIDEO_ERROR_PATH=data.error.message
VIDEO_COST_PATH=data.billing.actual_cost
VIDEO_PRICE_ENDPOINT=https://provider.example/v1/pricing
VIDEO_QUOTA_ENDPOINT=https://provider.example/v1/account/quota
VIDEO_MAX_COST_PER_TASK=0
```

接入时确认创建任务、查询任务、下载结果、价格和额度接口，再把字段映射到 `prompt`、`seconds`、`model` 等标准字段。无法确认价格或余额时，Skill 会阻止云视频请求。需要签名、文件上传或特殊响应格式的服务，应添加独立适配器。

## 接入外部免费视频模型

可以从模型官方文档寻找公开 API、免费额度或开发者试用计划，再按上一节配置。免费政策可能变化，因此必须提供可验证的价格来源和账户额度来源；`VIDEO_MAX_COST_PER_TASK=0` 只允许已验证为零费用的任务，空白价格不能当作免费。额度不足、价格接口不可用或状态异常时停止请求。

## 隐私和密钥安全

这个仓库不需要保存你的 IP 地址，也不应把 IP 写进日志、示例或提交记录。网络请求可能被 API 服务商在网络层记录，这是服务商的行为；Skill 不会主动收集或提交 IP。

发布前确认 `.env`、真实 API 密钥、Authorization 请求头、Cookie、个人文件路径、真实账户信息、私有日志、音频、视频、缓存、虚拟环境和本地模型目录没有加入 Git。只提交 `.env.example`，其中的密钥值保持为空或使用占位符。

任何曾经粘贴到聊天、Issue、截图或公开仓库的密钥，都应先撤销并重新生成。发布前可以检查：

```bash
git status --short
git grep -n -I -E 'sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|Bearer [A-Za-z0-9._-]+' -- . ':!README.md'
```

## 许可证

本 Skill 的代码和文档可使用 MIT License 发布。Kokoro 引擎、中文模型、Manim 及第三方视频服务各自有独立许可证和服务条款，发布或分发它们时请分别遵守上游条款。
