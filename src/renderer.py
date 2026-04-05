from collections import defaultdict

TITLES_PER_ROW = 5

DOMAIN_ICONS = {"movie": "🎬", "tv": "📺", "game": "🎮", "book": "📚"}


def render_thumb(item, domain="movie"):
    url = item.get("url", "#")
    poster = item.get("poster_url") or item.get("poster_path")
    if poster and poster.startswith("/"):
        poster = f"https://image.tmdb.org/t/p/w92{poster}"
    title = item.get("title", "")
    year = (item.get("release_date") or item.get("air_date") or "")[:4]
    icon = DOMAIN_ICONS.get(domain, "")

    img = f'<img src="{poster}" style="width:40px;border-radius:4px;" title="{title} ({year})">' if poster else f'<span style="font-size:10px;color:#aaa;background:#333;padding:2px 4px;border-radius:4px;">{icon} {title[:12]}</span>'
    return f'<a href="{url}" target="_blank" style="text-decoration:none;display:inline-block;margin:2px;">{img}</a>'


def render_card(rec):
    domain = rec.get("domain", "movie")
    tmdb_type = "tv" if domain == "tv" else "movie"
    tmdb_url = f"https://www.themoviedb.org/{tmdb_type}/{rec['id']}"
    img_url = rec.get("backdrop_url") or rec["poster_url"]

    # rewatch / past seasons
    rewatch_html = ""
    if rec["rewatch"]:
        thumbs = "".join(render_thumb(m, domain) for m in rec["rewatch"])
        label = "📺 Past seasons:" if domain == "tv" else "🔁 Rewatch first:"
        rewatch_html = f"""
        <div style="margin-top:6px;">
            <div style="font-size:11px;color:#aaa;">{label}</div>
            <div style="display:flex;flex-wrap:wrap;gap:2px;margin-top:4px;">{thumbs}</div>
        </div>"""

    # cross-domain franchise plan
    franchise_html = ""
    plan = rec.get("franchise_plan", {})
    for fdomain, items in plan.get("domains", {}).items():
        if not items:
            continue
        icon = DOMAIN_ICONS.get(fdomain.rstrip("s"), "")
        thumbs = "".join(render_thumb(item, fdomain.rstrip("s")) for item in items[:5])
        franchise_html += f"""
        <div style="margin-top:6px;">
            <div style="font-size:11px;color:#aaa;">{icon} Also in this universe ({fdomain}):</div>
            <div style="display:flex;flex-wrap:wrap;gap:2px;margin-top:4px;">{thumbs}</div>
        </div>"""

    domain_badge = f'<span style="font-size:10px;background:#333;padding:1px 5px;border-radius:4px;color:#aaa;">{DOMAIN_ICONS.get(domain,"")} {domain.upper()}</span>'

    return f"""
    <div style="width:260px;flex-shrink:0;background:#1a1a1a;border-radius:10px;overflow:hidden;box-sizing:border-box;">
        <a href="{tmdb_url}" target="_blank">
            <img src="{img_url}" style="width:100%;height:140px;object-fit:cover;display:block;">
        </a>
        <div style="padding:10px;">
            {domain_badge}
            <a href="{tmdb_url}" target="_blank" style="color:#fff;text-decoration:none;">
                <div style="font-size:13px;font-weight:bold;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:4px;">{rec['upcoming']}</div>
            </a>
            <div style="font-size:11px;color:#aaa;">📅 {rec['release_date']}</div>
            <div style="font-size:11px;color:#f5c518;">⭐ {rec['vote_average']}</div>
            <div style="font-size:11px;color:#888;margin-top:4px;">{rec['overview'][:80]}...</div>
            {rewatch_html}
            {franchise_html}
        </div>
    </div>"""


def render_html(recommendations: list, output_file="output.html"):
    groups = defaultdict(list)
    for rec in recommendations:
        genre = rec["genres"][0] if rec.get("genres") else "Other"
        domain = rec.get("domain", "movie")
        key = f"{DOMAIN_ICONS.get(domain, '')} {domain.capitalize()} — {genre}"
        groups[key].append(rec)

    sorted_groups = sorted(groups.items(), key=lambda x: -len(x[1]))

    sections = ""
    for genre, recs in sorted_groups:
        rows_html = ""
        for i in range(0, len(recs), TITLES_PER_ROW):
            chunk = recs[i:i + TITLES_PER_ROW]
            cards = "".join(render_card(r) for r in chunk)
            rows_html += f'<div style="display:flex;gap:12px;margin-bottom:12px;overflow-x:auto;padding-bottom:4px;">{cards}</div>'

        sections += f"""
        <section style="margin-bottom:40px;">
            <h2 style="color:#f5c518;border-bottom:1px solid #333;padding-bottom:6px;">{genre}</h2>
            {rows_html}
        </section>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>RewindRec</title>
    <style>
        body {{ font-family: sans-serif; background: #111; color: #eee; padding: 20px; max-width: 1400px; margin: 0 auto; }}
        h1 {{ color: #f5c518; }}
        ::-webkit-scrollbar {{ height: 6px; }}
        ::-webkit-scrollbar-thumb {{ background: #444; border-radius: 3px; }}
    </style>
</head>
<body>
    <h1>🎬 RewindRec — Watch &amp; Play Before the New Release</h1>
    {sections}
</body>
</html>"""

    with open(output_file, "w") as f:
        f.write(html)

    print(f"✅ HTML saved to {output_file}")
