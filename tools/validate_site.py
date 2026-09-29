#!/usr/bin/env python3
"""Lightweight site-wide QA for the static Pascoe Lab website.

Checks public HTML pages for core metadata, heading/navigation consistency,
image alt attributes and broken local links/assets. Legacy redirects and the
404 page are handled separately so they do not generate false failures.
"""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
NON_PUBLIC_HTML = {"stories/template.html"}
EDITORIAL_PHRASES = (
    "the next content pass",
    "captions are intentionally general",
    "photographs recovered from",
    "until the event dates",
    "future additions should",
)


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_title = False
        self.in_primary_nav = False
        self.title_parts: list[str] = []
        self.description = False
        self.viewport = False
        self.canonical = False
        self.h1_count = 0
        self.primary_nav_active = 0
        self.ids: list[str] = []
        self.images_without_alt: list[str] = []
        self.local_refs: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs_list: list[tuple[str, str | None]]) -> None:
        attrs = dict(attrs_list)
        classes = set((attrs.get("class") or "").split())

        if tag == "title":
            self.in_title = True
        elif tag == "meta":
            name = (attrs.get("name") or "").lower()
            if name == "description" and (attrs.get("content") or "").strip():
                self.description = True
            elif name == "viewport" and (attrs.get("content") or "").strip():
                self.viewport = True
        elif tag == "link":
            rel = set((attrs.get("rel") or "").lower().split())
            href = attrs.get("href") or ""
            if "canonical" in rel and href:
                self.canonical = True
            if "stylesheet" in rel or "icon" in rel:
                self._record_ref(tag, href)
        elif tag == "script":
            self._record_ref(tag, attrs.get("src") or "")
        elif tag == "img":
            if "alt" not in attrs:
                self.images_without_alt.append(attrs.get("src") or "<unknown image>")
            self._record_ref(tag, attrs.get("src") or "")
        elif tag == "a":
            self._record_ref(tag, attrs.get("href") or "")
            if self.in_primary_nav and "active" in classes:
                self.primary_nav_active += 1
        elif tag == "nav" and "site-nav" in classes:
            self.in_primary_nav = True
        elif tag == "h1":
            self.h1_count += 1

        if attrs.get("id"):
            self.ids.append(attrs["id"] or "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
        elif tag == "nav" and self.in_primary_nav:
            self.in_primary_nav = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)

    def _record_ref(self, tag: str, value: str) -> None:
        value = value.strip()
        if value:
            self.local_refs.append((tag, value))

    @property
    def title(self) -> str:
        return " ".join("".join(self.title_parts).split())


def is_redirect(text: str) -> bool:
    lowered = text.lower()
    return 'http-equiv="refresh"' in lowered or "http-equiv='refresh'" in lowered


def local_target(page: Path, ref: str) -> Path | None:
    parts = urlsplit(ref)
    if parts.scheme or parts.netloc or ref.startswith(("#", "mailto:", "tel:", "javascript:")):
        return None

    path_text = unquote(parts.path)
    if not path_text:
        return None

    if path_text.startswith("/"):
        target = ROOT / path_text.lstrip("/")
    else:
        target = page.parent / path_text

    if path_text.endswith("/"):
        target = target / "index.html"

    return target.resolve()


def audit_page(path: Path) -> tuple[list[str], list[str]]:
    rel = path.relative_to(ROOT)
    text = path.read_text(encoding="utf-8", errors="replace")
    redirect = is_redirect(text)
    special = rel.as_posix() == "404.html"

    parser = PageParser()
    parser.feed(text)

    errors: list[str] = []
    warnings: list[str] = []

    if not redirect and not special:
        if not parser.title:
            errors.append("missing <title>")
        if not parser.description:
            errors.append("missing meta description")
        if not parser.viewport:
            errors.append("missing viewport meta tag")
        if not parser.canonical:
            errors.append("missing canonical link")
        if parser.h1_count != 1:
            errors.append(f"expected exactly one <h1>, found {parser.h1_count}")
        if parser.primary_nav_active > 1:
            errors.append(f"multiple active primary-nav links ({parser.primary_nav_active})")

    if parser.images_without_alt:
        errors.append("images missing alt attribute: " + ", ".join(parser.images_without_alt[:5]))

    duplicate_ids = sorted({item for item in parser.ids if parser.ids.count(item) > 1})
    if duplicate_ids:
        errors.append("duplicate id(s): " + ", ".join(duplicate_ids[:8]))

    for tag, ref in parser.local_refs:
        target = local_target(path, ref)
        if target is None:
            continue
        try:
            target.relative_to(ROOT.resolve())
        except ValueError:
            warnings.append(f"{tag} reference resolves outside repository: {ref}")
            continue
        if not target.exists():
            errors.append(f"broken local {tag} reference: {ref}")

    lowered = text.lower()
    for phrase in EDITORIAL_PHRASES:
        if phrase in lowered:
            warnings.append(f"public-facing editorial placeholder: {phrase!r}")

    return errors, warnings


def audit_sitemap() -> list[str]:
    sitemap = ROOT / "sitemap.xml"
    if not sitemap.exists():
        return ["sitemap.xml is missing"]
    text = sitemap.read_text(encoding="utf-8", errors="replace")
    errors: list[str] = []
    for unwanted in ("/404.html", "/all-publications.html", "/publications/index.html"):
        if unwanted in text:
            errors.append(f"sitemap contains non-canonical/redirect URL: {unwanted}")
    return errors


def main() -> int:
    html_files = sorted(
        path for path in ROOT.rglob("*.html")
        if ".git" not in path.parts
        and "node_modules" not in path.parts
        and path.relative_to(ROOT).as_posix() not in NON_PUBLIC_HTML
    )

    total_errors = 0
    total_warnings = 0

    for path in html_files:
        errors, warnings = audit_page(path)
        if not errors and not warnings:
            continue
        rel = path.relative_to(ROOT)
        print(f"\n{rel}")
        for error in errors:
            print(f"  ERROR: {error}")
        for warning in warnings:
            print(f"  WARN:  {warning}")
        total_errors += len(errors)
        total_warnings += len(warnings)

    sitemap_errors = audit_sitemap()
    if sitemap_errors:
        print("\nsitemap.xml")
        for error in sitemap_errors:
            print(f"  ERROR: {error}")
        total_errors += len(sitemap_errors)

    print(f"\nChecked {len(html_files)} public HTML files: {total_errors} error(s), {total_warnings} warning(s).")
    return 1 if total_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
