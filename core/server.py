"""本地 HTTP 服务：把实时检索能力暴露成一个网页。"""
import json
import mimetypes
import os
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import gitpull
from . import i18n
from .searchapp import SearchService
from .webui import PAGE

STATIC_OK = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


class App:
    def __init__(self, cfg, log=print):
        self.cfg = cfg
        self.log = log
        self.svc = SearchService(cfg, log)
        self.html = PAGE.replace("%%MODEL%%", cfg["model"])

    def render(self, lang=""):
        """按语言把首页拼出来（语言包只影响这次响应，不进缓存）。"""
        payload = json.dumps(i18n.payload(lang), ensure_ascii=False)
        return self.html.replace("%%I18N%%", payload).encode("utf-8")


def make_handler(app):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt, *args):
            app.log(f"[web] {fmt % args}")

        # ---------- 工具 ----------
        def _json(self, obj, code=200):
            body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _file(self, path):
            if not os.path.isfile(path):
                self._json({"error": "文件不存在"}, 404)
                return
            ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
            with open(path, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "max-age=3600")
            self.end_headers()
            self.wfile.write(body)

        def _sse(self, generator):
            """服务端推送：边生成边下发，客户端能边翻边看。"""
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.close_connection = True
            self.end_headers()
            try:
                for event, data in generator:
                    chunk = f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
                    self.wfile.write(chunk.encode("utf-8"))
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception as e:
                app.log(f"[sse 错误] {e}")

        # ---------- 路由 ----------
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            path, qs = parsed.path, urllib.parse.parse_qs(parsed.query)
            try:
                if path in ("/", "/index.html"):
                    body = app.render((qs.get("lang") or [""])[0])
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                if path == "/api/search":
                    q = (qs.get("q") or [""])[0]
                    page = (qs.get("page") or ["1"])[0]
                    force = (qs.get("force") or ["0"])[0] == "1"
                    self._json(app.svc.search(q, page=page, force=force))
                    return
                if path == "/api/hot":
                    page = (qs.get("page") or ["1"])[0]
                    self._json(app.svc.hot(page=page))
                    return
                if path == "/api/weekly":
                    page = (qs.get("page") or ["1"])[0]
                    self._json(app.svc.weekly(page=page))
                    return
                if path == "/api/repo_stream":
                    name = (qs.get("name") or [""])[0]
                    self._sse(app.svc.stream_detail(name))
                    return
                if path == "/api/readme_sec":
                    name = (qs.get("name") or [""])[0]
                    idx = (qs.get("i") or ["0"])[0]
                    self._sse(app.svc.stream_readme_section(name, idx))
                    return
                if path == "/api/clone_prep":
                    name = (qs.get("name") or [""])[0]
                    self._json(app.svc.clone_prep(name))
                    return
                if path == "/api/clone":
                    name = (qs.get("name") or [""])[0]
                    dest = (qs.get("dest") or [""])[0]
                    job = (qs.get("job") or [""])[0]
                    self._sse(app.svc.clone_stream(name, dest, job))
                    return
                if path == "/api/clone_cancel":
                    job = (qs.get("job") or [""])[0]
                    gitpull.cancel(job)
                    self._json({"ok": True})
                    return
                if path == "/api/ls_dir":
                    pth = (qs.get("path") or [""])[0]
                    self._json(app.svc.list_dir(pth))
                    return
                if path == "/api/set_dir":
                    pth = (qs.get("path") or [""])[0]
                    r = app.svc.set_download_dir(pth)
                    if r.get("ok") and (qs.get("name") or [""])[0]:
                        r.update(app.svc.clone_prep((qs.get("name") or [""])[0]))
                    self._json(r)
                    return
                if path == "/api/open_folder":
                    folder = (qs.get("path") or [""])[0]
                    self._json({"ok": gitpull.open_folder(folder)})
                    return
                if path == "/api/models":
                    self._json(app.svc.list_models())
                    return
                if path == "/api/health":
                    names = app.svc.localizer.available()
                    self._json({"model": app.svc.localizer.model, "models": names,
                                "remaining": app.svc.client.remaining})
                    return
                if path.startswith("/cache/"):
                    fname = os.path.basename(urllib.parse.unquote(path[len("/cache/"):]))
                    if os.path.splitext(fname)[1].lower() in STATIC_OK:
                        self._file(os.path.join(app.svc.cache_dir, fname))
                        return
                self._json({"error": "not found"}, 404)
            except Exception as e:
                app.log(f"[web 错误] {e}")
                try:
                    self._json({"error": f"服务端异常：{e}"}, 500)
                except Exception:
                    pass

        def do_POST(self):
            parsed = urllib.parse.urlparse(self.path)
            try:
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length) if length else b"{}"
                payload = json.loads(raw.decode("utf-8") or "{}")
                if parsed.path == "/api/briefs":
                    self._json(app.svc.briefs(payload.get("items") or []))
                    return
                if parsed.path == "/api/model":
                    self._json(app.svc.set_model(payload.get("model") or ""))
                    return
                self._json({"error": "not found"}, 404)
            except Exception as e:
                app.log(f"[web 错误] {e}")
                try:
                    self._json({"error": f"服务端异常：{e}"}, 500)
                except Exception:
                    pass

    return Handler


def serve(cfg, port=8790, log=print):
    app = App(cfg, log)
    handler = make_handler(app)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
    httpd.daemon_threads = True
    url = f"http://127.0.0.1:{port}/"
    log(f"实时检索服务已启动：{url}")
    log(f"  模型：{cfg['model']}    按 Ctrl+C 停止")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        log("已停止")
    finally:
        httpd.server_close()
    return url
