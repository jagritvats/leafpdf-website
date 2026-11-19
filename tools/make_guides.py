"""Writes site/guides/**/index.html for leafpdf.org. Edit the guides here, then regenerate:

    python tools/make_guides.py site
    python tools/check_site.py

When Leaf's menus or shortcuts change, check them against the app source and update DATE and VERSION.
"""
from __future__ import annotations

import html
import json
import pathlib
import re
import sys

SITE = pathlib.Path(sys.argv[1])
BASE = "https://leafpdf.org"
DATE = "2026-11-19"
DATE_TEXT = "19 November 2026"
VERSION = "0.2.2"
OG_IMG = f"{BASE}/img/og-1200x630.png"
OG_ALT = ("Leaf: Edit PDFs. Keep them yours. A native PDF editor for Windows and Linux that works offline, "
          "next to a Leaf window editing a report.")
ORG = {"@type": "Organization", "name": "Synpse Labs", "url": f"{BASE}/"}

HEADER = """<a class="skip" href="#main">Skip to content</a>

<header class="site-header">
  <div class="wrap">
    <a class="brand" href="/" aria-label="Leaf, home">
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><defs><linearGradient id="lg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#43c463"/><stop offset="1" stop-color="#1f8a3b"/></linearGradient></defs><rect x="1" y="1" width="22" height="22" rx="5.5" fill="url(#lg)"/><g transform="translate(12 12) scale(.82) translate(-12 -12.5)"><path d="M4.5 19.5C3 10 9 3.5 20 4C20.5 15 14 21 4.5 19.5Z" fill="#fff" fill-opacity=".94"/><path d="M5 19L14.5 9.5" stroke="#2a9a48" stroke-width="1.3" stroke-linecap="round"/></g></svg>
      Leaf
    </a>
    <nav class="nav" aria-label="Main">
      <a class="nav-hide-sm" href="/#features">Features</a>
      <a class="nav-hide-sm" href="/#privacy">Privacy</a>
      <a class="nav-hide-sm" href="/guides/"{cur}>Guides</a>
      <a href="/#download">Download</a>
      <a href="https://github.com/jagritvats/Leaf-PDF-Viewer">GitHub</a>
      <button class="theme-toggle" id="theme-toggle" type="button" aria-label="Switch theme" hidden>
        <svg class="sun" viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2.2M12 19.3v2.2M4.6 4.6l1.6 1.6M17.8 17.8l1.6 1.6M2.5 12h2.2M19.3 12h2.2M4.6 19.4l1.6-1.6M17.8 6.2l1.6-1.6"/></svg>
        <svg class="moon" viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5Z"/></svg>
      </button>
    </nav>
  </div>
</header>"""

FOOTER = """<footer class="site-footer">
  <div class="wrap">
    <p>© 2026 Synpse Labs</p>
    <nav aria-label="Footer">
      <a href="/guides/">Guides</a>
      <a href="/privacy/">Privacy</a>
      <a href="https://github.com/jagritvats/Leaf-PDF-Viewer/blob/main/LICENSE">License</a>
      <a href="https://github.com/jagritvats/Leaf-PDF-Viewer">GitHub</a>
    </nav>
  </div>
</footer>"""

# name: (widths, jpg width, width, height)
SHOTS = {
    "edit-text": ((480, 720, 1040, 1300), 720, 1300, 730),
    "redact": ((480, 720, 1040, 1440), 720, 1720, 950),
    "forms": ((480, 644), 644, 644, 716),
    "signature": ((480, 720, 1040, 1440), 720, 1920, 865),
    "ocr": ((480, 720, 1040, 1200), 720, 1200, 702),
    "organize": ((480, 720, 1040, 1440), 720, 1920, 915),
    "focus": ((480, 720, 1040, 1440), 720, 1920, 1080),
    "start": ((480, 720, 1040, 1240), 720, 1240, 710),
}


def shot(name: str, alt: str, caption: str = "", narrow: bool = False) -> str:
    widths, jpg, w, h = SHOTS[name]
    sizes = "(min-width: 48rem) 26rem, calc(100vw - 2rem)" if narrow else "(min-width: 48rem) 42rem, calc(100vw - 2rem)"
    dark = ", ".join(f"/img/v1/{name}-dark-{x}.webp {x}w" for x in widths)
    light = ", ".join(f"/img/v1/{name}-light-{x}.webp {x}w" for x in widths)
    cap = f"\n        <figcaption>{caption}</figcaption>" if caption else ""
    return f"""<figure class="shot{' narrow' if narrow else ''}">
  <picture>
    <source type="image/webp" media="(prefers-color-scheme: dark)" data-theme-src="dark" srcset="{dark}" sizes="{sizes}">
    <source type="image/webp" srcset="{light}" sizes="{sizes}">
    <img src="/img/v1/{name}-light-{jpg}.jpg" width="{w}" height="{h}" alt="{html.escape(alt)}" loading="lazy" decoding="async">
  </picture>{cap}
      </figure>"""


def k(*keys: str) -> str:
    return " ".join(f"<kbd>{x}</kbd>" for x in keys)


def ui(text: str) -> str:
    return f'<span class="ui">{text}</span>'


def plain(fragment: str) -> str:
    text = re.sub(r"<kbd>(.*?)</kbd>\s*(?=<kbd>)", r"\1+", fragment)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


# --------------------------------------------------------------------------------------------- guides
GUIDES: list[dict] = []

GUIDES.append(dict(
    slug="edit-pdf-text-offline",
    title="Edit PDF text offline, for free (Windows, Linux) | Leaf",
    desc="Change the words already in a PDF on your own computer. Leaf rewrites them in the document's own font, with "
         "no upload. Steps, shortcuts and limits.",
    h1="Edit the text in a PDF, offline and free",
    card="Change the words already on the page, in the document's own font, with no upload.",
    note=k("I") + '<span class="where">Edit › Edit text</span>',
    lede="Many free tools can only put a new text box on top of a PDF. Leaf changes the words that are already "
         "there, in the document's own embedded font, at the same size, color and angle. It all happens on your "
         "computer: no upload and no account.",
    intro_shot=shot("edit-text", "A report in Leaf with one line in an edit outline and the word “promising” "
                    "selected, ready to be retyped in the document's own font."),
    steps=[
        ("Open the PDF",
         f"<p>Choose {ui('File › Open…')} ({k('Ctrl', 'O')}) or drag the file onto the Leaf window. On Windows, "
         f"with the installed app, you can also right-click a PDF in File Explorer and choose {ui('Edit with Leaf')} "
         f"(on Windows 11 it is under {ui('Show more options')}).</p>"),
        ("Pick the Edit text tool",
         f"<p>Press {k('I')}, choose {ui('Edit › Edit text')}, or click the Edit text button in the toolbar. As you "
         "move the pointer over the page, Leaf outlines the line under it.</p>"),
        ("Choose a line or a whole paragraph",
         f"<p>Press {k('Tab')} while the tool is active to switch between single lines and whole paragraphs (also "
         f"{ui('Edit › Edit whole paragraphs')}). Paragraph mode reflows the text as you type, and "
         f"{k('Shift', 'Enter')} starts a new line. Leaf remembers your choice.</p>"),
        ("Click and type",
         f"<p>Click the outlined text and type your change. {k('Enter')} applies it, {k('Esc')} cancels. Every "
         f"change is one undo step, so {k('Ctrl', 'Z')} takes it back.</p>"),
        ("Replace a word everywhere (optional)",
         f"<p>{ui('Edit › Replace…')} ({k('Ctrl', 'H')}) adds a replace row under the find bar. It can match case, "
         "whole words or a regular expression (use <code>\\1</code> or <code>$1</code> for groups). "
         f"{ui('Replace all')} is a single undo step. Lines that can't be changed faithfully are skipped and listed "
         f"with the reason. Tick {ui('Text boxes')} or {ui('Form fields')} to replace there too.</p>"),
        ("Save",
         f"<p>Press {k('Ctrl', 'S')}, or use {ui('File › Save As…')} to keep the original as it was. Leaf rewrites "
         "the file, so the old words are gone from it, not hidden under the new ones.</p>"),
    ],
    after="""<h2 id="limits">Limits</h2>
      <p>Leaf would rather refuse an edit than get it wrong. When it can't change text faithfully, it tells you why.</p>
      <ul>
        <li><strong>Some text can't be edited:</strong> Arabic, Hebrew, Indic and Thai scripts (they need shaping), vertical writing, text without a reliable character mapping, outlined or clipping text, and the invisible text that OCR adds to scans.</li>
        <li><strong>Missing characters:</strong> if the document's font lacks a character you type, Leaf takes it from a matching installed font and names that font in a warning.</li>
        <li><strong>Reading order:</strong> edited text is drawn after the rest of the page, so copy and paste and tagged-PDF structure (used by screen readers) don't follow the edit.</li>
        <li><strong>Signed files:</strong> in a digitally signed PDF, Leaf saves changes as an addition to the file so the signatures stay valid. The earlier revision, with the old text, stays inside the file.</li>
        <li><strong>Scans:</strong> the words on a scanned page are part of an image. OCR makes them searchable, not editable.</li>
      </ul>
      <h2 id="tips">Tips</h2>
      <ul>
        <li>To remove words without replacing them, use <a href="/guides/redact-pdf-permanently/">Redact</a>. Whiteout (<kbd>W</kbd>) only covers text; the text underneath stays in the file.</li>
        <li>Images on the page can be changed too: with the Select tool (<kbd>V</kbd>), click an image to move, resize, rotate, replace or delete it.</li>
        <li>To add new text rather than change existing text, use the Text box tool (<kbd>T</kbd>).</li>
      </ul>""",
    related=["redact-pdf-permanently", "ocr-scanned-pdf-searchable", "why-use-an-offline-pdf-editor"],
))

GUIDES.append(dict(
    slug="redact-pdf-permanently",
    title="Redact a PDF permanently, free and offline | Leaf",
    desc="A black box isn't a redaction. Leaf removes the text, images and data under each mark when you save, and "
         "finds emails, phone numbers and more for you.",
    h1="Redact a PDF permanently, so the text is really gone",
    card="Remove text, images and hidden data for real, and find every email or phone number first.",
    note=k("X") + '<span class="where">Insert › Redact</span>',
    lede="A black rectangle drawn over text is not a redaction: the words are still in the file, and anyone can copy "
         "them out. When you save, Leaf removes what is under each redaction mark: the text, image pixels, drawings, "
         "annotations, form fields and links. It runs on your computer, so the unredacted file never goes anywhere.",
    intro_shot=shot("redact", "An invoice in Leaf: email addresses marked for redaction, the Search & redact dialog "
                    "listing phone numbers it found, and the Redactions panel."),
    steps=[
        ("Open the PDF and pick Redact",
         f"<p>Open the document, then press {k('X')} or choose {ui('Insert › Redact')}.</p>"),
        ("Mark what should go",
         "<p>Drag across text to mark it; the mark snaps to whole words. Drag a box to mark anything else, such as a "
         f"photo, a signature or part of a drawing. Hold {k('Shift')} to always draw a box. You can also select text "
         f"with the Select tool ({k('V')}) and choose {ui('Edit › Redact selected text')}, which is on the "
         "right-click menu too.</p>"),
        ("Find every occurrence with Search & redact",
         f"<p>Choose {ui('Document › Search &amp; redact…')}. Pick what to look for: {ui('Text')}, "
         f"{ui('Email addresses')}, {ui('Phone numbers')}, {ui('Credit card numbers')}, {ui('IBANs')}, "
         f"{ui('Dates')} or a {ui('Custom regular expression')}, then {ui('Search')}. Every hit is listed, ticked, "
         f"with its page and the text around it. Untick anything that should stay, then choose {ui('Mark for redaction')}.</p>"),
        ("Review the marks",
         f"<p>{ui('View › Redactions panel')} lists every mark. Select one to go to it or remove it, or add overlay "
         f"text to show on the marks. The fill color is in the Style panel ({k('F6')}).</p>"),
        ("Remove hidden information (optional)",
         f"<p>{ui('Document › Sanitize document…')} removes, when you save: metadata, JavaScript and actions, "
         "attachments, comments and annotations, hidden text, hidden layers, links, page thumbnails and page labels. "
         "It can also flatten form fields into the page.</p>"),
        ("Save",
         f"<p>Leaf says how many marks are on how many pages, and names any digital signatures that will stop being "
         f"valid. Choose {ui('Save and remove')}. To keep the unredacted original, use {ui('File › Save As…')} and "
         "pick a new name.</p>"),
    ],
    after="""<h2 id="limits">Limits</h2>
      <ul>
        <li><strong>Saving makes it final.</strong> Until you save, marks are only marks and you can undo them. After you save, what was under them is gone from that file.</li>
        <li><strong>Signatures break.</strong> Redacting always rewrites the whole file, so existing digital signatures stop being valid. Leaf warns you first.</li>
        <li><strong>Patterns help, but check the document yourself.</strong> The built-in searches find emails, phone numbers, card numbers, IBANs and dates. Names, addresses and other details need a text search or a mark of your own.</li>
        <li><strong>Scans:</strong> on a scanned page the words are part of the image. Draw a box over them; the image pixels under it are removed.</li>
        <li><strong>Whiteout is not redaction.</strong> The Whiteout tool (<kbd>W</kbd>) only covers content; the text stays in the file.</li>
      </ul>
      <h2 id="check">Check the result</h2>
      <p>Open the saved file and use Find (<kbd>Ctrl</kbd> <kbd>F</kbd>) for a word you redacted. It shouldn't be found, and you shouldn't be able to select or copy anything under the marks.</p>""",
    related=["edit-pdf-text-offline", "ocr-scanned-pdf-searchable", "why-use-an-offline-pdf-editor"],
))

GUIDES.append(dict(
    slug="fill-and-sign-pdf-form",
    title="Fill and sign a PDF form without uploading it | Leaf",
    desc="Type into PDF form fields, tick boxes and add a drawn, typed or scanned signature, all on your own computer. "
         "Free with Leaf for Windows and Linux.",
    h1="Fill in and sign a PDF form without uploading it",
    card="Type into fields, tick boxes and add a drawn, typed or scanned signature.",
    note='<span class="where">Forms menu</span>' + k("Ctrl", "Shift", "G") + '<span class="where">Insert › Signature…</span>',
    lede="Rental applications, tax forms and contracts often hold the most personal details you have. Leaf fills "
         "them in and signs them on your computer, so they don't pass through anyone's server on the way.",
    intro_shot=shot("forms", "A rental application form in Leaf with filled-in fields, ticked boxes, a handwritten "
                    "signature and an empty required field outlined in red.", narrow=True),
    steps=[
        ("Open the form",
         f"<p>Open the PDF in Leaf. Form fields get a tinted background so they're easy to spot; "
         f"{ui('Forms › Highlight fields')} turns that on and off.</p>"),
        ("Fill in the fields",
         f"<p>Click a field and type. Tick checkboxes and radio buttons, and pick from dropdowns and lists. "
         f"{k('Tab')} moves to the next field in the order the form's author set. Required fields are marked.</p>"),
        ("Find what you missed",
         f"<p>{ui('Forms › Next required empty field')} ({k('Ctrl', 'Shift', 'J')}) jumps to the next required "
         "field that is still empty.</p>"),
        ("Add your signature",
         f"<p>Click an empty signature field, or choose {ui('Insert › Signature…')} ({k('Ctrl', 'Shift', 'G')}). "
         f"Draw your signature, type it, or use {ui('Image')} to pick a photo or scan: Leaf removes the white "
         f"background. Choose {ui('Save &amp; place')}. The signature is kept in your library, so next time you "
         f"pick it and choose {ui('Place selected')}. Drag it into place and resize it by its corners.</p>"),
        ("Save",
         f"<p>Press {k('Ctrl', 'S')}. To send a copy whose answers can't be edited as easily, choose "
         f"{ui('Forms › Save flattened copy…')} (also in the File menu): the fields become part of the page.</p>"),
    ],
    after="""<h2 id="more">More form tools</h2>
      <ul>
        <li><strong>Reuse answers:</strong> <span class="ui">Forms › Export form data…</span> saves the values as JSON or XFDF, and <span class="ui">Import form data…</span> fills a form from such a file.</li>
        <li><strong>Start over:</strong> <span class="ui">Forms › Reset form</span> puts every field back to the value it had when you opened the file.</li>
        <li><strong>A PDF without fields:</strong> type on it with the Text box tool (<kbd>T</kbd>), or create real fields from <span class="ui">Forms › Add field</span>.</li>
      </ul>
      <h2 id="limits">Limits</h2>
      <ul>
        <li>A drawn, typed or scanned signature is an image on the page. When you save, it becomes part of the page. It doesn't prove who signed or show whether the document changed later. If you need that, add a <a href="/guides/digitally-sign-pdf/">digital signature</a>.</li>
        <li>A flattened copy can't replace the open document; save it under a new name.</li>
      </ul>""",
    related=["digitally-sign-pdf", "merge-pdf-files", "why-use-an-offline-pdf-editor"],
))

GUIDES.append(dict(
    slug="merge-pdf-files",
    title="Merge PDF files offline and reorder pages | Leaf",
    desc="Combine PDFs into one file on your computer, then reorder, rotate, delete, extract or split pages. From "
         "File Explorer, the command line or inside Leaf.",
    h1="Merge PDFs, then reorder, rotate and extract pages",
    card="Combine files into one, then reorder, rotate, extract or split pages.",
    note=k("Ctrl", "Shift", "O") + '<span class="where">Pages › Organize pages</span>',
    lede="Leaf joins PDFs on your own computer, so there's no upload limit and nothing to wait for. Once the pages "
         "are together, you can put them in order, turn the sideways ones and take out the pages you need.",
    intro_shot=shot("organize", "Leaf's page organizer: eight pages from three documents as thumbnails in a grid, "
                    "three of them selected."),
    steps=[
        ("Combine the files",
         f"<p>Choose whichever is handiest:</p>"
         f"<ul><li><strong>File Explorer (Windows):</strong> select the PDFs, right-click and choose "
         f"{ui('Combine with Leaf')} (on Windows 11, under {ui('Show more options')}). They open as one new "
         f"document, sorted by file name with numbers in order (2 before 10). The right-click menu works for up to "
         f"15 files; {ui('Send to › Combine with Leaf')} has no limit. The installer adds both; Send to is an option "
         f"during setup.</li>"
         f"<li><strong>Inside Leaf:</strong> open the first PDF, then choose {ui('Pages › Insert pages from file…')}, "
         f"or drag PDFs from your file manager onto the Pages panel ({k('F4')}) where they should go.</li>"
         f"<li><strong>Command line:</strong> <code>leaf --merge a.pdf b.pdf c.pdf</code> opens the files, in that "
         "order, as one new document. On Windows, run <code>Leaf.exe --merge …</code> from the folder Leaf is "
         "installed in.</li></ul>"),
        ("Put the pages in order",
         f"<p>Drag thumbnails in the Pages panel ({k('F4')}). Select several with {k('Ctrl')} or {k('Shift')} and "
         f"drag them as a block. For a bigger view, {ui('Pages › Organize pages')} ({k('Ctrl', 'Shift', 'O')}) "
         f"shows every page in a full-window grid. {ui('Move to start')} ({k('Ctrl', 'Home')}), "
         f"{ui('Move to end')} ({k('Ctrl', 'End')}) and {ui('Reverse order')} are in the Pages menu.</p>"),
        ("Rotate, delete or duplicate pages",
         f"<p>Select the pages, then {ui('Rotate left')} ({k('Ctrl', 'Shift', 'L')}), {ui('Rotate right')} "
         f"({k('Ctrl', 'Shift', 'R')}), {ui('Delete pages')} ({k('Ctrl', 'Shift', 'Del')}) or "
         f"{ui('Duplicate pages')} ({k('Ctrl', 'Shift', 'D')}). You can also copy, cut and paste pages, even "
         "between two Leaf windows.</p>"),
        ("Extract or split",
         f"<p>{ui('Pages › Extract pages…')} copies a range such as <code>1-3, 7, 10-</code> into a new file; tick "
         f"{ui('Save each page as a separate file')} for one file per page. {ui('Pages › Split into files…')} cuts "
         "the document every few pages or before each selected page.</p>"),
        ("Save",
         f"<p>Press {k('Ctrl', 'S')} and pick a name for the combined document. Every step before this can be "
         f"undone with {k('Ctrl', 'Z')}.</p>"),
    ],
    after="""<h2 id="tips">Tips</h2>
      <ul>
        <li>Crop pages with the crop tool (<kbd>C</kbd>): drag a rectangle and apply it to this page, the selected pages, or all, odd or even pages.</li>
        <li>On Linux, the tarball includes a Dolphin service menu that adds Combine with Leaf to the right-click menu; see <a href="/guides/pdf-editor-linux/">Leaf on Linux</a>.</li>
      </ul>
      <h2 id="limits">Limits</h2>
      <ul>
        <li>A crop hides what's outside it; it doesn't remove that content from the file. To remove content, <a href="/guides/redact-pdf-permanently/">redact</a> it.</li>
        <li>Copied or duplicated pages bring their original comments, not unsaved changes to them.</li>
      </ul>""",
    related=["fill-and-sign-pdf-form", "pdf-editor-linux", "ocr-scanned-pdf-searchable"],
))

GUIDES.append(dict(
    slug="ocr-scanned-pdf-searchable",
    title="Make a scanned PDF searchable with offline OCR | Leaf",
    desc="Turn scanned pages into text you can search, select and copy. Leaf's OCR runs on your computer, English "
         "built in, other languages on request.",
    h1="Make a scanned PDF searchable, with OCR that runs offline",
    card="Turn scanned pages into text you can search, select and copy, without uploading them.",
    note='<span class="where">Document › Recognize text (OCR)…</span>',
    lede="A scanned PDF is a stack of pictures: you can't search it or copy a sentence out of it. Text recognition "
         "(OCR) finds the words and adds them as an invisible layer behind each page image, so the pages look the "
         "same but become searchable. Leaf does this on your computer.",
    intro_shot=shot("ocr", "A scanned letter in Leaf after text recognition: a search for “water” highlights its "
                    "four matches on the scanned page."),
    steps=[
        ("Open the scan",
         f"<p>Open the PDF. When a document looks scanned, Leaf offers to recognize its text; choose "
         f"{ui('Recognize text…')} in that message, or go on to the next step.</p>"),
        ("Start text recognition",
         f"<p>Choose {ui('Document › Recognize text (OCR)…')}.</p>"),
        ("Pick the language",
         "<p>English is built in. For another language, choose "
         f"{ui('Add languages…')}, tick the ones you need and download them. These are Tesseract language files, "
         "1 to 15 MB each, from the Tesseract project on GitHub; only the language files are downloaded, never your "
         "document. You can combine languages with a plus sign, such as <code>eng+hin</code>.</p>"),
        ("Choose pages and resolution",
         f"<p>Recognize {ui('All pages')}, the {ui('Current page')}, or a range such as <code>1-3, 7, 10-</code>. "
         f"{ui('Skip pages that already have text')} is on by default. 300 dpi suits most scans; a higher resolution "
         "finds small print better but is slower.</p>"),
        ("Recognize",
         f"<p>Choose {ui('Recognize')}. Leaf works in the background with per-page progress, and you can cancel. As "
         f"soon as it's done, Find ({k('Ctrl', 'F')}), selecting and copying work on the scanned pages.</p>"),
        ("Check and save",
         f"<p>{ui('View › Show recognized text')} tints each word by confidence: green when Leaf is sure, amber or "
         f"red when it isn't. Save ({k('Ctrl', 'S')}) to write the invisible text into the file. Changed your mind "
         f"before saving? {ui('Document › Remove recognized text')}, or undo.</p>"),
    ],
    after="""<h2 id="tips">Tips</h2>
      <ul>
        <li>From a terminal, <code>leaf ocr scan.pdf -o searchable.pdf</code> does the same without opening a window. On Windows, use <code>leaf-cli</code> from Leaf's folder.</li>
        <li>Once a scan is searchable, Find shows you where a name or number appears, so you can <a href="/guides/redact-pdf-permanently/">redact</a> it with a box.</li>
      </ul>
      <h2 id="limits">Limits</h2>
      <ul>
        <li>Recognition is only as good as the scan. Blurry, skewed or very small print gives more mistakes; check the amber and red words.</li>
        <li>Recognized text makes a page searchable, not editable: the Edit text tool doesn't change OCR text.</li>
        <li>Leaf connects to the internet only when you choose Add languages…, to download the language files you picked.</li>
      </ul>""",
    related=["redact-pdf-permanently", "edit-pdf-text-offline", "merge-pdf-files"],
))

GUIDES.append(dict(
    slug="digitally-sign-pdf",
    title="Digitally sign a PDF with a certificate, free | Leaf",
    desc="Add a PAdES digital signature to a PDF with your .p12 or .pfx certificate, or one Leaf creates. Visible or "
         "invisible, with optional timestamp.",
    h1="Add a digital signature to a PDF with your certificate",
    card="Sign with a .p12 or .pfx certificate, or one Leaf creates, and check other signatures offline.",
    note=k("F12") + '<span class="where">Document › Sign digitally…</span>',
    lede="A digital signature is not a picture of your handwriting. It is cryptographic proof of which certificate "
         "signed the document, and it shows whether the file changed afterwards. Leaf adds PAdES signatures with "
         "your own certificate file, on your computer.",
    intro_shot=shot("signature", "A services agreement in Leaf with two visible digital signatures, a banner saying "
                    "both are valid, and the Signatures panel showing integrity and trust for each signer."),
    steps=[
        ("Open the PDF and save your changes",
         "<p>Signing works on the saved file. If you have unsaved changes, Leaf asks you to save them first.</p>"),
        ("Start signing",
         f"<p>Choose {ui('Document › Sign digitally…')}.</p>"),
        ("Choose your certificate",
         f"<p>Pick your <code>.p12</code> or <code>.pfx</code> file with {ui('Browse…')} and enter its password. "
         f"No certificate? {ui('Create a self-signed certificate…')} makes one from your name, email and "
         "organization, protected by a password you choose.</p>"),
        ("Decide how it looks",
         f"<p>Under {ui('Place')}, choose an empty signature field in the form, {ui('New box')} to draw one on the "
         f"page next, or {ui('Invisible (no mark on the page)')}. For a visible signature, the appearance can be "
         f"text only or your handwritten signature, with {ui('Show name, date and reason')} if you like. "
         f"{ui('Reason')}, {ui('Location')} and {ui('Contact')} are optional.</p>"),
        ("Set the options",
         f"<p>{ui('Certify')} is meant for the first signature, usually the author's: it states which later changes are allowed "
         "(none; form filling and signing; or form filling, signing and comments). Leave it at "
         f"{ui('No — approval signature')} otherwise. A {ui('Timestamp server')} is optional: enter one and the "
         "server receives a hash of the signature, never the document.</p>"),
        ("Sign",
         "<p>Save the signed document as a new file (Leaf suggests <code>name-signed.pdf</code>) or sign this file "
         "in place. The signature is added to the end of the file, so earlier signatures stay valid.</p>"),
    ],
    after="""<h2 id="verify">Check signatures</h2>
      <p>Open a signed PDF and a banner shows whether its signatures are valid. The Signatures panel (<kbd>F12</kbd>, or <span class="ui">View › Signatures panel</span>) shows, for each one, its integrity, changes made after signing, whether the signer is trusted, and the timestamp. The check runs offline.</p>
      <p>A signer is trusted when their certificate is one of your trusted certificates or was issued by one of them. By default Leaf also trusts the certificates your system trusts (Settings › Signing). Select a signature and choose <span class="ui">Trust signer</span>, or manage the list in <span class="ui">Document › Trusted certificates…</span>.</p>
      <h2 id="limits">Limits</h2>
      <ul>
        <li><strong>Self-signed certificates</strong> show as “Signer not trusted” for other people until they trust your certificate. You can send them its <code>.pem</code> file from the Signatures panel's Details.</li>
        <li><strong>Certificate files only:</strong> Leaf signs with <code>.p12</code> or <code>.pfx</code> files. It doesn't use the Windows certificate store or smart cards yet, and doesn't add long-term validation (LTV) data.</li>
        <li><strong>Changes after signing:</strong> Leaf saves later edits as additions to the file so signatures stay valid. Redaction and Sanitize rewrite the whole file and break them; Leaf warns you before that happens.</li>
        <li>Whether a signature meets a legal requirement depends on what you sign, where, and with which certificate.</li>
      </ul>""",
    related=["fill-and-sign-pdf-form", "redact-pdf-permanently", "why-use-an-offline-pdf-editor"],
))

GUIDES.append(dict(
    slug="pdf-editor-linux",
    title="Free PDF editor for Linux: install and use Leaf",
    desc="Install Leaf on Linux from the AppImage or the tarball, then edit text, redact, fill forms, sign and OCR "
         "PDFs offline. Free and open source.",
    h1="Edit PDFs on Linux with Leaf",
    card="Install the AppImage or the tarball, then edit, redact, sign and OCR PDFs offline.",
    note='<span class="where">Linux x86_64</span>',
    lede="Leaf is a native PDF editor for Linux on x86_64. It follows your KDE or GNOME theme, light or dark, and "
         "works offline: edit existing text, redact, fill and sign forms, add digital signatures, recognize scanned "
         "text and organize pages.",
    intro_shot=shot("focus", "Leaf in Focus mode: a report fills the window, with only a floating toolbar at the top "
                    "and a page and zoom bar at the bottom."),
    steps=[
        ("Check the requirements",
         "<p>A 64-bit x86 system with glibc 2.34 or newer (Ubuntu 22.04, Debian 12, Fedora 35 and later all have "
         "it) and <code>libOpenGL.so.0</code>, which is the <code>libopengl0</code> package on Debian and "
         "Ubuntu.</p>"),
        ("Download",
         f"<p>Get the AppImage or the tarball from the <a href=\"/#download\">download section</a>. The AppImage is "
         "one file you run; the tarball is the app folder with its desktop entry, icons and a Dolphin service "
         "menu.</p>"),
        ("Run the AppImage",
         "<p>Make it executable, then run it:</p>"
         "<pre class=\"code\" tabindex=\"0\" aria-label=\"Run the AppImage\"><code>"
         "<span class=\"p\">$ </span>chmod +x Leaf-*-x86_64.AppImage\n"
         "<span class=\"p\">$ </span>./Leaf-*-x86_64.AppImage</code></pre>"
         "<p>If your system has no FUSE, add <code>--appimage-extract-and-run</code>.</p>"),
        ("Or unpack the tarball",
         "<pre class=\"code\" tabindex=\"0\" aria-label=\"Unpack and run the tarball\"><code>"
         "<span class=\"p\">$ </span>tar xzf leaf-*-linux-x86_64.tar.gz\n"
         "<span class=\"p\">$ </span>cd leaf-*-linux-x86_64\n"
         "<span class=\"p\">$ </span>./leaf/leaf</code></pre>"
         "<p>To add Leaf to your app menu, see <a href=\"#tarball\">Set up the tarball</a> below.</p>"),
        ("Open a PDF and start editing",
         f"<p>Drag a PDF onto the window or use {ui('File › Open…')} ({k('Ctrl', 'O')}). The list below links a guide for each task.</p>"),
    ],
    after="""<h2 id="use">What you can do</h2>
      <ul>
        <li><strong>Edit existing text:</strong> press <kbd>I</kbd> and click a line. <a href="/guides/edit-pdf-text-offline/">Edit PDF text</a></li>
        <li><strong>Redact:</strong> press <kbd>X</kbd>, or <span class="ui">Document › Search &amp; redact…</span>. <a href="/guides/redact-pdf-permanently/">Redact a PDF</a></li>
        <li><strong>Fill and sign forms:</strong> the Forms menu and <span class="ui">Insert › Signature…</span>. <a href="/guides/fill-and-sign-pdf-form/">Fill and sign a form</a></li>
        <li><strong>Digital signatures:</strong> <span class="ui">Document › Sign digitally…</span>, and <kbd>F12</kbd> to check them. <a href="/guides/digitally-sign-pdf/">Sign with a certificate</a></li>
        <li><strong>OCR:</strong> <span class="ui">Document › Recognize text (OCR)…</span>. <a href="/guides/ocr-scanned-pdf-searchable/">Make a scan searchable</a></li>
        <li><strong>Pages:</strong> <kbd>Ctrl</kbd> <kbd>Shift</kbd> <kbd>O</kbd> for the organizer, <code>leaf --merge a.pdf b.pdf</code> to combine files. <a href="/guides/merge-pdf-files/">Merge and organize</a></li>
      </ul>
      <h2 id="tarball">Set up the tarball</h2>
      <p>The tarball's desktop entry and Dolphin service menu start Leaf as <code>leaf</code>, so put a small launcher on your <code>PATH</code> first. From inside the unpacked folder:</p>
<pre class="code" tabindex="0" aria-label="Install a launcher, desktop entry and icons"><code><span class="c"># a launcher in ~/.local/bin (on the PATH of most distributions)</span>
<span class="p">$ </span>mkdir -p ~/.local/bin ~/.local/share/applications
<span class="p">$ </span>printf '#!/bin/sh\\nexec "%s/leaf/leaf" "$@"\\n' "$PWD" &gt; ~/.local/bin/leaf
<span class="p">$ </span>chmod +x ~/.local/bin/leaf

<span class="c"># the app menu entry and its icons</span>
<span class="p">$ </span>cp io.github.jagritvats.Leaf.desktop ~/.local/share/applications/
<span class="p">$ </span>cp -r icons ~/.local/share/

<span class="c"># KDE: Combine with Leaf in Dolphin's right-click menu</span>
<span class="p">$ </span>mkdir -p ~/.local/share/kio/servicemenus
<span class="p">$ </span>cp leaf-combine.desktop ~/.local/share/kio/servicemenus/
<span class="p">$ </span>chmod +x ~/.local/share/kio/servicemenus/leaf-combine.desktop</code></pre>
      <p>Keep the unpacked folder where it is: the launcher points to it. To make Leaf your default PDF app, open <span class="ui">Edit › Settings…</span> (<kbd>Ctrl</kbd> <kbd>,</kbd>), go to System and choose <span class="ui">Make Leaf the default PDF app…</span>. It needs the desktop entry installed and <code>xdg-mime</code> (xdg-utils).</p>
      <h2 id="trouble">If Leaf doesn't start</h2>
      <p>Run it from a terminal to see the error. A missing library is the usual cause. On Debian and Ubuntu, these packages cover what Leaf needs:</p>
<pre class="code" tabindex="0" aria-label="Install runtime libraries"><code><span class="p">$ </span>sudo apt install libopengl0 libegl1 libxkbcommon0 libxkbcommon-x11-0 \\
    libfontconfig1 libdbus-1-3 libxcb-cursor0</code></pre>
      <p>Leaf isn't in distribution repositories, the AUR or Flathub yet. Updates are published on the <a href="https://github.com/jagritvats/Leaf-PDF-Viewer/releases">releases page</a>.</p>""",
    related=["edit-pdf-text-offline", "merge-pdf-files", "why-use-an-offline-pdf-editor"],
))

GUIDES.append(dict(
    slug="why-use-an-offline-pdf-editor",
    title="Why use an offline, local PDF editor? | Leaf",
    desc="What happens to a document when you edit it online, what changes when the editor runs on your own "
         "computer, and when it matters most.",
    h1="Why use an offline PDF editor",
    card="What happens to a file when you edit it online, and when keeping it local matters.",
    note='<span class="where">Privacy</span>',
    lede="PDFs are often the documents that matter most: contracts, tax returns, medical letters, pay slips, "
         "IDs. Where you edit them decides who else handles them.",
    intro_shot="",
    steps=[],
    after="""<h2 id="online">What happens when you edit a PDF online</h2>
      <p>A web-based editor works on a server. To change your PDF, it has to:</p>
      <ol>
        <li>upload the whole file, including any hidden parts such as metadata, attachments and earlier revisions;</li>
        <li>store and process it on a computer run by someone else, in a country you may not know;</li>
        <li>send the result back, and keep or delete the file according to that service's policy.</li>
      </ol>
      <p>Many services handle this carefully. Still, the document has left your hands, and you depend on someone else's security, retention rules and staff. For some documents that alone is a problem: contracts, health records and client files often come with confidentiality duties or data-protection rules about who may receive them.</p>
      <h2 id="local">What changes with a local editor</h2>
      <ul>
        <li><strong>The file stays put.</strong> It is read from your disk, edited in memory and saved back. No copy is made anywhere else.</li>
        <li><strong>It works without a connection,</strong> on a train, on a locked-down network or when a service is down.</li>
        <li><strong>No upload limits.</strong> Big scans and long documents open as fast as your computer allows.</li>
        <li><strong>You can check it.</strong> With an open-source editor, anyone can read the code and see what it does with your files.</li>
      </ul>
      <p>A local editor doesn't make a file safe on its own: your computer still needs to be secure, and once you email the result, it's out. But it removes one step where a copy could leak.</p>
      <h2 id="leaf">How Leaf handles your files</h2>
      <div class="callout"><p>Leaf has no accounts, analytics, telemetry, crash reporting or ads. Documents are opened, edited and saved on your computer and are never uploaded anywhere.</p></div>
      <p>It goes online only when you ask for something that needs it:</p>
      <ul>
        <li><strong>Extra OCR languages:</strong> Add languages… downloads the language files you pick. No document content is sent.</li>
        <li><strong>Timestamped signatures:</strong> if you enter a timestamp server, it receives a hash of the signature, never the document.</li>
        <li><strong>Links in documents:</strong> a web link you click opens in your browser.</li>
      </ul>
      <p>Recovery copies of unsaved work are kept in your user profile and deleted when you save or close the document. The full details are in the <a href="/privacy/">privacy policy</a>, and the code is on <a href="https://github.com/jagritvats/Leaf-PDF-Viewer">GitHub</a> under the AGPL.</p>
      <h2 id="before-sharing">Before you share a PDF</h2>
      <p>Keeping a file local is half of it. Before it leaves your computer, check what it carries:</p>
      <ul>
        <li>Black boxes drawn over text don't remove it. <a href="/guides/redact-pdf-permanently/">Redact it for real.</a></li>
        <li>Metadata, comments, attachments and hidden text can hold more than the visible page. Leaf's Sanitize document removes them.</li>
        <li>A picture of a signature proves little. For proof of who signed and that nothing changed, use a <a href="/guides/digitally-sign-pdf/">digital signature</a>.</li>
      </ul>""",
    related=["redact-pdf-permanently", "fill-and-sign-pdf-form", "edit-pdf-text-offline"],
))

BY_SLUG = {g["slug"]: g for g in GUIDES}


# --------------------------------------------------------------------------------------------- page assembly
def head(title: str, desc: str, url: str, og_type: str, ld: dict) -> str:
    t, d = html.escape(title), html.escape(desc)
    ld_json = json.dumps(ld, ensure_ascii=False, indent=1).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t}</title>
<meta name="description" content="{d}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="Leaf">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:image" content="{OG_IMG}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{html.escape(OG_ALT)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{t}">
<meta name="twitter:description" content="{d}">
<meta name="twitter:image" content="{OG_IMG}">
<meta name="twitter:image:alt" content="{html.escape(OG_ALT)}">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#f6f8f4" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0f1a14" media="(prefers-color-scheme: dark)">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/icons/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="stylesheet" href="/assets/site.css">
<script type="application/ld+json">
{ld_json}
</script>
<script src="/assets/theme.js"></script>
<script src="/assets/site.js" defer></script>
</head>
<body>
"""


def breadcrumbs(items: list[tuple[str, str]]) -> dict:
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": name, "item": url} for i, (name, url) in enumerate(items)]}


def crumbs_html(current: str | None) -> str:
    if current is None:
        return """<nav class="crumbs" aria-label="Breadcrumb">
        <ol><li><a href="/">Home</a></li><li aria-current="page">Guides</li></ol>
      </nav>"""
    return f"""<nav class="crumbs" aria-label="Breadcrumb">
        <ol><li><a href="/">Home</a></li><li><a href="/guides/">Guides</a></li><li aria-current="page">{current}</li></ol>
      </nav>"""


CTA = """<aside class="guide-cta" aria-labelledby="cta-title">
        <div>
          <h2 id="cta-title">Get Leaf</h2>
          <p>Free and open source, for Windows 10 and 11 and Linux. Works offline.</p>
        </div>
        <a class="button" href="/#download">Download Leaf</a>
      </aside>"""


def related_html(slugs: list[str]) -> str:
    items = "\n".join(
        f'          <li><a href="/guides/{s}/">{BY_SLUG[s]["h1"]}</a><span>{BY_SLUG[s]["card"]}</span></li>' for s in slugs)
    return f"""<nav class="related" aria-labelledby="related-title">
        <h2 id="related-title">Related guides</h2>
        <ul>
{items}
        </ul>
      </nav>"""


def guide_page(g: dict) -> str:
    url = f"{BASE}/guides/{g['slug']}/"
    crumb = breadcrumbs([("Home", f"{BASE}/"), ("Guides", f"{BASE}/guides/"), (g["h1"], url)])
    common = {"name": g["h1"], "description": g["desc"], "url": url, "inLanguage": "en",
              "image": OG_IMG, "datePublished": DATE, "dateModified": DATE}
    if g["steps"]:
        main = {"@type": "HowTo", **common, "tool": [{"@type": "HowToTool", "name": f"Leaf {VERSION}"}],
                "step": [{"@type": "HowToStep", "position": i + 1, "name": name, "text": plain(body),
                          "url": f"{url}#step-{i + 1}"} for i, (name, body) in enumerate(g["steps"])]}
    else:
        main = {"@type": "TechArticle", "headline": g["h1"], **common, "author": ORG, "publisher": ORG,
                "about": {"@type": "SoftwareApplication", "name": "Leaf", "applicationCategory": "BusinessApplication",
                          "operatingSystem": "Windows 10, Windows 11, Linux", "url": f"{BASE}/",
                          "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}}}
    ld = {"@context": "https://schema.org", "@graph": [crumb, main]}

    parts = [head(g["title"], g["desc"], url, "article", ld), HEADER.replace("{cur}", ""), ""]
    body = [f"""<main id="main" class="page guide">
  <div class="wrap">
    <p class="margin-note">{g['note']}</p>
    <article>
      {crumbs_html(g['h1'])}
      <h1>{g['h1']}</h1>
      <p class="updated">Updated {DATE_TEXT} · Leaf {VERSION}</p>
      <p class="lede">{g['lede']}</p>"""]
    if g["intro_shot"]:
        body.append("      " + g["intro_shot"])
    if g["steps"]:
        body.append('      <h2 id="steps">Steps</h2>\n      <ol class="steps">')
        for i, (name, sbody) in enumerate(g["steps"]):
            body.append(f'        <li id="step-{i + 1}">\n          <h3>{name}</h3>\n          {sbody}\n        </li>')
        body.append("      </ol>")
    body.append("      " + g["after"])
    body.append("      " + CTA)
    body.append("      " + related_html(g["related"]))
    body.append("""    </article>
  </div>
</main>
""")
    parts.append("\n".join(body))
    parts.append(FOOTER)
    parts.append("</body>\n</html>\n")
    return "\n".join(parts)


HUB = dict(
    title="PDF guides: edit, redact, sign and OCR offline | Leaf",
    desc="Step-by-step guides for editing PDFs on your own computer with Leaf: change text, redact, fill and sign "
         "forms, merge pages, OCR and more.",
)


def hub_page() -> str:
    url = f"{BASE}/guides/"
    ld = {"@context": "https://schema.org", "@graph": [
        breadcrumbs([("Home", f"{BASE}/"), ("Guides", url)]),
        {"@type": "CollectionPage", "name": "Leaf guides", "description": HUB["desc"], "url": url, "inLanguage": "en",
         "mainEntity": {"@type": "ItemList", "itemListElement": [
             {"@type": "ListItem", "position": i + 1, "url": f"{BASE}/guides/{g['slug']}/", "name": g["h1"]}
             for i, g in enumerate(GUIDES)]}},
    ]}
    cards = "\n".join(f"""        <li>
          <a href="/guides/{g['slug']}/">
            <span class="guide-title">{g['h1']}</span>
            <span class="guide-sum">{g['card']}</span>
          </a>
        </li>""" for g in GUIDES)
    return "\n".join([
        head(HUB["title"], HUB["desc"], url, "website", ld),
        HEADER.replace("{cur}", ' aria-current="page"'),
        "",
        f"""<main id="main" class="page guide">
  <div class="wrap">
    <p class="margin-note">Leaf {VERSION}</p>
    <article>
      {crumbs_html(None)}
      <h1>Guides</h1>
      <p class="lede">How to get common PDF jobs done with Leaf, step by step, on your own computer. Each guide uses the menu names and shortcuts in Leaf {VERSION} and says plainly what Leaf can't do.</p>
      <ul class="guide-list">
{cards}
      </ul>
      <p class="hub-more">Leaf is free and open source, for Windows 10 and 11 and Linux. Something missing or wrong? <a href="https://github.com/jagritvats/Leaf-PDF-Viewer/issues">Open an issue on GitHub</a>.</p>
      {CTA}
    </article>
  </div>
</main>
""",
        FOOTER,
        "</body>\n</html>\n",
    ])


def main() -> None:
    out = SITE / "guides"
    out.mkdir(exist_ok=True)
    (out / "index.html").write_text(hub_page(), encoding="utf-8", newline="\n")
    print(f"{len(HUB['title']):3} {len(HUB['desc']):3} /guides/  {HUB['title']}")
    for g in GUIDES:
        d = out / g["slug"]
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(guide_page(g), encoding="utf-8", newline="\n")
        print(f"{len(g['title']):3} {len(g['desc']):3} /guides/{g['slug']}/  {g['title']}")


if __name__ == "__main__":
    main()
