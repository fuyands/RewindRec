# RewindRec

An open source project that helps you discover and revisit older entries in a franchise before a new release drops — across movies, TV shows, and games.

## What It Does

When a new movie or TV show is about to release, RewindRec:
- Finds past entries in the same collection or series to rewatch first
- Suggests related content across domains (e.g. a new movie → related TV shows and games)
- Groups results by genre and renders a dark-themed HTML page with posters and links

Results are rendered to `output.html` and can be opened in any browser.

## Project Structure

```
RewindRec/
├── main.py                  # Entry point
├── config.py                # API keys and mock date config
├── requirements.txt
└── src/
    ├── sources/
    │   ├── tmdb_movies.py   # Upcoming movies + collection lookup
    │   ├── tmdb_tv.py       # Upcoming TV + past seasons
    │   └── igdb.py          # Games lookup (requires IGDB keys)
    ├── franchise.py         # Cross-domain franchise linker
    ├── recommender.py       # Legacy recommender (superseded by main.py)
    ├── renderer.py          # HTML generation
    └── utils.py
```

## Getting Started

### Prerequisites

- Python 3.8+
- TMDB API key (free) — [themoviedb.org/settings/api](https://www.themoviedb.org/settings/api)
- IGDB credentials (free, optional for game suggestions) — [api.igdb.com](https://api.igdb.com)
  - Register a Twitch app at [dev.twitch.tv/console](https://dev.twitch.tv/console)
  - Enable IGDB access and grab your Client ID + Client Secret

### Installation

```bash
git clone https://github.com/your-username/RewindRec.git
cd RewindRec
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```
TMDB_API_KEY=your_tmdb_api_key

# Optional — enables game suggestions
IGDB_CLIENT_ID=your_twitch_client_id
IGDB_CLIENT_SECRET=your_twitch_client_secret
```

To simulate a past date for testing, set `MOCK_TODAY` in `config.py`:

```python
MOCK_TODAY = "2025-08-01"  # uses /discover/movie with that date range
MOCK_TODAY = None           # live mode, uses /movie/upcoming
```

Adjust the lookahead window in `src/sources/tmdb_movies.py`:

```python
UPCOMING_MONTHS_AHEAD = 3  # how many months ahead to look
```

### Run

```bash
python3 main.py
open output.html
```

## Cross-Domain Recommendation Logic

For each upcoming movie or TV show, RewindRec builds a franchise plan:

- Movies → searches for related TV shows and games using the franchise/collection name
- TV shows → surfaces past seasons of the same series + related movies and games
- Name matching uses substring overlap to find related entries across domains
- Game suggestions require IGDB credentials (see setup above)
- If no IGDB keys are set, game suggestions are silently skipped

Note: region filtering is intentionally removed so international releases (e.g. Japanese anime films) are included.

## Roadmap

- [ ] LLM-powered franchise resolver (Gemini) for smarter cross-domain matching
- [ ] Upcoming games as a first-class feed via IGDB
- [ ] Book suggestions via OpenLibrary
- [ ] Personalized watchlist filtering

## Contributing

Pull requests are welcome. Open an issue first for major changes.

1. Fork the repo
2. Create your branch (`git checkout -b feature/my-feature`)
3. Commit (`git commit -m 'Add my feature'`)
4. Push (`git push origin feature/my-feature`)
5. Open a pull request

## License

[MIT](LICENSE)
