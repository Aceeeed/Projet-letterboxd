import logging
import feedparser
import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

LETTERBOXD_BASE_RSS = "https://letterboxd.com/{username}/watchlist/rss/"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36 LetterboxdCinemaAlert/1.0"
)


def fetch_letterboxd_watchlist(username: str) -> List[Dict[str, Optional[str]]]:
    """
    Récupère la Watchlist Letterboxd d'un utilisateur via son flux RSS.

    :param username: Pseudo Letterboxd de l'utilisateur.
    :return: Liste de dictionnaires contenant les détails des films (title, year, link).
    """
    if not username or not username.strip():
        raise ValueError("Le nom d'utilisateur Letterboxd ne peut pas être vide.")

    url = LETTERBOXD_BASE_RSS.format(username=username.strip())
    logger.info(f"Récupération du flux RSS Letterboxd pour '{username}' : {url}")

    headers = {"User-Agent": DEFAULT_USER_AGENT}

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Erreur HTTP lors de la récupération de la Watchlist Letterboxd : {e}")
        raise

    feed = feedparser.parse(response.content)

    if feed.bozo:
        logger.warning(f"Avertissement de parsing RSS (bozo exception) : {feed.bozo_exception}")

    movies = []
    for entry in feed.entries:
        # Letterboxd fournit des tags personnalisés 'letterboxd_filmtitle' et 'letterboxd_filmyear'
        title = getattr(entry, "letterboxd_filmtitle", None) or getattr(entry, "film_title", None)
        year = getattr(entry, "letterboxd_filmyear", None) or getattr(entry, "film_year", None)

        # Fallback sur le titre standard RSS si les métadonnées spécifiques sont absentes
        if not title:
            raw_title = entry.get("title", "")
            # raw_title est souvent sous la forme "Film Name, Year" ou "Film Name"
            if ", " in raw_title:
                parts = raw_title.rsplit(", ", 1)
                title = parts[0]
                if not year and parts[1].isdigit():
                    year = parts[1]
            else:
                title = raw_title

        movie_info = {
            "title": title.strip() if title else "Inconnu",
            "year": str(year).strip() if year else None,
            "link": entry.get("link", ""),
        }
        movies.append(movie_info)

    logger.info(f"{len(movies)} films récupérés depuis la Watchlist Letterboxd de '{username}'.")
    return movies


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    test_user = sys.argv[1] if len(sys.argv) > 1 else "davidehrlich"
    try:
        results = fetch_letterboxd_watchlist(test_user)
        for m in results[:5]:
            print(f"- {m['title']} ({m['year']}) : {m['link']}")
    except Exception as err:
        print(f"Erreur : {err}")
