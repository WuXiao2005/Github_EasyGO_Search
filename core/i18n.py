"""界面文案多语言。

设计：**字典以中文原文为键**（`locales/<lang>.json`），前端拿到的也是这份表，
按文本节点匹配后整段替换。这样模板里现有的中文一个字都不用搬，也不会出现
"同一句话在 6 个模板里各写一遍"的屎山；要改文案只改 JSON。

- `normalize()` 把 `zh-CN` / `zh_TW` / `jp` 之类的写法归一成受支持的语言码
- `payload()` 给前端 `{lang, default, dict, prefix, labels}`
- 缺条目时前端保持中文原样（不静默失败，见 `tools/check_i18n.py`）
"""
import json
import os
import threading

LANGS = (
    ("zh-Hans", "简体中文"),
    ("zh-Hant", "繁體中文"),
    ("ja", "日本語"),
    ("fr", "Français"),
    ("ru", "Русский"),
    ("ko", "한국어"),
)

DEFAULT = "zh-Hans"

_ALIAS = {
    "zh": "zh-Hans", "zh-cn": "zh-Hans", "zh-sg": "zh-Hans", "zh-hans": "zh-Hans", "cn": "zh-Hans",
    "zh-tw": "zh-Hant", "zh-hk": "zh-Hant", "zh-mo": "zh-Hant", "zh-hant": "zh-Hant", "tw": "zh-Hant",
    "jp": "ja", "jpn": "ja", "kr": "ko", "kor": "ko", "fra": "fr", "fre": "fr", "rus": "ru",
}

_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "locales")
_cache = {}
_lock = threading.Lock()


def normalize(lang):
    """任意写法 → 受支持的语言码；认不出来就回简体中文。"""
    code = (lang or "").strip().lower().replace("_", "-")
    if code in _ALIAS:
        return _ALIAS[code]
    for supported, _label in LANGS:
        if supported.lower() == code:
            return supported
    for supported, _label in LANGS:
        if supported.lower().startswith(code + "-") or code.startswith(supported.lower()):
            return supported
    return DEFAULT


def table(lang):
    """读某个语言的字典（毫秒级，进程内缓存）。"""
    lang = normalize(lang)
    if lang == DEFAULT:
        return {}
    with _lock:
        if lang in _cache:
            return _cache[lang]
    data = {}
    path = os.path.join(_DIR, lang + ".json")
    if os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:  # 字典坏了不能让整页崩
            print(f"[i18n] 读取 {path} 失败: {e}")
            data = {}
    with _lock:
        _cache[lang] = data
    return data


def payload(lang):
    """给前端的一次性注入包。"""
    raw = table(lang)
    return {
        "lang": normalize(lang),
        "default": DEFAULT,
        "dict": {k: v for k, v in raw.items() if not k.startswith("__")},
        "prefix": raw.get("__prefix__", {}),
        "suffix": raw.get("__suffix__", {}),
        "labels": dict(LANGS),
    }


def label(lang):
    """语言码 → 按钮上显示的名字。"""
    code = normalize(lang)
    return dict(LANGS).get(code, code)


def keys(lang="zh-Hant"):
    """调试/自检用：某个语言已收录多少条。"""
    return len([k for k in table(lang) if not k.startswith("__")])
