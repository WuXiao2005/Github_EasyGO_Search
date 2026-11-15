# Github_EasyGO_Search・GitHub 翻译搜・零基础小白直接上手

# Github-EasyGO · Search GitHub by Translation · Ready to use out of the box

用中文描述你要什么，本机模型把它变成英文检索词，搜到 GitHub 上的开源项目，再把英文 README 翻成能直接读的通俗中文 —— 全程不联网云模型，推理 100% 在你自己的电脑上。

Describe what you want in Chinese; a model on your own machine turns it into English search terms, finds open-source projects on GitHub, and translates their English READMEs into plain Chinese you can actually read — all inference stays on your computer, with no cloud model service involved.

除了网页版检索，它还带一条命令行链路：每天抓一次数据、按 7 天快照差分算真实周增量，产出 HTML 日报，再把一周的日报聚合成 Obsidian 可用的 Markdown 周报。

Besides the web search, it ships a command-line pipeline that fetches data once a day, computes real weekly star growth from 7-day snapshot deltas, renders an HTML daily digest, and aggregates a week of digests into an Obsidian-friendly Markdown report.

界面支持六种语言，右上角下拉切换，页面结构和样式不变，只换文案与模型产出的语言。

The interface speaks six languages; a dropdown in the top bar switches them, keeping layout and styling identical while swapping only the copy and the language of the model output.



***

## 前置条件 / Prerequisites

Python 3.9 以上，安装时记得勾上 Add to PATH。

Python 3.9 or newer, and tick "Add to PATH" during installation.

Ollama 是可选的：不装也能用中文搜索、判断卡、代码地图和按钮导读，但 README 翻译与中文解读会显示「本地模型不可用」。

Ollama is optional: without it you still get Chinese search, the judgement card, the code map and the button guide, but README translation and Chinese analysis will say "local model unavailable".

git 也是可选的：不装就不能用「一键拉取到本地」，只能去网页下载 ZIP。

git is optional as well: without it the one-click clone is unavailable and you download a ZIP from the web instead.



***

## 快速开始 / Quick start

第一步，把仓库拉下来。

Step one, clone the repository.



```
git clone https://github.com/WuXiao2005/Github-EasyGO.git
cd Github-EasyGO
```

第二步，装好 Ollama 并拉一个适合本机显存的模型，4B 级大约 2.5 GB。

Step two, install Ollama and pull a model that fits your VRAM; a 4B model is roughly 2.5 GB.



```
ollama pull qwen3:4b
```

Windows 上装完确认托盘里的 Ollama 正在运行；默认地址是 `127.0.0.1:11434`，改过端口就同步改 `config.json` 的 `ollama_url`。

On Windows, check that Ollama is running in the tray; its default address is `127.0.0.1:11434`, and if you changed the port, update `ollama_url` in `config.json` accordingly.

第三步，先启动一次，首次会自动从 `config.example.json` 生成 `config.json`。

Step three, launch it once; the first run copies `config.example.json` into `config.json` automatically.



```
python run.py web
```

浏览器打开 `http://127.0.0.1:8790/`。

Open `http://127.0.0.1:8790/` in your browser.

第四步，把模型名对齐：编辑 `config.json` 的 `model`，填成 `ollama list` 里真实存在的名字。

Step four, align the model name: edit `model` in `config.json` and set it to a name that actually appears in `ollama list`.

示例文件里那个名字是作者本机的模型，你机器上没有时不改会一直提示「本地模型不可用」。

The name in the sample file is the author's local model; if your machine lacks it and you do not change it, the app keeps saying "local model unavailable".

两个强烈建议：填 token，配代理。

Two strong recommendations: set a token, and configure a proxy.

填 `token` 是因为匿名访问 GitHub API 只有 60 次 / 小时，一次搜索耗 1 次、一次详情耗 2 次，填了 Personal Access Token 才能放开用。

Set `token` because anonymous GitHub API access is limited to 60 requests per hour, a search costs one and a detail view costs two, and a Personal Access Token is what lets you use it freely.

配代理是因为国内直连 `github.com` 经常被重置，clone 和 API 都会失败。

Configure a proxy because direct access to `github.com` from mainland China is frequently reset, breaking both clone and API calls.

日报和周报是命令行模式，项目本身不带定时器，想每天自动跑要自己配 Windows 任务计划或 cron 调用 `python run.py daily`。

The daily and weekly modes are command-line only and the project ships no scheduler, so for automatic daily runs you wire up Windows Task Scheduler or cron to call `python run.py daily` yourself.

另外首次运行要预热 7 天才会出真实周增量，这期间走「首跑模式」。

Also, the first run needs a 7-day warm-up before real weekly growth appears, and during that window the app runs in "first-run mode".

四条常用命令，都在项目根目录执行。

Four everyday commands, all run from the project root.



```
python run.py web        # 实时检索页：翻译搜 GitHub（推荐先玩这个）
python run.py check      # 体检：Token、配额、模型、快照覆盖
python run.py daily      # 抓取 + 排名 + 汉化 + 出日报
python run.py weekly     # 聚合最近 7 份日报，出 Markdown 周报
```



***

## 为什么不用抓 trending 页面 / Why not scrape the trending page

`github.com/trending` 在 robots.txt 里明确禁止自动访问，直接爬既不合规、也极易因改版失效。

`github.com/trending` is explicitly disallowed for automated access in robots.txt, so scraping it is both non-compliant and quick to break when the page changes.

本项目改用官方 REST API 每日快照 `stargazers_count`，7 天后做差得到真实周增量。

This project instead snapshots `stargazers_count` daily through the official REST API and diffs it after 7 days to get real weekly growth.



```
本周 star 增量 = 今日快照 star − 7 天前快照 star
Weekly star growth = today's snapshot − the snapshot from 7 days ago
```

好处是数据可核验、口径干净；代价是首次运行需要 7 天预热，这期间用「本周新建仓库」加「近 7 天有推送的热门仓库」两组真实数据顶上，卡片上会标来源。

The upside is verifiable, cleanly defined data; the cost is a 7-day warm-up on first run, during which the list is backed by "repos created this week" plus "popular repos pushed in the last 7 days", with the source labelled on every card.

预热完成后脚本自动切换成真实周增量榜，无需人工干预。

Once warm-up completes, the script switches to the real weekly growth list automatically, with no manual step.



***

## 六种界面语言 / Six interface languages

右上角下拉可选：简体中文、繁體中文、日本語、Français、Русский、한국어，选择存在 localStorage 里，刷新后仍生效。

The top-bar dropdown offers Simplified Chinese, Traditional Chinese, Japanese, French, Russian and Korean; the choice is stored in localStorage and survives a reload.

做法是「资源表 + 单一匹配层」，没有六份模板：界面壳和规则层各一套字典，加一门语言只需补两份 JSON。

It works as "resource tables plus one matcher" rather than six templates: one dictionary for the UI shell and one for the rule layer, so adding a language means adding two JSON files.

模型产出也跟随语言：先用中文写出来，再整段译成目标语言，中间有一道语言护栏判定，判错就作废重来，用户看不到「先出中文再改口」。

Model output follows the language too: it writes in Chinese first, then translates the whole block, with a language guard in between that discards and retries a mismatched attempt so users never see Chinese appear and then get corrected.

缓存按语言隔离，同一仓库切来切去不会互相污染，切回来还能命中自己那份。

Caches are per-language, so switching back and forth never cross-contaminates and returning to a language still hits its own cache.



***

## 用法一：实时检索（`run.py web`） / Live search

用中文描述需求，直接搜到英文开源项目。

Describe a need in Chinese and get English open-source projects back.



```
你输入：本地大模型推理
You type: local LLM inference
    ↓ 本地模型翻译检索词（约 2 秒）
    → the local model condenses it into search terms (about 2 seconds)
英文检索："llm inference"
    → English search: "llm inference"
    ↓ GitHub Search API（每页 20 条，下滑自动续页）
    → GitHub Search API (20 per page, loads more on scroll)
结果：transformers / llama.cpp / vllm / airllm / BitNet …
    → hits: transformers / llama.cpp / vllm / airllm / BitNet …
    ↓ 批量一次模型调用，把英文描述译成夹叙夹议的中文速览（60-110 字，约 1.5 秒）
    → one batched model call turns English descriptions into 60–110 character Chinese briefs (about 1.5 seconds)
列表：中文介绍（2-3 句）+ 英文原文对照
    → list: a 2–3 sentence Chinese brief next to the original English
    ↓ 点进某个仓库：顶部立刻出仓库名/描述/星数（约 0.7 秒），正文边翻边出字
    → open a repo: the header with name, description and stars appears at once (about 0.7 seconds), body streams in
详情：速览 / 它是什么 / 核心机制 / 项目结构 / 快速上手 / 术语表 …（首字约 3 秒，整篇约 10 秒）
    → detail: quick take, what it is, core mechanism, project structure, quick start, glossary (first characters in about 3 seconds, whole text in about 10)
```

要点。

Key points.



* 首页两个榜，标题下方「热榜 / 周榜」按钮切换。

  Two leaderboards on the home page, switched by the "hot / weekly" buttons under the title.

* 热榜是累计星标最多的项目（`stars:>30000` 按星标排，缓存 12 小时），匿名配额下 GitHub 约给出 1253 个候选。

  The hot list is the most-starred projects overall (`stars:>30000`, sorted by stars, cached 12 hours); with the anonymous quota GitHub exposes roughly 1,253 candidates.

* 周榜是近 7 天新建的仓库里星标最高的（`created:>=今天-7天` 按星标排，缓存 6 小时），这是真实可复现的信号，不依赖本地历史快照。

  The weekly list is the most-starred among repos created in the last 7 days (`created:>=today-7d`, sorted by stars, cached 6 hours), a reproducible real signal that does not depend on local snapshot history.

* 两个榜都每页 20 条、下滑自动续页，单次最多加载 100 个（`webui.py` 里的 `FEED_CAP`）。

  Both page 20 items, load more on scroll, and cap at 100 items per session (`FEED_CAP` in `webui.py`).

* 检索词只取 1–3 个高频英文术语，因为 GitHub 把多词按 AND 处理，词越多结果越偏。

  The query is reduced to 1–3 high-frequency English terms, because GitHub ANDs multiple words and more words skews the results.

* 模型被要求优先用业界缩写（`llm inference` 而不是 `local large model inference`）。

  The model is instructed to prefer industry abbreviations (`llm inference` over `local large model inference`).

* 列表中文介绍是 2–3 句、60–110 字，一次调用批量翻 14 条。

  List briefs run 2–3 sentences and 60–110 characters, translated 14 at a time in one call.

* 详情走 SSE 流式：先推 `meta`（仓库名 / 描述 / 星数 / 协议，约 0.7 秒），再逐字推 `chunk`，最后 `done`。

  Detail uses SSE: `meta` first (name, description, stars, licence at about 0.7 seconds), then character-by-character `chunk`s, then `done`.

* 配图在后台下载完成后补一张，不阻塞正文。

  One illustration is appended once the background download finishes, without blocking the text.

* 详情是按需汉化：没点开的仓库不会被翻译，省算力。

  Detail translation is on demand: unopened repos are never translated, saving compute.

* 查询结果缓存 6 小时，同一关键词重复搜不消耗 API 配额；汉化结果按 README 指纹缓存。

  Search results are cached 6 hours so repeating a keyword costs no API quota, and translations are cached by a README fingerprint.

* 支持深链：`/?q=本地大模型推理` 自动检索，`/?q=...&repo=microsoft/BitNet` 直接打开该仓库详情。

  Deep links work: `/?q=...` searches automatically and `/?q=...&repo=microsoft/BitNet` opens that repo's detail directly.



***

## 用法二：详情页六块（先给判断，再给翻译） / Six detail blocks

点开一个仓库，页面自上而下是六块，前四块靠规则计算，不等模型。

Open a repo and the page reads as six blocks top to bottom, with the first four computed by rules rather than waiting on the model.



| 区块 / Block                     | 内容 / Content                                                                                                                                      | 来源 / Source                                                   | 耗时 / Time                          |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- | ---------------------------------- |
| 判断卡 / Judgement card           | 类别（拿来用 / 拿来读 / 清单）、活跃度状态点、协议能否商用、体积。 / Category (use it, read it, a list), activity dot, commercial-use licence, size.                            | 仓库元数据 + 目录树 /repo metadata and tree                           | <1 秒 / <1s                         |
| 我能不能跑起来 / Can I run it         | 运行环境、硬件提示、入口文件、从 README 原样抽取的安装命令（可复制）。 / Runtime, hardware notes, entry files, install commands copied verbatim from the README.                 | 根目录文件特征 + README 代码块 /root-file traits and README code blocks | <1 秒 / <1s                         |
| 代码地图 / Code map                | 每个顶层目录一句话，加「要看 / 跳过」标记。 / One sentence per top-level directory, marked read or skip.                                                              | 目录树 + 名称规则 /tree and naming rules                             | <1 秒 / <1s                         |
| 按钮导读 / Button guide            | GitHub 那排按钮逐个翻成「人话 + 该不该点」。 / Each GitHub button explained in plain words with whether to click it.                                               | 静态表 /static table                                             | 0                                  |
| README 翻译 / README translation | 按章节切开，点哪节翻哪节，边翻边出字，代码块原样保留。 / Split by section, translate the one you click, streaming, code blocks untouched.                                    | 模型逐节翻译 /per-section model translation                         | 首字约 2 秒 / 节 / \~2s per section     |
| 中文解读 / Chinese analysis        | 速览 / 它是什么 / 核心机制 / 项目结构 / 快速上手 / 术语表等十段固定结构。 / Ten fixed fields such as quick take, what it is, core mechanism, structure, quick start, glossary. | 模型 /model                                                     | 首字约 3 秒 / \~3s to first characters |

设计取舍有三条。

Three design decisions behind it.



* 能算的不问模型：类别、活跃度、能不能跑、目录职责全部规则化，所以点开就有一屏有用信息，不会被「模型在思考」的空白卡住。

  Never ask the model what can be computed: category, activity, runnability and directory duties are all rule-based, so opening a repo immediately yields a useful screen instead of a blank "thinking" state.

* README 不做整篇一把梭：4B 模型翻三千字会跑偏和截断，改成按 `#` / `##` 章节切开逐节翻。

  Never translate the whole README in one shot: a 4B model drifts and truncates past a few thousand characters, so it is split on `#` / `##` headings and translated section by section.

* 切分时跟踪 ``围栏状态，代码块里的 `# 注释` 不会被误当成标题。  ``

  `The splitter tracks` fences, so `# comments` inside code blocks are never mistaken for headings.

每节译文落盘缓存在 `out/search-cache/readme/`，缓存键含模型名和语言，换模型会重译。

Each section translation is cached under `out/search-cache/readme/`, keyed by model name and language, so switching models re-translates.



***

## 用法三：一键拉取到本地 / One-click clone

详情页顶部「拉取到本地」按钮点开是一个下载面板。

The "clone to local" button at the top of the detail view opens a download panel.



1. 默认位置是项目目录下的 `repos\<owner>__<repo>`，以 `config.json` 的 `download_dir` 为准。

   The default location is `repos\<owner>__<repo>` under the project directory, driven by `download_dir` in `config.json`.

2. 「换个位置…」会在面板里直接展开文件夹列表，不弹任何系统窗口：先列盘符（带剩余空间），点进目录逐层往下，点「用这个文件夹」立刻生效，写回 `config.json`。

   "Change location" expands a folder list inside the panel with no system dialog: drives first (with free space), drill down level by level, and "use this folder" takes effect at once and is written back to `config.json`.

3. 也可以直接输入路径，例如 `E:\repos`，点「用这个路径」生效。

   You can also type a path such as `E:\repos` and press "use this path".

4. 开始拉取后是进度条加实时百分比，可随时取消。

   Once cloning starts you get a progress bar with a live percentage, cancellable at any moment.

5. 完成后「打开文件夹」，面板显示占用体积。

   When it finishes, "open folder" appears and the panel shows the size on disk.

实现上有六个细节。

Six implementation details.



* 选位置完全在网页里完成，走后端 `/api/ls_dir`（列盘符 + 列子目录，`shutil.disk_usage` 算剩余空间），不依赖系统对话框，所以服务跑在后台会话里也能用。

  Folder selection happens entirely in the page via `/api/ls_dir` (drives, subdirectories, free space from `shutil.disk_usage`), with no system dialog, so it also works when the service runs in a background session.

* 选完会重新拉一次 `/api/clone_prep` 再渲染面板，保证「保存位置」显示的一定是服务端的最新值。

  After choosing, the panel refetches `/api/clone_prep` before rendering, so the displayed save location is always the server's latest value.

* 克隆时把 IE/Clash 那套系统代理通过 `-c http.proxy=` 传给 git，因为 git 不读 Windows 的代理设置；环境变量里已配代理就不重复处理。

  The system proxy from IE or Clash is passed to git via `-c http.proxy=` because git ignores Windows proxy settings, and an already configured proxy environment variable is not overridden.

* 克隆前在目标目录旁边写一个 `<目录>.digest-partial` 标记，失败或取消时清掉半成品目录（含只读的 `.pack` 文件），所以「重试拉取」不会被「目录已存在」挡住。

  A `<dir>.digest-partial` marker is written next to the target before cloning and the half-done directory is removed on failure or cancellation, including read-only `.pack` files, so retrying is never blocked by an existing directory.

* 取消用 `taskkill /T` 连 git 子进程一起杀，否则文件被占用删不掉。

  Cancellation uses `taskkill /T` to kill the git child process too, otherwise locked files cannot be removed.

* 用 `git clone --depth 1 --single-branch` 省时间省盘；目标目录已存在且非空时直接报错，不覆盖你的东西。

  The clone uses `git clone --depth 1 --single-branch` to save time and disk, and an existing non-empty target raises an error instead of overwriting your files.

面板上明写着一行：只下载代码，不执行仓库里任何脚本、不装依赖。

The panel states it explicitly: it only downloads code and never runs any script from the repo nor installs dependencies.



***

## 用法四：定时日报 + 周报（`run.py daily` / `weekly`） / Daily digest and weekly report

每天抓一次固定候选池，7 天快照差分算真实周增量，出 HTML 日报与 Markdown 周报。

Each run fetches a fixed candidate pool, computes real weekly growth from 7-day snapshot deltas, and renders an HTML digest plus a Markdown report.

快速验证只跑 3 个仓库，临时换模型不改配置。

For a quick check run only 3 repos, and switch models temporarily without touching the config.



```
python run.py daily --top 3
python run.py daily --model "Qwen3.5:9b-Claude-4.6-uncensored"
```

产物位置。

Where the output lands.



```
out/
├── 2026-11-15/
│   ├── 日报-2026-11-15.html     ← 双击即可看，单文件自包含 / single file, just double-click
│   ├── assets/                  ← 从原仓库 README 抓下来的配图 / images from the repo README
│   └── data.json                ← 当日结构化数据，周报靠它聚合 / structured data the weekly report aggregates
└── 周报-2026-11-15_至_2026-11-21.md
data/digest.db                   ← 快照库 + 译文缓存 / snapshots plus translation cache
```

日报怎么看：外层是列表页，每张卡片是仓库名、一句话中文速览、来源标记、语言、星数。

How to read the digest: the outer layer is a list where each card shows the repo name, a one-line Chinese brief, a source label, the language and the star count.

README 自带配图的在右侧显示原图缩略图；没有配图的一律走通栏纯文字排版，不做「无配图」占位框。

Repos whose README ships images get a thumbnail on the right; the rest use a full-width text layout with no empty placeholder frame.

顶部搜索框可按仓库名、语言、中文关键词过滤，也能按「本周新建 / 近 7 天活跃 / 有周增量」切换。

The search box on top filters by repo name, language or Chinese keyword, and you can switch between "created this week", "active in the last 7 days" and "has weekly growth".

内层是详情页，点卡片进入，包含它是什么、解决什么问题、核心机制、主要功能、项目结构解读、快速上手、值得学的点、术语表。

The inner layer is the detail view you reach by clicking a card, covering what it is, what problem it solves, core mechanism, main features, project structure, quick start, what is worth learning and a glossary.

详情页是一屏可滚动的侧栏视图，左上角「返回列表」回到外层，地址栏带 `#/r/N` 锚点。

The detail view is a single scrollable side panel, "back to list" in the top-left returns to the outer layer, and the address bar carries a `#/r/N` anchor.



***

## 网页上换模型 / Switching models in the page

首页顶部那枚「本地实时翻译・模型名」是按钮，点开就是一列本机模型（名字 / 参数量 / 量化 / 体积 / 下载时间），点一下即切换。

The "local live translation · model name" chip at the top of the home page is a button; it expands into a list of local models with parameter count, quantisation, size and download time, and one click switches.

每次打开都重新执行 `ollama list`，不是读缓存，新 `pull` 下来的模型刷新面板就能看到，不用重启服务。

It runs a real `ollama list` every time rather than reading a cache, so a freshly pulled model shows up on refresh without restarting the service.

选中后运行时立即生效，同时写回 `config.json`，下次启动还是这个模型。

The switch takes effect at once and is written back to `config.json`, so the next launch uses the same model.

参数量 ≥ 8B 的条目用琥珀色标注「可能吃力」——6 GB 显存能加载但生成会明显变慢，不拦你选。

Entries with 8B parameters or more get an amber "may be slow" note: 6 GB of VRAM can load them but generation slows noticeably, and the choice is not blocked.

切换后新请求走新模型；已经点开的详情如果正在流式翻译，会沿用旧模型跑完，避免中途换模型打断。

New requests use the new model after a switch, while an in-flight stream finishes on the old model so it is never interrupted.

速览和详解缓存按「仓库 + README 指纹 + 模型名 + 语言」存，换模型不会读到别的模型写的译文。

Brief and analysis caches key on repo, README fingerprint, model name and language, so switching models never reads translations written by another one.



***

## 配置项（`config.json`） / Configuration

仓库里只提交 `config.example.json`，`config.json` 被 `.gitignore` 排除，里面会有本机路径和 Token。

Only `config.example.json` is committed; `config.json` is git-ignored because it holds local paths and your token.

第一次运行如果发现没有 `config.json`，会自动从示例复制一份。

On first run, if `config.json` is missing, it is copied from the sample automatically.



| 字段 / Field              | 说明 / Meaning                                                                                                                                                                                                                                                                                            | 默认 / Default                      |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| `token`                 | GitHub PAT。留空也能跑：匿名 60 次 / 小时，单日一轮约 10–15 次调用；填了给 5000 / 小时，可跑更大候选池。也支持 `"env:GITHUB_TOKEN"` 从环境变量取。 / GitHub PAT. Empty still works at 60 requests/hour (a daily round costs about 10–15); a token raises it to 5000/hour and allows a wider pool. `"env:GITHUB_TOKEN"` reads it from the environment. | 空 /empty                          |
| `model`                 | 本地 Ollama 模型名。 / Local Ollama model name.                                                                                                                                                                                                                                                               | `maternion/spark-x2.5-heretic:4b` |
| `ollama_url`            | Ollama 服务地址。 / Ollama endpoint.                                                                                                                                                                                                                                                                         | `http://127.0.0.1:11434`          |
| `top_n`                 | 每日入榜条数。 / Repos per daily list.                                                                                                                                                                                                                                                                         | `8`                               |
| `pool_new_repos`        | 「本周新建」候选池大小。 / Pool size for "created this week".                                                                                                                                                                                                                                                       | `50`                              |
| `pool_active_repos`     | 「近 7 天活跃」候选池大小。 / Pool size for "active in the last 7 days".                                                                                                                                                                                                                                            | `50`                              |
| `new_repo_min_stars`    | 新建仓库星标门槛。 / Star threshold for new repos.                                                                                                                                                                                                                                                               | `5`                               |
| `active_repo_min_stars` | 活跃仓库星标门槛。 / Star threshold for active repos.                                                                                                                                                                                                                                                            | `2000`                            |
| `window_days`           | 增量窗口天数。 / Growth window in days.                                                                                                                                                                                                                                                                        | `7`                               |
| `readme_chars`          | 喂给模型的 README 截断长度。 / README characters fed to the model.                                                                                                                                                                                                                                                | `2500`                            |
| `images_per_repo`       | 每个仓库抓几张图。 / Images per repo.                                                                                                                                                                                                                                                                            | `2`                               |
| `out_dir` / `data_dir`  | 产物目录 / 数据目录，相对路径按项目根解析。 / Output and data directories; relative paths resolve against the project root.                                                                                                                                                                                                 | `out` / `data`                    |
| `timeout`               | 单次 HTTP 超时秒数。 / Per-request HTTP timeout.                                                                                                                                                                                                                                                               | `30`                              |
| `download_dir`          | 「拉取到本地」的保存目录，页面上选完会自动写回。 / Clone destination, written back when you pick a folder in the page.                                                                                                                                                                                                          | `repos`                           |

Token 只勾 `public_repo` 一项就够，其余都不要勾。

Tick only `public_repo` when creating the token; nothing else is needed.



***

## 接口一览 / API reference



| 路径 / Path                            | 说明 / Meaning                                                                                                                                                 |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `GET /api/search?q=&page=&lang=`     | 中文查询 → 翻检索词 → 搜索，返回结果、`total` 与速览。 / Chinese query, term condensation, search; returns results, `total` and briefs.                                          |
| `GET /api/hot?page=&lang=`           | 首页热榜（按累计星标），缓存 12 小时。 / Hot list by total stars, cached 12 hours.                                                                                            |
| `GET /api/weekly?page=&lang=`        | 周榜：近 7 天新建仓库按星标排，缓存 6 小时。 / Weekly list of repos created in the last 7 days by stars, cached 6 hours.                                                        |
| `POST /api/briefs`                   | 批量把英文描述译成速览，body 为 `{items:[...], lang}`，单次最多 14 条。 / Batch-translate descriptions into briefs; body `{items, lang}`, up to 14 items.                        |
| `GET /api/repo_stream?name=&lang=`   | SSE 完整汉化：`meta` → `facts` → 若干 `chunk` → `done`。 / SSE full translation: `meta`, `facts`, `chunk`s, `done`.                                                  |
| `GET /api/readme_sec?name=&i=&lang=` | SSE 逐节翻译 README：`start` → `chunk` → `done`，命中缓存直接 `done`。 / SSE per-section README translation: `start`, `chunk`, `done`, straight to `done` on a cache hit. |
| `GET /api/models`                    | 真跑一遍 `ollama list`，返回模型名 / 参数量 / 量化 / 体积 / 时间。 / Runs a real `ollama list` and returns names, parameter counts, quantisation, size and time.                 |
| `POST /api/model`                    | body `{"model":"名字"}`，运行时切换并写回配置。 / Body `{"model": "..."}`; switches at runtime and writes back to the config.                                              |
| `GET /api/health`                    | 当前模型与 API 配额。 / Current model and API quota.                                                                                                                 |
| `GET /api/clone_prep?name=`          | 默认保存目录、目标目录、是否已克隆、体积、磁盘剩余。 / Default destination, target, whether cloned, size and free space.                                                               |
| `GET /api/clone?name=&dest=&job=`    | SSE 克隆进度：`progress`（含 `pct`）→ `done` / `error`。 / SSE clone progress: `progress` with `pct`, then `done` or `error`.                                         |
| `GET /api/clone_cancel?job=`         | 取消正在跑的克隆（kill git 进程）。 / Cancel a running clone by killing the git process.                                                                                  |
| `GET /api/ls_dir?path=`              | 列盘符 / 列子目录，给页面内文件夹浏览器用。 / List drives and subdirectories for the in-page folder picker.                                                                      |
| `GET /api/set_dir?path=&name=`       | 指定保存目录并重算目标路径，选目录和手输路径都走它。 / Set the destination and recompute the target; used by both the picker and manual input.                                         |
| `GET /api/open_folder?path=`         | 在资源管理器里打开该目录。 / Open the directory in Explorer.                                                                                                              |

流式接口用 `Connection: close` 收尾，前端必须在收到 `done` 后主动 `close()`，否则 EventSource 会自动重连、把翻译重跑一遍。

Streaming endpoints end with `Connection: close`, so the frontend must call `close()` after `done`; otherwise EventSource reconnects and re-runs the translation.



***

## 模型怎么选 / Choosing a model

4B 级别模型足够胜任「读懂英文 README 再白话重写」。

A 4B model is enough for "read an English README and rewrite it in plain Chinese".

实测在 RTX 3060 Laptop（6 GB）上，4B / Q4\_K\_M 约 2.6–3.4 GB，可全量放进显存，单篇约 30–60 秒。

Measured on an RTX 3060 Laptop (6 GB): a 4B Q4\_K\_M model takes about 2.6–3.4 GB, loads entirely into VRAM, and handles one repo in about 30–60 seconds.

8 个仓库一轮约 5–8 分钟，凌晨跑完全无感。

A round of 8 repos takes roughly 5–8 minutes, which is painless when scheduled overnight.

三个坑已经写在代码里了。

Three pitfalls are already handled in the code.



1. Qwen3 系是思维链模型，默认先输出一长串 `thinking` 再给正文，`num_predict` 给小了正文直接为空；本项目固定带 `"think": false`，并在正文为空时从 `thinking` 里抢救 JSON。

   Qwen3 models are chain-of-thought by default and emit a long `thinking` block first, so a small `num_predict` leaves the body empty; this project always sends `"think": false` and salvages JSON from `thinking` when the body is empty.

2. 结构化输出用 Ollama 的 `format` schema 约束，把 10 个字段全部设为 required；仍然漏字段的话，代码降级只用元信息渲染，不会让整份日报挂掉。

   Structured output is constrained by an Ollama `format` schema marking all ten fields required; if fields are still missing, the renderer degrades to metadata only rather than failing the whole digest.

3. 半句话陷阱：小模型常把某个字段写一半就停，`validate()` 检查关键字段长度与句末标点，不合格自动带提示重试一次；缓存复用前也先过校验，避免坏译文被永久缓存。

   The half-sentence trap: small models stop mid-field, so `validate()` checks key field length and closing punctuation, retries once with a hint, and re-validates cached text before reuse so bad translations are never cached forever.

外语文案的阈值另有一套：中文仍按字数下限把关，外语只守「它是什么」「核心机制」两个核心字段，免得一份合格的法语或日语译文被中文字数标准拦在缓存外面。

Foreign-language text is validated by a different rule: Chinese keeps its minimum lengths, while other languages only enforce the two core fields, so a valid French or Japanese translation is never rejected by Chinese length heuristics and regenerated every time.

想换模型就拉一个再改配置。

To change models, pull one and update the config.



```
ollama pull qwen3:4b      # 或 / or qwen2.5:3b-instruct
```

社区模型多为 uncensored 变体，指令遵循会差一些，译文风格可能更飘。

Community models are often uncensored variants with weaker instruction following, so the style may drift more.



***

## 缓存与幂等 / Caching and idempotency

快照表 `snapshots(repo, day, stars, forks)` 主键去重，同一天重跑不产生脏数据。

The `snapshots(repo, day, stars, forks)` table is deduplicated by primary key, so rerunning on the same day leaves no dirty rows.

译文按「仓库 + 内容指纹」缓存：README、星数档位、模型名、语言没变就直接复用，重跑几乎零算力。

Translations cache on repo plus a content fingerprint: unchanged README, star bucket, model name and language mean instant reuse, so reruns cost almost nothing.

数据库一共四张表：`snapshots` 快照、`repos` 元数据、`localizations` 译文、`queries` 搜索缓存。

The database has four tables: `snapshots`, `repos` for metadata, `localizations` for translations and `queries` for search caching.

分节译文文件名是 `{repo}__{model}__{lang}__s{i}.md`，列表速览是 `{repo}.{lang}.brief`（中文沿用无后缀的旧文件）。

Section translations are named `{repo}__{model}__{lang}__s{i}.md` and briefs are `{repo}.{lang}.brief`, with Chinese reusing the older suffix-free file.

图片落到当天的 `assets/` 目录，带有效性校验，非 PNG / JPEG / GIF / WebP 一律丢弃，避免裂图。

Images land in that day's `assets/` directory with validation that drops anything not PNG, JPEG, GIF or WebP, preventing broken pictures.



***

## 目录结构 / Project layout



```
Github-EasyGO/
├── run.py                  # CLI 入口：web / daily / weekly / check
├── config.example.json     # 配置示例（config.json 不入库）
├── README.md               # 本文件：项目说明
├── core/
│   ├── github.py           # REST API 客户端、README 抓取、配图提取、目录树压缩
│   ├── store.py            # SQLite：快照 / 元数据 / 译文 / 查询
│   ├── localize.py         # Ollama 结构化汉化：schema 约束、半句话校验、失败降级
│   ├── pipeline.py         # 抓取 → 快照 → 排名 → 汉化 → 渲染，含 signature 指纹
│   ├── render.py           # 日报 HTML 与周报 Markdown
│   ├── searchapp.py        # 实时检索：检索词翻译、分页、榜单、速览、详情 SSE、语言护栏
│   ├── facts.py            # 详情页规则层：判断卡 / 能不能跑 / 代码地图 / 按钮导读 / README 切分
│   ├── gitpull.py          # 一键拉取：浅克隆进度、取消、失败自清理、打开文件夹
│   ├── server.py           # 本地 HTTP 服务与全部 /api 路由、SSE 收尾
│   ├── webui.py            # 前端单页：搜索、榜单、详情抽屉、模型面板、语言下拉
│   └── i18n.py             # 语言包：语言码归一、两套字典、注入前端 payload
├── locales/                # 界面壳字典 zh-Hant / ja / fr / ru / ko
│   └── facts/              # 规则层字典六份（含 zh-Hans 恒等映射）
├── tools/
│   ├── check_i18n.py       # i18n 自检：两套字典键对得上源码 + 内联 JS 语法
│   └── probe_ollama.py     # 模型输出排查探针
├── data/                   # digest.db（不入库）
└── out/                    # 日报、周报、缓存（不入库）
```

四个最容易混的文件，职责分清楚。

Four files are easiest to confuse, so here is who owns what.

`searchapp.py` 是后端业务核心，检索、榜单、详情流式、拉取、模型切换都在它；`webui.py` 只是它前面的那张脸。

`searchapp.py` is the backend core for search, feeds, detail streaming, cloning and model switching, while `webui.py` is just the face in front of it.

`facts.py` 负责「不用模型也能说清楚」的部分，所以它必须快，且任何时候都不许等模型。

`facts.py` owns everything explainable without the model, so it must be fast and must never wait on the model.

`i18n.py` 只管查表和归一语言码，不掺业务判断，界面壳和规则层是两套独立字典。

`i18n.py` only does lookups and language-code normalisation with no business logic, and the UI shell and rule layer are two independent dictionaries.

`localize.py` 是日报链路的批量汉化，`searchapp.py` 里的流式路径是网页链路的即时翻译，两者共用一个 Ollama 地址但互不干扰。

`localize.py` is the batch translation used by the digest pipeline while the streaming path in `searchapp.py` serves the web app; they share one Ollama endpoint without interfering.

零第三方依赖，只用 Python 标准库（`urllib` / `sqlite3` / `json` / `hashlib`），不需要 `pip install`。

There are no third-party dependencies; only the Python standard library is used (`urllib`, `sqlite3`, `json`, `hashlib`), so no `pip install` is needed.



***

## 开发自检 / Developer checks

改完文案或语言包，跑一次一致性自检。

After editing copy or language packs, run the consistency check.



```
python tools\check_i18n.py
```

它检查三件事：界面壳的键能否在模板里原样找到、规则层的键是否与源码一致、内联 JS 是否语法正确。

It verifies three things: UI-shell keys exist verbatim in the template, rule-layer keys match the source, and the inline JS is syntactically valid.

模型输出可疑时，用探针带上模型名问一次 Ollama，看它到底返回了什么。

When model output looks wrong, run the probe with the model name to see what Ollama actually returned.



```
python tools\probe_ollama.py "maternion/spark-x2.5-heretic:4b"
```



***

## 推到 GitHub / Pushing to GitHub

`.gitignore` 已经排除了 `out/`、`data/`、`__pycache__/`、`config.json`。

`.gitignore` already excludes `out/`, `data/`, `__pycache__/` and `config.json`.

日常提交就是三行，国内直连被重置时带代理推。

Everyday commits are three lines, and when the direct connection is reset, push through the proxy.



```
git add -A; git commit -m "说明这次改了什么"; git push

# 直连失败时 / when the direct connection fails
git -c http.proxy=http://127.0.0.1:7890 push
```



***

## 常见问题 / FAQ

页面打开了但内容没变：多半是进程没重启，模板是启动时一次性读进内存的，重启加 Ctrl+F5 即可。

The page opens but nothing changed: the process was probably not restarted; the template is read once at startup, so restart and press Ctrl+F5.

详情页打不开、日志出现 `[限流] 等待 120s 后重试`：GitHub 匿名配额用完了，等一小时或配一个 PAT。

The detail view will not open and the log says `[rate limit] retrying after 120s`: the anonymous GitHub quota is exhausted, so wait an hour or configure a PAT.

`python run.py` 报找不到文件：在 `core\` 目录里跑了，回到项目根目录再执行。

`python run.py` complains about a missing file: it was run inside `core\`, so go back to the project root.

拉取报 `Recv failure: Connection was reset`：直连被重置，挂代理后点「重试拉取」。

The clone fails with `Recv failure: Connection was reset`: the direct connection was reset, so enable the proxy and retry.

想清空缓存重来：删 `out/search-cache/` 和 `data/digest.db` 里的 `localizations` 行，但快照别删，删了要重新预热 7 天。

To wipe caches and start over: delete `out/search-cache/` and the `localizations` rows in `data/digest.db`, but keep the snapshots, since deleting them restarts the 7-day warm-up.



***

## 已知限制 / Known limitations

首跑模式不是真周增量：预热 7 天内的榜单由「本周新建」与「近 7 天活跃」构成，卡片上有标记。

First-run mode is not real weekly growth: during the 7-day warm-up the list is built from "created this week" and "active in the last 7 days", with a label on each card.

实时检索依赖 GitHub 配额：匿名只有 60 次 / 小时，搜索另算 10 次 / 分钟，一次搜索耗 1 次、一次详情耗 2 次。

Live search depends on the GitHub quota: 60 requests per hour anonymously plus a separate 10 per minute for search, where a search costs one and a detail costs two.

中文内容是导读，不是权威翻译：4B 级小模型偶有概括失准，关键细节请点「打开 GitHub 原仓库」核对。

The Chinese text is a guide, not an authoritative translation: a 4B model occasionally summarises inaccurately, so verify critical details via "open the original repo".

匿名配额下候选池只取 100 个仓库，可能漏掉暴涨的小项目，配 Token 后可放大。

Under the anonymous quota the candidate pool is about 100 repos and may miss fast-rising small projects; a token lets you widen it.

检索词翻译是一次成型，结果不理想就换个更具体的说法再搜，比反复点同一句更有效。

Query condensation is single-shot, so if results disappoint, rephrase more specifically rather than clicking the same query again.

GitHub 搜索最多返回 1000 条，翻到上限后没有下一页，界面上会写明。

GitHub search returns at most 1000 results, so pagination stops there and the UI says so.

流式翻译受显存限制是单线程排队，同时点开两个仓库，第二个会等第一个翻完。

Streaming translation is serialised by VRAM limits, so opening two repos at once makes the second wait for the first.

外语文案偶尔夹几个中文词，是 4B 模型译长句时的抖动，换更大的模型可明显改善。

Foreign-language copy occasionally leaks a few Chinese words, an artefact of the 4B model on long sentences that a larger model clearly improves.

速览和详解的旧缓存还是早期短版文案，想统一成长版可清空 `out/search-cache/` 再搜。

Old brief and analysis caches may still hold earlier short versions; to unify them into the longer format, clear `out/search-cache/` and search again.
