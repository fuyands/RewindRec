import requests
from datetime import date, timedelta
from config import API_KEY, BASE_URL, MOCK_TODAY

UPCOMING_MONTHS_AHEAD = 3


def _today():
    return MOCK_TODAY if MOCK_TODAY else date.today().isoformat()


def get_upcoming_movies(limit=20):
    today_str = _today()
    cutoff = (date.fromisoformat(today_str) + timedelta(days=30 * UPCOMING_MONTHS_AHEAD)).isoformat()
    is_mock_past = MOCK_TODAY and MOCK_TODAY < date.today().isoformat()
    results = []
    page = 1

    if is_mock_past:
        url = f"{BASE_URL}/discover/movie"
        while len(results) < limit:
            params = {
                "api_key": API_KEY, "language": "en-US",
                "sort_by": "popularity.desc",
                "primary_release_date.gte": today_str,
                "primary_release_date.lte": cutoff,
                "page": page
            }
            res = requests.get(url, params=params).json()
            results.extend(res.get("results", []))
            if page >= res.get("total_pages", 1):
                break
            page += 1
    else:
        url = f"{BASE_URL}/movie/upcoming"
        while len(results) < limit:
            params = {"api_key": API_KEY, "language": "en-US", "page": page}
            res = requests.get(url, params=params).json()
            batch = res.get("results", [])
            filtered = [m for m in batch if today_str <= m.get("release_date", "") <= cutoff]
            results.extend(filtered)
            if page >= res.get("total_pages", 1):
                break
            page += 1

    print(f"{'[MOCK]' if is_mock_past else '[LIVE]'} movies: {today_str} → {cutoff} ({len(results)} found)")
    return results[:limit]


def get_movie_details(movie_id):
    url = f"{BASE_URL}/movie/{movie_id}"
    return requests.get(url, params={"api_key": API_KEY}).json()


def get_collection_movies(collection_id):
    url = f"{BASE_URL}/collection/{collection_id}"
    res = requests.get(url, params={"api_key": API_KEY}).json()
    return res.get("parts", [])


def search_movies(query: str):
    url = f"{BASE_URL}/search/movie"
    res = requests.get(url, params={"api_key": API_KEY, "query": query}).json()
    return res.get("results", [])
