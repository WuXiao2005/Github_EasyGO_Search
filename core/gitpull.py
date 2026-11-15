"""一键拉取：目录选择、git 浅克隆（带进度）、打开文件夹。

只做 clone，绝不执行仓库里任何脚本，也不自动安装依赖。
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading

_lock = threading.Lock()
_jobs = {}          # job_id -> Popen
_cancel = set()     # 被取消的 job_id

PROGRESS = re.compile(r"(Receiving objects|Resolving deltas|Compressing objects|Counting objects|Enumerating objects|remote: Enumerating|Updating files):\s+(\d+)%(?:.*?([\d.]+)\s*(MiB|KiB|GiB))?", re.I)

# 这些错误基本都是"网络被拦/被重置"，而不是仓库不存在，提示要区别开
NET_FAIL = re.compile(
    r"Connection (was )?reset|Failed to connect|Could not resolve|unable to access|"
    r"Recv failure|Send failure|early EOF|RPC failed|timed out|TLS|SSL|proxy",
    re.I,
)

# 私有仓库 / 仓库名写错，git 会要求认证
AUTH_FAIL = re.compile(r"Authentication failed|could not read Username|terminal prompts disabled", re.I)


def system_proxy():
    """读本机系统代理（IE/Clash 那套），给 git 用。

    git 不读 Windows 的代理设置，直连 github.com 在国内经常被重置，
    这里把 127.0.0.1:7890 之类的代理顺手传给 git，避免"拉取失败"。
    环境变量里已经配了代理就不重复处理（git 自己会读）。
    """
    for key in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy"):
        if os.environ.get(key):
            return ""

    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings") as k:
            enable = winreg.QueryValueEx(k, "ProxyEnable")[0]
            server = str(winreg.QueryValueEx(k, "ProxyServer")[0] or "")
    except Exception:
        return ""

    if not enable or not server:
        return ""

    # ProxyServer 可能是 "127.0.0.1:7890"，也可能是 "http=1.2.3.4:80;https=1.2.3.4:443"
    if "=" in server:
        parts = {}
        for seg in server.split(";"):
            if "=" in seg:
                k2, v2 = seg.split("=", 1)
                parts[k2.strip().lower()] = v2.strip()
        server = parts.get("https") or parts.get("http") or ""
    if not server:
        return ""
    if "://" not in server:
        server = "http://" + server
    return server



def target_dir(base, full_name):
    owner, name = full_name.split("/", 1)
    safe = re.sub(r"[^A-Za-z0-9_.\-]", "_", f"{owner}__{name}")
    return os.path.join(base, safe)


def is_cloned(dest):
    return os.path.isdir(dest) and os.path.isdir(os.path.join(dest, ".git"))


def _force_rm(func, path, _exc):
    """git 的 .pack 文件在 Windows 上是只读的，直接删会失败，先改回可写。"""
    try:
        import stat
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def cleanup_partial(dest, tries=6):
    """清掉这次拉取留下的半成品目录（只删本次自己创建的，绝不动用户原有目录）。"""
    import time as _t
    for _ in range(tries):
        if not os.path.isdir(dest):
            return True
        try:
            shutil.rmtree(dest, onerror=_force_rm)
        except Exception:
            pass
        if not os.path.isdir(dest):
            return True
        _t.sleep(0.3)
    return not os.path.isdir(dest)


PARTIAL_MARK_SUFFIX = ".digest-partial"


def _partial_mark(dest):
    return dest + PARTIAL_MARK_SUFFIX


def _mark_partial(dest):
    try:
        with open(_partial_mark(dest), "w", encoding="utf-8") as f:
            f.write("clone in progress\n")
    except Exception:
        pass


def _clear_partial_mark(dest):
    try:
        os.remove(_partial_mark(dest))
    except Exception:
        pass


def _is_our_partial(dest):
    return os.path.isfile(_partial_mark(dest))


def open_folder(path):
    if not path or not os.path.isdir(path):
        return False
    try:
        if os.name == "nt":
            os.startfile(path)  # noqa: S606 - 只是打开资源管理器
        else:
            subprocess.Popen(["xdg-open", path])
        return True
    except Exception:
        return False


def folder_size_mb(path):
    total = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except Exception:
                pass
    return round(total / (1024 * 1024), 1)


def clone_stream(url, dest, job_id=""):
    """SSE 事件流：progress(带百分比) -> done / error。"""
    parent = os.path.dirname(dest)
    try:
        os.makedirs(parent, exist_ok=True)
    except Exception as e:
        yield ("error", {"error": f"无法创建目录：{e}"})
        return

    existed_before = os.path.isdir(dest)
    # 上一次没拉完（取消了 / 网络断了）留下的目录：只要是我们自己标记的，就先清掉重来
    if _is_our_partial(dest):
        if cleanup_partial(dest):
            existed_before = False
        _clear_partial_mark(dest)
    if is_cloned(dest):
        yield ("done", {"ok": True, "dir": dest, "existing": True,
                        "size_mb": folder_size_mb(dest), "text": "这个目录里已经有仓库了"})
        return
    if os.path.isdir(dest) and os.listdir(dest):
        yield ("error", {"error": f"目标目录已存在且不是空的：{dest}，请换个位置或先清空"})
        return

    _mark_partial(dest)

    proxy = system_proxy()
    note = f"（走本机代理 {proxy}）" if proxy else ""
    yield ("progress", {"pct": 0, "text": "正在连接 GitHub…" + note})
    cmd = ["git", "-c", "core.longpaths=true"]
    if proxy:
        cmd += ["-c", f"http.proxy={proxy}"]
    cmd += ["clone", "--depth", "1", "--single-branch", "--progress", url, dest]
    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace", bufsize=1,
        )
    except FileNotFoundError:
        yield ("error", {"error": "没找到 git 命令，请先安装 Git for Windows"})
        return
    except Exception as e:
        yield ("error", {"error": f"启动 git 失败：{e}"})
        return

    with _lock:
        _jobs[job_id or dest] = proc

    last = {"pct": 0}
    tail = []
    try:
        for line in proc.stderr:
            line = line.strip()
            if not line:
                continue
            tail.append(line)
            tail[:] = tail[-6:]
            m = PROGRESS.search(line)
            if m:
                pct = int(m.group(2))
                size = ""
                if m.group(3):
                    size = f"{m.group(3)} {m.group(4)}"
                # 收包阶段权重最高，前端进度条直接用它
                if m.group(1).lower().startswith("receiving"):
                    stage = "正在下载代码"
                    pct = 8 + int(pct * 0.82)
                elif m.group(1).lower().startswith("resolving"):
                    stage = "正在整理文件"
                    pct = 90 + int(pct * 0.08)
                else:
                    stage = "正在准备"
                    pct = max(pct, 8)
                if pct >= last["pct"] - 2:
                    last["pct"] = max(last["pct"], pct)
                    yield ("progress", {"pct": min(pct, 99), "text": stage + (f" · {size}" if size else "")})
            elif line.startswith("remote:") or "Cloning into" in line:
                yield ("progress", {"pct": last["pct"], "text": line.replace("remote:", "").strip()[:80]})
            if (job_id or dest) in _cancel:
                kill_tree(proc)
                # 取消也会留半成品目录，一并清掉，否则下次重试会被"目录已存在"挡住
                if not existed_before and cleanup_partial(dest):
                    _clear_partial_mark(dest)
                yield ("error", {"error": "已取消拉取"})
                return
        code = proc.wait()
    finally:
        with _lock:
            _jobs.pop(job_id or dest, None)
            _cancel.discard(job_id or dest)

    if code == 0 and is_cloned(dest):
        _clear_partial_mark(dest)
        yield ("done", {"ok": True, "dir": dest, "size_mb": folder_size_mb(dest), "text": "拉取完成"})
    else:
        # 半成品目录会让下一次"重试拉取"被"目录已存在"挡住，这里清掉
        cleaned = False
        if not existed_before:
            cleaned = cleanup_partial(dest)
            if cleaned:
                _clear_partial_mark(dest)

        msg = tail[-1] if tail else f"git 退出码 {code}"
        joined = " ".join(tail) + " " + msg
        if NET_FAIL.search(joined):
            hint = "（网络被重置/连不上，点「重试拉取」再来一次；本机代理要是换了端口，重启服务即可）"
        elif AUTH_FAIL.search(joined):
            hint = "（这个仓库可能不存在，或者是私有仓库需要登录）"
        else:
            hint = ""
        if cleaned:
            hint += "（已清掉这次的半成品目录）"
        yield ("error", {"error": f"拉取失败：{msg[:160]}{hint}", "cleaned": cleaned})


def kill_tree(proc):
    """连 git 的子进程一起杀掉，否则文件被占用，半成品目录删不掉。"""
    try:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                       capture_output=True, timeout=15)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
    try:
        proc.wait(timeout=10)
    except Exception:
        pass


def cancel(job_id):
    with _lock:
        _cancel.add(job_id)
        proc = _jobs.get(job_id)
    if proc and proc.poll() is None:
        kill_tree(proc)
