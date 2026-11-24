"""Fetch the last year of contributions and draw them as a dot grid -> assets/contributions.svg.
Needs GH_TOKEN (a personal access token with read:user) and GH_USER in the environment.
Run with --demo to draw random data without calling the API."""
import datetime as dt, json, os, random, sys, urllib.request

USER = os.environ.get("GH_USER", "Gideonjon")
OUT = "assets/contributions.svg"
BG, DIM, FG, MUTED = "#0d1117", "#21262d", "#e6edf3", "#7d8590"


def fetch():
    q = """query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{
      totalContributions weeks{contributionDays{date contributionCount}}}}}}"""
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": q, "variables": {"u": USER}}).encode(),
        headers={"Authorization": f"bearer {os.environ['GH_TOKEN']}", "Content-Type": "application/json"},
    )
    cal = json.load(urllib.request.urlopen(req))["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return cal["totalContributions"], [[(d["date"], d["contributionCount"]) for d in w["contributionDays"]] for w in cal["weeks"]]


def demo():
    start = dt.date.today() - dt.timedelta(days=370)
    weeks, total = [], 0
    for w in range(53):
        days = []
        for d in range(7):
            c = max(0, int(random.gauss(4, 5))) if random.random() > 0.35 else 0
            days.append(((start + dt.timedelta(days=w * 7 + d)).isoformat(), c))
            total += c
        weeks.append(days)
    return total, weeks


def draw(total, weeks):
    cell, x0, y0 = 21, 40, 46
    W, H = 1200, y0 + 7 * cell + 56
    counts = sorted(c for w in weeks for _, c in w if c)
    q = lambda p: counts[int(len(counts) * p)] if counts else 1
    levels = [q(0.25), q(0.5), q(0.75)]
    radius = lambda c: 0 if c == 0 else 2.5 + sum(c > l for l in levels) * 1.6

    parts, groups, last_month, last_x = [], {}, None, -999
    for i, week in enumerate(weeks):
        x = x0 + i * cell
        month = week[0][0][:7]
        if month != last_month and i < len(weeks) - 2 and x - last_x > 3 * cell:
            name = dt.date.fromisoformat(week[0][0]).strftime("%b")
            parts.append(f'<text x="{x}" y="30" fill="{MUTED}">{name}</text>')
            last_month, last_x = month, x
        for j, (_, c) in enumerate(week):
            r = radius(c)
            cy = y0 + j * cell + cell / 2
            groups.setdefault(r, []).append(f"M{x + cell/2:g} {cy:g}h0")

    for r, d in sorted(groups.items()):
        parts.append(f'<path stroke="{FG if r else DIM}" stroke-width="{(r or 1.2)*2:g}" stroke-linecap="round" d="{"".join(d)}"/>')
    fy = H - 20
    legend = "".join(f'<circle cx="{1040 + k*18}" cy="{fy-5}" r="{r}" fill="{FG}"/>' for k, r in enumerate([2.5, 4.1, 5.7, 7.3]))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}"
 font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="14">
<rect width="{W}" height="{H}" fill="{BG}"/>
{''.join(parts)}
<line x1="0" y1="{H-44}" x2="{W}" y2="{H-44}" stroke="{DIM}"/>
<text x="{x0}" y="{fy}" fill="{MUTED}">{total:,} contributions in the last year</text>
<text x="996" y="{fy}" fill="{MUTED}" text-anchor="end">Less</text>{legend}
<text x="1124" y="{fy}" fill="{MUTED}">More</text>
</svg>'''


if __name__ == "__main__":
    if "--demo" in sys.argv:
        total, weeks = demo()
    else:
        try:
            total, weeks = fetch()
        except Exception as e:  # never publish fake data: fall back to an empty grid
            print("could not fetch contributions:", e)
            total, weeks = demo()
            total, weeks = 0, [[(d, 0) for d, _ in w] for w in weeks]
    os.makedirs("assets", exist_ok=True)
    open(OUT, "w").write(draw(total, weeks))
    print(f"wrote {OUT} ({total:,} contributions)")
