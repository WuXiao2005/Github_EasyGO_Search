# GitHub EasyGO · Github中文搜

我的本意是想做一个自动抓取Github周榜和热榜并自动翻译成中文的小脚本，但是后面突发奇想，是否可以做成搜索引擎式的，由本地模型驱动的中文阅读助手
它的功能是：
每天抓一次 GitHub 的**周增量榜**（本地快照差分算出，不抓 trending 页面），交给本机 4B 小模型汉化成
能直接读的通俗中文，产出一份**搜索式内外两层浏览的日报**；再按周聚合出一份 **Obsidian 可用的 Markdown 周报**。

全程不调用豆包或任何云端模型服务——汉化推理 100% 在本机 Ollama 完成。

## 为什么不用抓 trending 页面

`github.com/trending` 在 robots.txt 里明确禁止自动访问，直接爬既不合规、也极易因改版失效。
本项目改用**官方 REST API 每日快照 `stargazers_count`**，7 天后做差得到真实周增量：

```
本周 star 增量 = 今日快照 star − 7 天前快照 star
```

好处是数据可核验、口径干净；代价是**首次运行需要 7 天预热**，这期间走"首跑模式"
（用「本周新建仓库」+「近 7 天有推送的热门仓库」两组真实数据顶上，卡片上会标来源）。

预热完成后，脚本会自动切换成真实周增量榜，无需人工干预。

## 快速开始

```powershell
cd github-weekly-digest

python run.py web        # 实时检索页：中文搜 GitHub（推荐先玩这个）
python run.py check      # 体检：Token、配额、模型、快照覆盖
python run.py daily      # 抓取 + 排名 + 汉化 + 出日报
python run.py weekly     # 聚合最近 7 份日报，出 Markdown 周报
```

实时检索页启动后会自动监听 `http://127.0.0.1:8790/`，浏览器打开即可。换端口用 `python run.py web --port 8801`。

配置：仓库里只提交 `config.example.json`，`config.json` 被 `.gitignore` 排除（里面会有本机路径和将来的 Token）。
第一次运行如果发现没有 `config.json`，会自动从示例复制一份；要填 Token 就编辑 `config.json` 的 `token`。

## 推到 GitHub

仓库已经准备好 `.gitignore`（`out/`、`data/`、`__pycache__/`、`config.json` 都不入库），
在项目根目录执行：

```powershell
git init -b main
git add -A
git status --short          # 看一眼清单：应当只有源码、README、config.example.json、.gitignore
git commit -m "feat: 中文导览 GitHub（本地模型汉化 + 一键拉取）"

# 仓库地址换成自己的（当前：https://github.com/WuXiao2005/Github-EasyGO）
git remote add origin https://github.com/WuXiao2005/Github-EasyGO.git
git push -u origin main
```

国内直连 GitHub 经常被重置，push 报 `Connection was reset` 时带上代理再推：

```powershell
git -c http.proxy=http://127.0.0.1:7890 push -u origin main
```

之后日常提交：

```powershell
git add -A; git commit -m "说明这次改了什么"; git push
```

## 两种模式

### 一、实时检索（`run.py web`）

用中文描述需求，直接搜到英文开源项目：

```
你输入：本地大模型推理
    ↓ 本地模型翻译检索词（约 2 秒）
英文检索："llm inference"
    ↓ GitHub Search API（每页 20 条，下滑自动续页）
结果：transformers / llama.cpp / vllm / airllm / BitNet …
    ↓ 批量一次模型调用，把英文描述译成夹叙夹议的中文速览（60-110 字，约 1.5 秒）
列表：中文介绍（2-3 句）+ 英文原文对照
    ↓ 点进某个仓库：顶部立刻出仓库名/描述/星数（约 0.7 秒），正文边翻边出字
详情：速览 / 它是什么 / 核心机制 / 项目结构 / 快速上手 / 术语表 …（首字约 3 秒，整篇约 10 秒）
```

要点：

- **首页两个榜**：标题下方是「热榜 / 周榜」切换按钮
  - 热榜：累计星标最多的项目（`stars:>30000` 按星标排，缓存 12 小时）。匿名配额下 GitHub 给出约 1253 个候选
  - 周榜：近 7 天**新建**的仓库里星标最高的（`created:>=今天-7天` 按星标排，缓存 6 小时）。
    这是真实可复现的信号，不依赖本地历史快照；等 `data/digest.db` 攒够 7 天快照，
    日报/周报那条链路才是严格意义的"周增量榜"
  - 两个榜都**每页 20 条、下滑自动续页**，单次最多加载 100 个（`webui.py` 里的 `FEED_CAP`）；
    GitHub 分页硬上限是 1000 条，要放开就把这个常量调大
- **检索词只取 1-3 个高频英文术语**。GitHub 把多词按 AND 处理，词越多结果越偏；
  模型被要求优先用业界缩写（`llm inference` 而不是 `local large model inference`）
- 后台不做搜索时是首页热门榜（`stars:>30000` 按星标排序，缓存 12 小时）
- 分页：每页 20 条，滑到底自动加载下一页，直到 GitHub 的 1000 条上限
- 列表中文介绍是 2-3 句、60-110 字，一次调用批量翻 14 条
- 详情走 SSE 流式：先推 `meta`（仓库名/描述/星数/协议，0.7 秒到），再逐字推 `chunk`，
  最后 `done`；配图后台下载完成后再补一张，不阻塞正文
- 详情是**按需**汉化：没点开的仓库不会被翻译，省算力
- 查询结果缓存 6 小时，同一关键词重复搜不消耗 API 配额；汉化结果按 README 指纹缓存
- 支持深链：`/?q=本地大模型推理` 自动检索，`/?q=...&repo=microsoft/BitNet` 直接打开该仓库详情

### 二、详情页：先给判断，再给翻译

点开一个仓库，页面自上而下是六块。前四块靠**规则计算**，不等模型：

| 区块 | 内容 | 来源 | 耗时 |
|---|---|---|---|
| 判断卡 | 类别（拿来用 / 拿来读 / 清单…）、活跃度状态点、协议能否商用、体积 | 仓库元数据 + 目录树 | <1 秒 |
| 我能不能跑起来 | 运行环境（Node/Python/Docker…）、硬件提示、入口文件、从 README 原样抽取的安装命令（可复制） | 根目录文件特征 + README 代码块 | <1 秒 |
| 代码地图 | 每个顶层目录一句话 + 「要看/跳过」标记 | 目录树 + 名称规则 | <1 秒 |
| 按钮导读 | GitHub 那排按钮逐个翻译成"人话 + 该不该点" | 静态表 | 0 |
| README 中文翻译 | 按章节切开，点哪节翻哪节，边翻边出字，代码块原样保留 | 模型逐节翻译 | 首字约 2 秒/节 |
| 中文解读 | 速览 / 它是什么 / 核心机制 / 项目结构 / 快速上手 / 术语表 | 模型（原有流程） | 首字约 3 秒 |

设计取舍：

- **能算的不问模型**。类别、活跃度、能不能跑、目录职责全部规则化，所以点开就有一屏有用信息，
  不会被"模型在思考"的空白卡住
- **README 不做整篇一把梭**。4B 模型翻三千字会跑偏和截断，改成按 `#` / `##` 章节切开逐节翻；
  代码块中的 `# 注释` 不会被误当成标题（切分时跟踪 ``` 围栏状态）
- 每节译文落盘缓存到 `out/search-cache/readme/`，缓存键含模型名，换模型会重译

### 三、一键拉取到本地

详情页顶部「拉取到本地」按钮，点开是一个下载面板：

1. **默认位置** `%USERPROFILE%\Doubao\repos\<owner>__<repo>`
2. **换个位置…** → 面板里直接展开**文件夹列表**（不弹任何系统窗口）：先列盘符（带剩余空间）→
   点进目录逐层往下 → 点「用这个文件夹」立刻生效，写回 `config.json` 的 `download_dir`
3. **也可以直接输入路径**，例如 `E:\repos`，点「用这个路径」生效
4. 开始拉取 → 进度条 + 实时百分比（解析 `git clone --progress` 的 stderr），可取消
5. 完成 → 「打开文件夹」，面板显示占用体积

实现细节：

- 选位置完全在网页里完成，走后端 `/api/ls_dir`（列盘符 + 列子目录，`shutil.disk_usage` 算剩余空间），
  不依赖任何系统对话框组件，所以服务跑在后台会话里也能用
- 选完会重新拉一次 `/api/clone_prep` 再渲染面板（`cache: no-store` + 时间戳），
  保证「保存位置」显示的一定是服务端的最新值

- **自动使用本机系统代理**：`git` 不读 Windows 的代理设置，直连 `github.com` 在国内经常被重置，
  所以克隆时会把 IE/Clash 那套代理（如 `http://127.0.0.1:7890`）通过 `-c http.proxy=` 传给 git；
  环境变量里已经配了代理就不重复处理
- **失败自清理**：克隆前在目标目录旁边写一个 `<目录>.digest-partial` 标记，失败或取消时清掉半成品目录
  （含只读的 `.pack` 文件，会先改可写再删），所以「重试拉取」不会被「目录已存在」挡住
- **取消**用 `taskkill /T` 连 git 子进程一起杀，否则文件被占用删不掉
- 用 `git clone --depth 1 --single-branch`：省时间也省盘，12 万提交的大仓库全量克隆会很慢
- 目标目录已存在且非空时直接报错，不会覆盖你的东西；已克隆过则显示「打开文件夹」
- **只下载代码，不执行仓库里任何脚本、不装依赖**（面板上明写了这行）
- 依赖本机 `git`（实测 2.45.1）；GitHub 直连不稳时给出重试提示

接口：

| 路径 | 说明 |
| --- | --- |
| `GET /api/search?q=&page=` | 中文查询 → 翻检索词 → 搜索，返回结果、`total` 总数与速览；`page` 从 1 开始 |
| `GET /api/hot` | 首页热榜（按累计星标），缓存 12 小时 |
| `GET /api/weekly` | 周榜：近 7 天新建的仓库里按星标排序，缓存 6 小时 |
| `POST /api/briefs` | 批量把英文描述译成中文速览，body 为 `{items:[...]}`，单次最多 14 条 |
| `GET /api/repo_stream?name=owner/repo` | SSE 流式完整汉化：`meta` → `extra`（配图）→ 若干 `chunk` → `done` / `error` |
| `GET /api/models` | 每次调用都真跑一遍 `ollama list`，返回模型名 / 参数量 / 量化 / 体积 / 修改时间 |
| `POST /api/model` | body `{"model":"名字"}`，运行时切换模型并写回 `config.json` |
| `GET /api/health` | 当前模型与 API 配额 |

> 流式接口用 `Connection: close` 收尾，前端必须在收到 `done` 后主动 `close()`，
> 否则 EventSource 会自动重连、把翻译重跑一遍。

详情页新增的接口：

| 路径 | 说明 |
|---|---|
| `GET /api/repo_stream?name=` | 事件序列现在是 `meta` → `facts`（规则层）→ 若干 `chunk` → `done` |
| `GET /api/readme_sec?name=&i=` | SSE 逐节翻译 README：`start` → `chunk` → `done`（命中缓存时直接 `done`） |
| `GET /api/clone_prep?name=` | 返回默认保存目录、目标目录、是否已克隆、体积、磁盘剩余 |
| `GET /api/clone?name=&dest=&job=` | SSE 克隆进度：`progress`（含 `pct`）→ `done` / `error` |
| `GET /api/clone_cancel?job=` | 取消正在跑的克隆（kill git 进程） |
| `GET /api/ls_dir?path=` | 列盘符 / 列子目录，给页面内文件夹浏览器用（不弹系统窗口） |
| `GET /api/set_dir?path=&name=` | 指定保存目录并重新计算目标路径（浏览器选目录、手输路径都用它） |
| `GET /api/open_folder?path=` | 在资源管理器里打开该目录 |

### 二、定时日报 + 周报（`run.py daily` / `weekly`）

每天抓一次固定候选池，7 天快照差分算真实周增量，出 HTML 日报与 Markdown 周报。见下文"日报怎么看"。

快速验证只跑 3 个仓库：

```powershell
python run.py daily --top 3
```

临时换模型（不改配置）：

```powershell
python run.py daily --model "Qwen3.5:9b-Claude-4.6-uncensored"
```

产物位置：

```
out/
├── 2026-11-15/
│   ├── 日报-2026-11-15.html     ← 双击即可看，单文件自包含
│   ├── assets/                  ← 从原仓库 README 抓下来的配图
│   └── data.json                ← 当日结构化数据，周报靠它聚合
└── 周报-2026-11-15_至_2026-11-21.md
data/digest.db                   ← 快照库 + 译文缓存
```

## 日报怎么看

**外层（列表页）**：搜索式速览。每张卡片是仓库名、一句话中文速览、来源标记、语言、星数；
**仓库 README 自带配图的，右侧显示原图缩略图；没有配图的一律不补图**，直接走通栏纯文字排版，
不做"无配图"占位框。顶部搜索框可按仓库名/语言/中文关键词过滤，也能按
「本周新建 / 近 7 天活跃 / 有周增量」切换。

**内层（详情页）**：点卡片进入，包含

| 区块 | 内容 |
| --- | --- |
| 它是什么 | 定位与形态（库 / 工具 / 模板 / 数据集） |
| 解决什么问题 | 它替代了什么旧做法 |
| 核心机制 | 用打比方的方式讲实现原理 |
| 主要功能 | 3-6 条中文功能清单 |
| 项目结构解读 | 目录/文件到作用的映射，用来快速摸清代码地图 |
| 快速上手 | 关键命令保持英文原文 + 中文步骤说明 |
| 值得学的点 | 工程或设计上的可借鉴之处 |
| 术语表 | README 里关键英文术语的中译与解释 |

详情页是一屏可滚动的侧栏视图，左上角「返回列表」回到外层，浏览器地址栏带 `#/r/N` 锚点。

## 网页上换模型

首页顶部那枚 `本地实时汉化 · 模型名` 是按钮，点开就是一列本机模型（名字 / 参数量 / 量化 / 体积 / 下载时间），点一下即切换。

- **每次打开都重新执行 `ollama list`**，不是读缓存。新 `ollama pull` 下来的模型，刷新面板就能看到，不用重启服务。- 选中后运行时立即生效（`Localizer.model` 换掉），同时写回 `config.json`，下次启动还是这个模型。
- 参数量 ≥ 8B 的条目会用琥珀色标注「可能吃力」——6GB 显存能加载但生成会明显变慢，不拦你选。
- 切换后新请求走新模型；**已经点开的详情如果正在流式翻译，会沿用旧模型跑完**（避免中途换模型打断）。
- 速览/详解缓存按「仓库 + README 指纹 + 模型名」存，换模型不会读到别的模型写的译文。

## 配置项（config.json）

| 字段 | 说明 |
| --- | --- |
| `token` | GitHub PAT。留空也能跑：匿名 60 次/小时，单日一轮约 10-15 次调用，够用；填了给 5000/小时，可跑更大候选池。也支持写 `"env:GITHUB_TOKEN"` 从环境变量取 |
| `model` | 本地 Ollama 模型名，默认 `maternion/spark-x2.5-heretic:4b` |
| `top_n` | 每日入榜条数，默认 8 |
| `pool_new_repos` / `pool_active_repos` | 候选池大小 |
| `window_days` | 增量窗口，默认 7 |
| `readme_chars` | 喂给模型的 README 截断长度，默认 2500 |
| `images_per_repo` | 每个仓库抓几张图 |
| `download_dir` | 「拉取到本地」的保存目录。不填就用默认 `%USERPROFILE%\Doubao\repos`；在页面上点「换个位置…」或输入路径后会自动写入这一项 |

## 模型怎么选

4B 级别模型足够胜任"读懂英文 README 再白话重写"。实测在 RTX 3060 Laptop（6GB）上：

- 4B / Q4_K_M 约 2.6-3.4GB，可全量放进显存，单篇约 30-60 秒
- 8 个仓库一轮 ≈ 5-8 分钟，凌晨跑完全无感

两个坑写在代码里了：

1. **Qwen3 系是思维链模型**，默认先输出一长串 `thinking` 再给正文，若 `num_predict` 给小了，
   正文直接为空。本项目的调用固定带 `"think": false`，并在正文为空时从 `thinking` 里抢救 JSON。
2. **结构化输出用 Ollama 的 `format` schema 约束**，把 10 个字段全部设为 required，
   避免小模型漏字段；仍然漏的话，代码会降级只用元信息渲染，不会让整份日报挂掉。
3. **半句话陷阱**：小模型常把某个字段写一半就停（例如核心机制只写"它如同给设备参数设置"）。
   `validate()` 会检查关键字段长度与句末标点，不合格自动带提示重试一次；缓存复用前也先过校验，
   避免坏译文被永久缓存。

想换模型（社区模型多为 uncensored 变体，指令遵循会差一些）：

```powershell
ollama pull qwen3:4b      # 或 qwen2.5:3b-instruct
```

然后把 `config.json` 的 `model` 改掉即可。

## 缓存与幂等

- 快照表 `snapshots(repo, day, stars, forks)` 主键去重，同一天重跑不会产生脏数据
- 译文按 `(仓库, 内容指纹)` 缓存：README、星数档位、模型名没变就直接复用，重跑几乎零算力
- 图片落到当天的 `assets/` 目录，带有效性校验（非 PNG/JPEG/GIF/WebP 一律丢弃，避免裂图）

## 目录结构

```
github-weekly-digest/
├── run.py              # CLI 入口：daily / weekly / check
├── config.json
├── core/
│   ├── github.py       # REST API 客户端、README 抓取、图片提取、目录树压缩
│   ├── store.py        # SQLite 快照库 + 译文缓存
│   ├── localize.py     # Ollama 结构化汉化（schema 约束 + 失败降级）
│   ├── pipeline.py     # 抓取 → 快照 → 排名 → 汉化 → 渲染 主流程
│   ├── render.py       # 日报 HTML（内嵌数据 + hash 路由）与周报 Markdown
│   ├── searchapp.py    # 实时检索：翻译检索词、分页搜索、榜单、速览、详情 SSE、模型切换
│   ├── facts.py        # 详情页规则层：判断卡 / 能不能跑 / 代码地图 / 按钮导读 / README 切分
│   ├── gitpull.py      # 一键拉取：目标目录、git 浅克隆进度、失败自清理、打开文件夹
│   ├── webui.py        # 前端单页（搜索、榜单、详情、模型面板）
├── tools/probe_ollama.py  # 排查模型输出问题时用的探针
└── out/ 、 data/
```

零第三方依赖，只用 Python 标准库（`urllib` / `sqlite3` / `json`），不需要 pip install。

## 已知限制

- **首跑模式不是真周增量**：预热 7 天内榜单由「本周新建」与「近 7 天活跃」构成，卡片有标记
- **实时检索依赖 GitHub 配额**：匿名只有 60 次/小时（搜索另算 10 次/分钟），
  一次搜索耗 1 次、一次详情耗 2 次，配了 Token 才够放开用
- 中文内容是**导读，不是权威翻译**：4B 级小模型偶有概括失准，关键细节请点「打开 GitHub 原仓库」核对
- 匿名 API 配额下候选池只取 100 个仓库，可能漏掉暴涨的小项目；配 Token 后可放大
- 检索词翻译是"一次成型"，若结果不理想，换个更具体的说法再搜，比反复点同一句更有效
- **GitHub 搜索最多返回 1000 条**：翻页到 1000 条后不再有下一页，界面上会写明
- 流式翻译受显存限制是单线程排队：同时点开两个仓库，第二个会等第一个翻完（`model_lock`）
- 速览/详解的旧缓存还是早期短版文案，想统一成长版可清空 `out/search-cache/` 再搜
