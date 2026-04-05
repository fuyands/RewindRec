from collections import defaultdict
from difflib import SequenceMatcher

TITLES_PER_ROW = 5
DOMAIN_ICONS = {"movie": "🎬", "tv": "📺", "game": "🎮", "games": "🎮", "book": "📚"}
DOMAIN_LABELS = {"movies": "movies", "tv": "TV shows", "games": "games"}


def _genre_score(group_key: str, preferred: list) -> float:
    """Return highest fuzzy match score between group key and any preferred genre."""
    if not preferred:
        return 0.0
    key_lower = group_key.lower()
    return max(
        SequenceMatcher(None, pref, key_lower).ratio()
        for pref in preferred
    )


def render_thumb(item, domain="movie"):
    url = item.get("url", "#")
    poster = item.get("poster_url") or item.get("poster_path")
    if poster and poster.startswith("/"):
        poster = f"https://image.tmdb.org/t/p/w92{poster}"
    title = item.get("title", "").replace('"', "&quot;")

    if poster:
        inner = f'<img src="{poster}" style="width:40px;border-radius:4px;" title="{title}">'
    else:
        icon = DOMAIN_ICONS.get(domain, "")
        inner = f'<span style="font-size:10px;color:#aaa;background:#333;padding:2px 4px;border-radius:4px;">{icon} {title[:12]}</span>'

    return f'<a href="{url}" target="_blank" style="text-decoration:none;display:inline-block;margin:2px;">{inner}</a>'


def render_card(rec):
    domain = rec.get("domain", "movie")
    tmdb_type = "tv" if domain == "tv" else "movie"
    tmdb_url = f"https://www.themoviedb.org/{tmdb_type}/{rec['id']}"
    img_url = rec.get("backdrop_url") or rec["poster_url"]

    rewatch_html = ""
    if rec["rewatch"]:
        thumbs = "".join(render_thumb(m, domain) for m in rec["rewatch"])
        label = "📺 Past seasons:" if domain == "tv" and all("Season" in m.get("title","") for m in rec["rewatch"]) else "🔁 Watch first:"
        rewatch_html = f"""
        <div style="margin-top:6px;">
            <div style="font-size:11px;color:#aaa;">{label}</div>
            <div style="display:flex;flex-wrap:wrap;gap:2px;margin-top:4px;">{thumbs}</div>
        </div>"""

    franchise_html = ""
    plan = rec.get("franchise_plan", {})
    for fdomain, items in plan.get("domains", {}).items():
        if not items:
            continue
        icon = DOMAIN_ICONS.get(fdomain, "")
        label = DOMAIN_LABELS.get(fdomain, fdomain)
        thumbs = "".join(render_thumb(item, fdomain) for item in items[:5])
        franchise_html += f"""
        <div style="margin-top:6px;">
            <div style="font-size:11px;color:#aaa;">{icon} Also in this universe ({label}):</div>
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


def render_html(recommendations: list, output_file="output.html", preferred_genres: list = None):
    groups = defaultdict(list)
    for rec in recommendations:
        genre = rec["genres"][0] if rec.get("genres") else "Other"
        domain = rec.get("domain", "movie")
        key = f"{DOMAIN_ICONS.get(domain, '')} {domain.capitalize()} — {genre}"
        groups[key].append(rec)

    preferred_genres = preferred_genres or []
    sorted_groups = sorted(
        groups.items(),
        key=lambda x: (-_genre_score(x[0], preferred_genres), -len(x[1]))
    )

    sections = ""
    for genre, recs in sorted_groups:
        # within each group: has suggestions first, then by popularity
        recs = sorted(recs, key=lambda r: (
            0 if (r.get("rewatch") or r.get("franchise_plan", {}).get("domains")) else 1,
            -r.get("popularity", 0)
        ))
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
