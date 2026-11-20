// Leaf website: theme toggle, theme-matched screenshots and direct download links.
// The page works without this file: buttons then point at the latest release on GitHub.
(function () {
  "use strict";

  var root = document.documentElement;
  var darkQuery = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;

  function store(key, value) {
    try { if (value === null) localStorage.removeItem(key); else localStorage.setItem(key, value); } catch (e) {}
  }
  function recall(key) {
    try { return localStorage.getItem(key); } catch (e) { return null; }
  }

  // ---- Theme ------------------------------------------------------------------------------------------------
  function chosenTheme() {
    var t = root.getAttribute("data-theme");
    return t === "light" || t === "dark" ? t : null;
  }
  function effectiveTheme() {
    return chosenTheme() || (darkQuery && darkQuery.matches ? "dark" : "light");
  }

  // Screenshots come as <picture> with a dark source limited to (prefers-color-scheme: dark). When the visitor
  // picks a theme by hand, point that media query at the choice so the screenshots follow it.
  function syncPictures() {
    var t = chosenTheme();
    var media = t === "dark" ? "all" : t === "light" ? "not all" : "(prefers-color-scheme: dark)";
    var sources = document.querySelectorAll("source[data-theme-src='dark']");
    for (var i = 0; i < sources.length; i++) {
      if (sources[i].getAttribute("media") !== media) sources[i].setAttribute("media", media);
    }
  }

  function syncToggle() {
    var btn = document.getElementById("theme-toggle");
    if (!btn) return;
    var next = effectiveTheme() === "dark" ? "light" : "dark";
    btn.setAttribute("aria-label", "Switch to " + next + " theme");
    btn.setAttribute("title", "Switch to " + next + " theme");
  }

  function setTheme(t) {
    // Picking the theme the system already uses means "follow the system" again.
    var system = darkQuery && darkQuery.matches ? "dark" : "light";
    if (t === system) {
      root.removeAttribute("data-theme");
      store("leaf-theme", null);
    } else {
      root.setAttribute("data-theme", t);
      store("leaf-theme", t);
    }
    syncPictures();
    syncToggle();
  }

  var toggle = document.getElementById("theme-toggle");
  if (toggle) {
    toggle.hidden = false;
    toggle.addEventListener("click", function () {
      setTheme(effectiveTheme() === "dark" ? "light" : "dark");
    });
  }
  if (darkQuery) {
    var onSystemChange = function () { syncToggle(); };
    if (darkQuery.addEventListener) darkQuery.addEventListener("change", onSystemChange);
    else if (darkQuery.addListener) darkQuery.addListener(onSystemChange);
  }
  syncPictures();
  syncToggle();

  // ---- The visitor's platform ------------------------------------------------------------------------------
  // The page's default is the Microsoft Store (Windows 10 and 11, like Leaf itself). Linux visitors get the AppImage; Mac visitors get the disk image
  // once a release has one (until then, a note instead of a Windows button); phones and tablets get a note,
  // since Leaf is a desktop app. The visitor's platform card is marked and listed first.
  var ua = navigator.userAgent || "";
  var uad = navigator.userAgentData;
  function detectPlatform() {
    var p = (uad && uad.platform) || navigator.platform || "";
    if ((uad && uad.mobile) || /Android|iPhone|iPad|iPod/.test(ua)) return "mobile";
    if (/Mac/.test(p) || /Macintosh/.test(ua)) return navigator.maxTouchPoints > 1 ? "mobile" : "mac";  // iPadOS says "Mac"
    if (/CrOS|Chrome OS|ChromeOS/.test(ua + p)) return "other";
    if (/Linux|X11/.test(ua) || /Linux/.test(p)) return "linux";  // a Windows browser never says X11 or Linux
    if (/Win/.test(p) || /Windows/.test(ua)) return "windows";
    return "other";
  }
  var platform = detectPlatform();
  root.setAttribute("data-platform", platform);

  var heroButton = document.getElementById("hero-download");
  var heroLabel = heroButton && heroButton.querySelector(".label");
  var heroOther = document.getElementById("hero-other");
  var heroNote = document.getElementById("hero-platform");

  function heroMessage(text) {
    if (heroButton) heroButton.hidden = !!text;
    if (heroNote) { heroNote.textContent = text || ""; heroNote.hidden = !text; }
  }

  // Linux and Mac visitors: the hero button becomes a GitHub download (the release page until the API answers)
  function heroAsset(asset, label) {
    if (heroButton) {
      heroButton.setAttribute("data-asset", asset);
      heroButton.href = "https://github.com/jagritvats/Leaf-PDF-Viewer/releases/latest";
    }
    if (heroLabel) heroLabel.textContent = label;
  }

  function markYours(id) {
    var card = document.getElementById(id);
    if (!card) return;
    card.classList.add("yours");
    var tag = card.querySelector(".yours-tag");
    if (tag) tag.hidden = false;
  }

  if (platform === "windows") {
    markYours("platform-windows");
  } else if (platform === "linux") {
    markYours("platform-linux");
    heroAsset("appimage", "Download for Linux");
    if (heroOther) heroOther.textContent = "Windows and other downloads";
  } else if (platform === "mac") {
    markYours("platform-mac");
    heroAsset("mac", "Download for Mac");
    if (heroOther) heroOther.textContent = "Windows and Linux downloads";
    heroMessage("Leaf for Mac is on its way. Today it runs on Windows and Linux.");
  } else if (platform === "mobile") {
    if (heroOther) heroOther.textContent = "See all downloads";
    heroMessage("Leaf is a desktop app for Windows and Linux. Open this page on your computer to download it.");
  }

  function macReleased() {
    var card = document.getElementById("platform-mac");
    if (card) card.setAttribute("data-mac-live", "true");
    if (platform === "mac") {
      heroMessage("");
      if (heroOther) heroOther.textContent = "Other downloads";
    }
  }

  // ---- Latest release from GitHub -------------------------------------------------------------------------
  // The one request this site makes to another server. Cached for an hour so repeat visits don't ask again.
  var API = "https://api.github.com/repos/jagritvats/Leaf-PDF-Viewer/releases/latest";
  var CACHE_KEY = "leaf-release";
  var CACHE_MS = 60 * 60 * 1000;
  var PATTERNS = {
    setup: /-windows-x64-setup\.exe$/i,
    zip: /-windows-x64\.zip$/i,
    appimage: /x86_64\.AppImage$/i,
    tarball: /-linux-x86_64\.tar\.gz$/i,
    mac: /-macos-arm64\.dmg$/i,
    sums: /^SHA256SUMS/i
  };

  function megabytes(bytes) {
    return Math.round(bytes / (1024 * 1024)) + " MB";
  }

  function apply(release) {
    if (!release || !release.assets || !release.tag_name) return;
    var found = {};
    release.assets.forEach(function (a) {
      for (var key in PATTERNS) {
        if (PATTERNS[key].test(a.name) && /^https:\/\/github\.com\//.test(a.browser_download_url)) found[key] = a;
      }
    });
    if (found.mac) macReleased();
    var links = document.querySelectorAll("[data-asset]");
    for (var i = 0; i < links.length; i++) {
      var a = found[links[i].getAttribute("data-asset")];
      if (!a) continue;
      links[i].href = a.browser_download_url;
      var size = links[i].querySelector(".size");
      if (size && a.size) size.textContent = megabytes(a.size);
    }
    var sizes = document.querySelectorAll("[data-size]");
    for (var j = 0; j < sizes.length; j++) {
      var s = found[sizes[j].getAttribute("data-size")];
      if (s && s.size) sizes[j].textContent = ", " + megabytes(s.size);
    }
    var version = release.tag_name.replace(/^v/, "");
    var when = "";
    if (release.published_at) {
      var d = new Date(release.published_at);
      if (!isNaN(d)) when = d.toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" });
    }
    var vs = document.querySelectorAll("[data-version]");
    for (var k = 0; k < vs.length; k++) {
      var kind = vs[k].getAttribute("data-version");
      vs[k].textContent = kind === "long" && when ? "Version " + version + ", released " + when + "." : "Version " + version;
    }
    var notes = document.querySelectorAll("[data-release]");
    for (var n = 0; n < notes.length; n++) {
      if (/^https:\/\/github\.com\//.test(release.html_url || "")) notes[n].href = release.html_url;
    }
  }

  function slim(r) {
    return {
      tag_name: r.tag_name, html_url: r.html_url, published_at: r.published_at,
      assets: (r.assets || []).map(function (a) { return { name: a.name, size: a.size, browser_download_url: a.browser_download_url }; })
    };
  }

  function loadRelease() {
    var cached = recall(CACHE_KEY);
    if (cached) {
      try {
        var c = JSON.parse(cached);
        if (c && c.at && Date.now() - c.at < CACHE_MS && c.release) { apply(c.release); return; }
      } catch (e) {}
    }
    if (!window.fetch) return;
    fetch(API, { headers: { Accept: "application/vnd.github+json" }, credentials: "omit", referrerPolicy: "no-referrer" })
      .then(function (res) { if (!res.ok) throw new Error("GitHub answered " + res.status); return res.json(); })
      .then(function (r) {
        var release = slim(r);
        apply(release);
        store(CACHE_KEY, JSON.stringify({ at: Date.now(), release: release }));
      })
      .catch(function () { /* Keep the links to the release page. */ });
  }

  if (document.querySelector("[data-asset]")) {
    if ("requestIdleCallback" in window) window.requestIdleCallback(loadRelease, { timeout: 2000 });
    else setTimeout(loadRelease, 200);
  }
})();
