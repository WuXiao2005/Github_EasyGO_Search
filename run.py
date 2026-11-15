"""GitHub 中文导览 —— 两种用法：

    python run.py web              启动实时检索页（中文搜 GitHub + 即时汉化）
    python run.py web --port 8790  指定端口

    python run.py daily            抓取 + 排名 + 汉化 + 生成日报
    python run.py daily --top 5    只处理前 5 个，用于快速验证
    python run.py weekly           把最近 7 份日报聚合成 Markdown
    python run.py check            检查 Token、配额、本地模型

全程离线推理：只访问 GitHub API / raw.githubusercontent.com 拉数据，
汉化一律在本机 Ollama，不调用任何云端模型服务。
"""
import argparse
import json
import os
import shutil
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from core.pipeline import run_daily
from core.render import render_weekly
from core.localize import Localizer


def load_cfg(args):
    config_path = os.path.join(BASE, "config.json")
    # 新克隆下来的仓库里没有 config.json（它被 .gitignore 排除），
    # 自动从 config.example.json 复制一份，省得先报错再手抄
    if not os.path.isfile(config_path):
        example = os.path.join(BASE, "config.example.json")
        if os.path.isfile(example):
            shutil.copyfile(example, config_path)
    with open(config_path, encoding="utf-8") as f:
        cfg = json.load(f)
    cfg["config_path"] = config_path
    for key in ("out_dir", "data_dir"):
        if not os.path.isabs(cfg[key]):
            cfg[key] = os.path.join(BASE, cfg[key])
    base_dir = cfg.get("download_dir") or "repos"
    if not os.path.isabs(base_dir):
        cfg["download_dir"] = os.path.join(BASE, base_dir)
    token = cfg.get("token") or ""
    if token.startswith("env:"):
        cfg["token"] = os.environ.get(token[4:], "")
    if args.top:
        cfg["top_n"] = args.top
    if args.model:
        cfg["model"] = args.model
    return cfg


def cmd_check(cfg):
    from core.github import GitHubClient
    from core.store import Store

    print("== 配置 ==")
    print(f"  模型：{cfg['model']}  ->  {cfg['ollama_url']}")
    print(f"  输出：{cfg['out_dir']}")
    print(f"  Token：{'已配置' if cfg.get('token') else '未配置（匿名限 60 次/小时，单日一轮约 15 次，够用）'}")

    print("== 本地模型 ==")
    loc = Localizer(cfg["model"], cfg["ollama_url"], log=lambda *_: None)
    names = loc.available()
    if not names:
        print("  [X] Ollama 连不上，确认 ollama 服务在跑")
    else:
        print(f"  已装模型：{', '.join(names)}")
        print(f"  [{'OK' if loc.ensure_model() else 'X'}] 目标模型 {cfg['model']} " + ("可用" if loc.ensure_model() else "缺失"))

    print("== GitHub 配额 ==")
    client = GitHubClient(cfg.get("token", ""), cfg.get("timeout", 30), log=lambda *_: None)
    try:
        data = client.api("/rate_limit")
        core = (data or {}).get("resources", {}).get("core", {})
        search = (data or {}).get("resources", {}).get("search", {})
        print(f"  core：{core.get('remaining')}/{core.get('limit')}（重置 {core.get('reset')}）")
        print(f"  search：{search.get('remaining')}/{search.get('limit')}")
    except Exception as e:
        print(f"  [X] 查询失败：{e}")

    print("== 快照覆盖 ==")
    store = Store(cfg["data_dir"])
    first, last, rows, days = store.coverage()
    print(f"  {rows} 条快照，覆盖 {days} 天（{first} ~ {last}）")
    if days < cfg["window_days"]:
        print(f"  还差 {cfg['window_days'] - days} 天才够算真实周增量，当前走首跑模式")
    store.close()


def main():
    ap = argparse.ArgumentParser(description="GitHub 周榜中文导览")
    ap.add_argument("cmd", choices=["web", "daily", "weekly", "check"], nargs="?", default="web")
    ap.add_argument("--top", type=int, default=0, help="覆盖每日处理条数，便于快速验证")
    ap.add_argument("--model", default="", help="指定本地模型，覆盖 config.json")
    ap.add_argument("--port", type=int, default=8790, help="web 模式端口")
    args = ap.parse_args()

    cfg = load_cfg(args)
    if args.cmd == "web":
        from core.server import serve

        serve(cfg, port=args.port)
    elif args.cmd == "daily":
        run_daily(cfg)
    elif args.cmd == "weekly":
        render_weekly(cfg)
    else:
        cmd_check(cfg)


if __name__ == "__main__":
    main()
