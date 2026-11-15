"""自检：两套字典都得对得上真源码，否则那条翻译永远不生效。

1. `locales/<lang>.json`（界面壳）：键必须能在 `core/webui.py` 的模板里原样找到
2. `locales/facts/<lang>.json`（规则层）：键必须是 `core/facts.py` 真的会用到的文案

用法：python tools/check_i18n.py
退出码非 0 表示有问题（CI 也可以直接跑）。
"""
import ast
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from core.webui import PAGE  # noqa: E402
from core import facts  # noqa: E402

LANGS = ("zh-Hans", "zh-Hant", "ja", "fr", "ru", "ko")


def norm(s):
    return re.sub(r"\s+", "", s or "")


def ui_keys():
    """界面壳：字典键 -> 是否能在模板里找到。"""
    page = norm(PAGE)
    locdir = os.path.join(BASE, "locales")
    files = sorted(f for f in os.listdir(locdir) if f.endswith(".json"))
    bad = 0
    base = None
    for f in files:
        with open(os.path.join(locdir, f), encoding="utf-8") as fh:
            data = json.load(fh)
        keys = [k for k in data if not k.startswith("__")]
        prefix = list((data.get("__prefix__") or {}).keys())
        missing = [k for k in keys if norm(k) not in page]
        missing_prefix = [k for k in prefix if norm(k) not in page]
        bad += len(missing) + len(missing_prefix)
        print(f"[界面壳] {f}: {len(keys)} 条，对不上 {len(missing)}" + (f"，前缀对不上 {len(missing_prefix)}" if missing_prefix else ""))
        for k in missing[:8]:
            print(f"    缺: {k}")
        for k in missing_prefix:
            print(f"    缺(前缀): {k}")
        ks = set(keys)
        if base is None:
            base = ks
        elif ks != base:
            print(f"    {f}: 与 {files[0]} 键不齐，多 {len(ks - base)} 少 {len(base - ks)}")
            bad += 1
    return bad


def facts_source_keys():
    """规则层真的会用到的中文原文：`_t(lang, "...")` 字面量 + 几张常量表里的文案。"""
    src = open(os.path.join(BASE, "core", "facts.py"), encoding="utf-8").read()
    tree = ast.parse(src)
    keys = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        if isinstance(fn, ast.Name) and fn.id == "_t" and len(node.args) >= 2:
            arg = node.args[1]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                keys.add(arg.value)
    for value, _read in facts.DIR_NOTES.values():
        if value:
            keys.add(value)
    for why in facts.ENTRY_NAMES.values():
        if why:
            keys.add(why)
    for _f, rt in facts.RUNTIMES:
        keys.add(rt["why"])
    for b in facts.BUTTONS:
        for text in (b["name"], b["zh"], b["act"]):
            if re.search(r"[\u4e00-\u9fff]", text):
                keys.add(text)
    return keys


def facts_keys():
    expect = facts_source_keys()
    locdir = os.path.join(BASE, "locales", "facts")
    bad = 0
    for code in LANGS:
        path = os.path.join(locdir, code + ".json")
        if not os.path.isfile(path):
            print(f"[规则层] 缺文件: locales/facts/{code}.json")
            bad += 1
            continue
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        miss = sorted(expect - set(data))
        extra = sorted(set(data) - expect)
        ph = [k for k in expect if k in data and "{}" in k and "{}" not in data[k]]
        bad += len(miss) + len(extra) + len(ph)
        print(f"[规则层] {code}: {len(data)} 条，源码要 {len(expect)} 条，缺 {len(miss)} 多 {len(extra)} 占位符丢失 {len(ph)}")
        for k in miss[:8]:
            print(f"    缺: {k}")
        for k in extra[:8]:
            print(f"    多: {k}")
        for k in ph[:4]:
            print(f"    占位符丢失: {k} -> {data[k]}")
    return bad


def js_syntax():
    """模板里的 JS 必须能跑：改文案时手滑多一个括号，整页都会白（这轮就踩过）。"""
    import shutil
    import subprocess
    import tempfile

    node = shutil.which("node")
    if not node:
        print("[JS 语法] 没装 node，跳过")
        return 0
    body = PAGE.split("<script>")[-1].split("</script>")[0]
    body = body.replace("%%I18N%%", "{}").replace("%%MODEL%%", "x")
    path = os.path.join(tempfile.gettempdir(), "_page_check.js")
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    r = subprocess.run([node, "--check", path], capture_output=True, text=True)
    if r.returncode:
        print("[JS 语法] 失败:\n" + (r.stderr or "")[:1200])
        return 1
    print("[JS 语法] OK")
    return 0


def main():
    bad = ui_keys() + facts_keys() + js_syntax()
    print("\n总计问题:", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
