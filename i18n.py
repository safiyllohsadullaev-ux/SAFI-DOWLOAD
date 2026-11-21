from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from config import LOCALES_DIR

SUPPORTED = ("tg", "ru")
DEFAULT_LANG = "tg"


@lru_cache(maxsize=4)
def _load(lang: str) -> dict[str, Any]:
    path = LOCALES_DIR / f"{lang}.json"
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def normalize_lang(lang: str | None) -> str:
    if lang in SUPPORTED:
        return lang
    return DEFAULT_LANG


def t(lang: str | None, key: str, **kwargs: Any) -> str:
    lang = normalize_lang(lang)
    data: Any = _load(lang)
    for part in key.split("."):
        if not isinstance(data, dict) or part not in data:
            data = _load(DEFAULT_LANG)
            for fallback_part in key.split("."):
                data = data[fallback_part]
            break
        data = data[part]
    text = str(data)
    if kwargs:
        text = text.format(**kwargs)
    return text
