"""自检：字典里的键必须能在页面模板里原样找到，否则那条翻译永远不生效。

用法：python tools/check_i18n.py
退出码非 0 表示有键对不上（CI 也可以直接跑）。
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from core.webui import PAGE  # noqa: E402


def norm(s):
    return re.sub(r"\s+", "", s or "")


def main():
    page = norm(PAGE)
    locdir = os.path.join(BASE, "locales")
    files = sorted(f for f in os.listdir(locdir) if f.endswith(".json"))
    bad_total = 0
    for f in files:
        with open(os.path.join(locdir, f), encoding="utf-8") as fh:
            data = json.load(fh)
        keys = [k for k in data if not k.startswith("__")]
        prefix = list((data.get("__prefix__") or {}).keys())
        missing = [k for k in keys if norm(k) not in page]
        missing_prefix = [k for k in prefix if norm(k) not in page]
        bad_total += len(missing) + len(missing_prefix)
        print(f"{f}: {len(keys)} 条，对不上 {len(missing)} 条" + (f"，前缀对不上 {len(missing_prefix)} 条" if missing_prefix else ""))
        for k in missing[:12]:
            print(f"    缺: {k}")
        for k in missing_prefix:
            print(f"    缺(前缀): {k}")
    # 多语言之间键是否统一
    base_keys = None
    for f in files:
        with open(os.path.join(locdir, f), encoding="utf-8") as fh:
            ks = {k for k in json.load(fh) if not k.startswith("__")}
        if base_keys is None:
            base_keys = ks
        elif ks != base_keys:
            print(f"{f}: 与 {files[0]} 的键不一致，多 {len(ks - base_keys)} 少 {len(base_keys - ks)}")
    return 1 if bad_total else 0


if __name__ == "__main__":
    sys.exit(main())
