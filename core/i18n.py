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
import re
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


def _load(path):
    """读一份字典（进程内缓存，按绝对路径做键）。"""
    with _lock:
        if path in _cache:
            return _cache[path]
    data = {}
    if os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:  # 字典坏了不能让整页崩
            print(f"[i18n] 读取 {path} 失败: {e}")
            data = {}
    with _lock:
        _cache[path] = data
    return data


def table(lang):
    """界面壳字典（locales/<lang>.json，以中文原文为键）。"""
    lang = normalize(lang)
    if lang == DEFAULT:
        return {}
    return _load(os.path.join(_DIR, lang + ".json"))


def facts_table(lang):
    """规则层字典（locales/facts/<lang>.json，facts.py 里 `i18n.tr()` 用）。"""
    return _load(os.path.join(_DIR, "facts", normalize(lang) + ".json"))


def tr(lang, text):
    """规则层翻译：查不到就原样返回中文。"""
    return facts_table(lang).get(text, text)


def _n(s):
    """跟前端 `i18nNorm` 一致：去掉所有空白再比对。

    JS 侧是按"去空白后的文本"查表的，所以键也必须同口径入库，
    否则 `README 里没找到…`、`共 {} 节。` 这类带空格的句子永远查不到。
    """
    return re.sub(r"\s+", "", s or "")


def payload(lang):
    """给前端的一次性注入包（键统一去空白，和前端 `i18nNorm` 对齐）。"""
    raw = table(lang)
    return {
        "lang": normalize(lang),
        "default": DEFAULT,
        "dict": {_n(k): v for k, v in raw.items() if not k.startswith("__")},
        "prefix": {_n(k): v for k, v in (raw.get("__prefix__") or {}).items()},
        "suffix": raw.get("__suffix__") or {},
        "labels": dict(LANGS),
    }


def label(lang):
    """语言码 → 按钮上显示的名字。"""
    code = normalize(lang)
    return dict(LANGS).get(code, code)


def keys(lang="zh-Hant"):
    """调试/自检用：某个语言已收录多少条。"""
    return len([k for k in table(lang) if not k.startswith("__")])
