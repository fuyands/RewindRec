import requests
from datetime import date, timedelta
from config import API_KEY, BASE_URL, MOCK_TODAY

UPCOMING_MONTHS_AHEAD = 3


def _today():
    return MOCK_TODAY if MOCK_TODAY else date.today().isoformat()


def get_upcoming_tv(limit=20):
    today_str = _today()
    cutoff = (date.fromisoformat(today_str) + timedelta(days=30 * UPCOMING_MONTHS_AHEAD)).isoformat()
    is_mock_past = MOCK_TODAY and MOCK_TODAY < date.today().isoformat()
    results = []
    page = 1

    url = f"{BASE_URL}/discover/tv"
    while len(results) < limit:
        params = {
            "api_key": API_KEY, "language": "en-US",
            "sort_by": "popularity.desc",
            "first_air_date.gte": today_str,
            "first_air_date.lte": cutoff,
            "page": page
        }
        res = requests.get(url, params=params).json()
        results.extend(res.get("results", []))
        if page >= res.get("total_pages", 1):
            break
        page += 1

    print(f"{'[MOCK]' if is_mock_past else '[LIVE]'} TV: {today_str} → {cutoff} ({len(results)} found)")
    return results[:limit]


def get_tv_details(tv_id):
    url = f"{BASE_URL}/tv/{tv_id}"
    return requests.get(url, params={"api_key": API_KEY}).json()


def get_past_seasons(tv_id):
    """Return all seasons that have already aired."""
    details = get_tv_details(tv_id)
    today = _today()
    seasons = [
        s for s in details.get("seasons", [])
        if s.get("air_date") and s["air_date"] < today and s["season_number"] > 0
    ]
    return sorted(seasons, key=lambda s: s.get("air_date", ""))


def search_tv(query: str):
    url = f"{BASE_URL}/search/tv"
    res = requests.get(url, params={"api_key": API_KEY, "query": query}).json()
    return res.get("results", [])
