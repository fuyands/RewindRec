from src.sources.tmdb_movies import get_upcoming_movies, get_movie_details, get_collection_movies, _today
from src.sources.tmdb_tv import get_upcoming_tv, get_past_seasons, get_tv_details
from src.franchise import fetch_candidates, apply_verification
from src.agent import batch_resolve, batch_verify
from src.renderer import render_html


def ask_preferred_genres() -> list:
    """Prompt user for preferred genres, return as lowercase list."""
    print("\n🎬 RewindRec — What genres do you enjoy?")
    print("Enter genres separated by commas (e.g. horror, sci-fi, action)")
    print("Press Enter to skip and show all genres.\n")
    raw = input("Your genres: ").strip()
    if not raw:
        return []
    return [g.strip().lower() for g in raw.split(",") if g.strip()]


def build_base_rec(item, domain):
    """Build a recommendation dict without franchise plan (added later)."""
    if domain == "movie":
        details = get_movie_details(item["id"])
        collection = details.get("belongs_to_collection")
        collection_name = collection["name"] if collection else "Standalone"
        today = _today()
        past = []
        if collection:
            movies = get_collection_movies(collection["id"])
            past = [m for m in movies if m["id"] != item["id"] and m.get("release_date", "") < today]
            past.sort(key=lambda x: x.get("release_date", ""), reverse=True)
        return {
            "id": item["id"],
            "upcoming": item["title"],
            "domain": "movie",
            "release_date": item.get("release_date", ""),
            "collection": collection_name,
            "franchise_name": collection["name"].replace(" Collection", "").strip() if collection else item["title"],
            "overview": item.get("overview", ""),
            "vote_average": item.get("vote_average", 0),
            "vote_count": item.get("vote_count", 0),
            "genres": [g["name"] for g in details.get("genres", [])],
            "budget": details.get("budget", 0),
            "popularity": item.get("popularity", 0),
            "poster_url": f"https://image.tmdb.org/t/p/w500{item['poster_path']}" if item.get("poster_path") else "N/A",
            "backdrop_url": f"https://image.tmdb.org/t/p/w780{item['backdrop_path']}" if item.get("backdrop_path") else None,
            "rewatch": past,
            "franchise_plan": {},
        }
    else:  # tv
        details = get_tv_details(item["id"])
        past = get_past_seasons(item["id"])
        return {
            "id": item["id"],
            "upcoming": item.get("name", ""),
            "domain": "tv",
            "release_date": item.get("first_air_date", ""),
            "collection": "TV Series",
            "franchise_name": item.get("name", ""),
            "overview": item.get("overview", ""),
            "vote_average": item.get("vote_average", 0),
            "vote_count": item.get("vote_count", 0),
            "genres": [g["name"] for g in details.get("genres", [])],
            "budget": 0,
            "popularity": item.get("popularity", 0),
            "poster_url": f"https://image.tmdb.org/t/p/w500{item['poster_path']}" if item.get("poster_path") else "N/A",
            "backdrop_url": f"https://image.tmdb.org/t/p/w780{item['backdrop_path']}" if item.get("backdrop_path") else None,
            "rewatch": [{"id": s["id"], "title": f"Season {s['season_number']}", "release_date": s.get("air_date", ""), "poster_path": s.get("poster_path")} for s in sorted(past, key=lambda x: x.get("air_date", ""), reverse=True)],
            "franchise_plan": {},
        }


def run():
    preferred_genres = ask_preferred_genres()
    recommendations = []

    print("Fetching upcoming movies...")
    for movie in get_upcoming_movies(limit=50):
        recommendations.append(build_base_rec(movie, "movie"))

    print("Fetching upcoming TV shows...")
    for show in get_upcoming_tv(limit=20):
        recommendations.append(build_base_rec(show, "tv"))

    if not recommendations:
        print("No recommendations found.")
        return

    # --- Gemini Call 1: batch resolve franchise + search terms ---
    print(f"[Agent] Resolving franchises for {len(recommendations)} titles...")
    seeds = [{"id": r["id"], "title": r["upcoming"], "domain": r["domain"]} for r in recommendations]
    resolved = batch_resolve(seeds)

    # fetch candidates per rec using resolved search terms
    candidates_map = {}
    for rec in recommendations:
        sid = str(rec["id"])
        resolution = resolved.get(sid, {})
        search_terms = resolution.get("search_terms", {})
        # movies search tv+games, tv shows search movies+games
        if rec["domain"] == "movie":
            search_terms.pop("movies", None)
        else:
            search_terms.pop("tv", None)
        if search_terms:
            candidates_map[sid] = fetch_candidates(search_terms)

    # --- Gemini Call 2: batch verify candidates ---
    verifications = [
        {
            "seed": {"id": r["id"], "title": r["upcoming"], "domain": r["domain"]},
            "candidates": {
                domain: [{"id": item["id"], "title": item["title"]} for item in items]
                for domain, items in candidates_map.get(str(r["id"]), {}).items()
            }
        }
        for r in recommendations
        if candidates_map.get(str(r["id"]))
    ]

    print(f"[Agent] Verifying {len(verifications)} franchise plans...")
    verified_map = batch_verify(verifications)

    # apply verification results back to recs
    for rec in recommendations:
        sid = str(rec["id"])
        raw_candidates = candidates_map.get(sid, {})
        verified = verified_map.get(sid, {})
        rec["franchise_plan"] = {"domains": apply_verification(raw_candidates, verified)}

        # for TV shows with no past seasons, pull verified movies into rewatch
        if rec["domain"] == "tv" and not rec["rewatch"]:
            related_movies = rec["franchise_plan"]["domains"].get("movies", [])
            if related_movies:
                rec["rewatch"] = related_movies
                rec["franchise_plan"]["domains"].pop("movies", None)

    # sort: has rewatch first, then by popularity
    recommendations = sorted(
        recommendations,
        key=lambda r: (0 if r["rewatch"] else 1, -r.get("popularity", 0))
    )

    with_rewatch = [r for r in recommendations if r["rewatch"]]
    print(f"{len(with_rewatch)} out of {len(recommendations)} have rewatch suggestions.")
    render_html(recommendations, preferred_genres=preferred_genres)


if __name__ == "__main__":
    run()
