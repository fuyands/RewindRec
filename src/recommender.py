from src.tmdb import get_movie_details, get_collection_movies, _today
from datetime import date


def recommend_from_collection(movie):
    details = get_movie_details(movie["id"])

    collection = details.get("belongs_to_collection")
    collection_name = collection["name"] if collection else "Standalone"
    past_movies = []

    if collection:
        movies = get_collection_movies(collection["id"])
        today = _today()
        past_movies = [m for m in movies if m["id"] != movie["id"] and m.get("release_date", "") < today]
        past_movies.sort(key=lambda x: x.get("release_date", ""))
        if past_movies:
            print(f"✅ {movie['title']} → {len(past_movies)} past films in '{collection['name']}'")
    else:
        print(f"⬜ {movie['title']} → no collection")

    return {
        "id": movie["id"],
        "upcoming": movie["title"],
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
    }
