"""
Franchise graph builder — given a title, fans out across all sources
to build a unified cross-domain catch-up plan.
"""
from src.sources import tmdb_movies, tmdb_tv, igdb


def _name_matches(name: str, title: str) -> bool:
    """Check if name and title share meaningful overlap."""
    n, t = name.lower().strip(), title.lower().strip()
    return n == t or t in n or n in t


def build_franchise_plan(title: str, domains: list = None) -> dict:
    if domains is None:
        domains = ["movies", "tv", "games"]

    plan = {"franchise": title, "domains": {}}

    if "movies" in domains:
        results = tmdb_movies.search_movies(title)
        matched = [m for m in results if _name_matches(m.get("title", ""), title)]
        plan["domains"]["movies"] = _format_movies(matched)

    if "tv" in domains:
        results = tmdb_tv.search_tv(title)
        matched = [r for r in results if _name_matches(r.get("name", ""), title)]
        if matched:
            plan["domains"]["tv"] = _format_tv(matched)

    if "games" in domains:
        results = igdb.search_games(title)
        matched = [g for g in results if _name_matches(g.get("name", ""), title)]
        plan["domains"]["games"] = _format_games(matched)

    return plan


def _format_movies(results: list) -> list:
    items = [
        {
            "id": m["id"],
            "title": m["title"],
            "release_date": m.get("release_date", ""),
            "poster_url": f"https://image.tmdb.org/t/p/w200{m['poster_path']}" if m.get("poster_path") else None,
            "url": f"https://www.themoviedb.org/movie/{m['id']}",
            "domain": "movie"
        }
        for m in results
    ]
    return sorted(items, key=lambda x: x["release_date"], reverse=True)[:8]


def _format_tv(results: list) -> list:
    items = [
        {
            "id": r["id"],
            "title": r.get("name", ""),
            "release_date": r.get("first_air_date", ""),
            "poster_url": f"https://image.tmdb.org/t/p/w200{r['poster_path']}" if r.get("poster_path") else None,
            "url": f"https://www.themoviedb.org/tv/{r['id']}",
            "domain": "tv"
        }
        for r in results
    ]
    return sorted(items, key=lambda x: x["release_date"], reverse=True)[:5]


def _format_games(results: list) -> list:
    items = []
    for g in results:
        raw_url = g.get("cover", {}).get("url", "")
        if raw_url.startswith("//"):
            raw_url = "https:" + raw_url
        poster_url = raw_url.replace("t_thumb", "t_cover_big") if raw_url else None
        slug = g.get("slug") or str(g["id"])
        items.append({
            "id": g["id"],
            "title": g.get("name", ""),
            "release_date": "",
            "poster_url": poster_url,
            "url": f"https://www.igdb.com/games/{slug}",
            "domain": "game"
        })
    return items[:8]
