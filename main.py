from src.sources.tmdb_movies import get_upcoming_movies, get_movie_details, get_collection_movies
from src.sources.tmdb_tv import get_upcoming_tv, get_past_seasons
from src.franchise import build_franchise_plan
from src.renderer import render_html
from src.sources.tmdb_movies import _today


def build_movie_rec(movie):
    details = get_movie_details(movie["id"])
    collection = details.get("belongs_to_collection")
    collection_name = collection["name"] if collection else "Standalone"
    past_movies = []

    if collection:
        today = _today()
        movies = get_collection_movies(collection["id"])
        past_movies = [m for m in movies if m["id"] != movie["id"] and m.get("release_date", "") < today]
        past_movies.sort(key=lambda x: x.get("release_date", ""), reverse=True)

    # cross-domain franchise plan
    franchise_name = collection["name"].replace(" Collection", "").strip() if collection else movie["title"]
    franchise_plan = build_franchise_plan(franchise_name, domains=["tv", "games"])

    return {
        "id": movie["id"],
        "upcoming": movie["title"],
        "domain": "movie",
        "release_date": movie["release_date"],
        "collection": collection_name,
        "overview": movie.get("overview", ""),
        "vote_average": movie.get("vote_average", 0),
        "vote_count": movie.get("vote_count", 0),
        "genres": [g["name"] for g in details.get("genres", [])],
        "budget": details.get("budget", 0),
        "popularity": movie.get("popularity", 0),
        "poster_url": f"https://image.tmdb.org/t/p/w500{movie['poster_path']}" if movie.get("poster_path") else "N/A",
        "backdrop_url": f"https://image.tmdb.org/t/p/w780{movie['backdrop_path']}" if movie.get("backdrop_path") else None,
        "rewatch": past_movies,
        "franchise_plan": franchise_plan,
    }


def build_tv_rec(show):
    from src.sources.tmdb_tv import get_tv_details
    past = get_past_seasons(show["id"])
    details = get_tv_details(show["id"])
    franchise_plan = build_franchise_plan(show.get("name", ""), domains=["movies", "games"])
    return {
        "id": show["id"],
        "upcoming": show.get("name", ""),
        "domain": "tv",
        "release_date": show.get("first_air_date", ""),
        "collection": "TV Series",
        "overview": show.get("overview", ""),
        "vote_average": show.get("vote_average", 0),
        "vote_count": show.get("vote_count", 0),
        "genres": [g["name"] for g in details.get("genres", [])],
        "budget": 0,
        "popularity": show.get("popularity", 0),
        "poster_url": f"https://image.tmdb.org/t/p/w500{show['poster_path']}" if show.get("poster_path") else "N/A",
        "backdrop_url": f"https://image.tmdb.org/t/p/w780{show['backdrop_path']}" if show.get("backdrop_path") else None,
        "rewatch": [{"id": s["id"], "title": f"Season {s['season_number']}", "release_date": s.get("air_date", ""), "poster_path": s.get("poster_path")} for s in sorted(past, key=lambda x: x.get("air_date", ""), reverse=True)],
        "franchise_plan": franchise_plan,
    }


def run():
    recommendations = []

    # movies
    for movie in get_upcoming_movies(limit=100):
        recommendations.append(build_movie_rec(movie))

    # TV shows
    for show in get_upcoming_tv(limit=50):
        recommendations.append(build_tv_rec(show))

    if not recommendations:
        print("No recommendations found.")
        return

    recommendations = sorted(
        recommendations,
        key=lambda r: (0 if r["rewatch"] else 1, -r.get("popularity", 0))
    )

    with_rewatch = [r for r in recommendations if r["rewatch"]]
    print(f"{len(with_rewatch)} out of {len(recommendations)} have rewatch/rewatch suggestions.")
    render_html(recommendations)


if __name__ == "__main__":
    run()
