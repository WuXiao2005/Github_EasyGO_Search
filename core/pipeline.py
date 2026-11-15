"""每日抓取 → 快照 → 排名 → 汉化 → 产出。"""
import datetime as dt
import hashlib
import json
import os
import re

from .github import GitHubClient, clean_text, extract_images, summarize_tree
from .localize import Localizer, validate
from .store import Store, days_ago, today_str


def normalize(item, origin):
    owner = (item.get("owner") or {}).get("login", "")
    return {
        "full_name": item.get("full_name", ""),
        "owner": owner,
        "name": item.get("name", ""),
        "description": clean_text(item.get("description")),
        "stars": item.get("stargazers_count", 0),
        "forks": item.get("forks_count", 0),
        "language": item.get("language") or "",
        "topics": item.get("topics") or [],
        "html_url": item.get("html_url", ""),
        "avatar": (item.get("owner") or {}).get("avatar_url", ""),
        "created_at": item.get("created_at", ""),
        "pushed_at": item.get("pushed_at", ""),
        "license": ((item.get("license") or {}).get("spdx_id") or ""),
        "default_branch": item.get("default_branch") or "main",
        "origin": origin,
    }


def build_pool(client, cfg, log):
    since = days_ago(cfg["window_days"])
    new_items = client.search_repos(
        f"created:>{since} stars:>{cfg['new_repo_min_stars']}",
        per_page=cfg["pool_new_repos"],
    )
    log(f"  本周新建候选：{len(new_items)} 个")
    active_items = client.search_repos(
        f"pushed:>{since} stars:>{cfg['active_repo_min_stars']}",
        per_page=cfg["pool_active_repos"],
    )
    log(f"  近期活跃候选：{len(active_items)} 个")

    pool = {}
    for it in new_items:
        if it.get("fork") or it.get("archived"):
            continue
        pool[it["full_name"]] = normalize(it, "new")
    for it in active_items:
        if it.get("fork") or it.get("archived") or it["full_name"] in pool:
            continue
        pool[it["full_name"]] = normalize(it, "active")
    return list(pool.values())


def rank(pool, store, cfg):
    """有 7 日快照就按真实增量排；没有就按新建/活跃两个真实口径排。"""
    window_start = days_ago(cfg["window_days"])
    for it in pool:
        stars_then, day_then = store.stars_on_or_before(it["full_name"], window_start)
        if stars_then is not None:
            span = (dt.date.today() - dt.date.fromisoformat(day_then)).days
            it["delta"] = max(it["stars"] - stars_then, 0)
            it["delta_span"] = span
            it["has_delta"] = span >= cfg["window_days"] - 1
        else:
            it["delta"] = None
            it["delta_span"] = 0
            it["has_delta"] = False

    delta_pool = [it for it in pool if it.get("has_delta")]
    delta_pool.sort(key=lambda x: (-x["delta"], -x["stars"]))

    new_pool = [it for it in pool if it["origin"] == "new" and not it.get("has_delta")]
    new_pool.sort(key=lambda x: -x["stars"])

    active_pool = [it for it in pool if it["origin"] == "active" and not it.get("has_delta")]
    active_pool.sort(key=lambda x: -x["stars"])

    mode = "delta" if len(delta_pool) >= cfg["top_n"] else "bootstrap"
    return delta_pool, new_pool, active_pool, mode


def select(delta_pool, new_pool, active_pool, top_n):
    """尽量给出真实增量的榜；不足时用真实的新建/活跃数据补齐。"""
    picked = []
    for it in delta_pool:
        if len(picked) >= top_n:
            break
        picked.append(it)
    quota_new = max((top_n - len(picked)) // 2, 1)
    for it in new_pool[:quota_new]:
        if len(picked) >= top_n:
            break
        picked.append(it)
    for it in active_pool:
        if len(picked) >= top_n:
            break
        picked.append(it)
    for it in new_pool[quota_new:]:
        if len(picked) >= top_n:
            break
        picked.append(it)
    return picked[:top_n]


SAFE = re.compile(r"[^a-zA-Z0-9_\-]")


def signature(meta, readme, model):
    raw = f"{meta['full_name']}|{meta['stars'] // 500}|{model}|{readme[:1200]}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def run_daily(cfg, log=print):
    day = today_str()
    out_day = os.path.join(cfg["out_dir"], day)
    assets = os.path.join(out_day, "assets")
    os.makedirs(assets, exist_ok=True)

    client = GitHubClient(cfg.get("token", ""), cfg.get("timeout", 30), log)
    store = Store(cfg["data_dir"])
    localizer = Localizer(cfg["model"], cfg["ollama_url"], log)

    log(f"[1/5] 抓取候选池（窗口 {cfg['window_days']} 天）")
    pool = build_pool(client, cfg, log)
    if not pool:
        log("候选池为空，检查网络或 Token。")
        return None

    saved = store.save_snapshot(pool, day)
    log(f"  快照入库 {saved} 条（累计覆盖天数 {store.coverage()[3]}）")
    store.save_meta(pool, day)

    log("[2/5] 计算排名")
    delta_pool, new_pool, active_pool, mode = rank(pool, store, cfg)
    picked = select(delta_pool, new_pool, active_pool, cfg["top_n"])
    log(f"  模式={mode}，增量池 {len(delta_pool)} / 新建 {len(new_pool)} / 活跃 {len(active_pool)}，入选 {len(picked)}")

    model_ok = localizer.ensure_model()
    if not model_ok:
        log("  警告：本地模型不可用，将只输出元信息，不做汉化。")

    records = []
    for idx, it in enumerate(picked, 1):
        log(f"[3/5] ({idx}/{len(picked)}) {it['full_name']}")
        readme = client.readme_text(it["full_name"]) or ""
        tree = client.tree(it["full_name"], it["default_branch"]) or []
        tree_summary = summarize_tree(tree)
        it["tree_summary"] = tree_summary

        if it.get("has_delta"):
            activity = f"近 {it['delta_span']} 天新增 {it['delta']} 星"
        elif it["origin"] == "new":
            activity = "本周新建仓库"
        else:
            activity = "近 7 天有推送的活跃项目"

        localized = None
        sig = signature(it, readme, cfg["model"])
        cached = store.get_localization(it["full_name"], sig)
        if cached and validate(cached) is None:
            localized = cached
            log("  使用缓存译文")
        elif model_ok:
            try:
                localized = localizer.localize(it, readme[: cfg["readme_chars"]], tree_summary, activity)
                if isinstance(localized, dict):
                    store.put_localization(it["full_name"], sig, localized, day)
                    log("  汉化完成")
                else:
                    localized = None
            except Exception as e:
                log(f"  [汉化失败] {e}")
        if localized is None:
            localized = {"速览": it["description"][:60] or "（未生成中文摘要）"}

        # 图片：README 首图 + GitHub 社交预览卡兜底
        imgs = []
        for i, url in enumerate(extract_images(readme, it["full_name"])[: cfg["images_per_repo"]]):
            ext = os.path.splitext(url.split("?")[0])[1].lower()
            if ext not in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
                ext = ".png"
            is_og = "opengraph.githubassets" in url
            fname = f"{idx:02d}-{SAFE.sub('_', it['full_name'])}-{i}{'-og' if is_og else ''}{ext}"
            dest = os.path.join(assets, fname)
            if os.path.exists(dest) or client.download(url, dest):
                imgs.append(f"assets/{fname}")

        records.append(
            {
                **it,
                "local": localized,
                "images": imgs,
                "readme_excerpt": readme[:400],
                "index": idx,
            }
        )

    records.sort(key=lambda r: r["index"])
    data = {
        "day": day,
        "mode": mode,
        "window_days": cfg["window_days"],
        "model": cfg["model"],
        "records": records,
    }
    with open(os.path.join(out_day, "data.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    log("[4/5] 渲染 HTML")
    from .render import render_daily

    html_path = render_daily(data, out_day, cfg, log)

    log("[5/5] 完成")
    store.close()
    log(f"  日报：{html_path}")
    log(f"  API 调用：{client.calls} 次，剩余配额：{client.remaining}")
    return data
