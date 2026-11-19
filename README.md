# leafpdf.org

The website for [Leaf](https://github.com/jagritvats/Leaf-PDF-Viewer), a local, open-source PDF editor for
Windows and Linux.

Plain HTML, CSS and a little vanilla JavaScript in `site/`. No framework and no build step: what's in `site/` is
what gets served. Nothing is loaded from other servers (no web fonts, analytics or CDNs) and nothing sets
cookies. The one outside request is the download buttons asking `api.github.com` for the latest release, so the
links point straight at the files. If that request fails, the buttons keep linking to the release page.

```
site/
  index.html            home: features, privacy, downloads, open source
  privacy/index.html    privacy policy (PRIVACY.md from the app repository)
  404.html
  assets/               site.css, theme.js (applies the saved theme before paint), site.js
  img/v1/               screenshots (WebP at several widths + a JPEG fallback), served as immutable
  img/og-1200x630.png   link preview image
  icons/, favicon.*     icons rendered from the Leaf icon
  _headers, _redirects  Cloudflare: security and cache headers, path redirects
  robots.txt, sitemap.xml, site.webmanifest
tools/                  image and icon generators, site checks, screenshot helper
deploy/, Dockerfile     the VM route (nginx in Docker behind Traefik)
wrangler.jsonc          the Cloudflare Workers route
```

## Preview locally

```sh
python -m http.server -d site 8765
```

Open <http://localhost:8765/> and stop the server with Ctrl+C when you're done. Then run the checks:

```sh
python tools/check_site.py
```

It checks that every page is well formed, that all local links and images exist, that there are no inline
scripts or `style` attributes (the Content Security Policy forbids them), that nothing is loaded from another
origin, and that no local paths or email addresses slipped into the output. For search engines it also checks that each page's title and description fit in a
search result, that its canonical URL is right and listed in `site/sitemap.xml`, and that structured data (JSON-LD)
parses.

## Common edits

- **Microsoft Store goes live:** in `site/index.html`, change `data-store-live="false"` to `"true"` on the
  downloads section (`<section class="downloads" id="download" ...>`). The "Coming soon" note is then replaced by
  a "Get it from the Store" button linking to `https://apps.microsoft.com/detail/9P865XPB1QP3`.
- **Leaf for Mac ships:** nothing to switch. When the latest release has a `*-macos-arm64.dmg`, the macOS card
  shows its Download button instead of "Coming soon", and Mac visitors get "Download for Mac" in the hero. Then
  add macOS to the system requirements, the FAQ answer and `operatingSystem` in the JSON-LD (`site/index.html`).
- **Platform detection** (`site/assets/site.js`): Windows, Linux and Mac visitors get their own hero button and
  see their platform's card first; phones and tablets get a note that Leaf is a desktop app. Without JavaScript
  the page shows the Windows installer.
- **A new Leaf release:** nothing to do. The buttons, version and file sizes come from GitHub's latest release.
  The asset names must keep their patterns (`*-windows-x64-setup.exe`, `*-windows-x64.zip`, `*x86_64.AppImage`,
  `*-linux-x86_64.tar.gz`, `SHA256SUMS*`); see `PATTERNS` in `site/assets/site.js`.
- **New screenshots:** they come from `marketing/out/screens/{light,dark}` in the app repository, checked out next
  to this one. Images under `img/v1/` are cached for a year as immutable, so write changed ones to a new folder:
  change `OUT` in `tools/make_images.py` to `img/v2`, run it, then update the paths in the HTML
  (`tools/picture_html.py NAME "alt text"` prints the `<picture>` markup). Needs Pillow with WebP:

  ```sh
  python tools/make_images.py --sheet     # --sheet also writes out/contact-sheet-*.png to check the crops
  python tools/make_brand.py              # icons, favicon.ico, img/og-1200x630.png (PySide6, on Windows)
  ```
- **Guides** (`site/guides/`) are generated: edit `tools/make_guides.py`, run `python tools/make_guides.py site`,
  then add any new page to `site/sitemap.xml` (the checks fail until you do). Check menu names and shortcuts against
  the Leaf source, and bump `DATE`/`VERSION` in the script when a guide changes.
- **After deploying new or changed pages:** `python tools/indexnow.py` tells Bing (and the engines that use its
  index, such as DuckDuckGo) to recrawl everything in the sitemap; pass paths (`/guides/`) to send only those.
  The key is `site/<32 hex>.txt`; keep that file. Google reads the sitemap through Search Console.
- **Screenshots of the site** for review (Windows, headless Edge, with the preview server running):
  `bash tools/shoot.sh desktop-light 1440 9800 light`. Headless Edge doesn't go below about 490 px wide; for
  phone widths, load the page in an iframe of the width you want.

## Deploy

### Route 1: Cloudflare Workers (static assets)

The Workers project `leafpdf-website` is connected to this GitHub repository. Cloudflare runs
`npx wrangler deploy` on every push to `main`, with no build command, and serves `site/` as configured in
`wrangler.jsonc`. Keep the worker name `leafpdf-website`: it has to match the Cloudflare project.

1. Commit and push to `main`. Cloudflare builds and deploys; the build log is under Workers & Pages ›
   leafpdf-website › Deployments.
2. `site/_headers` sets the security headers (CSP, HSTS, frame and referrer rules) and the cache lifetimes;
   `site/_redirects` has the path redirects. `not_found_handling: "404-page"` serves `404.html`, and
   `html_handling: "auto-trailing-slash"` serves `/privacy/` from `privacy/index.html`.
3. Custom domains: add `leafpdf.org` and `www.leafpdf.org` to the worker (Settings › Domains & Routes).
4. **www → apex:** `_redirects` in Workers static assets only takes paths, not hostnames, so make this a
   Cloudflare redirect rule on the zone: Rules › Redirect Rules, *when* hostname equals `www.leafpdf.org`,
   *then* dynamic redirect to `concat("https://leafpdf.org", http.request.uri.path)`, status 301, preserve the
   query string.
5. Check: `curl -sI https://leafpdf.org/ | grep -i content-security-policy` and open the site once with the
   browser's developer tools to see that the console has no errors.

Previewing a deploy locally needs Node: `npx wrangler dev` serves `site/` with the same headers. Don't run
`wrangler deploy` by hand; pushing to `main` does it.

### Route 2: the VM (Docker, nginx, Traefik)

The image is `nginxinc/nginx-unprivileged` with `deploy/nginx.conf` and `site/` copied in. It runs read-only on
port 8080, behind the shared Traefik edge on the external `synapse-edge` network, with the router rule
``Host(`leafpdf.org`) || Host(`www.leafpdf.org`)``. nginx sends the same headers as `site/_headers`, redirects
www to the apex, answers `/healthz`, and serves `404.html` for missing pages. The Compose project is named
`leafpdf-site`, so it never collides with other stacks on the VM.

One-time setup:

1. DNS: point `leafpdf.org` and `www.leafpdf.org` at the VM (through Cloudflare if the zone is proxied).
2. TLS: Traefik terminates TLS, so it needs a certificate that covers `leafpdf.org` and `www.leafpdf.org`
   (for example a Cloudflare Origin Certificate for the zone, added to Traefik's TLS configuration next to the
   existing ones). Without it Traefik serves its default certificate for these hosts.
3. The `synapse-edge` network must exist on the VM (the Synpse stack creates it).
4. In the GitHub repository, add the secrets `DEPLOY_SSH_KEY`, `DEPLOY_KNOWN_HOSTS`, `DEPLOY_USER`,
   `DEPLOY_HOST` and optionally `DEPLOY_PORT`; optionally the variables `DEPLOY_PATH` (default
   `/opt/leafpdf/site`), `LEAFPDF_LOCAL_PORT` (default 8120) and `LEAFPDF_HOST_RULE`.
5. Set the repository variable `DEPLOY_ENABLED` to `true`. It's the kill switch: with any other value the
   workflow skips everything.

Each deploy:

1. Actions › **Deploy to VM** › Run workflow. It only runs when started by hand (no push trigger).
2. The workflow runs `tools/check_site.py`, builds the arm64 image, pushes it to
   `ghcr.io/<owner>/<repo>:<sha>` and `:main`, copies `deploy/docker-compose.yml` and `deploy/deploy.sh` to the
   VM and runs the script.
3. `deploy.sh` pulls the image, restarts the service, waits for `/healthz`, checks that the home page answers,
   and removes older images of this site only.

By hand on the VM (same thing without Actions):

```sh
cd /opt/leafpdf/site/deploy
LEAFPDF_IMAGE=ghcr.io/jagritvats/leafpdf-website:main bash deploy.sh
```

If the GitHub repository has another name, pass the matching `LEAFPDF_IMAGE`.

## License

The site's text, images and design: © Synpse Labs, all rights reserved; see [LICENSE](LICENSE). Leaf itself is
AGPL-3.0-or-later, in its own repository.
