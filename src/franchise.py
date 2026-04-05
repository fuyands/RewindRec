"""
Franchise graph builder — uses Gemini agent for intelligent cross-domain matching.

Flow:
  1. batch_resolve: Gemini identifies franchise + search terms for all seeds
  2. Fetch candidates from TMDB + IGDB using those search terms
  3. batch_verify: Gemini filters unrelated candidates and adds reasons
"""
from src.sources import tmdb_movies, tmdb_tv, igdb


def fetch_candidates(search_terms: dict) -> dict:
    """Fetch raw candidates from each domain using Gemini-provided search terms."""
    candidates = {}

    for term in search_terms.get("movies", []):
        results = tmdb_movies.search_movies(term)
        candidates.setdefault("movies", []).extend(_format_movies(results))

    for term in search_terms.get("tv", []):
        results = tmdb_tv.search_tv(term)
        candidates.setdefault("tv", []).extend(_format_tv(results))

    for term in search_terms.get("games", []):
        results = igdb.search_games(term)
        candidates.setdefault("games", []).extend(_format_games(results))

    # deduplicate by id per domain
    for domain in candidates:
        seen = set()
        deduped = []
        for item in candidates[domain]:
            if item["id"] not in seen:
                seen.add(item["id"])
                deduped.append(item)
        candidates[domain] = deduped

    return candidates


def apply_verification(candidates: dict, verified: dict) -> dict:
    """Filter candidates using Gemini verification results. Attaches reason to each kept item."""
    result = {}
    for domain, items in candidates.items():
        verified_items = verified.get(domain, [])
        # Gemini sometimes returns int ids, ensure string comparison works
        verified_ids = {str(v["id"]): v.get("reason", "") for v in verified_items}
        kept = []
        for item in items:
            if str(item["id"]) in verified_ids:
                item["reason"] = verified_ids[str(item["id"])]
                kept.append(item)
        if kept:
            result[domain] = kept
    if not result:
        print(f"  [verify] all candidates filtered out. verified keys: {list(verified.keys())}, candidate keys: {list(candidates.keys())}")
    return result


def _format_movies(results: list) -> list:
    items = [
        {
            "id": m["id"],
            "title": m.get("title", ""),
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
    return sorted(items, key=lambda x: x["release_date"], reverse=True)[:8]


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
