#!/usr/bin/env python3
"""Refresh the tech-stack badge row in README.md from real GitHub repo language stats."""
import json
import os
import re
import sys
import urllib.request
from collections import Counter

USERNAME = "DanielLi8"
TOP_N = 8
README = os.path.join(os.path.dirname(__file__), "..", "README.md")
START = "<!-- TECH-STACK:START -->"
END = "<!-- TECH-STACK:END -->"

TOKEN = os.environ.get("GITHUB_TOKEN", "")

# color, logo slug, logo color per language; unlisted languages fall back to a plain grey badge
BADGES = {
    "TypeScript": ("3178C6", "typescript", "white"),
    "JavaScript": ("323330", "javascript", "%23F7DF1E"),
    "Python": ("3776AB", "python", "white"),
    "Java": ("007396", "openjdk", "white"),
    "Go": ("00ADD8", "go", "white"),
    "Rust": ("000000", "rust", "white"),
    "C": ("A8B9CC", "c", "white"),
    "C++": ("00599C", "cplusplus", "white"),
    "C#": ("239120", "csharp", "white"),
    "Ruby": ("CC342D", "ruby", "white"),
    "PHP": ("777BB4", "php", "white"),
    "Swift": ("F05138", "swift", "white"),
    "Kotlin": ("7F52FF", "kotlin", "white"),
    "Dart": ("0175C2", "dart", "white"),
    "HTML": ("E34F26", "html5", "white"),
    "CSS": ("1572B6", "css3", "white"),
    "Shell": ("4EAA25", "gnubash", "white"),
    "Nix": ("5277C3", "nixos", "white"),
    "Haskell": ("5D4F85", "haskell", "white"),
    "R": ("276DC3", "r", "white"),
    "Scala": ("DC322F", "scala", "white"),
    "Jupyter Notebook": ("F37626", "jupyter", "white"),
    "Vue": ("4FC08D", "vuedotjs", "white"),
    "Elixir": ("4B275F", "elixir", "white"),
}


def api(path):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Authorization": f"Bearer {TOKEN}" if TOKEN else "",
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{USERNAME}-readme-bot",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def owned_nonfork_repos():
    repos = []
    page = 1
    while True:
        data = api(f"/users/{USERNAME}/repos?per_page=100&page={page}")
        if not data:
            break
        repos.extend(r for r in data if not r.get("fork"))
        if len(data) < 100:
            break
        page += 1
    return repos


def top_languages():
    counter = Counter()
    for repo in owned_nonfork_repos():
        langs = api(f"/repos/{USERNAME}/{repo['name']}/languages")
        for lang, byte_count in langs.items():
            counter[lang] += byte_count
    return counter.most_common(TOP_N)


def badge_markdown(lang):
    color, logo, logo_color = BADGES.get(lang, ("555555", "", "white"))
    label = lang.upper().replace(" ", "%20").replace("+", "%2B").replace("#", "%23")
    url = f"https://img.shields.io/badge/{label}-{color}.svg?&style=flat"
    if logo:
        url += f"&logo={logo}&logoColor={logo_color}"
    return f"![{lang}]({url})"


def main():
    with open(README, encoding="utf-8") as f:
        content = f.read()

    if START not in content or END not in content:
        print(f"Markers {START} / {END} not found in README.md", file=sys.stderr)
        sys.exit(1)

    langs = top_languages()
    if not langs:
        print("No language data found, leaving README untouched.")
        return

    block = "&nbsp;\n".join(badge_markdown(lang) for lang, _ in langs)
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    new_content = pattern.sub(f"{START}\n{block}\n{END}", content, count=1)

    if new_content == content:
        print("Tech stack badges unchanged.")
        return

    with open(README, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Updated tech stack badges: {', '.join(l for l, _ in langs)}")


if __name__ == "__main__":
    main()
