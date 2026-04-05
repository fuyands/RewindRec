from collections import defaultdict

TITLES_PER_ROW = 5


def render_card(rec):
    rewatch_html = ""
    if rec["rewatch"]:
        thumbs = "".join(
            f"""<a href="https://www.themoviedb.org/movie/{m['id']}" target="_blank" style="text-decoration:none;display:inline-block;margin:2px;">
                {'<img src="https://image.tmdb.org/t/p/w92' + m['poster_path'] + '" style="width:40px;border-radius:4px;" title="' + m['title'] + ' (' + m.get('release_date','')[:4] + ')">' if m.get('poster_path') else '<span style="font-size:10px;color:#aaa;background:#333;padding:2px 4px;border-radius:4px;">' + m['title'][:15] + '</span>'}
            </a>"""
            for m in rec["rewatch"]
        )
        rewatch_html = f"""
        <div style="margin-top:6px;">
            <div style="font-size:11px;color:#aaa;">🔁 Rewatch first:</div>
            <div style="display:flex;flex-wrap:wrap;gap:2px;margin-top:4px;">{thumbs}</div>
        </div>"""

    img_url = rec.get("backdrop_url") or rec["poster_url"]
    tmdb_url = f"https://www.themoviedb.org/movie/{rec['id']}"

    return f"""
    <div style="width:260px;flex-shrink:0;background:#1a1a1a;border-radius:10px;overflow:hidden;box-sizing:border-box;">
        <a href="{tmdb_url}" target="_blank">
            <img src="{img_url}" style="width:100%;height:140px;object-fit:cover;display:block;">
        </a>
        <div style="padding:10px;">
            <a href="{tmdb_url}" target="_blank" style="color:#fff;text-decoration:none;">
                <div style="font-size:13px;font-weight:bold;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{rec['upcoming']}</div>
            </a>
            <div style="font-size:11px;color:#aaa;">📅 {rec['release_date']}</div>
            <div style="font-size:11px;color:#f5c518;">⭐ {rec['vote_average']}</div>
            <div style="font-size:11px;color:#888;margin-top:4px;">{rec['overview'][:80]}...</div>
            {rewatch_html}
        </div>
    </div>"""


def render_html(recommendations: list, output_file="output.html"):
    groups = defaultdict(list)
    for rec in recommendations:
        genre = rec["genres"][0] if rec.get("genres") else "Other"
        groups[genre].append(rec)

    sorted_groups = sorted(groups.items(), key=lambda x: -len(x[1]))

    sections = ""
    for genre, recs in sorted_groups:
        # chunk into rows of TITLES_PER_ROW
        rows_html = ""
        for i in range(0, len(recs), TITLES_PER_ROW):
            chunk = recs[i:i + TITLES_PER_ROW]
            cards = "".join(render_card(r) for r in chunk)
            rows_html += f"""
            <div style="display:flex;gap:12px;margin-bottom:12px;overflow-x:auto;padding-bottom:4px;">
                {cards}
            </div>"""

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
    <h1>🎬 RewindRec — Watch Before the New Release</h1>
    {sections}
</body>
</html>"""

    with open(output_file, "w") as f:
        f.write(html)

    print(f"✅ HTML saved to {output_file}")
