#!/usr/bin/env python3
"""Refresh the recent public-repository cards on resources.html from GitHub."""
from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
import urllib.request
from pathlib import Path

OWNER = "Benizao1980"
PAGE = Path("resources.html")
START = "<!-- GITHUB_REPOS_START -->"
END = "<!-- GITHUB_REPOS_END -->"
EXCLUDE = {"Benizao1980", "pascoe-lab", "Ben-style"}
LIMIT = 6


def fetch_repositories() -> list[dict]:
    url = f"https://api.github.com/users/{OWNER}/repos?per_page=100&type=owner&sort=updated&direction=desc"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "pascoe-lab-site-resource-sync",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def card(repo: dict) -> str:
    name = html.escape(repo["name"])
    url = html.escape(repo["html_url"], quote=True)
    description = html.escape((repo.get("description") or "Public analysis, software or training repository.").strip())
    language = html.escape(repo.get("language") or "GitHub")
    updated = repo.get("updated_at", "")[:10]
    try:
        label = dt.date.fromisoformat(updated).strftime("%b %Y")
    except ValueError:
        label = "recently"
    return (
        '<article class="card resource-card">'
        f'<p class="meta">{language} · updated {html.escape(label)}</p>'
        f'<h3>{name}</h3><p>{description}</p>'
        f'<a class="button ghost" href="{url}">Open repository</a>'
        '</article>'
    )


def main() -> None:
    repos = [
        repo for repo in fetch_repositories()
        if repo.get("name") not in EXCLUDE
        and not repo.get("fork")
        and not repo.get("archived")
        and not repo.get("private")
    ][:LIMIT]
    cards = "\n".join(card(repo) for repo in repos)
    block = f'{START}\n<div class="grid grid-3">\n{cards}\n</div>\n{END}'

    source = PAGE.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pattern.search(source):
        raise SystemExit("GitHub resource markers not found in resources.html")
    updated = pattern.sub(block, source, count=1)
    PAGE.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()
