"""
Gemini-powered agentic layer for RewindRec.

Call 1 — batch_resolve: given N seed titles, return franchise metadata + search terms per domain
Call 2 — batch_verify: given N seeds + their candidates, verify relevance, filter unrelated, add reasons
"""
import json
import time
import os
import hashlib
import google.generativeai as genai
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
_model = genai.GenerativeModel("gemini-2.5-flash")

BATCH_SIZE = 20  # paid tier supports much higher token limits
CACHE_FILE = ".gemini_cache.json"


def _load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {}


def _save_cache(cache: dict):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)


def _cache_key(prompt: str) -> str:
    return hashlib.md5(prompt.encode()).hexdigest()


def _call(prompt: str, retries=3) -> dict:
    """Call Gemini with caching and retry on 429."""
    cache = _load_cache()
    key = _cache_key(prompt)
    if key in cache:
        print("[Gemini] cache hit")
        return cache[key]

    for attempt in range(retries):
        try:
            response = _model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            result = json.loads(response.text)
            cache[key] = result
            _save_cache(cache)
            return result
        except Exception as e:
            msg = str(e)
            if "429" in msg and attempt < retries - 1:
                wait = 20 * (attempt + 1)
                print(f"[Gemini] rate limited, retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(f"[Gemini] error: {e}")
                return {}
    return {}


def batch_resolve(seeds: list) -> dict:
    """
    Call 1: resolve franchise + search terms for all seeds, chunked by BATCH_SIZE.
    Returns: {"<id>": {"franchise": "...", "search_terms": {...}, "reason": "..."}}
    """
    if not seeds:
        return {}

    all_results = {}
    total_batches = -(-len(seeds) // BATCH_SIZE)

    for i in range(0, len(seeds), BATCH_SIZE):
        chunk = seeds[i:i + BATCH_SIZE]
        print(f"[Agent] resolving batch {i//BATCH_SIZE + 1}/{total_batches} ({len(chunk)} titles)...")
        prompt = f"""You are a franchise expert. For each upcoming title below, identify:
1. The franchise/universe it belongs to
2. Search terms to find related content per domain (movies, tv, games)
3. A short 1-sentence reason explaining what this title is

Return JSON where each key is the title id (as string):
{{
  "<id>": {{
    "franchise": "<name>",
    "search_terms": {{
      "movies": ["<term>"],
      "tv": ["<term>"],
      "games": ["<term>"]
    }},
    "reason": "<1 sentence>"
  }}
}}

Titles:
{json.dumps(chunk, indent=2)}
"""
        result = _call(prompt)
        all_results.update(result)
        if i + BATCH_SIZE < len(seeds):
            time.sleep(5)

    return all_results


def batch_verify(verifications: list) -> dict:
    """
    Call 2: verify candidates against seeds, filter unrelated, add reasons.
    Uses stricter filtering for movies/TV and more lenient for games.
    Returns: {"<seed_id>": {"movies": [{"id": x, "reason": "..."}], "tv": [...], "games": [...]}}
    """
    if not verifications:
        return {}

    all_results = {}
    total_batches = -(-len(verifications) // BATCH_SIZE)

    for i in range(0, len(verifications), BATCH_SIZE):
        chunk = verifications[i:i + BATCH_SIZE]
        print(f"[Agent] verifying batch {i//BATCH_SIZE + 1}/{total_batches} ({len(chunk)} items)...")
        prompt = f"""You are a franchise expert verifying cross-domain recommendations.

For movies and TV candidates: keep ONLY direct adaptations, prequels, sequels, or spinoffs of the exact same named franchise. Be strict.

For games candidates: keep any game that shares the same IP, source material, or franchise name — even if it's a loose adaptation. Be lenient here since game titles often differ from movie/TV titles.

Do NOT keep thematically similar content (e.g. "Football Manager" is NOT related to a footballer documentary).

For each kept candidate, provide a short reason (max 10 words).

Return JSON where each key is the seed id (as string):
{{
  "<seed_id>": {{
    "movies": [{{"id": <id>, "reason": "<why relevant>"}}],
    "tv": [{{"id": <id>, "reason": "<why relevant>"}}],
    "games": [{{"id": <id>, "reason": "<why relevant>"}}]
  }}
}}

Omit domains with no relevant candidates entirely.

Data:
{json.dumps(chunk, indent=2)}
"""
        result = _call(prompt)
        all_results.update(result)
        if i + BATCH_SIZE < len(verifications):
            time.sleep(5)

    return all_results
