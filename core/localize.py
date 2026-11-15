"""本地 Ollama 结构化汉化。全程不联网云服务，只打 127.0.0.1。"""
import json
import urllib.error
import urllib.request

SCHEMA = {
    "type": "object",
    "properties": {
        "速览": {"type": "string"},
        "它是什么": {"type": "string"},
        "解决什么问题": {"type": "string"},
        "核心机制": {"type": "string"},
        "主要功能": {"type": "array", "items": {"type": "string"}},
        "项目结构": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "路径": {"type": "string"},
                    "作用": {"type": "string"},
                },
                "required": ["路径", "作用"],
            },
        },
        "快速上手": {"type": "string"},
        "值得学的点": {"type": "array", "items": {"type": "string"}},
        "适合谁": {"type": "string"},
        "术语表": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "英文": {"type": "string"},
                    "中文": {"type": "string"},
                    "解释": {"type": "string"},
                },
                "required": ["英文", "中文", "解释"],
            },
        },
    },
    "required": [
        "速览",
        "它是什么",
        "解决什么问题",
        "核心机制",
        "主要功能",
        "项目结构",
        "快速上手",
        "值得学的点",
        "适合谁",
        "术语表",
    ],
}

SYSTEM = """你是一名给中国程序员讲开源项目的中文编辑。你的任务不是逐字翻译，而是把英文 README 读懂后，
用通俗、准确、有信息量的中文重写，让一个刚入门的人也能看明白这个项目是干什么的、怎么用、值不值得学。

要求：
1. 只用中文表达，但专有名词、库名、命令、文件路径、代码片段保持英文原样，不要硬译。
2. 不要编造 README 里没有的功能、数字、作者信息。看不清就写得更概括，绝不虚构。
3. 语气平实，像技术博客，不要营销腔，不要"赋能""生态闭环"这类空话。
4. 每个字段都有字数上限，超了就是不合格。
5. 只输出 JSON 对象，不要输出任何解释性文字，不要用 markdown 代码块包裹。"""

PROMPT_TMPL = """请根据下面的仓库信息，输出 JSON。

仓库：{full_name}
官方描述：{description}
主语言：{language}
累计星数：{stars}
Topics：{topics}
本周/近期活跃度：{activity}

目录概览（顶层目录及文件数）：
{tree}

README 摘录（可能被截断）：
---
{readme}
---

各字段要求：
- 速览：一句话说清它是什么，≤30 字，不用句号结尾。
- 它是什么：2-3 句话说清定位和形态（是库、是工具、是模板还是数据集），≤120 字。
- 解决什么问题：说清它替代了什么旧做法，或填补了什么空缺，≤100 字。
- 核心机制：它内部怎么做到的，用打比方的方式讲，≤150 字。
- 主要功能：3-6 条，每条 ≤25 字，动词开头。
- 项目结构：从上面目录概览里挑 3-8 个最重要的目录或文件，说明各自作用，路径用真实路径。
- 快速上手：给出最关键的一两条安装/运行命令（保持英文原文），再用中文说明步骤，≤120 字。
- 值得学的点：3 条，每条 ≤30 字，说明这个项目在设计或工程上值得借鉴什么。
- 适合谁：什么阶段、什么方向的人适合看，≤40 字。
- 术语表：挑 2-5 个 README 里出现的关键英文术语，给中文译名和一句话解释。

注意：以上 10 个字段必须全部输出，一个都不能省略。
如果某项信息在材料里找不到，就基于仓库性质做保守概括（例如没有安装命令时，快速上手写"按 README 安装说明操作"），
宁可笼统也不要留空，更不要编造具体命令或数字。
"""


class Localizer:
    def __init__(self, model, base_url, log=print, timeout=180):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.log = log
        self.timeout = timeout

    def available(self):
        try:
            req = urllib.request.Request(self.base_url + "/api/tags")
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            names = [m.get("name", "") for m in data.get("models", [])]
            return names
        except Exception as e:
            self.log(f"[Ollama 不可用] {e}")
            return []

    def ensure_model(self):
        names = self.available()
        if not names:
            return False
        hit = any(n == self.model or n.startswith(self.model.split(":")[0] + ":") for n in names)
        if not hit:
            self.log(f"[模型缺失] 本地没有 {self.model}，现有：{names}")
        return hit

    def localize(self, meta, readme, tree_summary, activity):
        prompt = PROMPT_TMPL.format(
            full_name=meta["full_name"],
            description=meta.get("description") or "无",
            language=meta.get("language") or "未标注",
            stars=meta.get("stars", 0),
            topics=", ".join(meta.get("topics") or []) or "无",
            activity=activity,
            tree="\n".join(
                [f"- {d['path']}/ ({d['files']} 个文件)" for d in tree_summary.get("top_dirs", [])]
                + ["根目录文件：" + ", ".join(tree_summary.get("root_files", [])[:10])]
            ),
            readme=readme,
        )
        result = self._chat(prompt, prompt)
        problem = validate(result)
        if problem:
            self.log(f"    [字段不合格] {problem}，重试一次")
            hint = (
                f"你上一次的输出不合格：{problem}。"
                "请重新输出完整 JSON，所有字段都要是完整通顺的中文句子，不要半句就停。"
            )
            result = self._chat(prompt, prompt + "\n\n" + hint)
            problem = validate(result)
            if problem:
                self.log(f"    [重试仍不合格] {problem}，保留现有结果")
        return result

    def _chat(self, prompt, user_content):
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": user_content},
            ],
            "stream": False,
            "format": SCHEMA,
            # 关键：Qwen3 系模型默认先输出长思维链，会把输出预算耗光导致正文为空
            "think": False,
            "options": {"temperature": 0.3, "top_p": 0.9, "num_ctx": 8192, "num_predict": 3000},
            "keep_alive": "10m",
        }
        req = urllib.request.Request(
            self.base_url + "/api/chat",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        msg = payload.get("message") or {}
        content = msg.get("content") or ""
        if not content.strip():
            # 有些版本不支持 think=false，退回从思维链里抢救
            content = msg.get("thinking") or ""
        if payload.get("done_reason") == "length":
            self.log("    [注意] 输出被长度截断，结果可能不完整")
        return parse_json_loose(content)


def validate(data, lang="zh-Hans"):
    """小模型容易只写半句话，这里做最低限度把关。返回问题描述或 None。

    非中文时不套用中文字数阈值（法语/俄语同样意思要长得多，日语又更短），
    只守「它是什么」「核心机制」两个核心字段，避免整份译文被拦在缓存外面。
    """
    if not isinstance(data, dict):
        return "不是 JSON 对象"
    if lang != "zh-Hans":
        # 外语没有中文那套字数直觉，只守三条核心字段，别把整份译文拦在缓存外面
        for key in ("它是什么", "核心机制"):
            if not str(data.get(key) or "").strip():
                return f"缺少字段「{key}」"
            if len(str(data.get(key))) < 12:
                return f"「{key}」过短"
        return None
    required = ["速览", "它是什么", "核心机制", "适合谁"]
    for key in required:
        if not str(data.get(key) or "").strip():
            return f"缺少字段「{key}」"
    if len(str(data.get("它是什么"))) < 25:
        return "「它是什么」过短"
    mech = str(data.get("核心机制"))
    if len(mech) < 25:
        return "「核心机制」过短或只有半句"
    if not mech.endswith(("。", "！", "？", "”")) and len(mech) < 40:
        return "「核心机制」疑似未写完"
    return None


def parse_json_loose(text):
    """模型偶尔会带 ```json 包裹或前后废话，尽力抢救。"""
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]
    return json.loads(text)
