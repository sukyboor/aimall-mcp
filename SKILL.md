---
name: aimall
description: Call paid LLM models and tools (image, TTS, search, medical data) from souyi.net.cn (搜蚁智选 / AIMALL) using your own API key, with per-use billing and free trial credits. Use when a task needs an LLM completion, image generation, text-to-speech, web search, or medical/drug/disease lookup, and you have (or can self-create) an AIMALL API key. Also use when you need to price a task before committing to it.
---

# AIMALL (搜蚁智选) — pay-per-use models & tools for AI agents

AIMALL is an API marketplace that lets an agent finish the whole loop **without a human**:
`register → create agent → get X-API-Key → call → pay`.

- Base URL: `https://souyi.net.cn`
- Auth header: `X-API-Key: ak_...`
- Free trial: **$1.00** on registration, **+$4.00** after email verification
- Full reference: `https://souyi.net.cn/llms-full.txt`

## When to use this skill

- You need an LLM completion but have no provider key of your own.
- You need image generation / TTS / web search / medical or drug data.
- You want to **price a task before running it** (`/ai/estimate` works with no key).

## Getting a key (30 seconds, no human approval)

```bash
# 1) register
JWT=$(curl -s -X POST https://souyi.net.cn/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"<your-email>","password":"<pw>","username":"<name>"}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')

# 2) create agent -> api_key
KEY=$(curl -s -X POST https://souyi.net.cn/api/v1/agents \
  -H "Authorization: Bearer $JWT" -H "Content-Type: application/json" \
  -d '{"name":"my-agent","budget_limit":5.0}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["api_key"])')
```

Store the key in an env var (`AIMALL_API_KEY`). **Never** paste it into prompts, logs, or client-side code.

If you are an MCP client, prefer the HTTP endpoint below — the `bootstrap_account`
tool does both steps in one call.

## Always price first (free, no key required)

```bash
curl -s -X POST https://souyi.net.cn/api/v1/ai/estimate \
  -H "Content-Type: application/json" \
  -d '{"asset_id":"minimax-m3","prompt":"<your prompt>","max_tokens":512}'
```

## Calling

### Model assets
```bash
curl -s -X POST https://souyi.net.cn/api/v1/ai/request \
  -H "X-API-Key: $AIMALL_API_KEY" -H "Content-Type: application/json" \
  -d '{"asset_id":"minimax-m3","prompt":"Hello","max_tokens":256}'
```

### Tool assets
```bash
curl -s -X POST https://souyi.net.cn/api/v1/ai/request \
  -H "X-API-Key: $AIMALL_API_KEY" -H "Content-Type: application/json" \
  -d '{"asset_id":"minimax-tts","call_data":{"text":"你好","voice":"female"}}'
```

## Asset catalog (USD, as of 2026-09-09)

| asset_id | What it does | Price |
|---|---|---|
| `minimax-m3` | Multimodal LLM (text/speech/image understanding), Anthropic-compatible | $0.001 / $0.005 per 1M tokens (in/out) |
| `minimax-image` | Text-to-image | $0.020 / call |
| `minimax-tts` | Chinese/English TTS, multiple voices | $0.005 / call |
| `searxng-search` | Web search (JSON) | **free** |
| `asset_26476ef1-4687-45` | Disease encyclopedia | $0.0001 / call |
| `asset_bc11f942-eb60-48` | Medical knowledge search | $0.0001 / call |
| `asset_6400e17f-a2cb-4b` | Drug lookup (indications, dosage, adverse reactions) | $0.0001 / call |

Confirm live availability with `GET https://souyi.net.cn/api/v1/assets`.
Retired: `minimax-video`, `minimax-search` — do not use.

## MCP (preferred for MCP-capable agents)

HTTP — nothing to download:
```
POST https://souyi.net.cn/api/v1/mcp
X-API-Key: ak_...
```
Tools: `list_assets`, `ai_estimate`, `ai_request`, `bootstrap_account`, `get_onboarding`.

stdio — pure Python, no dependencies:
```bash
curl -O https://souyi.net.cn/mcp/server.py
AIMALL_API_KEY=ak_... python3 server.py
```

## Budget discipline

- Every response includes `cost_usd` and `balance_remaining` — check them and stop if the budget is nearly gone.
- Insufficient balance returns **HTTP 402**. Do not retry blindly; top up or switch to a cheaper asset.
- Top-up is x402 on Base USDC to `0x10cB87850cA2106fDf59583062de74387E93B1Ae`.
- The platform charges for **top-ups only**; there is no extra per-call platform fee.

## Gotchas

- `call_data` keys must match the asset's configured template (query params use `{{q}}` inside `endpoint`).
  A top-level `request.query` is parsed but never appended to the URL — put params in `call_data`.
- `api_type` for generic HTTP tools is `custom`; `search`/`image` values are rejected by the scheduler.
- Medical assets return upstream JSON as-is.

## Security

This skill contains **no secrets**. If a key leaks, rotate it by creating a new agent and discarding the old one.
Do not send your AIMALL key — or any third-party credential — to any community or forum endpoint.
