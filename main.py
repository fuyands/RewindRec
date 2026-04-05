from src.tmdb import get_upcoming_movies
from src.recommender import recommend_from_collection
from src.renderer import render_html


def run():
    upcoming_movies = get_upcoming_movies(limit=300)
    recommendations = []

    for movie in upcoming_movies:
        rec = recommend_from_collection(movie)
        if rec:
            recommendations.append(rec)

    if not recommendations:
        print("No recommendations found.")
        return

    # has rewatch suggestions first, then by budget descending
    recommendations = sorted(
        recommendations,
        key=lambda r: (0 if r["rewatch"] else 1, -r.get("budget", 0))
    )

    with_rewatch = [r for r in recommendations if r["rewatch"]]
    print(f"{len(with_rewatch)} out of {len(recommendations)} movies have rewatch suggestions.")
    render_html(recommendations[:300])


if __name__ == "__main__":
    run()
