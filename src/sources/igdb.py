"""
IGDB source — stub ready for your API key.
IGDB uses Twitch OAuth. Set IGDB_CLIENT_ID and IGDB_CLIENT_SECRET in .env
"""
import requests
from config import IGDB_CLIENT_ID, IGDB_CLIENT_SECRET

_access_token = None


def _get_token():
    global _access_token
    if _access_token:
        return _access_token
    res = requests.post(
        "https://id.twitch.tv/oauth2/token",
        params={
            "client_id": IGDB_CLIENT_ID,
            "client_secret": IGDB_CLIENT_SECRET,
            "grant_type": "client_credentials"
        }
    ).json()
    _access_token = res.get("access_token")
    return _access_token


def _headers():
    return {
        "Client-ID": IGDB_CLIENT_ID,
        "Authorization": f"Bearer {_get_token()}"
    }


def search_games(query: str) -> list:
    if not IGDB_CLIENT_ID or not IGDB_CLIENT_SECRET:
        return []
    res = requests.post(
        "https://api.igdb.com/v4/games",
        headers=_headers(),
        data=f'search "{query}"; fields id,name,slug,first_release_date,cover.url,summary,franchises.name; limit 5;'
    )
    return res.json() if res.ok else []


def get_franchise_games(franchise_name: str) -> list:
    if not IGDB_CLIENT_ID or not IGDB_CLIENT_SECRET:
        return []
    res = requests.post(
        "https://api.igdb.com/v4/games",
        headers=_headers(),
        data=f'search "{franchise_name}"; fields id,name,first_release_date,cover.url,summary; limit 10;'
    )
    return res.json() if res.ok else []
