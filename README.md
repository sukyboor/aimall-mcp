# aimall-mcp

Official MCP server for **[AIMALL / 搜蚁智选](https://souyi.net.cn)** — a pay-per-use API marketplace built for **autonomous AI agents**.

An agent can discover the catalogue, price a call, register itself, get an API key, call hosted models and tools, and pay from its balance — **without a human in the loop**.

```
Agent → list_assets → ai_estimate → bootstrap_account → ai_request → (billed, order_id + balance returned)
```

---

## Two ways to connect

### 1. Remote (recommended) — no install

Streamable HTTP endpoint:

```json
{
  "mcpServers": {
    "aimall": {
      "url": "https://souyi.net.cn/api/v1/mcp",
      "headers": { "X-API-Key": "ak_..." }
    }
  }
}
```

Claude Desktop / Cursor / Claude Code / any MCP client: point it at `https://souyi.net.cn/api/v1/mcp` with an `X-API-Key` header.

### 2. Local stdio — zero dependencies

```bash
curl -O https://souyi.net.cn/mcp/server.py   # or clone this repo
python3 server.py                            # Python 3.9+, stdlib only
```

```json
{
  "mcpServers": {
    "aimall": {
      "command": "python3",
      "args": ["/absolute/path/to/server.py"],
      "env": { "AIMALL_API_KEY": "ak_...", "AIMALL_BASE_URL": "https://souyi.net.cn" }
    }
  }
}
```

---

## Tools

| Tool | Auth | What it does |
|---|---|---|
| `list_assets` | none | List available models/tools with `asset_id` and unit price |
| `ai_estimate` | none | Estimate a call's cost in USD **without charging** — a budget gate before you commit |
| `ai_request` | key | Call an asset; returns result, `order_id`, `cost_usd`, `balance_remaining`, `latency_ms` |
| `bootstrap_account` | none | Self-register and create an agent; returns a ready-to-use `ak_...` key |
| `get_onboarding` | none | Onboarding steps + links to machine-readable docs |

Only `ai_request` requires a key. `list_assets`, `ai_estimate` and `get_onboarding` are open so an agent can evaluate the marketplace before spending anything.

---

## Self-serve onboarding (the interesting part)

An agent with no account can bootstrap itself in one tool call:

```json
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"bootstrap_account","arguments":{"email":"agent@example.com","password":"secret123","username":"my-agent"}}}
```

Response:

```
账号已创建。
API Key: ak_xxxxxxxxxxxxxxxx
当前余额: $1.00（注册赠送，可直接调用）
```

No email confirmation, no dashboard, no human. Put that key in `X-API-Key` and start calling.

---

## Pricing & payment

- Registration grants **$1 free trial**; email verification adds **$4**.
- Billing is **per call** or **per token**, deducted from the agent's balance.
- `ai_estimate` is free — price it before you run it.
- Top-ups: **x402** (USDC on Base) for agent-autonomous payment, plus standard top-up.

---

## Machine-readable surfaces

Agents and crawlers should use these instead of the HTML site:

| File | Purpose |
|---|---|
| [`https://souyi.net.cn/llms.txt`](https://souyi.net.cn/llms.txt) | Overview for LLMs |
| [`https://souyi.net.cn/llms-full.txt`](https://souyi.net.cn/llms-full.txt) | Full catalogue, endpoints, pricing, curl examples |
| [`https://souyi.net.cn/openapi.json`](https://souyi.net.cn/openapi.json) | OpenAPI 3 spec |
| [`https://souyi.net.cn/.well-known/agent.json`](https://souyi.net.cn/.well-known/agent.json) | Agent card (protocols, auth, capabilities) |
| [`SKILL.md`](./SKILL.md) | Capability package — install so an agent *knows how* to use AIMALL |

### `SKILL.md`

`SKILL.md` is the highest-leverage file here. Dropping it into an agent's skills directory doesn't just tell the agent AIMALL exists — it teaches the actual call sequence and cost discipline.

```bash
curl -O https://souyi.net.cn/SKILL.md
```

---

## Quick check that it works

```bash
curl -s -X POST https://souyi.net.cn/api/v1/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_assets","arguments":{}}}'
```

Supports MCP protocol versions `2025-06-18`, `2025-03-26`, `2024-11-05` with negotiation.

---

## x402 payment (optional)

No wallet top-up needed: call with no API key → server returns a `402` quote →
pay exactly that Base USDC → resend with the tx hash. Zero platform fee.

---

## Links

- Platform: <https://souyi.net.cn>
- For agents: <https://souyi.net.cn/for-agents.html>
- Docs: <https://souyi.net.cn/llms-full.txt>

## License

MIT — see [LICENSE](./LICENSE).
