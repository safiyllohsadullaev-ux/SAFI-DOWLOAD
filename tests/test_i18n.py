import json
from pathlib import Path

from i18n import t

LOCALES = Path(__file__).resolve().parents[1] / "locales"


def _keys(data, prefix=""):
    keys = set()
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            keys |= _keys(value, path)
        else:
            keys.add(path)
    return keys


def test_locales_match():
    tg = json.loads((LOCALES / "tg.json").read_text(encoding="utf-8"))
    ru = json.loads((LOCALES / "ru.json").read_text(encoding="utf-8"))
    assert _keys(tg) == _keys(ru)


def test_format_and_fallback():
    assert "интизор" in t("tg", "download.wait")
    assert "подождите" in t("ru", "download.wait").lower() or "Подождите" in t("ru", "download.wait")
    assert "{seconds}" not in t("tg", "errors.rate_limit", seconds=12)
    assert "12" in t("tg", "errors.rate_limit", seconds=12)
