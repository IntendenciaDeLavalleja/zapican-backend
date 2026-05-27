"""Sanitización HTML para contenido editable (bleach)."""
from __future__ import annotations

import bleach

ALLOWED_TAGS = [
    "p", "br", "hr", "strong", "em", "u", "s", "blockquote", "code", "pre",
    "ul", "ol", "li", "h2", "h3", "h4", "h5", "h6",
    "a", "img", "figure", "figcaption",
    "table", "thead", "tbody", "tr", "th", "td",
    "span", "div",
]

ALLOWED_ATTRS = {
    "*": ["class", "id"],
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "title", "width", "height", "loading"],
    "td": ["colspan", "rowspan"],
    "th": ["colspan", "rowspan", "scope"],
}

ALLOWED_PROTOCOLS = ["http", "https", "mailto", "tel"]


def sanitize_html(value: str | None) -> str:
    if not value:
        return ""
    cleaned = bleach.clean(
        value,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
    return bleach.linkify(cleaned, callbacks=[_set_safe_link_attrs])


def _set_safe_link_attrs(attrs, new=False):
    href_key = (None, "href")
    href = attrs.get(href_key, "")
    if href.startswith(("http://", "https://")):
        attrs[(None, "rel")] = "noopener noreferrer nofollow"
        attrs[(None, "target")] = "_blank"
    return attrs
