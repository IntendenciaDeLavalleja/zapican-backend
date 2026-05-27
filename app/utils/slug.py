"""Slugify simple sin dependencias externas."""
from __future__ import annotations

import re
import unicodedata

_slug_strip_re = re.compile(r"[^a-z0-9]+")


def slugify(value: str, max_length: int = 200) -> str:
    if not value:
        return ""
    norm = unicodedata.normalize("NFKD", value)
    norm = norm.encode("ascii", "ignore").decode("ascii")
    norm = norm.lower()
    norm = _slug_strip_re.sub("-", norm).strip("-")
    return norm[:max_length]


def ensure_unique_slug(model, slug_field: str, base: str, ignore_id=None,
                       extra_filters=None, max_length: int = 200) -> str:
    """Garantiza unicidad agregando -2, -3, ... si hace falta."""
    base = (base or "").strip("-")[:max_length] or "item"
    candidate = base
    i = 2
    while True:
        q = model.query.filter(getattr(model, slug_field) == candidate)
        if extra_filters:
            for f in extra_filters:
                q = q.filter(f)
        if ignore_id is not None:
            q = q.filter(model.id != ignore_id)
        if not q.first():
            return candidate
        suffix = f"-{i}"
        candidate = base[: max_length - len(suffix)] + suffix
        i += 1
