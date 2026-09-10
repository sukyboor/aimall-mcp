# AIMALL CLI

> This folder is the canonical home of the **AIMALL CLI skill**. The repo was merged:
> the old `sukyboor/aimall-cli-skill` now redirects here. Maintain everything in
> [`sukyboor/aimall-mcp`](https://github.com/sukyboor/aimall-mcp).

The **`aimall` CLI** lets a human (or an agent driving a shell) call AIMALL's AI
API marketplace from the command line — chat, image, search, TTS, and more —
without opening the website. It is the human-facing counterpart to the MCP server
in the parent repo: agents use **MCP**, people use the **CLI**.

## Install

Download the prebuilt binary (no build step):

```bash
# macOS Apple Silicon
curl -O https://souyi.net.cn/cli/aimall-darwin-arm64 && chmod +x aimall-darwin-arm64 && sudo mv aimall-darwin-arm64 /usr/local/bin/aimall
# macOS Intel
curl -O https://souyi.net.cn/cli/aimall-darwin-amd64  && chmod +x aimall-darwin-amd64  && sudo mv aimall-darwin-amd64 /usr/local/bin/aimall
# Linux x86_64
curl -O https://souyi.net.cn/cli/aimall-linux-amd64   && chmod +x aimall-linux-amd64   && sudo mv aimall-linux-amd64 /usr/local/bin/aimall
# Windows
Invoke-WebRequest -Uri "https://souyi.net.cn/cli/aimall-windows-amd64.exe" -OutFile "aimall.exe"
```

## Quick start

```bash
aimall config -k ak_xxxxxxxxxxxxxxxx     # or skip — see x402 below
aimall assets                            # list models & tools with prices
aimall chat "write a quicksort in Python"
aimall call minimax-m3 "write an HTTP server"
aimall balance
```

## x402 payment (wallet, no signup)

Call without an API key; the server returns a `402` quote (Base USDC amount +
recipient address). Send exactly that amount from your wallet, then resend the
request with the tx hash:

```bash
aimall chat "write a quicksort"                       # -> 402 quote
aimall chat --pay-tx 0xYOUR_TX_HASH "write a quicksort"   # -> result
```

Top-up works the same way (`aimall x402 topup --amount 10 --email you@x.com`).
AIMALL verifies on-chain via the public Base RPC — zero platform fee, zero gas
passed to you.

## Skill for agents

`SKILL.md` in this folder teaches an agent *how* to drive the CLI. Install it:

```text
安装 skill https://github.com/sukyboor/aimall-mcp/cli-skill
```

## Links

- Platform: <https://souyi.net.cn>
- MCP server (for agents): parent repo [`../`](../)
- Full docs: <https://souyi.net.cn/llms-full.txt>
