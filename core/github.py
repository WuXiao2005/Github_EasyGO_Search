"""GitHub REST API 客户端。只依赖标准库，避免额外安装。"""
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"


class GitHubError(RuntimeError):
    pass


class GitHubClient:
    def __init__(self, token="", timeout=30, log=print):
        self.token = token or os.environ.get("GITHUB_TOKEN", "") or os.environ.get("GH_TOKEN", "")
        self.timeout = timeout
        self.log = log
        self.calls = 0
        self.remaining = None

    # ---------- 底层请求 ----------
    def _headers(self, accept="application/vnd.github+json"):
        h = {"Accept": accept, "User-Agent": "github-weekly-digest/1.0"}
        if self.token:
            h["Authorization"] = "Bearer " + self.token
        return h

    def api(self, path, params=None):
        url = API + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        return self._fetch_json(url, self._headers())

    def _fetch_json(self, url, headers, retries=3):
        for attempt in range(retries):
            req = urllib.request.Request(url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    self.calls += 1
                    self._track_rate(resp.headers)
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                self._track_rate(e.headers)
                if e.code == 404:
                    return None
                if e.code in (403, 429):
                    reset = self._reset_seconds(e.headers)
                    wait = min(max(reset, 5), 120) if reset else 60
                    if attempt < retries - 1:
                        self.log(f"    [限流] 等待 {wait}s 后重试")
                        time.sleep(wait)
                        continue
                    raise GitHubError(f"请求被限流或禁止: {url} (剩余 {self.remaining})")
                raise GitHubError(f"HTTP {e.code}: {url} - {e.read()[:200]!r}") from e
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                if attempt < retries - 1:
                    time.sleep(2 * (attempt + 1))
                    continue
                raise GitHubError(f"网络错误: {url} - {e}") from e
        return None

    def _track_rate(self, headers):
        if not headers:
            return
        rem = headers.get("X-RateLimit-Remaining")
        if rem is not None:
            try:
                self.remaining = int(rem)
            except ValueError:
                pass

    @staticmethod
    def _reset_seconds(headers):
        if not headers:
            return None
        reset = headers.get("X-RateLimit-Reset")
        if not reset:
            return None
        try:
            return int(reset) - int(time.time())
        except (TypeError, ValueError):
            return None

    # ---------- 业务接口 ----------
    def search_repos(self, query, sort="stars", per_page=50, page=1):
        data = self.api(
            "/search/repositories",
            {"q": query, "sort": sort, "order": "desc", "per_page": per_page, "page": page},
        )
        return (data or {}).get("items", [])

    def search_page(self, query, sort=None, per_page=20, page=1):
        """返回原始结果（含 total_count），用于分页展示。"""
        params = {"q": query, "per_page": per_page, "page": page}
        if sort:
            params["sort"] = sort
            params["order"] = "desc"
        return self.api("/search/repositories", params) or {}

    def readme_text(self, full_name):
        """优先走 raw CDN（不消耗 API 配额），失败再退回 API。"""
        for name in ("README.md", "readme.md", "README.rst", "README.txt", "README"):
            url = f"{RAW}/{full_name}/HEAD/{name}"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "github-weekly-digest/1.0"})
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    if resp.status == 200:
                        return resp.read().decode("utf-8", errors="replace")
            except urllib.error.HTTPError:
                continue
            except Exception:
                continue
        data = self.api(f"/repos/{full_name}/readme")
        if not data or not data.get("content"):
            return ""
        import base64

        try:
            return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        except Exception:
            return ""

    def tree(self, full_name, branch="main"):
        data = self.api(f"/repos/{full_name}/git/trees/{branch}", {"recursive": 1})
        if not data:
            return []
        return data.get("tree", [])

    def raw_url(self, full_name, path, branch="HEAD"):
        return f"{RAW}/{full_name}/{branch}/{path}"

    def download(self, url, dest_path):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "github-weekly-digest/1.0"})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read()
            if len(body) > 8 * 1024 * 1024 or len(body) < 6 * 1024:
                return False
            if not is_image_bytes(body):
                return False
            with open(dest_path, "wb") as f:
                f.write(body)
            return True
        except Exception as e:
            self.log(f"    [图片失败] {url} - {e}")
            return False


def is_image_bytes(data):
    """不是真图片就别写盘，否则页面会裂图。"""
    if data[:4] == b"\x89PNG":
        return True
    if data[:2] == b"\xff\xd8":
        return True
    if data[:4] == b"GIF8":
        return True
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return True
    if data[:5] == b"<?xml" or data[:4] == b"<svg":
        return False
    return False


# ---------- README 处理 ----------
IMG_MD = re.compile(r"!\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
IMG_TAG = re.compile(r"<img[^>]+src=[\"']([^\"']+)[\"']", re.I)
EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\u2600-\u27BF\u2190-\u21FF\u2B00-\u2BFF\uFE00-\uFE0F\u200D]"
)


def clean_text(s):
    """去掉描述里的 emoji 与多余空白，避免页面出现乱码方块。"""
    if not s:
        return ""
    s = EMOJI.sub("", str(s))
    return re.sub(r"\s+", " ", s).strip()


def extract_images(readme, full_name):
    """提取 README 里的图片并补全成可直接下载的绝对地址。"""
    urls = []
    for m in IMG_MD.finditer(readme or ""):
        urls.append(m.group(1))
    for m in IMG_TAG.finditer(readme or ""):
        urls.append(m.group(1))
    out = []
    seen = set()
    for u in urls:
        if not u or u.startswith("data:"):
            continue
        u = u.strip()
        if u.startswith("//"):
            u = "https:" + u
        elif u.startswith("/"):
            u = f"{RAW}/{full_name}/HEAD{u}"
        elif not u.startswith("http"):
            base = f"{RAW}/{full_name}/HEAD/"
            u = urllib.parse.urljoin(base, u.lstrip("./"))
        if "badge" in u or "shields.io" in u or "badgen" in u or "travis-ci" in u or u.endswith(".svg"):
            continue
        if u in seen:
            continue
        seen.add(u)
        out.append(u)
    return out


def summarize_tree(tree, max_entries=6000):
    """把 git tree 压成顶层目录 + 关键文件，喂给模型做结构解读。"""
    entries = tree[:max_entries]
    top_dirs = {}
    root_files = []
    for item in entries:
        path = item.get("path", "")
        typ = item.get("type", "")
        depth = path.count("/")
        if typ == "blob" and depth == 0:
            root_files.append(path)
        elif depth == 0 and typ == "tree":
            top_dirs.setdefault(path, 0)
        elif depth == 1 and typ == "blob":
            seg = path.split("/")[0]
            top_dirs[seg] = top_dirs.get(seg, 0) + 1
    ranked = sorted(top_dirs.items(), key=lambda kv: -kv[1])
    return {
        "total_entries": len(tree),
        "top_dirs": [{"path": k, "files": v} for k, v in ranked[:18]],
        "root_files": sorted(root_files)[:14],
    }
