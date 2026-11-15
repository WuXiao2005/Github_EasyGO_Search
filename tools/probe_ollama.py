import json
import sys
import urllib.request

BASE = "http://127.0.0.1:11434"
model = sys.argv[1] if len(sys.argv) > 1 else "qwen3:4b"

# 1) 先看模型信息：模板、参数
try:
    req = urllib.request.Request(BASE + "/api/show",
                                 data=json.dumps({"model": model}).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        info = json.loads(r.read().decode())
    print("== show ==")
    print("details:", json.dumps(info.get("details"), ensure_ascii=False)[:300])
    params = info.get("parameters") or ""
    print("params:", str(params)[:300])
    print("template head:", (info.get("template") or "")[:200].replace("\n", "\\n"))
except Exception as e:
    print("show failed:", e)
    sys.exit(1)

# 2) 跑一次最简单的 JSON 输出
body = {
    "model": model,
    "messages": [{"role": "user", "content": "用中文一句话说明 Git 是什么。以 JSON 输出：{\"说明\": \"...\"}"}],
    "stream": False,
    "format": {"type": "object", "properties": {"说明": {"type": "string"}}, "required": ["说明"]},
    "options": {"temperature": 0.2, "num_predict": 200},
}
req = urllib.request.Request(BASE + "/api/chat",
                             data=json.dumps(body, ensure_ascii=False).encode(),
                             headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=120) as r:
    raw = json.loads(r.read().decode())
print("== chat ==")
print("keys:", list(raw.keys()))
print("done_reason:", raw.get("done_reason"))
print("eval_count:", raw.get("eval_count"))
msg = raw.get("message") or {}
print("content:", repr(msg.get("content"))[:500])
print("thinking:", repr(msg.get("thinking"))[:500])
print("error:", raw.get("error"))
