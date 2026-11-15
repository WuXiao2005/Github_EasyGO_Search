"""仓库事实层：全部靠规则计算，不调用模型。

详情页最上面的几块（这是什么 / 值不值得看 / 我能不能跑 / 代码地图 / 按钮导读）
以及 README 目录，都在这里生成，所以点开仓库 1 秒内就能出内容。
"""
import re
from datetime import datetime, timezone

# 根目录常见大文件/配置，绝大多数情况不用读
HARD_SKIP = {
    ".github", ".vscode", ".idea", ".agents", ".claude", ".openclaw", ".git",
    "node_modules", "dist", "build", "target", "vendor", "coverage", "__pycache__",
    ".venv", "venv", "site-packages", "patches", "git-hooks",
}

SKIP_SUFFIX = (".lock", "-lock.yaml", "-lock.json", ".d.mts", ".d.ts", ".map")

# 目录名 -> (一句话, 是否建议读)
DIR_NOTES = {
    "src": ("核心实现代码，真正干活的地方", True),
    "lib": ("库代码，被上层调用的公共实现", True),
    "app": ("应用层代码，程序的骨架", True),
    "apps": ("多个可运行应用的集合（每个子目录是一个应用）", True),
    "packages": ("拆分的多个子包（monorepo 结构）", True),
    "core": ("核心逻辑，一般从这里的入口读起", True),
    "docs": ("官方文档，比读源码快得多", True),
    "doc": ("官方文档", True),
    "examples": ("可直接跑的例子，学一个项目最快的入口", True),
    "example": ("示例代码", True),
    "samples": ("示例代码", True),
    "demo": ("演示代码，看效果用", True),
    "demos": ("演示代码", True),
    "tutorials": ("教程，按顺序读", True),
    "notebooks": ("交互式笔记，适合一步步跑", True),
    "test": ("测试，想知道边界行为时看", False),
    "tests": ("测试，想知道边界行为时看", False),
    "ui": ("界面代码", True),
    "web": ("网页前端", True),
    "frontend": ("前端界面", True),
    "server": ("服务端实现", True),
    "api": ("对外接口定义", True),
    "scripts": ("运维/构建脚本，用的时候再看", False),
    "tools": ("开发辅助工具，非主流程", False),
    "skills": ("技能/插件定义，扩展能力用", True),
    "extensions": ("扩展插件", True),
    "plugins": ("插件", True),
    "crates": ("Rust 子模块", True),
    "deploy": ("部署配置（Docker/K8s 等）", False),
    "config": ("默认配置文件，改参数时看", False),
    "assets": ("图片等静态资源", False),
    "static": ("静态资源", False),
    "public": ("对外静态资源", False),
    "qa": ("质量保障相关", False),
    "security": ("安全相关策略与文档", False),
    "custodian-skills": ("内置技能定义", True),
    "changelog": ("更新日志，想知道最近改了什么可以翻", False),
    "patches": ("依赖补丁，跟使用无关", False),
}

ENTRY_NAMES = {
    "main.py": "Python 入口",
    "app.py": "Python 入口",
    "__main__.py": "Python 模块入口",
    "manage.py": "Django 管理入口",
    "index.js": "Node 入口",
    "index.ts": "Node/TS 入口",
    "main.js": "Node 入口",
    "main.ts": "Node/TS 入口",
    "server.js": "服务端入口",
    "main.go": "Go 入口",
    "main.rs": "Rust 入口",
    "META-INF": "",
    "setup.py": "Python 安装脚本",
    "pyproject.toml": "Python 项目定义",
    "package.json": "Node 项目定义（脚本在 scripts 里）",
    "Cargo.toml": "Rust 项目定义",
    "go.mod": "Go 模块定义",
    "pom.xml": "Java 项目定义（Maven）",
    "build.gradle": "Java/Android 构建脚本",
    "Dockerfile": "容器构建：一条命令就能跑起来",
    "docker-compose.yml": "容器编排：docker compose up 启动",
    "Makefile": "构建入口：make 看任务",
    "CMakeLists.txt": "C/C++ 构建脚本",
    "openclaw.mjs": "命令行入口",
}

RUNTIMES = [
    ("package.json", {"name": "Node.js", "why": "有 package.json，需要 Node 环境"}),
    ("requirements.txt", {"name": "Python", "why": "有 requirements.txt，pip 安装依赖"}),
    ("pyproject.toml", {"name": "Python", "why": "有 pyproject.toml，pip/uv 安装"}),
    ("Cargo.toml", {"name": "Rust", "why": "有 Cargo.toml，需要 cargo 编译"}),
    ("go.mod", {"name": "Go", "why": "有 go.mod，需要 Go 工具链"}),
    ("pom.xml", {"name": "Java", "why": "Maven 项目，需要 JDK"}),
    ("build.gradle", {"name": "Java/Kotlin", "why": "Gradle 项目，需要 JDK"}),
    ("gemfile", {"name": "Ruby", "why": "有 Gemfile，需要 Ruby"}),
    ("composer.json", {"name": "PHP", "why": "有 composer.json，需要 PHP"}),
]

HW_PAT = re.compile(r"\b(?:CUDA|cuDNN|cuda|VRAM|vram|显存|GPU|NVIDIA|ROCm)\b")
HW_STRONG = re.compile(r"(显存|VRAM|需要.{0,6}显卡|requires?\s+(?:a\s+)?GPU|8GB\s+VRAM|24GB)", re.I)

CMD_PAT = re.compile(
    r"^(?:\\?\$?\s*)?(npm|pnpm|yarn|pip|pip3|python|python3|uv|curl|wget|docker|docker-compose|"
    r"git|brew|apt|apt-get|cargo|go|iwr|npm install|npx|bun|make|conda|mamba|composer|bundle)\b",
    re.I,
)

FENCE = re.compile(r"```[^\n]*\n(.*?)```", re.S)
HEADING = re.compile(r"^(#{1,2})\s+(.+?)\s*$", re.M)


def _days_since(iso_str):
    if not iso_str:
        return None
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - dt).days


def _freshness(pushed_at):
    days = _days_since(pushed_at)
    if days is None:
        return {"level": "unknown", "text": "提交时间未知", "days": None}
    if days <= 0:
        return {"level": "active", "text": "今天还有提交", "days": 0}
    if days <= 30:
        return {"level": "active", "text": f"最近 {max(days, 0)} 天内还在提交", "days": days}
    if days <= 180:
        return {"level": "half", "text": f"最近 {days} 天内有提交", "days": days}
    if days <= 730:
        return {"level": "slow", "text": f"约 {days // 30} 个月前有提交，更新变慢", "days": days}
    return {"level": "gone", "text": f"已经 {days // 365} 年没动静，基本停更", "days": days}


def _license_info(spdx):
    spdx = (spdx or "").strip()
    if not spdx or spdx.upper() == "NOASSERTION":
        return {"spdx": spdx or "未声明", "vibe": "没有明确协议，商用前要自己确认"}
    if spdx in ("MIT", "ISC", "BSD-2-Clause", "BSD-3-Clause", "Apache-2.0"):
        return {"spdx": spdx, "vibe": "宽松协议，可以商用、可以改，保留版权声明即可"}
    if spdx in ("GPL-2.0", "GPL-3.0", "AGPL-3.0"):
        return {"spdx": spdx, "vibe": "传染性协议，自己用没问题，分发要开源"}
    if spdx in ("MPL-2.0", "EPL-2.0"):
        return {"spdx": spdx, "vibe": "弱传染，改了它的文件需要开源那部分"}
    if spdx in ("Unlicense", "CC0-1.0"):
        return {"spdx": spdx, "vibe": "等同于放弃版权，随便用"}
    return {"spdx": spdx, "vibe": "小众协议，用之前看一眼条款"}


def _install_cmds(readme):
    """从 README 的代码块里挑一段最像安装命令的，原样展示（不翻译代码）。"""
    blocks = [b.strip("\n") for b in FENCE.findall(readme or "")]
    best = None
    for b in blocks:
        lines = [ln.strip() for ln in b.splitlines() if ln.strip() and not ln.strip().startswith("#")]
        if not lines:
            continue
        hit = sum(1 for ln in lines if CMD_PAT.match(ln))
        if hit == 0:
            continue
        if best is None or hit / len(lines) > best[0]:
            best = (hit / len(lines), lines)
    if not best:
        return []
    lines = [ln for ln in best[1] if len(ln) <= 180][:4]
    return lines


def _stack(root_files_lower):
    out = []
    for fname, rt in RUNTIMES:
        if fname in root_files_lower:
            out.append(rt)
    if "dockerfile" in root_files_lower or "docker-compose.yml" in root_files_lower:
        out.append({"name": "Docker（可选）", "why": "带 Dockerfile，不想配环境可以直接容器跑"})
    return out


def _kind(tree_sum, root_lower, readme):
    dirs = {d["path"] for d in tree_sum.get("top_dirs", [])}
    has_src = bool(dirs & {"src", "lib", "app", "apps", "packages", "core", "crates"})
    has_docs = bool(dirs & {"docs", "doc", "examples", "example"})
    readme_low = (readme or "")[:4000].lower()
    if "awesome" in readme_low and not has_src:
        return {"label": "清单/索引类", "why": "它本身不是程序，是一份整理好的资源清单一类，价值在于目录而不是代码"}
    if len(re.findall(r"\[[^\]]+\]\(http", readme or "")) > 40 and not has_src:
        return {"label": "资源清单", "why": "README 里基本都是外链，直接读 README 目录就够了"}
    if not has_src and not _stack(root_lower):
        return {"label": "文档/资料仓库", "why": "看不到可运行的代码主体，多半是文档、教程或资料"}
    if "tutorial" in readme_low or "教程" in readme_low or "course" in readme_low:
        return {"label": "教程/练手项目", "why": "定位是带着你一步步做，按章节顺序读比直接跑更值"}
    if has_docs and has_src:
        return {"label": "拿来用的产品", "why": "有完整实现也有文档，正确的用法是装上跑起来，而不是从头读源码"}
    if has_src:
        return {"label": "代码库", "why": "以代码为主，先看 examples/docs 再决定要不要深入"}
    return {"label": "尚不确定", "why": "结构信息不足，建议直接看 README 开头"}


def _code_map(tree_sum, root_files):
    rows = []
    for d in tree_sum.get("top_dirs", []):
        name = d["path"]
        low = name.lower()
        files = d.get("files", 0)
        if low in HARD_SKIP:
            rows.append({"path": name + "/", "files": files, "note": "配置/工具目录，看项目时可以跳过", "read": False})
            continue
        note, read = DIR_NOTES.get(low, ("", True))
        if not note:
            note = "其他内容" if files > 20 else "少量文件"
        rows.append({"path": name + "/", "files": files, "note": note, "read": read})
    # 建议读的排前面，跳过的沉到后面；同类里文件多的靠前
    rows.sort(key=lambda r: (not r["read"], -r["files"]))
    entries = []
    for f in root_files:
        low = f.lower()
        if low in ENTRY_NAMES and ENTRY_NAMES[low]:
            entries.append({"path": f, "why": ENTRY_NAMES[low]})
    # 真正的入口排前面，项目定义/构建脚本排后面
    entries.sort(key=lambda e: (
        0 if ("入口" in e["why"]) else 1 if ("安装" not in e["why"] and "定义" not in e["why"]) else 2,
        e["path"],
    ))
    return rows, entries


def _verdict(kind, fresh, lic, noisy, stack):
    bits = [kind["label"]]
    if fresh["level"] in ("active", "half"):
        bits.append("还在维护")
    elif fresh["level"] in ("slow", "gone"):
        bits.append("更新变慢甚至停更")
    if noisy and noisy.get("level") == "loud":
        bits.append("issue 很多，属于很热但也很吵的项目")
    if stack:
        bits.append("需要 " + " / ".join(s["name"].split("（")[0] for s in stack[:2]) + " 环境")
    return "；".join(bits) + "。"


BUTTONS = [
    {"name": "Code（绿色按钮）", "zh": "拿代码走人", "act": "唯一必点：复制 clone 地址或下 zip"},
    {"name": "Releases", "zh": "发过的成品版本", "act": "想直接用、不想编译就来这"},
    {"name": "Issues", "zh": "别人遇到过的坑", "act": "装不上、报错先在这搜"},
    {"name": "Pull requests", "zh": "别人正在改的东西", "act": "普通使用者可以忽略"},
    {"name": "Actions", "zh": "自动构建流水线", "act": "维护者看的，可忽略"},
    {"name": "Projects", "zh": "开发计划看板", "act": "可忽略"},
    {"name": "Security", "zh": "漏洞通告入口", "act": "关心安全时才点"},
    {"name": "Insights", "zh": "提交活跃度统计", "act": "想判断项目死活时可以点"},
    {"name": "Star", "zh": "收藏+点赞", "act": "给作者鼓励，不影响你能不能跑"},
    {"name": "Fork", "zh": "复制一份到你自己的账号", "act": "想改代码才需要，使用者不必点"},
    {"name": "main / Branches", "zh": "最新代码 / 历史分支", "act": "默认保持 main 就行"},
    {"name": "Tags", "zh": "打过版本号的提交", "act": "下载请走 Releases，别在这找"},
    {"name": "About 右侧的 Topics", "zh": "项目自己贴的标签", "act": "只能当关键词看，不代表质量"},
]


def _clean_title(s):
    s = re.sub(r"[`*_#]", "", s or "")
    s = re.sub(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F]", "", s)  # 去掉 emoji
    s = re.sub(r"\s{2,}", " ", s).strip(" -—·")
    return s


def split_readme_sections(readme, min_chars=40, max_sections=24):
    """按一级/二级标题切 README，忽略代码块里的 # 注释行，供前端逐节翻译。"""
    text = readme or ""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"^\s*(\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)|<img[^>]*>\s*)+$", "", text, flags=re.M)
    lines = text.splitlines()
    marks = []          # (行号, 层级, 标题)
    fence = None
    for idx, ln in enumerate(lines):
        s = ln.strip()
        m = re.match(r"^(```+|~~~+)", s)
        if m:
            token = m.group(1)[0]
            if fence is None:
                fence = token
                continue
            if fence == token:
                fence = None
            continue
        if fence is not None:
            continue
        hm = re.match(r"^(#{1,2})\s+(.+?)\s*$", ln)
        if hm:
            marks.append((idx, len(hm.group(1)), _clean_title(hm.group(2))))

    out = []
    if not marks:
        body = text.strip()
        if body:
            out.append({"i": 0, "title": "正文", "level": 1, "chars": len(body), "body": body})
        return out
    head = "\n".join(lines[: marks[0][0]]).strip()
    if len(head) >= min_chars:
        out.append({"i": 0, "title": "开头", "level": 1, "chars": len(head), "body": head})
    for k, (idx, level, title) in enumerate(marks):
        end = marks[k + 1][0] if k + 1 < len(marks) else len(lines)
        body = "\n".join(lines[idx + 1: end]).strip()
        if len(body) < min_chars:
            continue
        title = (title[:26] + "…") if len(title) > 27 else title
        out.append({"i": len(out), "title": title, "level": level, "chars": len(body), "body": body})
        if len(out) >= max_sections:
            break
    return out


def build(repo, tree, readme):
    """把 GitHub 原始数据压成前端直接可渲染的事实字典。"""
    tree_sum = {
        "top_dirs": [],
        "root_files": [],
    }
    top = {}
    root_files = []
    for item in (tree or []):
        path = item.get("path", "")
        typ = item.get("type", "")
        depth = path.count("/")
        if typ == "blob" and depth == 0:
            root_files.append(path)
        elif depth == 0 and typ == "tree":
            top.setdefault(path, 0)
        elif depth == 1 and typ == "blob":
            seg = path.split("/")[0]
            top[seg] = top.get(seg, 0) + 1
    tree_sum["top_dirs"] = [{"path": k, "files": v} for k, v in sorted(top.items(), key=lambda kv: -kv[1])]
    tree_sum["root_files"] = root_files

    root_lower = {f.lower() for f in root_files}
    stars = repo.get("stargazers_count", 0) or 0
    open_issues = repo.get("open_issues_count", 0) or 0
    kind = _kind(tree_sum, root_lower, readme)
    fresh = _freshness(repo.get("pushed_at"))
    lic = _license_info((repo.get("license") or {}).get("spdx_id"))
    stack = _stack(root_lower)
    size_mb = round((repo.get("size") or 0) / 1024.0, 1)

    noisy = None
    if stars >= 5000 and open_issues > 0:
        ratio = open_issues / max(stars, 1)
        if ratio > 0.008:
            noisy = {"level": "loud", "text": f"{open_issues} 个未关 issue，讨论很热闹，翻起来容易被淹"}
        else:
            noisy = {"level": "calm", "text": f"{open_issues} 个未关 issue，相对克制"}
    elif open_issues:
        noisy = {"level": "calm", "text": f"{open_issues} 个未关 issue"}

    hardware = None
    if HW_STRONG.search(readme or ""):
        hardware = "README 提到显卡/显存，本地跑大概率要 GPU"
    elif HW_PAT.search((readme or "")[:6000]):
        hardware = "README 出现 GPU/CUDA 字样，可能支持加速（不一定要）"

    rows, entries = _code_map(tree_sum, root_files)
    sections = split_readme_sections(readme)

    return {
        "kind": kind,
        "fresh": fresh,
        "license": lic,
        "noisy": noisy,
        "runtime": stack,
        "hardware": hardware,
        "size_mb": size_mb,
        "files": len(tree or []),
        "install_cmds": _install_cmds(readme),
        "entry": entries[:4],
        "map": rows[:12],
        "buttons": BUTTONS,
        "verdict": _verdict(kind, fresh, lic, noisy, stack),
        "readme_toc": [{"i": s["i"], "title": s["title"], "chars": s["chars"]} for s in sections],
        "repo_url": repo.get("html_url") or "",
        "default_branch": repo.get("default_branch") or "main",
    }
