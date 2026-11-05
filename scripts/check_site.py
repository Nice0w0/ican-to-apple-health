"""Check that the download pages agree with themselves and the sitemap.

Each page carries its FAQ twice: as FAQPage JSON-LD and as visible <details> items
(<summary><h3>question</h3></summary><p>answer</p>). Google requires the two to match, so this fails when one is edited
without the other. It also checks each page's dateModified against its
<lastmod> in sitemap.xml.

    python3 scripts/check_site.py
"""

import html
import json
import re
import sys
from pathlib import Path

PUBLIC = Path(__file__).resolve().parent.parent / "public"
SITE = "https://ican-health-sync.vercel.app"
PAGES = {"/": "index.html", "/en/": "en/index.html"}


def text(fragment):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", fragment)).split())


def check(url, path, lastmod):
    errors = []
    s = (PUBLIC / path).read_text(encoding="utf-8")
    ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', s, re.S).group(1))
    nodes = {n["@type"]: n for n in ld["@graph"]}

    structured = [(q["name"], q["acceptedAnswer"]["text"]) for q in nodes["FAQPage"]["mainEntity"]]
    section = re.search(r'<section[^>]*id="faq"[^>]*>(.*?)</section>', s, re.S)
    if not section:
        return [f"{path}: FAQ section not found"]
    visible = [(text(q), text(a)) for q, a in re.findall(r"<summary>\s*<h3>(.*?)</h3>.*?</summary>\s*<p>(.*?)</p>", section.group(1), re.S)]
    if structured != visible:
        for i in range(max(len(structured), len(visible))):
            a = structured[i] if i < len(structured) else None
            b = visible[i] if i < len(visible) else None
            if a != b:
                errors.append(f"{path}: FAQ #{i + 1} differs\n  JSON-LD: {a}\n  visible: {b}")

    modified = nodes["SoftwareApplication"].get("dateModified")
    if modified != lastmod.get(SITE + url):
        errors.append(f"{path}: dateModified {modified} != sitemap lastmod {lastmod.get(SITE + url)}")
    return errors


def main():
    sitemap = (PUBLIC / "sitemap.xml").read_text(encoding="utf-8")
    lastmod = dict(re.findall(r"<loc>(.*?)</loc>\s*<lastmod>(.*?)</lastmod>", sitemap))
    errors = [e for url, path in PAGES.items() for e in check(url, path, lastmod)]
    for e in errors:
        print(e, file=sys.stderr)
    print("ok" if not errors else f"{len(errors)} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
