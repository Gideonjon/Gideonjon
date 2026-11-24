"""Screenshot each site in sites.json and build an animated card -> assets/cards/<slug>.svg.
The card shows the site's icon, name and domain, a loading bar, then the screenshot fading in.
Run: python scripts/cards.py   (needs: pip install playwright && playwright install chromium)
Set CHROME_PATH to use an existing Chrome instead of Playwright's."""
import base64, html, json, os, re, sys, textwrap
from urllib.parse import urlparse, urljoin
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "cards")
SITES = json.load(open(os.environ.get("SITES_FILE", os.path.join(HERE, "sites.json"))))
W, HEAD, SHOT_H, FOOT = 600, 44, 375, 70          # card layout (px)
H = HEAD + SHOT_H + FOOT
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI','Helvetica Neue',Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


TO_PNG = """async ([b64, mime]) => {
    const blob = await (await fetch(`data:${mime};base64,${b64}`)).blob();
    const url = URL.createObjectURL(blob);
    const img = new Image();
    await new Promise((ok, bad) => { img.onload = ok; img.onerror = bad; img.src = url; });
    const c = document.createElement('canvas'); c.width = c.height = 64;
    c.getContext('2d').drawImage(img, 0, 0, 64, 64);
    return c.toDataURL('image/png').split(',')[1];
}"""


def grab(page, url):
    page.goto(url, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(3000)  # let intro animations settle
    if page.evaluate("() => !!document.querySelector('flt-glass-pane, flutter-view, flt-scene-host')"):
        page.wait_for_timeout(9000)  # Flutter web apps keep painting after network idle
    shot = page.screenshot(type="jpeg", quality=72)
    icon_href = page.evaluate("""() => {
        const l = [...document.querySelectorAll('link[rel~="icon"], link[rel="apple-touch-icon"]')];
        const best = l.find(x => /png|svg/.test(x.type || x.href)) || l[0];
        return best ? best.href : '/favicon.ico';
    }""")
    candidates = [urljoin(url, icon_href), urljoin(url, "/favicon.ico"),
                  f"https://www.google.com/s2/favicons?domain={urlparse(url).netloc}&sz=64"]
    for href in candidates:
        try:
            r = page.request.get(href, timeout=15000)
            if not r.ok or len(r.body()) < 50:
                continue
            mime = r.headers.get("content-type", "image/png").split(";")[0]
            if href.endswith(".svg"):
                mime = "image/svg+xml"
            png = page.evaluate(TO_PNG, [base64.b64encode(r.body()).decode(), mime])
            if png:
                return shot, base64.b64decode(png), "image/png"
        except Exception:
            pass
    return shot, None, "image/png"


def card(site, shot, icon, mime):
    domain = urlparse(site["url"]).netloc.removeprefix("www.")
    lines = textwrap.wrap(site["desc"], 72)[:2]
    shot64 = base64.b64encode(shot).decode()
    icon_el = (f'<image href="data:{mime};base64,{base64.b64encode(icon).decode()}" x="16" y="14" width="16" height="16"/>'
               if icon else f'<circle cx="24" cy="22" r="6" fill="#3fb950"/>')
    desc = "".join(f'<text x="16" y="{HEAD + SHOT_H + 28 + i * 20}" class="d">{html.escape(t)}</text>' for i, t in enumerate(lines))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<style>
  .n {{ font: 600 15px {FONT}; fill: #e6edf3 }}
  .u {{ font: 12px {MONO}; fill: #7d8590 }}
  .d {{ font: 14px {FONT}; fill: #c9d1d9 }}
  .bar {{ transform-origin: 0 0; animation: load 1.4s cubic-bezier(.4,0,.2,1) forwards }}
  .barbg {{ animation: hide .3s 1.4s forwards }}
  .shot {{ opacity: 0; animation: show .6s 1.2s ease-out forwards }}
  .skel {{ animation: hide .4s 1.4s forwards }}
  .pulse {{ animation: pulse 1s ease-in-out infinite }}
  @keyframes load {{ 0% {{ transform: scaleX(0) }} 60% {{ transform: scaleX(.7) }} 100% {{ transform: scaleX(1) }} }}
  @keyframes show {{ to {{ opacity: 1 }} }}
  @keyframes hide {{ to {{ opacity: 0 }} }}
  @keyframes pulse {{ 50% {{ opacity: .45 }} }}
</style>
<clipPath id="c"><rect width="{W}" height="{H}" rx="8"/></clipPath>
<g clip-path="url(#c)">
<rect width="{W}" height="{H}" fill="#0d1117"/>
{icon_el}
<text x="40" y="27" class="n">{html.escape(site["name"])}</text>
<text x="{W - 16}" y="27" class="u" text-anchor="end">{html.escape(domain)} ↗</text>
<g class="skel"><g class="pulse" fill="#161b22">
  <rect x="0" y="{HEAD}" width="{W}" height="{SHOT_H}"/>
  <rect x="40" y="{HEAD + 70}" width="260" height="26" rx="4" fill="#21262d"/>
  <rect x="40" y="{HEAD + 110}" width="200" height="26" rx="4" fill="#21262d"/>
  <rect x="40" y="{HEAD + 160}" width="320" height="10" rx="3" fill="#21262d"/>
  <rect x="40" y="{HEAD + 180}" width="280" height="10" rx="3" fill="#21262d"/>
  <rect x="40" y="{HEAD + 220}" width="110" height="32" rx="6" fill="#21262d"/>
</g></g>
<image class="shot" href="data:image/jpeg;base64,{shot64}" x="0" y="{HEAD}" width="{W}" height="{SHOT_H}" preserveAspectRatio="xMidYMin slice"/>
<rect class="barbg" x="0" y="{HEAD}" width="{W}" height="2" fill="#21262d"/>
<rect class="bar" x="0" y="{HEAD}" width="{W}" height="2" fill="#3fb950"/>
<line x1="0" y1="{HEAD + SHOT_H}" x2="{W}" y2="{HEAD + SHOT_H}" stroke="#30363d"/>
{desc}
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="8" fill="none" stroke="#30363d"/>
</svg>'''


def main():
    os.makedirs(OUT, exist_ok=True)
    only = sys.argv[1:]
    with sync_playwright() as p:
        kw = {"executable_path": os.environ["CHROME_PATH"]} if os.environ.get("CHROME_PATH") else {}
        browser = p.chromium.launch(**kw)
        page = browser.new_page(viewport={"width": 1280, "height": 800}, color_scheme="dark")
        for site in SITES:
            if only and slug(site["name"]) not in only:
                continue
            try:
                shot, icon, mime = grab(page, site["url"])
            except Exception as e:  # keep the previous card if a site is down
                print(f"skip {site['name']}: {e}")
                continue
            path = os.path.join(OUT, slug(site["name"]) + ".svg")
            open(path, "w").write(card(site, shot, icon, mime))
            print(f"wrote {path} ({os.path.getsize(path)//1024} KB)")
        browser.close()


if __name__ == "__main__":
    main()
