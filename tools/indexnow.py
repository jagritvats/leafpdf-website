"""Tell IndexNow search engines (Bing, Yandex, Seznam, Naver; DuckDuckGo and others use Bing's index) which pages
changed. Run after a deploy that adds or changes pages:

    python tools/indexnow.py                  # every URL in site/sitemap.xml
    python tools/indexnow.py /guides/ ...     # just these paths

The key is the name of the site/<32 hex>.txt file (its content is the key too); it proves we own the host.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
import urllib.request

SITE = pathlib.Path(__file__).resolve().parent.parent / "site"
HOST = "leafpdf.org"


def main(paths: list[str]) -> int:
    keys = [f for f in SITE.glob("*.txt") if re.fullmatch(r"[0-9a-f]{32}", f.stem)]
    if len(keys) != 1:
        print("expected one site/<32 hex>.txt key file")
        return 1
    key = keys[0].stem
    if paths:
        urls = [f"https://{HOST}/{p.lstrip('/')}" for p in paths]
    else:
        urls = re.findall(r"<loc>([^<]+)</loc>", (SITE / "sitemap.xml").read_text(encoding="utf-8"))
    body = json.dumps({"host": HOST, "key": key, "keyLocation": f"https://{HOST}/{key}.txt", "urlList": urls})
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body.encode(), method="POST",
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=30) as r:
        print(f"IndexNow: HTTP {r.status} for {len(urls)} URLs")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
