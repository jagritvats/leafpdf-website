"""Static checks for site/ (no network): run before every deploy.

    python tools/check_site.py

- every HTML page parses with balanced tags, has one <h1>, a <title>, lang and a meta description (except 404);
- no inline <script> bodies, no on* handler attributes and no style="" attributes (the CSP allows neither);
- every local href/src/srcset target exists; images have alt text and width/height;
- the only external resources are links (<a href>) and the GitHub API in assets/site.js: nothing is loaded from
  another origin;
- no localhost, local file paths or email addresses anywhere in the output.
Exits 1 and lists the problems if anything fails.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlsplit

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr",
        "path", "rect", "circle", "stop"}
SVG_SELF_CLOSING_OK = {"path", "rect", "circle", "stop", "line", "polyline", "ellipse"}


class Page(HTMLParser):
    def __init__(self, name: str) -> None:
        super().__init__(convert_charrefs=True)
        self.name = name
        self.stack: list[str] = []
        self.problems: list[str] = []
        self.refs: list[str] = []
        self.external: list[str] = []
        self.h1 = 0
        self.title = False
        self.desc = False
        self.lang = False
        self.in_script = False
        self.ld_json = False
        self.ld_blocks: list[str] = []
        self.canonical = ""
        self.title_text = ""
        self.ids: set[str] = set()
        self.anchors: list[str] = []

    def err(self, msg: str) -> None:
        self.problems.append(f"{self.name}:{self.getpos()[0]}: {msg}")

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self._check(tag, a)
        if tag not in VOID:
            self.stack.append(tag)
        if tag == "script":
            self.in_script = True
            self.ld_json = a.get("type") == "application/ld+json"
            if self.ld_json:
                self.ld_blocks.append("")

    def handle_startendtag(self, tag, attrs):
        a = dict(attrs)
        self._check(tag, a)
        if tag not in VOID and tag not in SVG_SELF_CLOSING_OK:
            self.err(f"<{tag}/> self-closed")

    def _check(self, tag, a):
        for k in a:
            if k.startswith("on"):
                self.err(f"inline handler {k} on <{tag}>")
        if "style" in a:
            self.err(f"style attribute on <{tag}>")
        if "id" in a:
            if a["id"] in self.ids:
                self.err(f"duplicate id {a['id']}")
            self.ids.add(a["id"])
        if tag == "html":
            self.lang = bool(a.get("lang"))
        if tag == "h1":
            self.h1 += 1
        if tag == "meta" and a.get("name") == "description":
            self.desc = True
            if not 50 <= len(a.get("content") or "") <= 170:
                self.err(f"meta description is {len(a.get('content') or '')} characters (aim for 50-170)")
        if tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href") or ""
        if tag == "img":
            if "alt" not in a:
                self.err("img without alt")
            if not (a.get("width") and a.get("height")):
                self.err(f"img without width/height: {a.get('src')}")
        if tag == "script" and a.get("src"):
            self.refs.append(a["src"])
        for attr in ("href", "src"):
            if attr in a and a[attr] is not None:
                v = a[attr]
                if tag == "a" and attr == "href":
                    if v.startswith("#"):
                        self.anchors.append(v[1:])
                    elif v.startswith(("http://", "https://")):
                        self.external.append(v)
                    elif not v.startswith(("mailto:",)):
                        self.refs.append(v)
                elif tag == "meta" or attr == "href" and tag == "link" and a.get("rel") == "canonical":
                    pass
                elif v.startswith(("http://", "https://", "//")):
                    self.err(f"external resource <{tag} {attr}={v}>")
                else:
                    self.refs.append(v)
        if "srcset" in a:
            for part in a["srcset"].split(","):
                url = part.strip().split(" ")[0]
                if url.startswith(("http://", "https://", "//")):
                    self.err(f"external srcset {url}")
                self.refs.append(url)

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_script = False
        if tag in VOID:
            return
        if not self.stack or self.stack[-1] != tag:
            self.err(f"</{tag}> does not close <{self.stack[-1] if self.stack else 'nothing'}>")
            if tag in self.stack:
                while self.stack and self.stack.pop() != tag:
                    pass
            return
        self.stack.pop()

    def handle_data(self, data):
        if self.in_script and self.ld_json:  # structured data: not executed, so the CSP allows it
            self.ld_blocks[-1] += data
        elif self.in_script and data.strip():
            self.err("inline script body")
        if self.stack and self.stack[-1] == "title" and data.strip():
            self.title = True
            self.title_text += data.strip()


def resolve(page: pathlib.Path, ref: str) -> pathlib.Path | None:
    path = urlsplit(ref).path
    if not path:
        return None
    target = SITE / path.lstrip("/") if path.startswith("/") else page.parent / path
    if path.endswith("/"):
        target = target / "index.html"
    return target


def main() -> int:
    problems: list[str] = []
    external: set[str] = set()
    sitemap = set(re.findall(r"<loc>([^<]+)</loc>", (SITE / "sitemap.xml").read_text(encoding="utf-8")))
    pages: set[str] = set()
    for page in sorted(SITE.rglob("*.html")):
        name = page.relative_to(SITE).as_posix()
        p = Page(name)
        p.feed(page.read_text(encoding="utf-8"))
        p.close()
        problems += p.problems
        if p.stack:
            problems.append(f"{name}: unclosed tags {p.stack}")
        if p.h1 != 1:
            problems.append(f"{name}: {p.h1} <h1> elements")
        if not p.title or not p.lang:
            problems.append(f"{name}: missing <title> or lang")
        if not p.desc and name != "404.html":
            problems.append(f"{name}: missing meta description")
        if len(p.title_text) > 65:
            problems.append(f"{name}: title is {len(p.title_text)} characters (search results cut at ~60)")
        for block in p.ld_blocks:
            try:
                data = json.loads(block)
            except ValueError as e:
                problems.append(f"{name}: invalid JSON-LD: {e}")
                continue
            if "@context" not in json.dumps(data):
                problems.append(f"{name}: JSON-LD without @context")
        if name != "404.html":
            url = "https://leafpdf.org/" + (name[: -len("index.html")] if name.endswith("index.html") else name)
            if p.canonical != url:
                problems.append(f"{name}: canonical {p.canonical!r}, expected {url!r}")
            elif url not in sitemap:
                problems.append(f"{name}: {url} missing from sitemap.xml")
            pages.add(url)
        for anchor in p.anchors:
            if anchor not in p.ids:
                problems.append(f"{name}: link to missing #{anchor}")
        for ref in p.refs:
            target = resolve(page, ref)
            if target is not None and not target.exists():
                problems.append(f"{name}: missing {ref}")
            frag = urlsplit(ref).fragment
            if frag and target is not None and target.exists():
                if f'id="{frag}"' not in target.read_text(encoding="utf-8"):
                    problems.append(f"{name}: {ref} points at a missing id")
        external.update(p.external)

    for url in sorted(sitemap - pages):
        problems.append(f"sitemap.xml: {url} is not a page")

    leak = re.compile(r"localhost|127\.0\.0\.1|[A-Za-z]:\\\\|[A-Za-z]:/(?:Users|dev)|/home/\w|"
                      r"[\w.+-]+@[\w-]+\.[\w.]+")
    for f in sorted(SITE.rglob("*")):
        if f.is_file() and f.suffix in {".html", ".css", ".js", ".txt", ".xml", ".webmanifest", ".svg"} or f.name.startswith("_"):
            text = f.read_text(encoding="utf-8")
            for m in leak.finditer(text):
                problems.append(f"{f.relative_to(SITE).as_posix()}: looks private or local: {m.group(0)}")

    js = (SITE / "assets" / "site.js").read_text(encoding="utf-8")
    for url in re.findall(r"https://[^\s\"']+", js):
        if not url.startswith(("https://api.github.com/", "https://github.com/")) and "\\/" not in url:
            problems.append(f"assets/site.js: unexpected URL {url}")

    if problems:
        print("\n".join(problems))
        return 1
    print(f"site ok: {len(list(SITE.rglob('*.html')))} pages; external links:")
    for url in sorted(external):
        print("  " + url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
