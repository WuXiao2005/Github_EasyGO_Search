"""日报 HTML 与周报 Markdown 渲染。零模板引擎依赖，用占位符替换。"""
import html
import json
import os
import re
import glob
import datetime as dt

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%%TITLE%%</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%230f6f63'/%3E%3Cpath d='M8 20l4-8 4 6 4-10 4 12' stroke='%23fff' stroke-width='2.2' fill='none' stroke-linecap='round'/%3E%3C/svg%3E">
<style>
:root{
  --bg:#f4f6f7; --card:#ffffff; --ink:#15181d; --muted:#636d7d; --line:#e2e6ea;
  --accent:#0f6f63; --accent-soft:#e6f2f0; --delta:#a15c07; --delta-soft:#fdf2e2;
  --radius:12px; --mono:ui-monospace,"Cascadia Mono","SF Mono",Consolas,monospace;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:"Segoe UI",-apple-system,"PingFang SC","Microsoft YaHei",system-ui,sans-serif;
  font-size:15px;line-height:1.65;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
img{max-width:100%;display:block}

/* ===== 顶栏 ===== */
.topbar{position:sticky;top:0;z-index:20;background:rgba(244,246,247,.92);backdrop-filter:blur(10px);
  border-bottom:1px solid var(--line)}
.topbar-in{max-width:1080px;margin:0 auto;padding:14px 20px 12px}
.brandline{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.logo{width:26px;height:26px;flex:none}
.brand{font-weight:650;font-size:16px;letter-spacing:.2px}
.datechip{font-family:var(--mono);font-size:12px;color:var(--muted);padding:2px 8px;border:1px solid var(--line);border-radius:999px}
.search{margin-top:12px;display:flex;align-items:center;gap:10px;background:var(--card);border:1px solid var(--line);
  border-radius:999px;padding:0 16px;height:44px;transition:border-color .2s,box-shadow .2s}
.search:focus-within{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
.search svg{width:16px;height:16px;flex:none;color:var(--muted)}
.search input{flex:1;min-width:0;border:0;outline:0;background:transparent;font-size:15px;color:var(--ink);height:42px}
.search input::placeholder{color:#9aa3af}
.filters{margin-top:10px;display:flex;gap:8px;flex-wrap:wrap}
.chip{border:1px solid var(--line);background:var(--card);color:var(--muted);border-radius:999px;
  padding:5px 12px;font-size:13px;cursor:pointer;transition:.15s}
.chip:hover{border-color:#c6ced7;color:var(--ink)}
.chip[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:#fff}
.notice{max-width:1080px;margin:14px auto 0;padding:0 20px;font-size:13px;color:var(--muted)}
.notice b{color:var(--delta);font-weight:600}

/* ===== 列表 ===== */
.list{max-width:1080px;margin:0 auto;padding:16px 20px 60px;display:flex;flex-direction:column;gap:10px}
.row{display:grid;grid-template-columns:44px minmax(0,1fr) 132px;gap:16px;align-items:start;
  background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:16px 18px;
  cursor:pointer;transition:border-color .15s,box-shadow .15s,transform .15s}
.row:hover{border-color:#cfd6de;box-shadow:0 2px 14px rgba(20,30,40,.06)}
.row:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.row.noimg{grid-template-columns:44px minmax(0,1fr);padding-right:22px}
.rank{font-family:var(--mono);font-size:13px;color:var(--muted);padding-top:3px;text-align:right}
.rmain{min-width:0}
.rtitle{font-size:16px;font-weight:600;letter-spacing:.1px;overflow-wrap:anywhere}
.rtitle .owner{color:var(--muted);font-weight:450}
.brief{margin:5px 0 0;color:#333a44;font-size:14px}
.meta{display:flex;flex-wrap:wrap;gap:14px;margin-top:10px;font-size:12.5px;color:var(--muted);align-items:center}
.badge{display:inline-flex;align-items:center;gap:5px;border-radius:6px;padding:2px 7px;font-size:12px;font-weight:600}
.b-new{background:var(--accent-soft);color:var(--accent)}
.b-delta{background:var(--delta-soft);color:var(--delta)}
.b-active{background:#eef0f3;color:#4a5462}
.dot{width:8px;height:8px;border-radius:50%;display:inline-block}
.thumb{width:132px;height:82px;object-fit:cover;border-radius:8px;border:1px solid var(--line);background:#f0f2f4}
.thumb.empty{display:flex;align-items:center;justify-content:center;color:#c2c9d2;font-size:11px}
.empty-state{text-align:center;padding:70px 20px;color:var(--muted)}
.count{font-size:12.5px;color:var(--muted);padding:0 20px;max-width:1080px;margin:0 auto}

/* ===== 详情 ===== */
.detail{position:fixed;inset:0;background:var(--bg);z-index:30;overflow-y:auto;display:none}
.detail.show{display:block}
.dbar{position:sticky;top:0;background:rgba(244,246,247,.95);backdrop-filter:blur(10px);
  border-bottom:1px solid var(--line);z-index:5}
.dbar-in{max-width:880px;margin:0 auto;padding:12px 20px;display:flex;align-items:center;gap:12px}
.back{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--line);background:var(--card);
  border-radius:999px;padding:6px 14px;font-size:13.5px;cursor:pointer;color:var(--ink)}
.back:hover{border-color:#c6ced7}
.dwrap{max-width:880px;margin:0 auto;padding:24px 20px 80px}
.hero{border-radius:var(--radius);overflow:hidden;border:1px solid var(--line);background:#eef1f3}
.hero img{width:100%;height:260px;object-fit:cover;object-position:center}
.hero img.ogcard{object-fit:contain;background:#fff;height:220px}
.dhead{margin-top:20px}
.dtitle{font-size:23px;font-weight:650;line-height:1.35;overflow-wrap:anywhere}
.dtitle a:hover{color:var(--accent)}
.lede{font-size:16px;color:#2c333c;margin:10px 0 0;padding-left:12px;border-left:3px solid var(--accent)}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);
  border:1px solid var(--line);border-radius:10px;overflow:hidden;margin-top:18px}
.stat{background:var(--card);padding:12px 14px}
.stat .k{font-size:11.5px;color:var(--muted);letter-spacing:.4px}
.stat .v{font-family:var(--mono);font-size:17px;font-weight:600;margin-top:2px}
.stat .v.hi{color:var(--delta)}
.sec{margin-top:28px}
.sec h2{font-size:15px;font-weight:650;margin:0 0 10px;display:flex;align-items:center;gap:8px;color:#0d2b27}
.sec h2::before{content:"";width:4px;height:15px;border-radius:2px;background:var(--accent);display:block}
.sec p{margin:0;color:#2b323b;font-size:15px}
.sec ul{margin:0;padding-left:20px;color:#2b323b}
.sec li{margin:6px 0}
.tree{background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden}
.tree-row{display:grid;grid-template-columns:minmax(120px,240px) minmax(0,1fr);gap:14px;padding:10px 14px;
  border-bottom:1px solid #f0f2f4;font-size:13.5px}
.tree-row:last-child{border-bottom:0}
.tree-row code{font-family:var(--mono);color:var(--accent);overflow-wrap:anywhere}
.tree-row span{color:#4b545f}
.codebox{background:#0f1720;color:#e6edf3;border-radius:10px;padding:14px 16px;font-family:var(--mono);
  font-size:13px;line-height:1.7;overflow-x:auto;white-space:pre-wrap;overflow-wrap:anywhere}
.terms{width:100%;border-collapse:collapse;font-size:13.5px;background:var(--card);
  border:1px solid var(--line);border-radius:10px;overflow:hidden}
.terms th{text-align:left;padding:9px 12px;background:#f7f9fa;color:var(--muted);font-weight:600;font-size:12.5px}
.terms td{padding:9px 12px;border-top:1px solid #f0f2f4;vertical-align:top}
.terms td code{font-family:var(--mono);color:var(--accent)}
.openrepo{display:inline-flex;align-items:center;gap:7px;margin-top:26px;background:var(--accent);color:#fff;
  border-radius:9px;padding:10px 18px;font-size:14px;font-weight:550}
.openrepo:hover{background:#0b5b51}
.foot{max-width:880px;margin:0 auto;padding:0 20px 40px;color:var(--muted);font-size:12.5px}

@media (max-width:720px){
  .row{grid-template-columns:32px minmax(0,1fr);padding:14px}
  .thumb{display:none}
  .stats{grid-template-columns:repeat(2,1fr)}
  .tree-row{grid-template-columns:1fr;gap:4px}
  .hero img{height:190px}
  .dtitle{font-size:20px}
}
@media (max-width:400px){ .rank{display:none} .row{grid-template-columns:minmax(0,1fr)} }
</style>
</head>
<body>

<header class="topbar">
  <div class="topbar-in">
    <div class="brandline">
      <svg class="logo" viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="8" fill="#0f6f63"/><path d="M8 20l4-8 4 6 4-10 4 12" stroke="#fff" stroke-width="2.2" fill="none" stroke-linecap="round"/></svg>
      <span class="brand">GitHub 周榜 · 中文导览</span>
      <span class="datechip">%%DATE%%</span>
      <span class="datechip">%%MODE%%</span>
    </div>
    <div class="search">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>
      <input id="q" type="search" placeholder="搜索仓库名、语言、关键词…" autocomplete="off" aria-label="搜索">
    </div>
    <div class="filters" id="filters">%%FILTERS%%</div>
  </div>
</header>

<div class="notice">%%NOTICE%%</div>

<div class="count" id="count"></div>
<main class="list" id="list">%%CARDS%%</main>
<div class="empty-state" id="empty" hidden>没有匹配的结果，换个关键词试试。</div>

<section class="detail" id="detail">
  <div class="dbar"><div class="dbar-in">
    <button class="back" id="backBtn" type="button">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M15 5l-7 7 7 7"/></svg>
      返回列表
    </button>
    <span class="datechip" id="detailDate">%%DATE%%</span>
  </div></div>
  <div class="dwrap" id="detailBody"></div>
  <div class="foot">中文内容由本地 %%MODEL%% 模型生成，仅作导读，细节请以原文为准。</div>
</section>

<script>
const DATA = %%DATA%%;
const REPOS = DATA.records;

/* ===== 列表筛选 ===== */
const qEl = document.getElementById('q');
const listEl = document.getElementById('list');
const emptyEl = document.getElementById('empty');
const countEl = document.getElementById('count');
const chips = Array.from(document.querySelectorAll('.chip'));
const rows = Array.from(document.querySelectorAll('.row'));
let kind = 'all';

function refresh(){
  const q = (qEl.value || '').trim().toLowerCase();
  let visible = 0;
  rows.forEach(function(r){
    const okKind = (kind === 'all') || (r.dataset.kind === kind);
    const okText = !q || r.dataset.text.indexOf(q) !== -1;
    const show = okKind && okText;
    r.style.display = show ? '' : 'none';
    if (show) visible++;
  });
  emptyEl.hidden = visible !== 0;
  countEl.textContent = '共 ' + visible + ' 个项目 · 点击查看中文详解';
}

qEl.addEventListener('input', refresh);
chips.forEach(function(c){
  c.addEventListener('click', function(){
    kind = c.dataset.kind;
    chips.forEach(function(x){ x.setAttribute('aria-pressed', x === c ? 'true' : 'false'); });
    refresh();
  });
});

/* ===== 详情 ===== */
const detail = document.getElementById('detail');
const detailBody = document.getElementById('detailBody');
const esc = function(s){
  return String(s == null ? '' : s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
};
const fmt = function(n){ return (n == null ? '—' : Number(n).toLocaleString('en-US')); };

function section(title, inner){
  if (!inner) return '';
  return '<div class="sec"><h2>' + title + '</h2>' + inner + '</div>';
}
function para(t){ return t ? '<p>' + esc(t) + '</p>' : ''; }
function ul(items){
  if (!items || !items.length) return '';
  return '<ul>' + items.map(function(i){ return '<li>' + esc(i) + '</li>'; }).join('') + '</ul>';
}

function openDetail(i){
  const r = REPOS[i];
  const loc = r.local || {};
  const heroUrl = (r.images && r.images.length) ? r.images[0] : '';
  const kindBadge = r.has_delta
    ? '<span class="badge b-delta">近' + (r.delta_span || 7) + '天 +' + fmt(r.delta) + '</span>'
    : (r.origin === 'new' ? '<span class="badge b-new">本周新建</span>' : '<span class="badge b-active">近7天活跃</span>');

  let h = '';
  if (heroUrl) h += '<div class="hero"><img src="' + esc(heroUrl) + '" alt="" class="' + (/-og\./.test(heroUrl) ? 'ogcard' : '') + '"></div>';

  h += '<div class="dhead">';
  h += '<h1 class="dtitle"><a href="' + esc(r.html_url) + '" target="_blank" rel="noopener">' + esc(r.full_name) + '</a></h1>';
  if (loc['速览']) h += '<p class="lede">' + esc(loc['速览']) + '</p>';
  h += '</div>';

  h += '<div class="stats">'
    + '<div class="stat"><div class="k">累计 STAR</div><div class="v">' + fmt(r.stars) + '</div></div>'
    + '<div class="stat"><div class="k">' + (r.has_delta ? '近'+ (r.delta_span||7) +'天新增' : '上榜类型') + '</div><div class="v' + (r.has_delta ? ' hi' : '') + '">' + (r.has_delta ? '+' + fmt(r.delta) : (r.origin === 'new' ? '新建' : '活跃')) + '</div></div>'
    + '<div class="stat"><div class="k">FORK</div><div class="v">' + fmt(r.forks) + '</div></div>'
    + '<div class="stat"><div class="k">主语言</div><div class="v">' + esc(r.language || '—') + '</div></div>'
    + '</div>';

  h += section('它是什么', para(loc['它是什么']));
  h += section('解决什么问题', para(loc['解决什么问题']));
  h += section('核心机制', para(loc['核心机制']));
  h += section('主要功能', ul(loc['主要功能']));

  const treeRows = loc['项目结构'] || [];
  if (treeRows.length){
    h += '<div class="sec"><h2>项目结构解读</h2><div class="tree">'
      + treeRows.map(function(t){
          return '<div class="tree-row"><code>' + esc(t['路径']) + '</code><span>' + esc(t['作用']) + '</span></div>';
        }).join('')
      + '</div></div>';
  } else if (r.tree_summary && r.tree_summary.top_dirs && r.tree_summary.top_dirs.length){
    let rows2 = r.tree_summary.top_dirs.map(function(t){
      return '<div class="tree-row"><code>' + esc(t.path) + '/</code><span>' + t.files + ' 个文件</span></div>';
    }).join('');
    if (r.tree_summary.root_files && r.tree_summary.root_files.length){
      rows2 += r.tree_summary.root_files.slice(0, 8).map(function(f){
        return '<div class="tree-row"><code>' + esc(f) + '</code><span>根目录文件</span></div>';
      }).join('');
    }
    h += '<div class="sec"><h2>目录概览</h2><div class="tree">' + rows2 + '</div></div>';
  }

  if (loc['快速上手']) h += '<div class="sec"><h2>快速上手</h2><div class="codebox">' + esc(loc['快速上手']) + '</div></div>';
  h += section('值得学的点', ul(loc['值得学的点']));
  h += section('适合谁', para(loc['适合谁']));

  const terms = loc['术语表'] || [];
  if (terms.length){
    h += '<div class="sec"><h2>术语表</h2><table class="terms"><thead><tr><th style="width:22%">英文</th><th style="width:22%">中文</th><th>解释</th></tr></thead><tbody>'
      + terms.map(function(t){
          return '<tr><td><code>' + esc(t['英文']) + '</code></td><td>' + esc(t['中文']) + '</td><td>' + esc(t['解释']) + '</td></tr>';
        }).join('')
      + '</tbody></table></div>';
  }

  if (r.description) h += section('官方原始描述', '<p style="color:#5b6472">' + esc(r.description) + '</p>');

  h += '<a class="openrepo" href="' + esc(r.html_url) + '" target="_blank" rel="noopener">打开 GitHub 原仓库'
    + '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 17L17 7M9 7h8v8"/></svg></a>';

  detailBody.innerHTML = h;
  detail.classList.add('show');
  detail.scrollTop = 0;
  document.body.style.overflow = 'hidden';
}

function closeDetail(){
  detail.classList.remove('show');
  document.body.style.overflow = '';
  if (location.hash) history.replaceState(null, '', location.pathname);
}

rows.forEach(function(r, i){
  r.addEventListener('click', function(){ openDetail(Number(r.dataset.idx)); });
  r.addEventListener('keydown', function(e){ if (e.key === 'Enter') openDetail(Number(r.dataset.idx)); });
  r.tabIndex = 0;
});
document.getElementById('backBtn').addEventListener('click', closeDetail);

function applyHash(){
  const m = /^#\/r\/(\d+)$/.exec(location.hash || '');
  if (m) openDetail(Number(m[1])); else detail.classList.remove('show'), document.body.style.overflow = '';
}
window.addEventListener('hashchange', applyHash);
applyHash();
refresh();
</script>
</body>
</html>
"""

KIND_LABEL = {"new": "本周新建", "active": "近 7 天活跃"}


def _esc(s):
    return html.escape(str(s or ""), quote=True)


def _fmt(n):
    try:
        return f"{int(n):,}"
    except (TypeError, ValueError):
        return "—"


def _card(rec):
    loc = rec.get("local") or {}
    kind = "delta" if rec.get("has_delta") else rec.get("origin", "active")
    if rec.get("has_delta"):
        badge = f'<span class="badge b-delta">近{rec.get("delta_span") or 7}天 +{_fmt(rec.get("delta"))}</span>'
    elif kind == "new":
        badge = '<span class="badge b-new">本周新建</span>'
    else:
        badge = '<span class="badge b-active">近 7 天活跃</span>'
    brief = loc.get("速览") or (rec.get("description") or "")[:70]
    has_img = bool(rec.get("images"))
    row_cls = "row" if has_img else "row noimg"
    thumb = (
        f'<img class="thumb" src="{_esc(rec["images"][0])}" alt="" loading="lazy">'
        if has_img
        else ""
    )
    text_blob = " ".join(
        [
            rec.get("full_name", ""),
            rec.get("description", ""),
            rec.get("language", ""),
            " ".join(rec.get("topics") or []),
            json.dumps(loc, ensure_ascii=False),
        ]
    ).lower()
    owner, _, name = rec["full_name"].partition("/")
    return f"""<article class="{row_cls}" data-idx="{rec['index'] - 1}" data-kind="{kind}" data-text="{_esc(text_blob)}">
  <div class="rank">{rec['index']:02d}</div>
  <div class="rmain">
    <div class="rtitle"><span class="owner">{_esc(owner)}/</span>{_esc(name)}</div>
    <p class="brief">{_esc(brief)}</p>
    <div class="meta">{badge}<span>{_esc(rec.get('language') or '未标注')}</span><span>★ {_fmt(rec.get('stars'))}</span><span>Fork {_fmt(rec.get('forks'))}</span></div>
  </div>
  {thumb}
</article>"""


def render_daily(data, out_day, cfg, log=print):
    recs = data["records"]
    counts = {
        "all": len(recs),
        "delta": sum(1 for r in recs if r.get("has_delta")),
        "new": sum(1 for r in recs if not r.get("has_delta") and r.get("origin") == "new"),
        "active": sum(1 for r in recs if not r.get("has_delta") and r.get("origin") == "active"),
    }
    chips = [f'<button class="chip" type="button" data-kind="all" aria-pressed="true">全部 {counts["all"]}</button>']
    if counts["delta"]:
        chips.append(f'<button class="chip" type="button" data-kind="delta" aria-pressed="false">有周增量 {counts["delta"]}</button>')
    chips.append(f'<button class="chip" type="button" data-kind="new" aria-pressed="false">本周新建 {counts["new"]}</button>')
    if counts["active"]:
        chips.append(f'<button class="chip" type="button" data-kind="active" aria-pressed="false">近 7 天活跃 {counts["active"]}</button>')

    mode_text = "周增量榜" if data["mode"] == "delta" else "首跑模式"
    if data["mode"] == "delta":
        notice = "排名依据：过去 7 天的真实 Star 增量（本地快照差分算出）。"
    else:
        notice = (
            "<b>首跑模式：</b>本地还没有 7 天份的快照，暂时拿不到真实周增量，"
            "本期榜单由「本周新建仓库」与「近 7 天有推送的热门仓库」两组真实数据构成，"
            "每张卡片都标注了来源。连续跑满 7 天后会自动切换为真实周增量榜。"
        )

    payload = json.dumps({"records": [
        {
            "full_name": r["full_name"],
            "html_url": r["html_url"],
            "stars": r["stars"],
            "forks": r["forks"],
            "language": r["language"],
            "description": r["description"],
            "topics": r.get("topics") or [],
            "origin": r.get("origin"),
            "has_delta": r.get("has_delta"),
            "delta": r.get("delta"),
            "delta_span": r.get("delta_span"),
            "images": r.get("images") or [],
            "local": r.get("local") or {},
            "tree_summary": r.get("tree_summary") or {},
        }
        for r in recs
    ]}, ensure_ascii=False).replace("</", "<\\/")

    out = (
        TEMPLATE.replace("%%TITLE%%", f"GitHub 周榜日报 · {data['day']}")
        .replace("%%DATE%%", data["day"])
        .replace("%%MODE%%", mode_text)
        .replace("%%MODEL%%", _esc(data.get("model", "local")))
        .replace("%%NOTICE%%", notice)
        .replace("%%FILTERS%%", "".join(chips))
        .replace("%%CARDS%%", "\n".join(_card(r) for r in recs))
        .replace("%%DATA%%", payload)
    )
    path = os.path.join(out_day, f"日报-{data['day']}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(out)
    log(f"  已写入 {path}")
    return path


# ---------------- 周报 ----------------
def render_weekly(cfg, log=print, days=7):
    out_root = cfg["out_dir"]
    files = sorted(glob.glob(os.path.join(out_root, "*", "data.json")))[-days:]
    if not files:
        log("没有找到任何日报数据，先跑一次 daily。")
        return None

    day_map = {}
    for fp in files:
        try:
            with open(fp, encoding="utf-8") as f:
                d = json.load(f)
        except Exception as e:
            log(f"  跳过损坏文件 {fp}: {e}")
            continue
        day_map[d["day"]] = d

    if not day_map:
        return None

    ordered_days = sorted(day_map)
    start, end = ordered_days[0], ordered_days[-1]

    repo_stats = {}
    for day in ordered_days:
        for r in day_map[day]["records"]:
            st = repo_stats.setdefault(
                r["full_name"],
                {
                    "full_name": r["full_name"],
                    "url": r["html_url"],
                    "appearances": 0,
                    "first": day,
                    "last": day,
                    "delta": 0,
                    "stars": r["stars"],
                    "language": r["language"],
                    "brief": (r.get("local") or {}).get("速览") or r.get("description", ""),
                    "what": (r.get("local") or {}).get("它是什么", ""),
                },
            )
            st["appearances"] += 1
            st["last"] = day
            st["stars"] = max(st["stars"], r["stars"])
            if r.get("has_delta") and r.get("delta"):
                st["delta"] += r["delta"]

    ranked = sorted(repo_stats.values(), key=lambda x: (-x["appearances"], -x["delta"], -x["stars"]))
    total_repos = len(ranked)
    repeat = sum(1 for x in ranked if x["appearances"] > 1)
    lang_count = {}
    for x in ranked:
        lang_count[x["language"] or "未标注"] = lang_count.get(x["language"] or "未标注", 0) + 1
    top_langs = sorted(lang_count.items(), key=lambda kv: -kv[1])[:5]

    lines = []
    lines.append("---")
    lines.append(f"title: GitHub 周榜周报 {start} ~ {end}")
    lines.append(f"date: {end}")
    lines.append("tags:")
    lines.append("  - github")
    lines.append("  - 开源周报")
    lines.append("  - 中文导览")
    lines.append("---")
    lines.append("")
    lines.append(f"# GitHub 周榜周报 · {start} ~ {end}")
    lines.append("")
    lines.append("> 由本地抓取 + 本地 4B 模型汉化生成，仅供学习导读，细节以原仓库为准。")
    lines.append("")
    lines.append("## 本周概览")
    lines.append("")
    lines.append(f"- 统计区间：{start} 至 {end}，共 {len(ordered_days)} 份日报")
    lines.append(f"- 上榜项目：{total_repos} 个不重复仓库，其中 {repeat} 个多次上榜")
    if top_langs:
        lines.append("- 语言分布：" + "、".join(f"{k}（{v}）" for k, v in top_langs))
    delta_total = sum(x["delta"] for x in ranked)
    if delta_total:
        lines.append(f"- 累计观测 Star 增量：{delta_total:,}")
    lines.append("")
    hot = [x for x in ranked if x["appearances"] > 1]
    if hot:
        lines.append("## 多次上榜项目（更值得关注）")
    else:
        lines.append("## 本周项目一览（当前只有一份日报，暂无多次上榜对比）")
        hot = ranked[:5]
    lines.append("")
    lines.append("| 项目 | 上榜次数 | 累计增量 | 语言 | 一句话 |")
    lines.append("| --- | --- | --- | --- | --- |")
    for x in hot[:12]:
        d = f"+{x['delta']:,}" if x["delta"] else "—"
        brief = x["brief"].replace("|", "\\|")[:50]
        lines.append(f"| [{x['full_name']}]({x['url']}) | {x['appearances']} | {d} | {x['language'] or '—'} | {brief} |")
    lines.append("")
    lines.append("## 全部上榜项目")
    lines.append("")
    for i, x in enumerate(ranked, 1):
        lines.append(f"### {i}. [{x['full_name']}]({x['url']})")
        lines.append("")
        lines.append(f"- 首次上榜：{x['first']}　最近上榜：{x['last']}　上榜次数：{x['appearances']}")
        lines.append(f"- 星数：{x['stars']:,}　语言：{x['language'] or '未标注'}")
        if x["brief"]:
            lines.append(f"- 速览：{x['brief']}")
        if x["what"]:
            lines.append(f"- 它是：{x['what']}")
        lines.append("")
    lines.append("## 每日入口")
    lines.append("")
    for day in reversed(ordered_days):
        lines.append(f"- {day}：日报 `{day}/日报-{day}.html`（{len(day_map[day]['records'])} 个项目）")

    md = "\n".join(lines) + "\n"
    path = os.path.join(out_root, f"周报-{start}_至_{end}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(md)
    log(f"  周报已写入 {path}")
    return path
