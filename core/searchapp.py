"""实时中文检索 GitHub：中文查询 -> 英文检索词 -> 结果中文速览 -> 按需流式汉化详解。"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import threading
import time
import urllib.request
from datetime import date, timedelta

from . import facts as factsmod
from . import gitpull
from . import i18n
from .github import GitHubClient, clean_text, extract_images, summarize_tree
from .localize import Localizer, validate, parse_json_loose
from .pipeline import signature
from .store import Store, today_str

EXPAND_SCHEMA = {
    "type": "object",
    "properties": {
        "keywords": {"type": "array", "items": {"type": "string"}},
        "intent": {"type": "string"},
    },
    "required": ["keywords", "intent"],
}

EXPAND_SYSTEM = """你是 GitHub 检索助手，负责把中文技术需求翻译成能在 GitHub 上精准命中的英文检索词。

关键规则：
1. **关键词只要 1-3 个，通常 2 个最好**。GitHub 搜索把多个词当 AND 处理，词越多结果越少越偏。
2. 必须用 GitHub 上真实高频的英文术语，**优先用业界通用缩写**，不要按中文词序直译。
   反例："local large model inference"（没人这么写）；正例："llm inference"。
3. 只输出英文，不要中文；技术名词保留原写法。
4. intent 用一句中文说明你的检索意图，方便用户判断翻得对不对。
5. 只输出 JSON。

参考映射（中文 -> 英文关键词）：
- 本地跑大模型 / 本地推理 -> llm inference
- 大模型微调 -> llm finetune
- 知识库问答 -> rag
- 语音转文字 -> speech to text
- 文字转语音 -> tts
- 股票回测 -> backtesting
- 视频自动剪辑 -> video editing
- 网页爬虫 -> web scraper
- 文档转换 -> document converter
- 量化交易 -> quantitative trading
- 图像生成 -> image generation
- 桌面客户端 -> desktop app
"""

# 流式输出用的分节格式（比增量解析 JSON 稳定得多）
SECTIONS = [
    "速览", "它是什么", "解决什么问题", "核心机制", "主要功能",
    "项目结构", "快速上手", "值得学的点", "适合谁", "术语表",
]

STREAM_SYSTEM = """你是一名给中国程序员讲开源项目的中文编辑。读懂英文 README 后，用通俗准确的中文重写。

硬性要求：
1. 严格按用户给的【字段名】格式输出纯文本，每个字段独立成段，不要输出 JSON、不要用 markdown 代码块。
2. 专有名词、库名、命令、文件路径保持英文原样，不要硬译。
3. 不编造 README 里没有的功能、数字、作者信息；看不清就写得更概括。
4. 语气像技术博客，不要营销腔。
5. 列表类字段每条单独一行，以 "- " 开头。
6. 不要输出 markdown 代码块（```），命令直接用单反引号包住。"""

STREAM_PROMPT = """请根据下面的仓库信息，按指定格式输出中文解读。

仓库：{full_name}
官方描述：{description}
主语言：{language}
累计星数：{stars}
Topics：{topics}

目录概览（顶层目录及文件数）：
{tree}

README 摘录（可能被截断）：
---
{readme}
---

严格按下面的格式输出，一个字段都不要少：

【速览】一句话说清它是什么，≤30 字。
【它是什么】2-3 句，说清定位和形态（库/工具/模板/数据集），≤140 字。
【解决什么问题】说清替代了什么旧做法或填补了什么空缺，≤120 字。
【核心机制】内部怎么做到的，用打比方的方式讲，≤160 字。
【主要功能】
- 3-6 条，每条 ≤28 字，动词开头
【项目结构】
- 从目录概览里挑 3-8 个重要目录，格式：src/ ：存放核心实现
【快速上手】给出最关键的一两条命令（用单反引号包裹，禁止用三反引号代码块），再用中文说步骤，≤140 字。
【值得学的点】
- 3 条，每条 ≤32 字
【适合谁】什么阶段、什么方向的人适合看，≤40 字。
【术语表】
- 英文 | 中文 | 一句话解释（2-5 条）
"""

CJK = re.compile(r"[\u4e00-\u9fff]")


class SearchService:
    def __init__(self, cfg, log=print):
        self.cfg = cfg
        self.log = log
        self.client = GitHubClient(cfg.get("token", ""), cfg.get("timeout", 30), log)
        self.localizer = Localizer(cfg["model"], cfg["ollama_url"], log)
        self.store = Store(cfg["data_dir"])
        self.model_lock = threading.Lock()  # 单卡单模型，串行调用避免互相拖慢
        self.cache_dir = os.path.join(cfg["out_dir"], "search-cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.readme_cache = os.path.join(self.cache_dir, "readme")
        os.makedirs(self.readme_cache, exist_ok=True)
        self._facts_mem = {}   # name -> (time, facts)，避免详情页每次都重算

    # ---------- 模型管理 ----------
    def list_models(self):
        """每次调用都真跑一遍 `ollama list`，用户新下载的模型立刻能看到。"""
        rows = self._ollama_list()
        if rows is None:
            # ollama 命令不在 PATH 时退回 HTTP 接口，至少别让面板空着
            rows = self._models_from_api()
        details = self._tags_detail()

        out = []
        for r in rows:
            name = r.get("name", "")
            d = details.get(name, {})
            out.append(
                {
                    "name": name,
                    "size": d.get("size_text") or r.get("size") or "",
                    "modified": r.get("modified") or "",
                    "params": d.get("params", ""),
                    "quant": d.get("quant", ""),
                    "current": name == self.localizer.model,
                }
            )
        out.sort(key=lambda x: (not x["current"], x["name"].lower()))
        return {"models": out, "current": self.localizer.model, "count": len(out)}

    def _ollama_list(self):
        exe = shutil.which("ollama") or "ollama"
        try:
            proc = subprocess.run(
                [exe, "list"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=20,
            )
        except Exception as e:
            self.log(f"[ollama list 失败] {e}")
            return None
        if proc.returncode != 0:
            self.log(f"[ollama list 退出码 {proc.returncode}] {(proc.stderr or '').strip()[:200]}")
            return None
        rows = []
        for line in (proc.stdout or "").splitlines():
            line = line.rstrip()
            if not line or line.upper().startswith("NAME"):
                continue
            parts = re.split(r"\s{2,}", line.strip())
            if len(parts) < 2:
                parts = line.split()
            if len(parts) < 2:
                continue
            # ollama list 的列是 NAME / ID / SIZE / MODIFIED，ID 是 12 位十六进制
            name = parts[0]
            size, modified = "", []
            for tok in parts[1:]:
                if not size and re.fullmatch(r"[\d.]+\s*[KMGT]i?B", tok):
                    size = tok
                elif re.fullmatch(r"[0-9a-f]{8,}", tok) and not modified:
                    continue
                else:
                    modified.append(tok)
            rows.append({"name": name, "size": size, "modified": " ".join(modified)})
        return rows

    def _models_from_api(self):
        try:
            req = urllib.request.Request(self.localizer.base_url + "/api/tags")
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            self.log(f"[/api/tags 失败] {e}")
            return []
        out = []
        for m in data.get("models", []):
            gb = (m.get("size") or 0) / (1024 ** 3)
            out.append(
                {
                    "name": m.get("name", ""),
                    "size": f"{gb:.1f} GB" if gb else "",
                    "modified": "",
                }
            )
        return out

    def _tags_detail(self):
        """用 /api/tags 补齐参数量、量化档位这两列（ollama list 不给）。"""
        try:
            req = urllib.request.Request(self.localizer.base_url + "/api/tags")
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception:
            return {}
        info = {}
        for m in data.get("models", []):
            d = m.get("details") or {}
            gb = (m.get("size") or 0) / (1024 ** 3)
            info[m.get("name", "")] = {
                "params": d.get("parameter_size", ""),
                "quant": d.get("quantization_level", ""),
                "size_text": f"{gb:.1f} GB" if gb else "",
            }
        return info

    def set_model(self, name):
        name = (name or "").strip()
        if not name:
            return {"error": "模型名为空"}
        names = [m["name"] for m in self.list_models()["models"]]
        if name not in names:
            for n in names:
                if n.split(":")[0] == name.split(":")[0]:
                    name = n
                    break
            else:
                return {"error": f"本机没有模型 {name}，先 ollama pull"}

        with self.model_lock:
            self.localizer.model = name
            self.cfg["model"] = name
        self._persist_config(name)
        self.log(f"[模型切换] -> {name}")
        return {"ok": True, "model": name}

    def _persist_config(self, name):
        self._write_config("model", name)

    def _write_config(self, key, value):
        path = self.cfg.get("config_path")
        if not path or not os.path.isfile(path):
            return
        try:
            with open(path, encoding="utf-8") as f:
                raw = json.load(f)
            raw[key] = value
            with open(path, "w", encoding="utf-8") as f:
                json.dump(raw, f, ensure_ascii=False, indent=2)
                f.write("\n")
        except Exception as e:
            self.log(f"[写回 config.json 失败] {e}")

    # ---------- 中文 → 英文检索词 ----------
    def expand(self, q):
        if not CJK.search(q):
            return {"keywords": [q], "intent": "已是英文，直接检索", "expanded": q, "from_model": False}
        if not self.localizer.available():
            return {"keywords": [q], "intent": "本地模型不可用，使用原始查询", "expanded": q, "from_model": False}

        prompt = (
            f"用户输入的中文检索需求：{q}\n\n"
            '请输出 JSON：{"keywords": [英文关键词...], "intent": "中文意图说明"}'
        )
        body = {
            "model": self.localizer.model,
            "messages": [
                {"role": "system", "content": EXPAND_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "format": EXPAND_SCHEMA,
            "think": False,
            "options": {"temperature": 0.2, "num_ctx": 4096, "num_predict": 600},
            "keep_alive": "10m",
        }
        try:
            with self.model_lock:
                if not self.localizer.ensure_model():
                    raise RuntimeError("模型缺失")
                data = self._post_chat(body)
            keywords = [str(k).strip() for k in (data.get("keywords") or []) if str(k).strip()]
            if not keywords:
                raise ValueError("关键词为空")
            keywords = keywords[:3]
            return {
                "keywords": keywords,
                "intent": data.get("intent") or "",
                "expanded": " ".join(keywords[:2]),
                "from_model": True,
            }
        except Exception as e:
            self.log(f"[检索词翻译失败] {e}")
            return {"keywords": [q], "intent": "检索词翻译失败，退回原始查询", "expanded": q, "from_model": False}

    def _post_chat(self, body):
        req = urllib.request.Request(
            self.localizer.base_url + "/api/chat",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=240) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        msg = payload.get("message") or {}
        content = msg.get("content") or msg.get("thinking") or ""
        return parse_json_loose(content)

    # ---------- 搜索（支持分页） ----------
    def search(self, q, page=1, limit=20, force=False):
        q = (q or "").strip()
        if not q:
            return {"error": "查询为空"}
        page = max(1, int(page or 1))
        qkey = hashlib.sha1(f"{q.lower()}|{page}|{limit}".encode("utf-8")).hexdigest()[:16]
        if not force:
            cached = self.store.get_query(qkey)
            if cached:
                cached["cached"] = True
                return cached

        started = time.time()
        ex = self.expand(q)
        try:
            res = self.client.search_page(
                f'{ex["expanded"]} fork:false archived:false', per_page=limit, page=page
            )
        except Exception as e:
            return {"error": f"GitHub 检索失败：{e}"}

        items = (res or {}).get("items", [])
        results = []
        for it in items:
            results.append(
                {
                    "full_name": it.get("full_name"),
                    "html_url": it.get("html_url"),
                    "stars": it.get("stargazers_count", 0),
                    "forks": it.get("forks_count", 0),
                    "language": it.get("language") or "",
                    "description": clean_text(it.get("description")),
                    "topics": it.get("topics") or [],
                    "updated": it.get("pushed_at") or "",
                    "brief": self._cached_brief(it.get("full_name")),
                }
            )

        payload = {
            "q": q,
            "page": page,
            "expanded": ex["expanded"],
            "intent": ex["intent"],
            "from_model": ex["from_model"],
            "took": round(time.time() - started, 1),
            "total": (res or {}).get("total_count", 0),
            "results": results,
            "quick": {"keywords": ex["keywords"], "intent": ex["intent"], "from_model": ex["from_model"]},
            "cached": False,
        }
        self.store.put_query(qkey, payload)
        return payload

    # ---------- 首页热榜（支持分页） ----------
    def hot(self, limit=20, page=1):
        page = max(1, int(page or 1))
        key = f"hot|{page}|{limit}"
        cached = self.store.get_query(key, max_age_hours=12)
        if cached:
            cached["cached"] = True
            return cached
        try:
            res = self.client.search_page(
                "stars:>30000 fork:false archived:false", per_page=limit, page=page, sort="stars"
            )
        except Exception as e:
            return {"error": f"获取热榜失败：{e}"}
        results = []
        for it in (res or {}).get("items", []):
            results.append(
                {
                    "full_name": it.get("full_name"),
                    "html_url": it.get("html_url"),
                    "stars": it.get("stargazers_count", 0),
                    "forks": it.get("forks_count", 0),
                    "language": it.get("language") or "",
                    "description": clean_text(it.get("description")),
                    "topics": it.get("topics") or [],
                    "brief": self._cached_brief(it.get("full_name")),
                }
            )
        payload = {
            "hot": True,
            "page": page,
            "results": results,
            "total": (res or {}).get("total_count", 0),
        }
        self.store.put_query(key, payload)
        return payload

    # ---------- 周榜 ----------
    def weekly(self, limit=20, page=1):
        """近 7 天新建的项目，按星标排序——真实新晋榜，不依赖本地历史快照。"""
        page = max(1, int(page or 1))
        since = (date.today() - timedelta(days=7)).isoformat()
        key = f"weekly|{since}|{page}|{limit}"
        cached = self.store.get_query(key, max_age_hours=6)
        if cached:
            cached["cached"] = True
            return cached
        q = f"created:>={since} stars:>50 fork:false archived:false"
        try:
            res = self.client.search_page(q, per_page=limit, page=page, sort="stars")
        except Exception as e:
            return {"error": f"获取周榜失败：{e}"}
        results = []
        for it in (res or {}).get("items", []):
            results.append(
                {
                    "full_name": it.get("full_name"),
                    "html_url": it.get("html_url"),
                    "stars": it.get("stargazers_count", 0),
                    "forks": it.get("forks_count", 0),
                    "language": it.get("language") or "",
                    "description": clean_text(it.get("description")),
                    "topics": it.get("topics") or [],
                    "created": it.get("created_at") or "",
                    "brief": self._cached_brief(it.get("full_name")),
                }
            )
        payload = {
            "weekly": True,
            "since": since,
            "page": page,
            "results": results,
            "total": (res or {}).get("total_count", 0),
        }
        self.store.put_query(key, payload)
        return payload

    # ---------- 速览译文（列表用，批量一次调用） ----------
    def briefs(self, items):
        items = [m for m in (items or []) if m.get("full_name")][:14]
        if not items:
            return {"briefs": {}}
        done, todo = {}, []
        for m in items:
            cached = self._cached_brief(m["full_name"])
            if cached:
                done[m["full_name"]] = cached
            else:
                todo.append(m)
        if not todo:
            return {"briefs": done, "cached": True}
        if not self.localizer.available():
            return {"briefs": done, "error": "本地模型不可用"}

        lines = "\n".join(
            "- {}｜{}｜{}".format(
                m["full_name"], m.get("language") or "未标注", (m.get("description") or "")[:220]
            )
            for m in todo
        )
        prompt = (
            "下面是若干 GitHub 仓库的英文描述。请为每个仓库写 2-3 句中文介绍，共 60-110 字：\n"
            "第一句说它是干什么的，第二句说它解决什么实际问题或有什么特点，必要时补一句适合什么人用。\n"
            "不要营销腔，不要复述仓库名，不要分点，就是一段话。\n"
            '只输出 JSON：{"briefs": [{"full_name": "...", "brief": "..."}]}\n\n' + lines
        )
        body = {
            "model": self.localizer.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "format": {
                "type": "object",
                "properties": {
                    "briefs": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "full_name": {"type": "string"},
                                "brief": {"type": "string"},
                            },
                            "required": ["full_name", "brief"],
                        },
                    }
                },
                "required": ["briefs"],
            },
            "think": False,
            "options": {"temperature": 0.25, "num_ctx": 4096, "num_predict": 1200},
            "keep_alive": "10m",
        }
        try:
            with self.model_lock:
                data = self._post_chat(body)
            for row in data.get("briefs", []):
                name, brief = row.get("full_name"), (row.get("brief") or "").strip()
                if name and brief:
                    done[name] = brief
                    self._save_brief(name, brief)
        except Exception as e:
            self.log(f"[速览翻译失败] {e}")
            return {"briefs": done, "error": str(e)}
        return {"briefs": done}

    def _brief_path(self, name):
        safe = re.sub(r"[^a-zA-Z0-9_\-]", "_", name)
        return os.path.join(self.cache_dir, safe + ".brief")

    def _cached_brief(self, name):
        p = self._brief_path(name)
        if os.path.exists(p):
            try:
                with open(p, encoding="utf-8") as f:
                    return f.read().strip() or None
            except Exception:
                return None
        return None

    def _save_brief(self, name, brief):
        try:
            with open(self._brief_path(name), "w", encoding="utf-8") as f:
                f.write(brief)
        except Exception:
            pass

    # ---------- 规则层：判断卡 / 能不能跑 / 代码地图 / 按钮导读 ----------
    def _facts_for(self, name, repo, tree, readme, lang="zh-Hans"):
        # 每个语言单独缓存一份：同一仓库切语言时不用重算
        key = name + "#" + i18n.normalize(lang)
        hit = self._facts_mem.get(key)
        if hit and time.time() - hit[0] < 1800:
            return hit[1]
        data = factsmod.build(repo, tree, readme, i18n.normalize(lang))
        # README 正文也顺手存一份，逐节翻译时不用再抓
        data["_readme"] = readme
        self._facts_mem[key] = (time.time(), data)
        if len(self._facts_mem) > 80:
            oldest = min(self._facts_mem, key=lambda k: self._facts_mem[k][0])
            self._facts_mem.pop(oldest, None)
        return data

    def _readme_and_sections(self, name, lang="zh-Hans"):
        hit = self._facts_mem.get(name + "#" + i18n.normalize(lang))
        readme = hit[1].get("_readme") if hit else None
        if not readme:
            readme = self.client.readme_text(name) or ""
        return readme, factsmod.split_readme_sections(readme, lang=i18n.normalize(lang))

    # ---------- README 逐节翻译 ----------
    def stream_readme_section(self, name, index, lang="zh-Hans"):
        if not name:
            yield ("error", {"error": "缺少仓库名"})
            return
        try:
            index = int(index)
        except Exception:
            index = 0
        readme, sections = self._readme_and_sections(name, lang)
        if not sections:
            yield ("error", {"error": "这个仓库没有可切的 README 小节"})
            return
        if index < 0 or index >= len(sections):
            yield ("error", {"error": "小节序号超出范围"})
            return
        sec = sections[index]
        body = sec.get("body", "")
        if not body:
            yield ("error", {"error": "这个小节是空的"})
            return
        title = sec["title"]
        yield ("start", {"title": title, "chars": len(body), "index": index})

        # 缓存命中直接发成品，切模型后会按新模型重译
        cached = self._read_section_cache(name, index)
        if cached:
            yield ("done", {"text": cached, "source": "cache", "title": title, "index": index})
            return

        if not self.localizer.ensure_model():
            yield ("error", {"error": "本地模型不可用，无法翻译"})
            return
        prompt = (
            f"仓库 {name} 的 README 小节标题：{title}\n\n"
            f"原文如下：\n---\n{body[:3000]}\n---\n\n"
            "请译成中文，保留原来的段落与列表结构；代码块、命令、链接地址、库名一律原样保留；"
            "不要加自己的评论，不要压缩内容。"
        )
        payload = {
            "model": self.localizer.model,
            "messages": [
                {"role": "system", "content": "你是技术文档译者。把英文 README 译成通顺的中文，保留 markdown 结构与代码块原样。"},
                {"role": "user", "content": prompt},
            ],
            "stream": True,
            "think": False,
            "options": {"temperature": 0.2, "num_ctx": 8192, "num_predict": 1200},
            "keep_alive": "10m",
        }
        req = urllib.request.Request(
            self.localizer.base_url + "/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        parts = []
        stats = {"tokens": 0, "tps": None}
        started = None
        try:
            with self.model_lock:
                with urllib.request.urlopen(req, timeout=300) as resp:
                    for line in resp:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line.decode("utf-8"))
                        except Exception:
                            continue
                        piece = (chunk.get("message") or {}).get("content") or ""
                        if piece:
                            if started is None:
                                started = time.time()
                            parts.append(piece)
                            span = max(time.time() - started, 0.001)
                            tps = round(len(parts) / span, 1)
                            stats["tokens"] = len(parts)
                            stats["tps"] = tps
                            yield ("chunk", {"text": piece, "tps": tps})
                        if chunk.get("done"):
                            ec, ed = chunk.get("eval_count"), chunk.get("eval_duration")
                            if ec and ed:
                                stats["tokens"] = ec
                                stats["tps"] = round(ec / (ed / 1e9), 1)
                            break
        except Exception as e:
            self.log(f"[README 小节翻译失败] {e}")
            yield ("error", {"error": f"翻译中断：{e}"})
            return
        text = "".join(parts).strip()
        if text:
            self._write_section_cache(name, index, text)
        yield ("done", {"text": text, "source": "model", "title": title, "index": index, **stats})

    def _section_cache_path(self, name, index):
        tag = re.sub(r"[^A-Za-z0-9_.\-]", "_", self.localizer.model)
        safe = re.sub(r"[^a-zA-Z0-9_\-]", "_", name)
        return os.path.join(self.readme_cache, f"{safe}__{tag}__s{index}.md")

    def _read_section_cache(self, name, index):
        p = self._section_cache_path(name, index)
        if os.path.isfile(p):
            try:
                with open(p, encoding="utf-8") as f:
                    return f.read()
            except Exception:
                return None
        return None

    def _write_section_cache(self, name, index, text):
        try:
            with open(self._section_cache_path(name, index), "w", encoding="utf-8") as f:
                f.write(text)
        except Exception:
            pass

    # ---------- 一键拉取 ----------
    def download_base(self):
        base = self.cfg.get("download_dir") or os.path.join(os.path.expanduser("~"), "Doubao", "repos")
        return base

    def clone_prep(self, name):
        base = self.download_base()
        dest = gitpull.target_dir(base, name) if name else ""
        size = 0
        hit = self._facts_mem.get(name)
        if hit:
            size = hit[1].get("size_mb", 0)
        return {
            "base": base,
            "dest": dest,
            "exists": gitpull.is_cloned(dest) if dest else False,
            "size_mb": size,
            "disk_free_gb": self._disk_free_gb(dest),
        }

    def _disk_free_gb(self, dest):
        try:
            probe = dest or self.download_base()
            while probe and not os.path.isdir(probe):
                probe = os.path.dirname(probe)
            if not probe:
                return None
            return round(shutil.disk_usage(probe).free / (1024 ** 3), 1)
        except Exception:
            return None

    def set_download_dir(self, path):
        path = (path or "").strip().strip('"')
        if not path:
            return {"error": "目录为空"}
        raw_path = path
        path = os.path.normpath(path)
        # normpath 会把 "E:\" 变成 "E:"（盘符相对路径），会把 target_dir 拼坏，这里补回分隔符
        if re.fullmatch(r"[A-Za-z]:", path):
            path = path + "\\"
        try:
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            self.log(f"[set_dir] 失败 {raw_path!r} -> {path!r}: {e}")
            return {"error": f"无法使用这个目录：{e}"}
        self.cfg["download_dir"] = path
        self._write_config("download_dir", path)
        self.log(f"[set_dir] 收到 {raw_path!r} → 生效 {path!r}")
        return {"ok": True, "base": path}

    def list_dir(self, path=""):
        """给页面内的文件夹浏览器用：列盘符 / 列子目录，不弹任何系统窗口。"""
        path = (path or "").strip().strip('"')
        if not path:
            drives = []
            for d in "CDEFGHIJK":
                root = f"{d}:\\"
                if os.path.isdir(root):
                    free = 0
                    try:
                        free = round(shutil.disk_usage(root).free / (1024 ** 3), 1)
                    except Exception:
                        pass
                    drives.append({"name": f"{d}:", "path": root, "free_gb": free})
            return {"path": "", "parent": "", "dirs": drives, "base": self.download_base()}

        path = os.path.abspath(path)
        if not os.path.isdir(path):
            return {"error": f"这个目录不存在：{path}"}
        try:
            names = sorted(os.listdir(path), key=lambda s: s.lower())
        except Exception as e:
            return {"error": f"读不了这个目录：{e}"}

        dirs = []
        for n in names:
            full = os.path.join(path, n)
            if n.startswith(".") or n.startswith("$"):
                continue
            try:
                if os.path.isdir(full):
                    dirs.append({"name": n, "path": full})
            except Exception:
                pass

        cut = path.rstrip("\\")
        parent = os.path.dirname(cut)
        if cut.count(":") == 1 and len(cut) <= 2:
            parent = ""      # 盘符根目录，上一级回到盘符列表
        free = 0
        try:
            free = round(shutil.disk_usage(path).free / (1024 ** 3), 1)
        except Exception:
            pass
        return {"path": path, "parent": parent, "dirs": dirs[:300], "free_gb": free,
                "base": self.download_base()}

    def clone_stream(self, name, dest="", job_id=""):
        if not name:
            yield ("error", {"error": "缺少仓库名"})
            return
        if not dest:
            dest = gitpull.target_dir(self.download_base(), name)
        dest = os.path.normpath(dest)
        url = f"https://github.com/{name}.git"
        for ev in gitpull.clone_stream(url, dest, job_id):
            yield ev

    # ---------- 详情：流式汉化 ----------
    def stream_detail(self, name, lang="zh-Hans"):
        """生成 SSE 事件：meta（立刻显示基本信息） -> chunk（边翻边出字） -> done。"""
        if not name:
            yield ("error", {"error": "缺少仓库名"})
            return

        repo = self.client.api(f"/repos/{name}")
        if not repo:
            yield ("error", {"error": "仓库不存在或 API 配额不足"})
            return

        meta = {
            "full_name": repo["full_name"],
            "description": clean_text(repo.get("description")),
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "language": repo.get("language") or "",
            "topics": repo.get("topics") or [],
            "html_url": repo.get("html_url"),
            "license": ((repo.get("license") or {}).get("spdx_id") or ""),
            "default_branch": repo.get("default_branch") or "main",
            "pushed_at": repo.get("pushed_at"),
        }

        # 先把基本信息推过去：用户点开立刻能看到仓库名与描述，不用等任何翻译
        yield ("meta", {"meta": meta, "images": []})

        readme = self.client.readme_text(name) or ""
        tree = self.client.tree(name, meta["default_branch"]) or []

        # 规则层（判断卡 / 能不能跑 / 代码地图 / 按钮导读 / README 目录）：0 模型开销
        facts_data = self._facts_for(name, repo, tree, readme, lang)
        yield ("facts", {"facts": facts_data})

        sig = signature(meta, readme, self.localizer.model)

        # 配图后台下载，不阻塞正文
        img_result = {"images": []}

        def _grab_images():
            try:
                urls = extract_images(readme, name)[:2]
            except Exception:
                return
            got = []
            for i, url in enumerate(urls):
                ext = os.path.splitext(url.split("?")[0])[1].lower()
                if ext not in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
                    ext = ".png"
                fname = re.sub(r"[^a-zA-Z0-9_\-]", "_", name) + f"-{i}{ext}"
                dest = os.path.join(self.cache_dir, fname)
                if os.path.exists(dest) or self.client.download(url, dest):
                    got.append(f"/cache/{fname}")
            img_result["images"] = got

        img_thread = threading.Thread(target=_grab_images, daemon=True)
        img_thread.start()
        images_sent = False

        def _maybe_images():
            nonlocal images_sent
            if images_sent or not img_result["images"]:
                return None
            images_sent = True
            return ("extra", {"images": img_result["images"]})

        # 命中缓存 -> 直接把成品发过去，不用等模型
        cached = self.store.get_localization(name, sig)
        if cached and validate(cached) is None:
            img_thread.join(timeout=8)
            ev = _maybe_images()
            if ev:
                yield ev
            yield ("full", {"local": cached, "source": "cache"})
            yield ("done", {"source": "cache"})
            return

        if not self.localizer.ensure_model():
            yield ("error", {"error": "本地模型不可用，无法翻译"})
            return

        tree_summary = summarize_tree(tree)
        prompt = STREAM_PROMPT.format(
            full_name=meta["full_name"],
            description=meta["description"] or "无",
            language=meta["language"] or "未标注",
            stars=meta["stars"],
            topics=", ".join(meta["topics"]) or "无",
            tree="\n".join(
                [f"- {d['path']}/ ({d['files']} 个文件)" for d in tree_summary.get("top_dirs", [])]
                + ["根目录文件：" + ", ".join(tree_summary.get("root_files", [])[:10])]
            ),
            readme=readme[: self.cfg["readme_chars"]],
        )
        body = {
            "model": self.localizer.model,
            "messages": [
                {"role": "system", "content": STREAM_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            "stream": True,
            "think": False,
            "options": {"temperature": 0.3, "num_ctx": 8192, "num_predict": 1600},
            "keep_alive": "10m",
        }
        req = urllib.request.Request(
            self.localizer.base_url + "/api/chat",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        full_text = []
        started_at = None
        stats = {"tokens": 0, "tps": None}
        try:
            with self.model_lock:
                with urllib.request.urlopen(req, timeout=300) as resp:
                    for line in resp:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line.decode("utf-8"))
                        except Exception:
                            continue
                        piece = (chunk.get("message") or {}).get("content") or ""
                        if piece:
                            now = time.time()
                            if started_at is None:
                                started_at = now
                            full_text.append(piece)
                            n = len(full_text)
                            tps = None
                            if n > 1 and started_at:
                                span = max(now - started_at, 0.001)
                                tps = round((n - 1) / span, 1)
                            stats["tokens"] = n
                            stats["tps"] = tps
                            yield ("chunk", {"text": piece, "n": n, "tps": tps})
                            ev = _maybe_images()
                            if ev:
                                yield ev
                        if chunk.get("done"):
                            # Ollama 在最后一帧给出精确的 eval_count / eval_duration（纳秒）
                            ec, ed = chunk.get("eval_count"), chunk.get("eval_duration")
                            if ec and ed:
                                stats["tokens"] = ec
                                stats["tps"] = round(ec / (ed / 1e9), 1)
                            elif started_at:
                                stats["tps"] = round(len(full_text) / max(time.time() - started_at, 0.001), 1)
                            break
        except Exception as e:
            self.log(f"[流式汉化失败] {e}")
            yield ("error", {"error": f"翻译中断：{e}"})
            return

        text = "".join(full_text)
        ev = _maybe_images()
        if ev:
            yield ev
        parsed = parse_sections(text)
        if parsed:
            if validate(parsed) is None:
                self.store.put_localization(name, sig, parsed, today_str())
            yield ("done", {"source": "model", "parsed": parsed, **stats})
        else:
            yield ("done", {"source": "model-raw", "raw": text, **stats})


def parse_sections(text):
    """把【字段】分段文本解析成结构化字典。"""
    found = re.split(r"【([^】]{1,8})】", text or "")
    data = {}
    for i in range(1, len(found) - 1, 2):
        key = found[i].strip()
        val = found[i + 1].strip()
        if not val:
            continue
        if key in ("主要功能", "值得学的点", "项目结构", "术语表"):
            items = []
            for ln in val.splitlines():
                ln = ln.strip()
                if not ln:
                    continue
                ln = re.sub(r"^[-•*]\s*", "", ln)
                items.append(ln)
            if key == "术语表":
                rows = []
                for ln in items:
                    parts = [p.strip() for p in ln.split("|")]
                    if len(parts) >= 2:
                        rows.append(
                            {"英文": parts[0], "中文": parts[1], "解释": parts[2] if len(parts) > 2 else ""}
                        )
                data[key] = rows
            elif key == "项目结构":
                rows = []
                for ln in items:
                    m = re.match(r"([^：:]+)[：:]\s*(.*)", ln)
                    if m:
                        rows.append({"路径": m.group(1).strip(), "作用": m.group(2).strip()})
                data[key] = rows
            else:
                data[key] = [re.sub(r"^[（(]\d+[)）]\s*", "", x) for x in items if x]
        else:
            data[key] = re.sub(r"\s*\n\s*", " ", val).strip()
    if len(data) < 4:
        return None
    return data
