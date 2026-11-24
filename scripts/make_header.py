"""Generate assets/header.svg: name, role, bio on the left; halftone ripple dots on the right."""
import math, os, sys

W, H = 1200, 340
BG = "#0d1117"
out = sys.argv[1] if len(sys.argv) > 1 else "assets/header.svg"

dots = []
step = 9
# ripple centres for the interference pattern
centres = [(1000, 120, 0.075), (1130, 260, 0.06), (900, 40, 0.05)]
for y in range(step // 2, H, step):
    for x in range(step // 2, W, step):
        v = sum(math.sin(math.hypot(x - cx, y - cy) * f) for cx, cy, f in centres) / len(centres)
        fade = min(1.0, max(0.0, (x - 720) / 300))  # fade in from the left
        r = (v + 1) / 2 * 3.6 * fade
        if r > 0.5:
            dots.append((round(r * 2) / 2, x, y))

levels = {}
for r, x, y in dots:
    levels.setdefault(r, []).append(f"M{x} {y}h0")
paths = "".join(f'<path stroke-width="{r*2:g}" d="{"".join(d)}"/>' for r, d in sorted(levels.items()))

font = "-apple-system,BlinkMacSystemFont,'Segoe UI','Helvetica Neue',Arial,sans-serif"
mono = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<style>
  @keyframes pulse {{ 0%,100% {{ opacity:.55 }} 50% {{ opacity:1 }} }}
  .dots {{ animation: pulse 6s ease-in-out infinite; }}
</style>
<rect width="{W}" height="{H}" fill="{BG}"/>
<g class="dots" stroke="#e6edf3" stroke-linecap="round" fill="none">{paths}</g>
<rect x="0" y="0" width="760" height="{H}" fill="url(#fade)"/>
<defs><linearGradient id="fade" x1="0" x2="1">
  <stop offset="0.75" stop-color="{BG}" stop-opacity="1"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/>
</linearGradient></defs>
<text x="48" y="150" font-family="{font}" font-size="88" font-weight="700" fill="#ffffff" letter-spacing="-3">Gideon Jones</text>
<text x="52" y="190" font-family="{mono}" font-size="17" fill="#7d8590">@Gideonjon</text>
<text x="52" y="236" font-family="{font}" font-size="21" fill="#c9d1d9">Mobile Engineer — Android &amp; iOS. 5+ years in fintech &amp; Web3.</text>
<text x="52" y="266" font-family="{font}" font-size="21" fill="#c9d1d9">Trading apps · crypto payments · SDKs · MVPs to production.</text>
<circle cx="58" cy="304" r="5" fill="#3fb950"/>
<text x="72" y="310" font-family="{mono}" font-size="15" fill="#3fb950">open to full-time, contract &amp; freelance</text>
</svg>'''

os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
open(out, "w").write(svg)
print(f"wrote {out}: {len(svg)//1024} KB, {len(dots)} dots")
