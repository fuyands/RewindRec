import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"

IGDB_CLIENT_ID = os.getenv("IGDB_CLIENT_ID")
IGDB_CLIENT_SECRET = os.getenv("IGDB_CLIENT_SECRET")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Set to None to use today's date, or override for testing e.g. "2025-08-01"
MOCK_TODAY = "2025-08-01"

if not API_KEY:
    raise ValueError("Please set TMDB_API_KEY in your .env file")
