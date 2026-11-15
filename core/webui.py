"""实时检索页面的前端模板。"""

PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>中文搜 GitHub</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%230f6f63'/%3E%3Cpath d='M8 20l4-8 4 6 4-10 4 12' stroke='%23fff' stroke-width='2.2' fill='none' stroke-linecap='round'/%3E%3C/svg%3E">
<style>
:root{
  --bg:#f4f6f7;--card:#fff;--ink:#15181d;--muted:#636d7d;--line:#e2e6ea;
  --accent:#0f6f63;--accent-soft:#e6f2f0;--delta:#a15c07;
  --mono:ui-monospace,"Cascadia Mono","SF Mono",Consolas,monospace;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-size:15px;line-height:1.65;
  font-family:"Segoe UI",-apple-system,"PingFang SC","Microsoft YaHei",system-ui,sans-serif;
  -webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}

/* 顶部搜索区 */
.hero{padding:52px 20px 20px;max-width:900px;margin:0 auto}
.brandrow{display:flex;align-items:center;gap:10px}
.logo{width:26px;height:26px}
.brand{font-weight:650;font-size:17px}
.tag{font-size:12px;color:var(--muted);border:1px solid var(--line);border-radius:999px;padding:2px 8px;font-family:var(--mono)}
.modelbtn{display:inline-flex;align-items:center;gap:6px;background:var(--card);cursor:pointer;
  padding:4px 10px;color:var(--muted);transition:border-color .15s,color .15s,background .15s}
.modelbtn:hover{border-color:#bfdcd7;color:var(--accent);background:var(--accent-soft)}
.modelbtn svg{width:11px;height:11px;flex:none;opacity:.7}
.modelbtn b{font-weight:550;color:var(--ink);font-family:var(--mono)}
.modelbtn:hover b{color:var(--accent)}
h1{font-size:26px;line-height:1.35;margin:18px 0 6px;font-weight:650;letter-spacing:-.2px}
.sub{color:var(--muted);font-size:14px;margin:0 0 20px}
.feedrow{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin:0 0 18px}
.feedtabs{display:inline-flex;background:var(--card);border:1px solid var(--line);border-radius:11px;padding:3px;gap:2px}
.feedtab{border:0;background:transparent;border-radius:8px;padding:7px 16px;font:inherit;font-size:14px;
  color:var(--muted);cursor:pointer;transition:background .15s,color .15s;font-weight:500}
.feedtab:hover{color:var(--ink);background:#f4f7f7}
.feedtab.active{background:var(--accent);color:#fff;font-weight:600;box-shadow:0 1px 3px rgba(15,111,99,.22)}
.feedtab.active:hover{background:#0d6459;color:#fff}
.feedhint{font-size:13px;color:var(--muted)}
.searchbox{display:flex;gap:10px;align-items:center;background:var(--card);border:1px solid var(--line);
  border-radius:14px;padding:6px 6px 6px 16px;box-shadow:0 1px 2px rgba(20,30,40,.04)}
.searchbox:focus-within{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
.searchbox svg{width:18px;height:18px;color:var(--muted);flex:none}
#q{flex:1;min-width:0;border:0;outline:0;background:transparent;font-size:16px;height:46px;color:var(--ink)}
#q::placeholder{color:#9aa3af}
#go{border:0;background:var(--accent);color:#fff;border-radius:10px;height:42px;padding:0 20px;
  font-size:15px;font-weight:600;cursor:pointer}
#go:hover{background:#0b5b51}
#go:disabled{background:#9fb8b3;cursor:default}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
.chip{border:1px solid var(--line);background:var(--card);color:var(--muted);border-radius:999px;
  padding:5px 12px;font-size:13px;cursor:pointer}
.chip:hover{border-color:#c6ced7;color:var(--ink)}

/* 状态行 */
.statusbar{max-width:900px;margin:0 auto;padding:6px 20px 0;font-size:13px;color:var(--muted);min-height:22px}
.statusbar .arrow{color:var(--accent);font-family:var(--mono)}
.statusbar b{color:var(--ink);font-weight:600}
.pillbar{max-width:900px;margin:8px auto 0;padding:0 20px;display:flex;flex-wrap:wrap;gap:8px}
.pill{font-family:var(--mono);font-size:12px;background:var(--accent-soft);color:var(--accent);
  border-radius:6px;padding:3px 9px}
.listtitle{max-width:900px;margin:14px auto 0;padding:0 20px;font-size:13px;color:var(--muted);
  display:flex;align-items:baseline;gap:10px}
.listtitle strong{color:var(--ink);font-size:15px;font-weight:650}

/* 结果 */
.results{max-width:900px;margin:0 auto;padding:12px 20px 40px;display:flex;flex-direction:column;gap:10px}
.res{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px;
  cursor:pointer;transition:border-color .15s,box-shadow .15s}
.res:hover{border-color:#cfd6de;box-shadow:0 2px 14px rgba(20,30,40,.06)}
.res:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.rhead{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}
.rank{font-family:var(--mono);font-size:12px;color:var(--muted)}
.rname{font-weight:600;font-size:16px;overflow-wrap:anywhere}
.rname .own{color:var(--muted);font-weight:450}
.rb{border:1px solid var(--line);border-radius:5px;font-size:11px;color:var(--muted);padding:1px 6px;font-family:var(--mono)}
.brief{margin:7px 0 0;font-size:14px;color:#2c333c;line-height:1.7}
.brief.loading{color:#8d97a4}
.brief.loading::after{content:" 翻译中…";font-size:12px;color:#b3bcc7}
.en{margin:6px 0 0;font-size:12.5px;color:var(--muted);line-height:1.5}
.rmeta{display:flex;flex-wrap:wrap;gap:14px;margin-top:10px;font-size:12.5px;color:var(--muted);align-items:center}
.dot{width:8px;height:8px;border-radius:50%;background:var(--accent);display:inline-block;margin-right:5px;vertical-align:1px}
.empty{padding:56px 20px;text-align:center;color:var(--muted)}
.err{color:#a3371f}
.more{display:flex;justify-content:center;padding:14px 0 40px;color:var(--muted);font-size:13px;gap:10px;align-items:center}
.spinner{width:20px;height:20px;border:2.5px solid var(--line);border-top-color:var(--accent);
  border-radius:50%;animation:spin 1s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}

.drawer{position:fixed;inset:0;background:var(--bg);z-index:30;overflow-y:auto;display:none}
.drawer.show{display:block}
.dbar{position:sticky;top:0;background:rgba(244,246,247,.95);backdrop-filter:blur(10px);
  border-bottom:1px solid var(--line);z-index:8}
.dbarin{max-width:820px;margin:0 auto;padding:12px 20px;display:flex;align-items:center;gap:12px}
.back{border:1px solid var(--line);background:var(--card);border-radius:999px;padding:6px 14px;
  font-size:13.5px;cursor:pointer;color:var(--ink);display:inline-flex;align-items:center;gap:6px}
.back:hover{border-color:#c6ced7}
.dhead{max-width:820px;margin:0 auto;padding:20px 20px 0}
.dname{font-size:21px;font-weight:650;line-height:1.35;overflow-wrap:anywhere}
.dname .own{color:var(--muted);font-weight:450}
.ddesc{font-size:13.5px;color:#4b545f;margin-top:8px}
.dstats{display:flex;flex-wrap:wrap;gap:16px;margin-top:14px;font-size:12.5px;color:var(--muted)}
.dstats b{font-family:var(--mono);color:var(--ink);font-weight:600;font-size:14px}
.streamtag{display:inline-flex;align-items:center;gap:6px;font-size:12px;color:var(--accent);
  background:var(--accent-soft);border-radius:999px;padding:2px 9px;margin-top:14px}
.streamtag b{font-family:var(--mono);font-weight:600;color:var(--accent)}
.streamtag.done{background:#eef0f3;color:#4a5462}
.streamtag.done b{color:#2b333c}
.streamtag i{width:6px;height:6px;border-radius:50%;background:var(--accent);animation:pulse 1.2s infinite}
@keyframes pulse{50%{opacity:.2}}
.dbody{max-width:820px;margin:0 auto;padding:12px 20px 70px}
.heroimg{border-radius:12px;overflow:hidden;border:1px solid var(--line);background:#fff;margin-top:18px}
.heroimg img{width:100%;max-height:300px;object-fit:contain;background:#fff}
.lede{font-size:16px;color:#2c333c;margin:16px 0 0;padding-left:12px;border-left:3px solid var(--accent)}
.sec{margin-top:24px}
.sec h2{font-size:14px;font-weight:650;margin:0 0 8px;display:flex;align-items:center;gap:8px;color:#0d2b27}
.sec h2::before{content:"";width:4px;height:14px;border-radius:2px;background:var(--accent)}
.sec p{margin:0;color:#2b323b}
.sec ul{margin:0;padding-left:20px;color:#2b323b}
.sec li{margin:4px 0}
.tree{background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden}
.tree-row{display:grid;grid-template-columns:minmax(120px,230px) minmax(0,1fr);gap:14px;
  padding:9px 14px;border-bottom:1px solid #f0f2f4;font-size:13.5px}
.tree-row:last-child{border-bottom:0}
.tree-row code{font-family:var(--mono);color:var(--accent);overflow-wrap:anywhere}
.tree-row span{color:#4b545f}
.terms{width:100%;border-collapse:collapse;font-size:13.5px;background:var(--card);
  border:1px solid var(--line);border-radius:10px;overflow:hidden}
.terms th{text-align:left;padding:9px 12px;background:#f7f9fa;color:var(--muted);font-size:12.5px}
.terms td{padding:9px 12px;border-top:1px solid #f0f2f4;vertical-align:top}
.terms td code{font-family:var(--mono);color:var(--accent)}

/* 判断卡 / 能不能跑 / 代码地图 / 按钮导读 */
.facts{margin-top:20px}
.judge{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.badge{display:inline-flex;align-items:center;gap:7px;font-size:12.5px;border-radius:999px;
  padding:4px 11px;background:#f3f6f7;border:1px solid var(--line);color:#4b545f}
.badge b{color:var(--ink);font-weight:600}
.dot{width:7px;height:7px;border-radius:50%;display:inline-block;flex:none}
.dot.active{background:var(--accent)}
.dot.half{background:var(--delta)}
.dot.slow{background:#9aa4b0}
.dot.gone{background:#b4453a}
.dot.unknown{background:#c3cad2}
.verdict{margin:10px 0 0;font-size:13.5px;color:#2b323b}
.block{margin-top:20px}
.block h3{font-size:13px;font-weight:650;color:#0d2b27;margin:0 0 8px;
  display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.block h3 em{font-style:normal;font-size:11.5px;color:var(--muted);font-weight:400}
.cmds{position:relative;background:#fbfcfc;border:1px solid var(--line);border-radius:10px;
  padding:11px 14px;font-family:var(--mono);font-size:12.5px;line-height:1.8;color:#22303a;
  white-space:pre-wrap;overflow-wrap:anywhere}
.cmds button{position:absolute;top:9px;right:9px;font-family:var(--sans);font-size:11.5px;
  border:1px solid var(--line);background:#fff;border-radius:6px;padding:2px 8px;color:var(--muted);cursor:pointer}
.brow{display:flex;gap:10px;align-items:baseline;padding:7px 0;font-size:13px;border-bottom:1px dashed #edf0f3}
.brow:last-child{border-bottom:0}
.brow .k{color:var(--muted);min-width:64px;font-size:12.5px;flex:none}
.brow .v{color:#2b323b;min-width:0;flex:1}
.mapbox{background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden}
.maprow{display:grid;grid-template-columns:minmax(110px,200px) minmax(0,1fr) auto;gap:12px;
  padding:9px 13px;border-bottom:1px solid #f0f2f4;font-size:13px;align-items:center}
.maprow:last-child{border-bottom:0}
.maprow code{font-family:var(--mono);color:var(--accent);overflow-wrap:anywhere}
.maprow span{color:#4b545f;min-width:0}
.tag{font-size:11px;border-radius:5px;padding:1px 7px;font-family:var(--sans);white-space:nowrap}
.tag.read{background:var(--accent-soft);color:var(--accent)}
.tag.skip{background:#f0f2f4;color:#7b8590}

/* 拉取面板 */
.pullbar{display:flex;gap:8px;margin-top:14px;flex-wrap:wrap;align-items:center}
.btn-accent{background:var(--accent);color:#fff;border:0;border-radius:9px;padding:9px 17px;
  font-size:13.5px;font-weight:550;cursor:pointer}
.btn-accent:disabled{opacity:.55;cursor:default}
.btn-ghost{background:#fff;border:1px solid var(--line);border-radius:9px;padding:9px 14px;
  font-size:13px;color:var(--ink);cursor:pointer}
.btn-ghost:hover{border-color:#c6ced7}
.pullpanel{margin-top:12px;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 15px}
.pullpanel .lab{font-size:12px;color:var(--muted)}
.pullpath{font-family:var(--mono);font-size:12px;color:#3a434e;word-break:break-all;margin-top:3px}
.bar{height:4px;background:#eef1f3;border-radius:3px;overflow:hidden;margin-top:12px}
.bar i{display:block;height:100%;width:0;background:var(--accent);transition:width .3s}
.pullhint{font-size:12px;color:var(--muted);margin-top:8px}

/* 页面内文件夹浏览器（系统对话框弹不出来时的兜底） */
.dbrw{margin-top:12px;border:1px solid var(--line);border-radius:10px;overflow:hidden;background:#fcfdfd}
.dbhead{display:flex;justify-content:space-between;align-items:center;gap:10px;
  padding:9px 12px;border-bottom:1px solid var(--line);font-size:12.5px;color:var(--ink)}
.dbcur{font-family:var(--mono);font-size:11.5px;color:var(--muted);word-break:break-all;text-align:right}
.dbbody{max-height:230px;overflow:auto}
.dbrow{display:flex;align-items:center;gap:8px;padding:7px 12px;font-size:12.5px;cursor:pointer;
  border-bottom:1px solid #f2f4f6}
.dbrow:hover{background:#f2f7f6}
.dbrow:last-child{border-bottom:0}
.dbicon{color:var(--accent);font-size:11px}
.dbname{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.dbfree{margin-left:auto;font-family:var(--mono);font-size:11px;color:var(--muted)}
.dbfoot{display:flex;gap:8px;padding:9px 12px;border-top:1px solid var(--line);flex-wrap:wrap}

/* README 分节翻译 */
.toc{display:flex;flex-wrap:wrap;gap:7px;margin-top:2px}
.toc button{font-size:12.5px;border:1px solid var(--line);background:#fff;border-radius:999px;
  padding:4px 12px;cursor:pointer;color:#3a434e;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.toc button:hover{border-color:#c6ced7}
.toc button.active{background:var(--accent);color:#fff;border-color:var(--accent)}
.rsec{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin-top:11px;
  font-size:13.5px;line-height:1.8;color:#2b323b;white-space:pre-wrap;overflow-wrap:anywhere}
.cursor{display:inline-block;width:2px;height:1.05em;background:var(--accent);
  animation:blink .9s step-end infinite;vertical-align:-3px;margin-left:2px}
@keyframes blink{50%{opacity:0}}
.waitline{padding:34px 0;color:var(--muted);font-size:13.5px;display:flex;align-items:center;gap:10px}
.openrepo{display:inline-flex;align-items:center;gap:7px;margin-top:26px;background:var(--accent);
  color:#fff;border-radius:9px;padding:10px 18px;font-size:14px;font-weight:550}
.foot{max-width:820px;margin:0 auto;padding:0 20px 40px;color:var(--muted);font-size:12.5px}

/* 模型选择浮层 */
.mmask{position:fixed;inset:0;background:rgba(16,22,28,.34);z-index:60;display:none;
  align-items:center;justify-content:center;padding:18px}
.mmask.show{display:flex}
.mcard{width:100%;max-width:580px;background:var(--card);border-radius:14px;
  box-shadow:0 20px 56px rgba(15,25,35,.24);max-height:min(84vh,760px);display:flex;flex-direction:column;overflow:hidden}
.mhead{padding:18px 20px 13px;border-bottom:1px solid var(--line);display:flex;
  justify-content:space-between;align-items:flex-start;gap:14px}
.mtitle{font-size:16px;font-weight:650}
.msub{font-size:12.5px;color:var(--muted);margin-top:5px;line-height:1.6}
.msub code{font-family:var(--mono);background:#f2f5f5;border-radius:4px;padding:1px 5px;font-size:12px;color:var(--accent)}
.mrefresh{border:1px solid var(--line);background:var(--card);border-radius:8px;padding:5px 12px;
  font-size:12.5px;cursor:pointer;color:var(--muted);flex:none}
.mrefresh:hover{border-color:#c6ced7;color:var(--ink)}
.mlist{overflow-y:auto;padding:8px;flex:1}
.mrow{display:flex;width:100%;align-items:center;gap:12px;background:var(--card);
  border:1px solid transparent;border-radius:10px;padding:11px 12px;text-align:left;
  cursor:pointer;font:inherit;color:inherit;transition:background .12s,border-color .12s}
.mrow:hover{background:#f6f8f9;border-color:var(--line)}
.mrow[aria-selected="true"]{background:var(--accent-soft);border-color:#bfdcd7}
.mrow:disabled{opacity:.6;cursor:progress}
.mdot{width:14px;height:14px;border-radius:50%;border:2px solid #c7ced6;flex:none;position:relative}
.mrow[aria-selected="true"] .mdot{border-color:var(--accent)}
.mrow[aria-selected="true"] .mdot::after{content:"";position:absolute;inset:2px;border-radius:50%;background:var(--accent)}
.minfo{min-width:0;flex:1}
.mname{display:block;font-family:var(--mono);font-size:13.5px;overflow-wrap:anywhere;line-height:1.45}
.mmeta{font-size:12px;color:var(--muted);margin-top:4px;display:flex;flex-wrap:wrap;gap:4px 10px}
.mwarn{color:var(--delta)}
.mbadge{font-size:11.5px;color:var(--accent);background:#fff;border:1px solid #bfdcd7;
  border-radius:5px;padding:1px 7px;flex:none}
.mempty{padding:26px 16px;text-align:center;color:var(--muted);font-size:13px}
.mfoot{padding:11px 20px 14px;border-top:1px solid var(--line);font-size:12px;
  color:var(--muted);line-height:1.65}
.toast{position:fixed;left:50%;bottom:34px;transform:translate(-50%,14px);background:#15181d;color:#fff;
  font-size:13px;padding:9px 17px;border-radius:8px;opacity:0;pointer-events:none;transition:.22s;z-index:70;max-width:80vw}
.toast.show{opacity:1;transform:translate(-50%,0)}

@media (max-width:720px){
  .hero{padding:30px 16px 14px}
  h1{font-size:21px}
  .results{padding:10px 16px 30px}
  .tree-row{grid-template-columns:1fr;gap:4px}
  .brief{font-size:13.5px}
}
</style>
</head>
<body>

<div class="hero">
  <div class="brandrow">
    <svg class="logo" viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="8" fill="#0f6f63"/><path d="M8 20l4-8 4 6 4-10 4 12" stroke="#fff" stroke-width="2.2" fill="none" stroke-linecap="round"/></svg>
    <span class="brand">中文搜 GitHub</span>
    <button class="tag modelbtn" id="modelBtn" type="button" title="点击切换本地模型">
      本地实时翻译 · <b id="modelLabel">%%MODEL%%</b>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>
    </button>
  </div>
  <h1>用中文描述你要什么，直接搜英文开源项目</h1>
  <div class="feedrow">
    <div class="feedtabs" role="tablist">
      <button class="feedtab active" type="button" data-feed="hot" role="tab">热榜</button>
      <button class="feedtab" type="button" data-feed="weekly" role="tab">周榜</button>
    </div>
    <span class="feedhint" id="feedHint">按累计星标排序 · 点任意项目看中文解析</span>
  </div>

  <div class="searchbox">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>
    <input id="q" type="text" placeholder="例如：本地跑大模型推理、股票回测、视频自动剪辑…" autocomplete="off" spellcheck="false">
    <button id="go" type="button">搜索</button>
  </div>

  <div class="chips" id="chips">
    <button class="chip" type="button">本地大模型推理</button>
    <button class="chip" type="button">股票量化回测</button>
    <button class="chip" type="button">视频自动剪辑</button>
    <button class="chip" type="button">文档转 Markdown</button>
    <button class="chip" type="button">网页爬虫反爬</button>
  </div>
</div>

<div class="statusbar" id="status"></div>
<div class="pillbar" id="pills"></div>
<div class="listtitle" id="listTitle"></div>
<main class="results" id="results">
  <div class="empty"><div class="spinner" style="margin:0 auto 12px"></div>正在加载热门项目…</div>
</main>
<div class="more" id="more" hidden></div>

<section class="drawer" id="drawer">
  <div class="dbar"><div class="dbarin">
    <button class="back" id="back" type="button">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M15 5l-7 7 7 7"/></svg>
      返回结果
    </button>
    <span class="tag" id="drawerTag"></span>
  </div></div>
  <div class="dhead" id="dhead"></div>
  <div class="dbody" id="dbody"></div>
  <div class="foot">翻译内容由本地模型实时生成，仅作导读，实际内容以原仓库为准。</div>
</section>

<div class="mmask" id="mmask">
  <div class="mcard" role="dialog" aria-modal="true" aria-labelledby="mtitle">
    <div class="mhead">
      <div>
        <div class="mtitle" id="mtitle">选择本地模型</div>
        <div class="msub">每次打开默认执行 <code>ollama list</code>，模型列表会在执行后出现</div>
      </div>
      <button class="mrefresh" id="mrefresh" type="button">刷新</button>
    </div>
    <div class="mlist" id="mlist"></div>
    <div class="mfoot">选中即切换。标黄的模型为超过8B的模型，翻译的最终速度由机器性能决定。</div>
  </div>
</div>
<div class="toast" id="toast"></div>

<script>
const $ = (s) => document.querySelector(s);
const qEl = $('#q'), goEl = $('#go'), resultsEl = $('#results');
const statusEl = $('#status'), pillsEl = $('#pills'), listTitle = $('#listTitle');
const moreEl = $('#more');
const drawer = $('#drawer'), dbody = $('#dbody'), dhead = $('#dhead'), drawerTag = $('#drawerTag');

const state = { q: '', page: 1, total: 0, loading: false, items: [], mode: 'hot', done: false };

const esc = (s) => String(s == null ? '' : s)
  .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const fmt = (n) => (n == null ? '—' : Number(n).toLocaleString('en-US'));
const setStatus = (h) => { statusEl.innerHTML = h; statusEl.style.display = h ? 'block' : 'none'; };

/* ---------- 列表渲染 ---------- */
function card(it, i){
  const own = it.full_name.split('/')[0], name = it.full_name.split('/')[1];
  const brief = it.brief
    ? '<p class="brief">' + esc(it.brief) + '</p>'
    : '<p class="brief loading">' + esc((it.description || '').slice(0, 80) || '暂无描述') + '</p>';
  return '<article class="res" tabindex="0" data-i="' + i + '">'
    + '<div class="rhead"><span class="rank">' + String(i+1).padStart(2,'0') + '</span>'
    + '<span class="rname"><span class="own">' + esc(own) + '/</span>' + esc(name) + '</span>'
    + (it.language ? '<span class="rb">' + esc(it.language) + '</span>' : '')
    + '</div>' + brief
    + (it.description && it.brief ? '<p class="en">' + esc(it.description.slice(0, 130)) + '</p>' : '')
    + '<div class="rmeta"><span><span class="dot"></span>★ ' + fmt(it.stars) + '</span>'
    + '<span>Fork ' + fmt(it.forks) + '</span>'
    + (it.topics && it.topics.length ? '<span>' + esc(it.topics.slice(0,3).join(' · ')) + '</span>' : '')
    + '</div></article>';
}

function paint(append, from){
  if (!append){
    resultsEl.innerHTML = state.items.map(card).join('');
  } else {
    const start = (from == null) ? 0 : from;
    resultsEl.insertAdjacentHTML('beforeend', state.items.slice(start).map((x, k) => card(x, start + k)).join(''));
  }
  resultsEl.querySelectorAll('.res').forEach(el => {
    if (el.dataset.bound) return;
    el.dataset.bound = '1';
    el.addEventListener('click', () => openDetail(Number(el.dataset.i)));
    el.addEventListener('keydown', e => { if (e.key === 'Enter') openDetail(Number(el.dataset.i)); });
  });
}

/* ---------- 热榜 / 周榜 ---------- */
const feedHint = $('#feedHint');

function resultTitle(main, sub){
  listTitle.innerHTML = '<strong>' + esc(main) + '</strong><span>' + esc(sub) + '</span>';
}

function markTab(feed){
  document.querySelectorAll('.feedtab').forEach(b => {
    b.classList.toggle('active', b.dataset.feed === feed);
  });
}

const FEED_API = { hot: '/api/hot', weekly: '/api/weekly' };
const FEED_CAP = 100;   // 每个榜最多加载 100 个，避免把匿名 API 配额烧光

async function loadHot(page){ return loadFeed('hot', page || 1); }
async function loadWeekly(page){ return loadFeed('weekly', page || 1); }

async function loadFeed(feed, page){
  state.mode = 'feed';
  state.feed = feed;
  if (page === 1){
    state.items = [];
    state.total = 0;
    state.done = false;
    markTab(feed);
    feedHint.textContent = feed === 'weekly'
      ? '近 7 天新建的高星项目 · 每周滚动更新'
      : '按累计星标排序 · 点任意项目看中文解析';
    resultTitle(feed === 'weekly' ? '周榜' : '热榜', '正在加载…');
    setStatus('');
    resultsEl.innerHTML = '<div class="empty"><div class="spinner" style="margin:0 auto 12px"></div>正在加载…</div>';
  }
  try{
    const d = await (await fetch(FEED_API[feed] + '?page=' + page)).json();
    if (d.error){ resultsEl.innerHTML = '<div class="empty err">' + esc(d.error) + '</div>'; return; }
    const list = d.results || [];
    const before = state.items.length;
    state.items = (page === 1) ? list : state.items.concat(list);
    state.total = d.total || state.items.length;
    state.page = page;
    state.done = list.length < 20 || state.items.length >= FEED_CAP;
    if (page === 1) paint(false); else paint(true, before);
    loadBriefs(list);
    if (feed === 'weekly'){
      resultTitle('周榜', d.since + ' 之后新建 · 按星标排序');
    } else {
      resultTitle('热榜', '累计星标最多的项目 · GitHub 共 ' + fmt(state.total) + ' 个');
    }
    moreUpdate();
    autoMore();
  } catch(e){
    resultsEl.innerHTML = '<div class="empty err">加载失败：' + esc(e.message) + '</div>';
  }
}

document.querySelectorAll('.feedtab').forEach(btn => {
  btn.addEventListener('click', () => {
    if (btn.dataset.feed === 'weekly') loadWeekly();
    else loadHot();
  });
});

/* ---------- 搜索 ---------- */
async function doSearch(){
  const q = qEl.value.trim();
  if (!q) return;
  goEl.disabled = true;
  state.q = q; state.page = 1; state.done = false; state.items = [];
  markTab('');
  feedHint.textContent = '用中文描述需求，模型会翻成英文检索词';
  resultsEl.innerHTML = '<div class="empty"><div class="spinner" style="margin:0 auto 12px"></div>正在翻译检索词并搜索 GitHub…</div>';
  setStatus(''); pillsEl.innerHTML = ''; resultTitle('搜索结果', '');
  try{
    const d = await (await fetch('/api/search?q=' + encodeURIComponent(q) + '&page=1')).json();
    if (d.error){ resultsEl.innerHTML = '<div class="empty err">' + esc(d.error) + '</div>'; return; }
    state.mode = 'search';
    state.total = d.total || 0;
    state.items = d.results || [];
    state.done = state.items.length < 20;
    renderStatus(d);
    resultTitle('搜索结果', 'GitHub 命中约 ' + fmt(state.total) + ' 个仓库');
    paint(false);
    moreUpdate();
    autoMore();
    loadBriefs(state.items);
  } catch(e){
    resultsEl.innerHTML = '<div class="empty err">请求失败：' + esc(e.message) + '</div>';
  } finally { goEl.disabled = false; }
}

async function loadMore(){
  if (state.done || state.loading || !state.mode) return;
  state.loading = true;
  moreEl.hidden = false;
  moreEl.innerHTML = '<div class="spinner"></div>正在加载更多…';
  const page = state.page + 1;
  try{
    let d;
    if (state.mode === 'search'){
      d = await (await fetch('/api/search?q=' + encodeURIComponent(state.q) + '&page=' + page)).json();
    } else {
      d = await (await fetch(FEED_API[state.feed] + '?page=' + page)).json();
    }
    if (d.error){ moreEl.innerHTML = '<span class="err">' + esc(d.error) + '</span>'; return; }
    const list = d.results || [];
    if (!list.length){ state.done = true; moreEl.innerHTML = '已经是全部结果了'; return; }
    const before = state.items.length;
    state.items = state.items.concat(list);
    state.page = page;
    if (state.total === 0 && d.total) state.total = d.total;
    const cap = state.mode === 'search' ? 1000 : FEED_CAP;
    state.done = list.length < 20 || state.items.length >= cap;
    paint(true, before);
    loadBriefs(list);
  } catch(e){
    moreEl.innerHTML = '<span class="err">加载失败：' + esc(e.message) + '</span>';
  } finally {
    state.loading = false;
    moreUpdate();
    autoMore();
  }
}

/* 屏幕很高、一屏没填满时也继续拉下一页 */
function autoMore(){
  if (!state.mode || state.done || state.loading) return;
  if (document.body.offsetHeight < window.innerHeight + 400) setTimeout(loadMore, 60);
}

function moreUpdate(){
  if (!state.mode){ moreEl.hidden = true; return; }
  moreEl.hidden = false;
  const cap = state.mode === 'search' ? '（GitHub 最多返回 1000 条）' : '（本页最多加载 100 个）';
  if (state.done){
    moreEl.innerHTML = '已加载 ' + state.items.length + ' / ' + fmt(state.total) + ' 个' + cap;
    return;
  }
  moreEl.innerHTML = '已加载 ' + state.items.length + ' / ' + fmt(state.total) + ' 个 · 继续下滑自动加载';
}

window.addEventListener('scroll', () => {
  if (window.innerHeight + window.scrollY > document.body.offsetHeight - 600) loadMore();
});

function renderStatus(d){
  setStatus('中文「<b>' + esc(d.q) + '</b>」 → 英文检索「<b>' + esc(d.expanded) + '</b>」'
    + (d.from_model ? '' : '（模型未参与，直接检索原文）')
    + '　·　用时 ' + d.took + 's · ' + (d.cached ? '命中缓存' : '实时检索'));
  pillsEl.innerHTML = ((d.quick && d.quick.keywords) || []).map(k => '<span class="pill">' + esc(k) + '</span>').join('');
}

/* ---------- 批量中文介绍（每批 14 条，服务端上限） ---------- */
async function loadBriefs(items){
  const pending = (items || []).filter(x => !x.brief);
  if (!pending.length) return;
  for (let i = 0; i < pending.length && i < 42; i += 14){
    await briefsBatch(pending.slice(i, i + 14));
  }
}

async function briefsBatch(items){
  if (!items.length) return;
  try{
    const r = await fetch('/api/briefs', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({items: items.map(x => ({
        full_name: x.full_name, description: x.description, language: x.language
      }))})
    });
    const d = await r.json();
    const map = d.briefs || {};
    let changed = false;
    state.items.forEach(it => { if (map[it.full_name] && map[it.full_name] !== it.brief){ it.brief = map[it.full_name]; changed = true; } });
    if (changed) paint(false);
  } catch(e){ /* 静默失败，保留英文描述 */ }
}

/* ---------- 详情：先出头部，正文流式 ---------- */
function openDetail(i){
  const it = state.items[i];
  if (!it) return;
  drawer.classList.add('show');
  document.body.style.overflow = 'hidden';
  drawer.scrollTop = 0;
  drawerTag.textContent = it.full_name;
  state.detailName = it.full_name;
  state.facts = null;

  // 立刻用列表里已有的数据把头部画出来，不等网络
  dhead.innerHTML = '<div class="dname"><span class="own">' + esc(it.full_name.split('/')[0]) + '/</span>'
    + esc(it.full_name.split('/')[1]) + '</div>'
    + (it.brief || it.description ? '<div class="ddesc">' + esc(it.brief || it.description) + '</div>' : '')
    + '<div class="dstats"><span>★ <b>' + fmt(it.stars) + '</b></span>'
    + '<span>Fork <b>' + fmt(it.forks) + '</b></span>'
    + '<span>语言 <b>' + esc(it.language || '—') + '</b></span></div>'
    + '<div class="streamtag" id="streamtag"><i></i>正在读取仓库信息…</div>';
  dbody.innerHTML = '<div class="waitline" id="waitline"><div class="spinner"></div>正在准备本地翻译…</div>';

  startStream(it.full_name);
}

/* 顶部状态胶囊：翻译中显示实时 tok/s，完成后显示完成与均速 */
function updateTag(mode, tps, n){
  const el = document.getElementById('streamtag');
  if (!el) return;
  const rate = (tps && tps > 0) ? '<b>' + Number(tps).toFixed(1) + '</b> tok/s' : '';
  if (mode === 'live'){
    el.className = 'streamtag';
    el.innerHTML = '<i></i>本地模型实时翻译中' + (rate ? ' · ' + rate : ' · 首字已出');
  } else if (mode === 'cache'){
    el.className = 'streamtag done';
    el.innerHTML = '翻译完成 · 来自缓存';
  } else {
    el.className = 'streamtag done';
    el.innerHTML = '翻译完成' + (rate ? ' · ' + rate : '');
  }
}

let es = null;
function startStream(name){
  if (es) { es.close(); es = null; }
  const buffer = { text: '' };
  es = new EventSource('/api/repo_stream?name=' + encodeURIComponent(name));

  es.addEventListener('meta', (ev) => {
    const d = JSON.parse(ev.data);
    const m = d.meta || {};
    const tag = d.meta ? '<div class="streamtag" id="streamtag"><i></i>本地模型实时翻译中</div>' : '';
    dhead.innerHTML = '<div class="dname"><span class="own">' + esc((m.full_name||'').split('/')[0]) + '/</span>'
      + esc((m.full_name||'').split('/')[1]) + '</div>'
      + (m.description ? '<div class="ddesc">' + esc(m.description) + '</div>' : '')
      + '<div class="dstats"><span>★ <b>' + fmt(m.stars) + '</b></span>'
      + '<span>Fork <b>' + fmt(m.forks) + '</b></span>'
      + '<span>语言 <b>' + esc(m.language || '—') + '</b></span>'
      + '<span>协议 <b>' + esc(m.license || '—') + '</b></span></div>' + tag
      + '<div class="pullbar">'
      + '<button class="btn-accent" id="pullbtn">拉取到本地</button>'
      + '<a class="btn-ghost" href="' + esc(m.html_url||'#') + '" target="_blank" rel="noopener">打开原仓库 ↗</a>'
      + '</div><div id="pullarea"></div>';
    document.getElementById('pullbtn').addEventListener('click', pullOpen);
    let hero = '';
    if (d.images && d.images.length) hero = '<div class="heroimg"><img src="' + esc(d.images[0]) + '" alt=""></div>';
    dbody.innerHTML = hero
      + '<div id="factsarea"></div>'
      + '<div id="readmearea"></div>'
      + '<div class="sec" style="margin-top:26px"><h2>中文解读</h2></div>'
      + '<div id="streamarea"><div class="waitline"><div class="spinner"></div>模型正在读 README，马上开始出字…</div></div>';
  });

  // 规则层：判断卡 / 能不能跑 / 代码地图 / 按钮导读 / README 目录
  es.addEventListener('facts', (ev) => {
    const d = JSON.parse(ev.data);
    state.facts = d.facts || {};
    const area = document.getElementById('factsarea');
    if (area) area.innerHTML = renderFacts(state.facts);
    renderReadmeToc(state.facts);
  });

  es.addEventListener('extra', (ev) => {
    const d = JSON.parse(ev.data);
    if (!d.images || !d.images.length) return;
    if (document.querySelector('.heroimg')) return;
    const area = document.getElementById('streamarea');
    const html = '<div class="heroimg"><img src="' + esc(d.images[0]) + '" alt="" loading="lazy"></div>';
    if (area) area.insertAdjacentHTML('beforebegin', html);
    else dbody.insertAdjacentHTML('afterbegin', html);
  });

  es.addEventListener('chunk', (ev) => {
    const d = JSON.parse(ev.data);
    buffer.text += d.text || '';
    paintStream(buffer.text, false);
    updateTag('live', d.tps, d.n);
  });

  es.addEventListener('full', (ev) => {
    const d = JSON.parse(ev.data);
    paintStructured(d.local || {});
    es.close(); es = null;
  });

  es.addEventListener('done', (ev) => {
    const d = JSON.parse(ev.data);
    // 正文已经边翻边显示过了，这里只收尾，不整体重绘，避免闪烁
    if (buffer.text.trim()) paintStream(buffer.text, true);
    else if (d.parsed) paintStructured(d.parsed);
    updateTag(d.source === 'cache' ? 'cache' : 'done', d.tps, d.tokens);
    es.close(); es = null;
  });

  es.addEventListener('error', (ev) => {
    let msg = '翻译连接中断';
    try { const d = JSON.parse(ev.data); if (d && d.error) msg = d.error; } catch(e){}
    const area = document.getElementById('streamarea') || dbody;
    area.insertAdjacentHTML('beforeend', '<div class="sec"><p class="err">' + esc(msg) + '</p></div>');
    if (es) { es.close(); es = null; }
  });
}

function fmtSize(mb){
  if (!mb) return '';
  if (mb >= 1024) return (mb / 1024).toFixed(1) + ' GB';
  return Math.round(mb) + ' MB';
}

/* ---------- 规则层渲染：判断卡 / 能不能跑 / 代码地图 / 按钮导读 ---------- */
function renderFacts(f){
  const fresh = f.fresh || {}, lic = f.license || {}, kind = f.kind || {};
  let h = '<div class="facts"><div class="judge">'
    + '<span class="badge">类别 <b>' + esc(kind.label || '—') + '</b></span>'
    + '<span class="badge"><i class="dot ' + (fresh.level || 'unknown') + '"></i>' + esc(fresh.text || '—') + '</span>'
    + '<span class="badge">协议 <b>' + esc(lic.spdx || '—') + '</b></span>'
    + (f.size_mb ? '<span class="badge">体积 <b>' + fmtSize(f.size_mb) + '</b></span>' : '')
    + '</div>';
  h += '<p class="verdict">' + esc(f.verdict || '') + '</p>';
  if (lic.vibe) h += '<p class="pullhint">协议 ' + esc(lic.spdx || '—') + '：' + esc(lic.vibe) + '</p>';

  // 我能不能跑起来
  h += '<div class="block"><h3>我能不能跑起来 <em>按仓库结构判断，不靠模型猜</em></h3>';
  if (f.runtime && f.runtime.length){
    h += '<div class="brow"><span class="k">运行环境</span><span class="v">'
      + f.runtime.map(r => '<span class="badge" title="' + esc(r.why) + '">' + esc(r.name) + '</span>').join(' ')
      + '</span></div>';
  } else {
    h += '<div class="brow"><span class="k">运行环境</span><span class="v">没看到常见语言栈的文件，可能是纯静态项目或文档仓库</span></div>';
  }
  if (f.hardware) h += '<div class="brow"><span class="k">硬件</span><span class="v">' + esc(f.hardware) + '</span></div>';
  if (f.entry && f.entry.length){
    h += '<div class="brow"><span class="k">入口文件</span><span class="v">'
      + f.entry.slice(0, 3).map(e => '<code>' + esc(e.path) + '</code> ' + esc(e.why)).join('<br>') + '</span></div>';
  }
  if (f.install_cmds && f.install_cmds.length){
    h += '<div style="margin-top:10px"><div class="cmds" data-cmd="' + esc(f.install_cmds.join('\n')) + '">'
      + '<button onclick="copyCmd(this)">复制</button>' + esc(f.install_cmds.join('\n')) + '</div>'
      + '<div class="pullhint">从 README 里原样提取的安装命令，代码不翻译</div></div>';
  } else {
    h += '<div class="brow"><span class="k">安装</span><span class="v">README 里没找到现成安装命令，看下面「快速上手」那段</span></div>';
  }
  h += '</div>';

  // 代码地图
  if (f.map && f.map.length){
    h += '<div class="block"><h3>代码地图 <em>哪块是心脏，哪块可以跳过</em></h3><div class="mapbox">'
      + f.map.map(r => '<div class="maprow"><code>' + esc(r.path) + '</code><span>' + esc(r.note) + '</span>'
          + '<span class="tag ' + (r.read ? 'read' : 'skip') + '">' + (r.read ? '要看' : '跳过') + '</span></div>').join('')
      + '</div></div>';
  }

  // 按钮导读
  h += '<div class="block"><h3>按钮导读 <em>GitHub 那一排按钮到底是什么</em></h3>'
    + '<table class="terms"><thead><tr><th style="width:32%">按钮</th><th style="width:24%">人话</th><th>该不该点</th></tr></thead><tbody>'
    + (f.buttons || []).map(b => '<tr><td><code>' + esc(b.name) + '</code></td><td>' + esc(b.zh) + '</td><td>' + esc(b.act) + '</td></tr>').join('')
    + '</tbody></table></div>';
  h += '</div>';
  return h;
}

function copyCmd(btn){
  const box = btn.closest('.cmds');
  const text = box ? box.dataset.cmd : '';
  try { navigator.clipboard.writeText(text); btn.textContent = '已复制'; setTimeout(() => { btn.textContent = '复制'; }, 1400); }
  catch(e){ btn.textContent = '复制失败'; }
}

/* ---------- README 分节翻译 ---------- */
let esR = null;
function renderReadmeToc(f){
  const area = document.getElementById('readmearea');
  if (!area) return;
  const toc = (f && f.readme_toc) || [];
  if (!toc.length){ area.innerHTML = ''; return; }
  area.innerHTML = '<div class="sec"><h2>README 中文翻译</h2>'
    + '<p class="pullhint">共 ' + toc.length + ' 节。点标题逐节翻，边翻边出字；代码块与命令原样保留。</p>'
    + '<div class="toc">' + toc.map(s => '<button data-sec="' + s.i + '">' + esc(s.title) + '</button>').join('') + '</div>'
    + '<div id="rsecbox"></div></div>';
  area.querySelectorAll('.toc button').forEach(b => {
    b.addEventListener('click', () => openSection(Number(b.dataset.sec)));
  });
}

function openSection(i){
  const box = document.getElementById('rsecbox');
  if (!box) return;
  document.querySelectorAll('#readmearea .toc button').forEach(b => {
    b.classList.toggle('active', Number(b.dataset.sec) === i);
  });
  if (esR){ esR.close(); esR = null; }
  box.innerHTML = '<div class="rsec"><div class="spinner" style="display:inline-block;vertical-align:-4px;margin-right:8px"></div>正在翻译这一节…</div>';
  esR = new EventSource('/api/readme_sec?name=' + encodeURIComponent(state.detailName) + '&i=' + i);
  esR.addEventListener('start', () => {
    box.innerHTML = '<div class="rsec" id="rsecline"><span class="cursor"></span></div>';
  });
  esR.addEventListener('chunk', (ev) => {
    const d = JSON.parse(ev.data);
    const el = document.getElementById('rsecline');
    if (el) el.textContent += d.text || '';
  });
  esR.addEventListener('done', (ev) => {
    let d = {};
    try { d = JSON.parse(ev.data); } catch(e){}
    const el = document.getElementById('rsecline');
    if (el && d.text) el.textContent = d.text;
    if (esR){ esR.close(); esR = null; }
  });
  esR.addEventListener('error', () => {
    const el = document.getElementById('rsecline');
    if (el && !el.textContent) el.innerHTML = '<span class="err">这一节翻译失败，换个模型或重试</span>';
    if (esR){ esR.close(); esR = null; }
  });
}

/* ---------- 一键拉取 ---------- */
let esC = null, pullJob = '';
async function pullOpen(){
  if (!state.detailName) return;
  const box = document.getElementById('pullarea');
  if (box) box.innerHTML = '<div class="pullhint">正在读取下载信息…</div>';
  try{
    const p = await (await fetch('/api/clone_prep?name=' + encodeURIComponent(state.detailName))).json();
    state.pull = p;
    renderPullPanel(p);
  } catch(e){
    if (box) box.innerHTML = '<div class="pullhint err">读取失败：' + esc(e.message) + '</div>';
  }
}

function renderPullPanel(p, hint){
  const box = document.getElementById('pullarea');
  if (!box) return;
  const size = p.size_mb ? '（约 ' + fmtSize(p.size_mb) + '）' : '';
  box.innerHTML = '<div class="pullpanel">'
    + '<div class="lab">保存位置</div>'
    + '<div class="pullpath">' + esc(p.dest || p.base || '') + '</div>'
    + '<div class="pullbar">'
    + (p.exists
        ? '<button class="btn-accent" id="pullopen">打开文件夹</button>'
        : '<button class="btn-accent" id="pullgo">开始拉取' + size + '</button>')
    + '<button class="btn-ghost" id="pullpick">换个位置…</button>'
    + '<button class="btn-ghost" id="pullcancel" hidden>取消</button>'
    + '</div>'
    + '<div class="pullbar" style="margin-top:2px">'
    + '<input id="pullinput" placeholder="也可以直接输入路径，例如 E:\\repos" '
    + 'style="flex:1;min-width:200px;border:1px solid var(--line);border-radius:8px;padding:7px 11px;font-size:12.5px;font-family:var(--mono)">'
    + '<button class="btn-ghost" id="pulluse">用这个路径</button>'
    + '</div>'
    + '<div class="bar"><i id="pullbarfill"></i></div>'
    + '<div class="pullhint" id="pullhint">'
    + (hint ? hint : (p.exists ? '这个位置已经有仓库了，可以直接打开。' :
        '只下载代码，不会执行仓库里的任何脚本，依赖需要你自己装。' + (p.disk_free_gb ? ' 该盘剩余 ' + p.disk_free_gb + ' GB。' : '')))
    + '</div>'
    + '<div class="dbrw" id="dbrw" hidden></div>'
    + '</div>';

  const pick = document.getElementById('pullpick');
  if (pick) pick.addEventListener('click', pullPick);
  const use = document.getElementById('pulluse');
  if (use) use.addEventListener('click', pullSetDir);
  const open = document.getElementById('pullopen');
  if (open) open.addEventListener('click', () => {
    fetch('/api/open_folder?path=' + encodeURIComponent(state.pull.dest)).then(r => r.json()).then(d => {
      if (!d.ok) setPullHint('打开失败，路径：' + state.pull.dest);
    });
  });
  const go = document.getElementById('pullgo');
  if (go) go.addEventListener('click', pullStart);
}

function setPullHint(t){
  const el = document.getElementById('pullhint');
  if (el) el.innerHTML = esc(t);
}

async function pullSetDir(){
  const inp = document.getElementById('pullinput');
  const path = (inp && inp.value || '').trim();
  if (!path){ setPullHint('先填一个目录，比如 E:\\repos'); return; }
  setPullHint('正在检查目录…');
  try{
    const r = await (await fetch('/api/set_dir?name=' + encodeURIComponent(state.detailName)
      + '&path=' + encodeURIComponent(path) + '&_=' + Date.now(), {cache:'no-store'})).json();
    if (r.error){ setPullHint(r.error); return; }
    await refreshPullPanel('保存位置已设为 ' + r.base);
  } catch(e){
    setPullHint('设置目录失败：' + e.message);
  }
}

async function refreshPullPanel(msg){
  // 不信任任何一次响应里的 dest，重新向服务端要一份最新状态再渲染
  try{
    const p = await (await fetch('/api/clone_prep?name=' + encodeURIComponent(state.detailName)
      + '&_=' + Date.now(), {cache:'no-store'})).json();
    state.pull = p;
    renderPullPanel(p, msg);
  }catch(e){ setPullHint('刷新失败：' + e.message); }
}

async function pullPick(){
  // 不再弹系统对话框：直接展开页面内的文件夹列表，点目录 → 确认
  setPullHint('选一个文件夹，点「用这个文件夹」就生效。');
  openDirBrowser('');
}

/* ---------- 页面内文件夹浏览器 ---------- */
async function openDirBrowser(path){
  const box = document.getElementById('dbrw');
  if (!box) return;
  box.hidden = false;
  box.innerHTML = '<div class="pullhint">正在读取目录…</div>';
  try{
    const d = await (await fetch('/api/ls_dir?path=' + encodeURIComponent(path || ''))).json();
    if (d.error){ box.innerHTML = '<div class="pullhint err">' + esc(d.error) + '</div>'
      + '<div class="dbfoot"><button class="btn-ghost" id="dbclose">收起</button></div>';
      const c = document.getElementById('dbclose');
      if (c) c.addEventListener('click', () => { box.hidden = true; box.innerHTML = ''; });
      return;
    }
    renderDirBrowser(d);
  } catch(e){
    box.innerHTML = '<div class="pullhint err">读取失败：' + esc(e.message) + '</div>';
  }
}

function renderDirBrowser(d){
  const box = document.getElementById('dbrw');
  if (!box) return;
  const rows = (d.dirs || []).map(it =>
      '<div class="dbrow" data-p="' + esc(it.path) + '">'
      + '<span class="dbicon">▸</span><span class="dbname">' + esc(it.name) + '</span>'
      + (it.free_gb ? '<span class="dbfree">' + it.free_gb + ' GB 可用</span>' : '')
      + '</div>').join('')
    || '<div class="pullhint" style="padding:0 12px 10px">这里没有子文件夹，可以直接选当前目录。</div>';
  box.innerHTML = '<div class="dbhead"><span>选择保存位置</span><span class="dbcur">'
    + esc(d.path || '此电脑 · 先选一个盘') + (d.free_gb ? ' · ' + d.free_gb + ' GB 可用' : '') + '</span></div>'
    + '<div class="dbbody">' + rows + '</div>'
    + '<div class="dbfoot">'
    + (d.path ? '<button class="btn-accent" id="dbok">用这个文件夹</button>' : '')
    + (d.path ? '<button class="btn-ghost" id="dbup">上一级</button>' : '')
    + '<button class="btn-ghost" id="dbclose">收起</button>'
    + '</div>';

  box.querySelectorAll('.dbrow').forEach(el => {
    el.addEventListener('click', () => openDirBrowser(el.getAttribute('data-p')));
  });
  const up = document.getElementById('dbup');
  if (up) up.addEventListener('click', () => openDirBrowser(d.parent || ''));
  const btnOk = document.getElementById('dbok');
  if (btnOk) btnOk.addEventListener('click', async () => {
    setPullHint('正在设置目录…');
    try{
      const r = await (await fetch('/api/set_dir?name=' + encodeURIComponent(state.detailName)
        + '&path=' + encodeURIComponent(d.path) + '&_=' + Date.now(), {cache:'no-store'})).json();
      if (r.error){ setPullHint(r.error); return; }
      await refreshPullPanel('保存位置已设为 ' + r.base);
    } catch(e){ setPullHint('设置目录失败：' + e.message); }
  });
  const cl = document.getElementById('dbclose');
  if (cl) cl.addEventListener('click', () => { box.hidden = true; box.innerHTML = ''; });
}

function pullStart(){
  if (!state.detailName) return;
  if (esC){ esC.close(); esC = null; }
  pullJob = 'j' + Date.now();
  const go = document.getElementById('pullgo');
  const cancel = document.getElementById('pullcancel');
  if (go){ go.disabled = true; go.textContent = '拉取中…'; }
  if (cancel) cancel.hidden = false;
  setPullHint('正在连接 GitHub…');
  esC = new EventSource('/api/clone?name=' + encodeURIComponent(state.detailName)
    + '&dest=' + encodeURIComponent(state.pull.dest) + '&job=' + pullJob);
  esC.addEventListener('progress', (ev) => {
    const d = JSON.parse(ev.data);
    const fill = document.getElementById('pullbarfill');
    if (fill && typeof d.pct === 'number') fill.style.width = Math.max(2, d.pct) + '%';
    if (d.text) setPullHint(d.text);
  });
  esC.addEventListener('done', (ev) => {
    const d = JSON.parse(ev.data);
    const fill = document.getElementById('pullbarfill');
    if (fill) fill.style.width = '100%';
    setPullHint((d.existing ? '这个目录里已经有仓库了' : '拉取完成') + (d.size_mb ? ' · 占用 ' + d.size_mb + ' MB' : '') + ' · ' + d.dir);
    if (go){ go.hidden = true; }
    if (cancel) cancel.hidden = true;
    const bar = document.querySelector('.pullpanel .pullbar');
    if (bar && !document.getElementById('pullopen')){
      const b = document.createElement('button');
      b.className = 'btn-accent';
      b.id = 'pullopen';
      b.textContent = '打开文件夹';
      b.addEventListener('click', () => {
        fetch('/api/open_folder?path=' + encodeURIComponent(d.dir)).then(r => r.json());
      });
      bar.insertBefore(b, bar.firstChild);
    }
    if (esC){ esC.close(); esC = null; }
  });
  esC.addEventListener('error', (ev) => {
    let msg = '拉取失败';
    try { const d = JSON.parse(ev.data); if (d && d.error) msg = d.error; } catch(e){}
    setPullHint(msg);
    if (go){ go.disabled = false; go.textContent = '重试拉取'; }
    if (cancel) cancel.hidden = true;
    if (esC){ esC.close(); esC = null; }
  });
}

/* 取消按钮：先拆 SSE，再通知后端 kill git */
document.addEventListener('click', function(ev){
  const t = ev.target;
  if (t && t.id === 'pullcancel'){
    fetch('/api/clone_cancel?job=' + encodeURIComponent(pullJob)).then(r => r.json());
    if (esC){ esC.close(); esC = null; }
    setPullHint('已取消拉取');
    const go = document.getElementById('pullgo');
    if (go){ go.disabled = false; go.textContent = '重新拉取'; }
    t.hidden = true;
  }
});

/* 把【字段】流式文本渲染成分节内容，末尾带光标 */
function paintStream(text, finished){
  let area = document.getElementById('streamarea');
  if (!area){ dbody.innerHTML = '<div id="streamarea"></div>'; area = $('#streamarea'); }
  const parts = text.split(/【([^】]{1,8})】/);
  let h = '';
  if (parts[0].trim()) h += '<p class="ddesc">' + esc(parts[0].trim()) + '</p>';
  for (let k = 1; k < parts.length; k += 2){
    const name = parts[k].trim();
    const body = (parts[k+1] || '');
    const isLast = (k + 2 >= parts.length);
    h += renderSection(name, body, isLast && !finished);
  }
  area.innerHTML = h || '<div class="waitline"><div class="spinner"></div>模型正在组织语言…</div>';
  if (finished && area.innerHTML === '') area.innerHTML = '<div class="waitline">没有生成内容，换一个仓库试试</div>';
}

function renderSection(name, body, typing){
  const cur = typing ? '<span class="cursor"></span>' : '';
  if (name === '速览'){
    return '<p class="lede">' + esc(body.trim()) + cur + '</p>';
  }
  if (name === '主要功能' || name === '值得学的点'){
    const items = body.split('\n').map(s => s.replace(/^[-•*]\s*/, '').trim()).filter(Boolean);
    return '<div class="sec"><h2>' + esc(name) + '</h2><ul>'
      + items.map(x => '<li>' + esc(x) + '</li>').join('') + '</ul>' + (typing && !items.length ? cur : '') + '</div>';
  }
  if (name === '项目结构'){
    const rows = body.split('\n').map(s => s.replace(/^[-•*]\s*/, '').trim()).filter(Boolean).map(s => {
      const m = s.match(/([^：:]+)[：:]\s*(.*)/);
      return m ? {p: m[1], d: m[2]} : {p: s, d: ''};
    });
    if (!rows.length && typing) return '<div class="sec"><h2>项目结构</h2><p>' + cur + '</p></div>';
    return '<div class="sec"><h2>项目结构解读</h2><div class="tree">'
      + rows.map(r => '<div class="tree-row"><code>' + esc(r.p) + '</code><span>' + esc(r.d) + '</span></div>').join('')
      + '</div></div>';
  }
  if (name === '术语表'){
    const rows = body.split('\n').map(s => s.replace(/^[-•*]\s*/, '').trim()).filter(Boolean)
      .map(s => s.split('|').map(x => x.trim())).filter(p => p.length >= 2);
    if (!rows.length && typing) return '<div class="sec"><h2>术语表</h2><p>' + cur + '</p></div>';
    return '<div class="sec"><h2>术语表</h2><table class="terms"><thead><tr>'
      + '<th style="width:24%">英文</th><th style="width:20%">中文</th><th>解释</th></tr></thead><tbody>'
      + rows.map(p => '<tr><td><code>' + esc(p[0]) + '</code></td><td>' + esc(p[1]) + '</td><td>' + esc(p[2] || '') + '</td></tr>').join('')
      + '</tbody></table></div>';
  }
  const txt = body.trim();
  if (!txt && !typing) return '';
  const clean = escapeInlineCode(txt.replace(/```[a-zA-Z]*/g, '').replace(/```/g, ''));
  return '<div class="sec"><h2>' + esc(name) + '</h2><p>' + clean + cur + '</p></div>';
}

/* 把 `命令` 渲染成行内 code，其余转义 */
function escapeInlineCode(text){
  return esc(text).replace(/`([^`]{1,80})`/g, '<code style="font-family:var(--mono);background:#f2f5f5;border-radius:4px;padding:1px 5px;font-size:13px">$1</code>');
}

/* 结构化数据（缓存命中或已解析）直接渲染 */
function paintStructured(L){
  const area = document.getElementById('streamarea') || dbody;
  const order = ['速览','它是什么','解决什么问题','核心机制','主要功能','项目结构','快速上手','值得学的点','适合谁','术语表'];
  let h = '';
  if (L['速览']) h += '<p class="lede">' + esc(L['速览']) + '</p>';
  order.slice(1).forEach(k => {
    const v = L[k];
    if (!v) return;
    if (Array.isArray(v)){
      if (k === '主要功能' || k === '值得学的点'){
        h += '<div class="sec"><h2>' + k + '</h2><ul>' + v.map(x => '<li>' + esc(x) + '</li>').join('') + '</ul></div>';
      } else if (k === '项目结构'){
        h += '<div class="sec"><h2>项目结构解读</h2><div class="tree">'
          + v.map(t => '<div class="tree-row"><code>' + esc(t['路径']) + '</code><span>' + esc(t['作用']) + '</span></div>').join('')
          + '</div></div>';
      } else if (k === '术语表'){
        h += '<div class="sec"><h2>术语表</h2><table class="terms"><thead><tr>'
          + '<th style="width:24%">英文</th><th style="width:20%">中文</th><th>解释</th></tr></thead><tbody>'
          + v.map(t => '<tr><td><code>' + esc(t['英文']) + '</code></td><td>' + esc(t['中文']) + '</td><td>' + esc(t['解释']) + '</td></tr>').join('')
          + '</tbody></table></div>';
      }
    } else {
      h += '<div class="sec"><h2>' + k + '</h2><p>' + escapeInlineCode(String(v).replace(/```[a-zA-Z]*/g, '').replace(/```/g, '')) + '</p></div>';
    }
  });
  area.innerHTML = h || '<div class="waitline">本次没有生成内容</div>';
}

function closeDrawer(){
  if (es) { es.close(); es = null; }
  drawer.classList.remove('show');
  document.body.style.overflow = '';
}
$('#back').addEventListener('click', closeDrawer);
document.addEventListener('keydown', e => {
  if (e.key !== 'Escape') return;
  if (mmask.classList.contains('show')) { mmask.classList.remove('show'); return; }
  closeDrawer();
});

goEl.addEventListener('click', doSearch);
qEl.addEventListener('keydown', e => { if (e.key === 'Enter') doSearch(); });
document.querySelectorAll('.chip').forEach(c => c.addEventListener('click', () => {
  qEl.value = c.textContent.trim(); doSearch();
}));

/* ---------- 模型选择 ---------- */
const modelBtn = $('#modelBtn'), modelLabel = $('#modelLabel');
const mmask = $('#mmask'), mlist = $('#mlist'), toastEl = $('#toast');
let toastTimer = null;
function toast(msg){
  toastEl.textContent = msg;
  toastEl.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toastEl.classList.remove('show'), 2400);
}

function openModels(){
  mmask.classList.add('show');
  loadModels();
}

async function loadModels(){
  mlist.innerHTML = '<div class="mempty"><div class="spinner" style="margin:0 auto 10px"></div>正在执行 ollama list…</div>';
  try{
    const d = await (await fetch('/api/models')).json();
    if (d.error){ mlist.innerHTML = '<div class="mempty err">' + esc(d.error) + '</div>'; return; }
    const list = d.models || [];
    if (!list.length){
      mlist.innerHTML = '<div class="mempty">ollama 里还没有模型，先 <code>ollama pull qwen3:4b</code></div>';
      return;
    }
    if (d.current && modelLabel.textContent !== d.current) modelLabel.textContent = d.current;
    mlist.innerHTML = list.map(modelRow).join('');
    mlist.querySelectorAll('.mrow').forEach(el => {
      el.addEventListener('click', () => switchModel(el.dataset.name, el));
    });
  } catch(e){
    mlist.innerHTML = '<div class="mempty err">读取失败：' + esc(e.message) + '</div>';
  }
}

function heavyModel(params){
  const m = /([\d.]+)\s*B/i.exec(params || '');
  return m ? parseFloat(m[1]) >= 8 : false;
}

function modelRow(m){
  const heavy = heavyModel(m.params);
  const meta = [m.params, m.quant, m.size, m.modified].filter(Boolean);
  const metaHtml = meta.map((x, i) => '<span' + (i === 0 && heavy ? ' class="mwarn"' : '') + '>' + esc(x) + '</span>').join('');
  return '<button class="mrow" type="button" data-name="' + esc(m.name) + '" aria-selected="' + (m.current ? 'true' : 'false') + '">'
    + '<span class="mdot"></span>'
    + '<span class="minfo"><span class="mname">' + esc(m.name) + '</span>'
    + '<span class="mmeta">' + metaHtml + '</span></span>'
    + (m.current ? '<span class="mbadge">当前</span>' : '')
    + '</button>';
}

async function switchModel(name, el){
  if (el) el.disabled = true;
  try{
    const r = await fetch('/api/model', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({model: name})
    });
    const d = await r.json();
    if (d.error){ toast(d.error); if (el) el.disabled = false; return; }
    modelLabel.textContent = d.model;
    mmask.classList.remove('show');
    toast('已切换到 ' + d.model);
  } catch(e){
    toast('切换失败：' + e.message);
    if (el) el.disabled = false;
  }
}

modelBtn.addEventListener('click', openModels);
$('#mrefresh').addEventListener('click', loadModels);
mmask.addEventListener('click', e => { if (e.target === mmask) mmask.classList.remove('show'); });

/* 启动 */
const params = new URLSearchParams(location.search);
const initialQ = params.get('q');
const wantRepo = params.get('repo');
const initialFeed = params.get('feed');
if (params.get('models')) openModels();
if (initialFeed === 'weekly' && !initialQ){ loadWeekly().then(() => { openRepoDeepLink(); }); }
else if (initialQ){ qEl.value = initialQ; doSearch().then(openRepoDeepLink); }
else { loadHot().then(openRepoDeepLink); }

function openRepoDeepLink(){
  if (!wantRepo) return;
  const idx = state.items.findIndex(x => x.full_name === wantRepo);
  if (idx !== -1) openDetail(idx);
  if (params.get('pull')) setTimeout(pullOpen, 1200);   // 调试用：直接打开拉取面板
}
</script>
</body>
</html>
"""
