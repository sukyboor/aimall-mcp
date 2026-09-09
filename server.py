#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜蚁智选 (AIMALL) 官方 MCP Server —— 零依赖，纯标准库实现。

让任何支持 MCP 的 Agent（Claude Desktop / Cursor / Dify / Coze / LangChain）
一键接入搜蚁智选的大模型与工具市场，按量付费。

环境变量:
  AIMALL_API_KEY   必填（ai_request / ai_estimate 需要）。Agent 的 X-API-Key，
                   在 https://souyi.net.cn 注册后「我的 Agent」页面创建获取。
  AIMALL_BASE_URL  可选，默认 https://souyi.net.cn

运行:
  python3 server.py
"""
import asyncio
import json
import os
import sys
import urllib.error
import urllib.request

BASE_URL = os.environ.get("AIMALL_BASE_URL", "https://souyi.net.cn").rstrip("/")
API_KEY = os.environ.get("AIMALL_API_KEY", "")

# Protocol versions we understand, newest first. On `initialize` we echo back
# the client's version when supported, else our newest (MCP version negotiation).
SUPPORTED_VERSIONS = ["2025-06-18", "2025-03-26", "2024-11-05"]
LATEST_VERSION = SUPPORTED_VERSIONS[0]
SERVER_VERSION = "1.1.0"


# ----------------------------- 底层 HTTP -----------------------------
def _http(method, path, body=None, api_key=None, token=None):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    # 带浏览器 UA：否则 Cloudflare 会把 urllib 默认 UA 当 bot 拦截（生产域名 souyi.net.cn 经 CF 代理）
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
    }
    if api_key:
        headers["X-API-Key"] = api_key
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode("utf-8")
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "ignore")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"detail": raw}
    except Exception as e:  # 网络错误等
        return 0, {"detail": str(e)}


def _short(obj, limit=6000):
    s = obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False, indent=2)
    if len(s) <= limit:
        return s
    return s[:limit] + f"\n... (truncated, total {len(s)} chars)"


# ----------------------------- 业务工具 -----------------------------
def list_assets(api_type=""):
    status, data = _http("GET", "/api/v1/assets")
    if status != 200:
        return f"[error] GET /assets -> {status}: {_short(data)}"
    items = data.get("data", []) if isinstance(data, dict) else data
    if api_type:
        items = [a for a in items if a.get("api_type") == api_type]
    if not items:
        return "（当前市场无可用资产）"
    lines = []
    for a in items:
        if a.get("api_type") == "model":
            price = f"in ${a.get('price_input')}/out ${a.get('price_output')} 每百万 token"
        else:
            price = f"${a.get('price_per_call')} 每次调用"
        lines.append(
            f"- {a.get('asset_id')} | {a.get('name')} | {a.get('api_type')} | {price} | status={a.get('status')}"
        )
    return "搜蚁智选可用资产：\n" + "\n".join(lines)


def ai_estimate(asset_id, prompt, max_tokens=512):
    # Deliberately usable WITHOUT a key: "price it before you sign up" is the
    # cheapest way for an agent to evaluate AIMALL. The REST handler prices
    # anonymous callers against a zero balance.
    status, data = _http(
        "POST", "/api/v1/ai/estimate",
        {"asset_id": asset_id, "prompt": prompt, "max_tokens": max_tokens},
        api_key=API_KEY,
    )
    if status != 200:
        return f"[error] estimate -> {status}: {_short(data)}"
    return _short(data)


def ai_request(asset_id, prompt="", model="", max_tokens=0, call_data=None):
    if not API_KEY:
        return "[error] 未设置 AIMALL_API_KEY。请先在 https://souyi.net.cn 注册并创建 Agent 获取 ak_...，再设为环境变量后重启本 Server。"
    body = {"asset_id": asset_id}
    if prompt:
        body["prompt"] = prompt
    if model:
        body["model"] = model
    if max_tokens:
        body["max_tokens"] = max_tokens
    if call_data:
        body["call_data"] = call_data
    status, data = _http("POST", "/api/v1/ai/request", body, api_key=API_KEY)
    if status != 200:
        return f"[error] request -> {status}: {_short(data)}"
    # 真实产出在 data.result（模型类）或 data.content（工具类），优先提取给 Agent
    d = data.get("data", data) if isinstance(data, dict) else data
    out = ""
    if isinstance(d, dict):
        out = d.get("result") or d.get("content") or d.get("result_content") or ""
    if out:
        meta = []
        for k in ("order_id", "cost_usd", "balance_remaining", "asset_name", "provider", "latency_ms"):
            if isinstance(d, dict) and k in d:
                meta.append(f"{k}: {d[k]}")
        return ("结果:\n" + str(out) + ("\n\n" + "\n".join(meta) if meta else ""))
    return _short(data)


def bootstrap_account(email, password, username):
    """注册并创建 Agent，返回可用的 API Key（会创建真实账号）。"""
    s1, d1 = _http(
        "POST", "/api/v1/auth/register",
        {"email": email, "password": password, "username": username},
    )
    if s1 != 200:
        return f"[error] register -> {s1}: {_short(d1)}"
    token = d1["data"]["token"]
    s2, d2 = _http("POST", "/api/v1/agents", {"name": f"{username}-agent"}, token=token)
    if s2 != 200:
        return f"[error] create agent -> {s2}: {_short(d2)}"
    ak = d2["data"]["api_key"]
    bal = d1["data"].get("balance_usd")
    return (
        f"账号已创建。\nAPI Key: {ak}\n"
        f"当前余额: ${bal}（注册赠送，可直接调用）\n\n"
        f"请将该 key 设为环境变量 AIMALL_API_KEY，并重启本 MCP Server 后，"
        f"即可使用 list_assets / ai_request / ai_estimate。"
    )


def get_onboarding():
    return (
        "搜蚁智选 (AIMALL) 接入指引：\n"
        "1. 注册：https://souyi.net.cn （注册即送 $1，邮箱验证再送 $4）\n"
        "2. 创建 Agent 获取 API Key（ak_...）：平台「我的 Agent」页面，"
        "   或直接调用本 Server 的 bootstrap_account 工具自助创建\n"
        "3. 把 key 设为环境变量 AIMALL_API_KEY，重启本 MCP Server\n"
        "4. list_assets 浏览工具 -> ai_estimate 预估费用 -> ai_request 调用\n\n"
        "机器可读文档：\n"
        "  - https://souyi.net.cn/llms.txt\n"
        "  - https://souyi.net.cn/openapi.json\n"
        "  - https://souyi.net.cn/.well-known/agent.json"
    )


# ----------------------------- MCP 协议层 -----------------------------
TOOLS = [
    {
        "name": "list_assets",
        "description": "列出搜蚁智选市场中的可用 AI 资产（大模型 / 工具），含 asset_id、类型与单价。先用它找到要调用的 asset_id。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "api_type": {
                    "type": "string",
                    "enum": ["", "model", "tool", "mcp", "data", "custom"],
                    "description": "按类型过滤，留空返回全部",
                }
            },
            "required": [],
        },
    },
    {
        "name": "ai_estimate",
        "description": "在不扣费的情况下预估一次 AI 调用的费用（USD）。调用前用它做预算闸门。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "asset_id": {"type": "string", "description": "从 list_assets 获得的资产 ID"},
                "prompt": {"type": "string", "description": "model 类必填的提示词"},
                "max_tokens": {"type": "integer", "description": "最大输出 token，默认 512", "default": 512},
            },
            "required": ["asset_id", "prompt"],
        },
    },
    {
        "name": "ai_request",
        "description": "调用搜蚁智选的某个 AI 资产（大模型对话或工具），按量计费并返回结果、订单号与余额。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "asset_id": {"type": "string", "description": "从 list_assets 获得的资产 ID"},
                "prompt": {"type": "string", "description": "model 类必填的提示词"},
                "model": {"type": "string", "description": "model 类可选，缺省用资产默认模型"},
                "max_tokens": {"type": "integer", "description": "model 类可选，最大输出 token"},
                "call_data": {"type": "object", "description": "tool 类必填，传给上游工具的参数对象"},
            },
            "required": ["asset_id"],
        },
    },
    {
        "name": "bootstrap_account",
        "description": "（可选）自助注册账号并创建 Agent，返回可用的 API Key。会创建真实账号，仅首次接入时使用。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "注册邮箱"},
                "password": {"type": "string", "description": "密码（>=6 位）"},
                "username": {"type": "string", "description": "用户名"},
            },
            "required": ["email", "password", "username"],
        },
    },
    {
        "name": "get_onboarding",
        "description": "返回搜蚁智选的接入指引与机器可读文档链接。",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def dispatch_sync(name, args):
    if name == "list_assets":
        return list_assets(args.get("api_type", ""))
    if name == "ai_estimate":
        return ai_estimate(args.get("asset_id"), args.get("prompt", ""), int(args.get("max_tokens", 512)))
    if name == "ai_request":
        return ai_request(
            args["asset_id"], args.get("prompt", ""), args.get("model", ""),
            int(args.get("max_tokens", 0) or 0), args.get("call_data"),
        )
    if name == "bootstrap_account":
        return bootstrap_account(args["email"], args["password"], args["username"])
    if name == "get_onboarding":
        return get_onboarding()
    return f"[error] unknown tool: {name}"


async def main():
    queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    async def pump():
        while True:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:
                await queue.put(None)
                return
            await queue.put(line)

    async def handle():
        out = sys.stdout

        def send(obj):
            out.write(json.dumps(obj, ensure_ascii=False) + "\n")
            out.flush()

        while True:
            item = await queue.get()
            if item is None:
                return
            try:
                msg = json.loads(item)
            except Exception:
                continue
            mid = msg.get("id")
            method = msg.get("method")
            if method == "initialize":
                requested = (msg.get("params") or {}).get("protocolVersion", "")
                version = requested if requested in SUPPORTED_VERSIONS else LATEST_VERSION
                send({
                    "jsonrpc": "2.0", "id": mid,
                    "result": {
                        "protocolVersion": version,
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "aimall-mcp", "version": SERVER_VERSION},
                    },
                })
            elif method == "notifications/initialized":
                continue
            elif method == "tools/list":
                send({"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}})
            elif method == "tools/call":
                params = msg.get("params", {})
                name = params.get("name")
                args = params.get("arguments", {})
                try:
                    res = await asyncio.to_thread(dispatch_sync, name, args)
                    send({
                        "jsonrpc": "2.0", "id": mid,
                        "result": {"content": [{"type": "text", "text": str(res)}]},
                    })
                except Exception as e:
                    send({
                        "jsonrpc": "2.0", "id": mid,
                        "error": {"code": -32000, "message": str(e)},
                    })
            else:
                if mid is not None:
                    send({
                        "jsonrpc": "2.0", "id": mid,
                        "error": {"code": -32601, "message": "method not found: " + str(method)},
                    })

    await asyncio.gather(pump(), handle())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
