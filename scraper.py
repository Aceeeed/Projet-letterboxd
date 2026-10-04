import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36 LetterboxdCinemaAlert/1.0"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
}


def scrape_cinema_example(
    url: Optional[str] = None, cinema_name: str = "Cinéma Indépendant Exemple"
) -> List[Dict[str, Any]]:
    """
    Exemple générique de scraper pour cinéma indépendant.
    À adapter avec l'URL cible et les sélecteurs CSS réels du cinéma souhaité.

    :param url: URL de la programmation du cinéma.
    :param cinema_name: Nom du cinéma (pour affichage dans l'e-mail).
    :return: Liste de dictionnaires contenant les détails des séances / films à l'affiche.
    """
    if not url:
        logger.info(
            f"Aucune URL fournie pour '{cinema_name}'. Utilisation d'un jeu de données d'exemple."
        )
        return [
            {
                "title": "2001: A Space Odyssey",
                "cinema": cinema_name,
                "schedule": "Mercredi 20h30, Samedi 18h00",
                "link": "https://example.com/2001-space-odyssey",
            },
            {
                "title": "Mulholland Drive",
                "cinema": cinema_name,
                "schedule": "Jeudi 21h00, Dimanche 16h30",
                "link": "https://example.com/mulholland-drive",
            },
            {
                "title": "Portrait de la jeune fille en feu",
                "cinema": cinema_name,
                "schedule": "Vendredi 19h00",
                "link": "https://example.com/portrait-de-la-jeune-fille",
            },
        ]

    logger.info(f"Scraping de la programmation cinéma sur {url} ({cinema_name})...")
    movies = []

    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Erreur lors de la requête vers le site du cinéma ({url}) : {e}")
        return movies

    soup = BeautifulSoup(response.text, "html.parser")

    # =========================================================================
    # TODO: Adapter les sélecteurs CSS ci-dessous selon la structure HTML cible
    # Exemple hypothétique :
    # <div class="film-card">
    #     <h3 class="film-title"><a href="/film/123">Titre du Film</a></h3>
    #     <div class="screenings">Mercredi 20h00, Samedi 18h00</div>
    # </div>
    # =========================================================================
    film_cards = soup.select(".film-card, .movie-item, article.film")

    if not film_cards:
        logger.warning(
            f"Aucun élément trouvé avec les sélecteurs par défaut sur {url}. "
            "Pensez à inspecter la page et mettre à jour les sélecteurs CSS."
        )

    for card in film_cards:
        title_element = card.select_one(".film-title, h2, h3, .title")
        if not title_element:
            continue

        title = title_element.get_text(strip=True)

        # Lien vers la fiche du film (si disponible)
        link_element = title_element.find("a") or card.find("a")
        film_link = link_element.get("href") if link_element else url
        if film_link and not film_link.startswith("http"):
            from urllib.parse import urljoin
            film_link = urljoin(url, film_link)

        # Horaires / Séances (si disponibles)
        schedule_element = card.select_one(".screenings, .seances, .horaires, .schedule")
        schedule = schedule_element.get_text(strip=True) if schedule_element else "Consulter le site"

        movies.append(
            {
                "title": title,
                "cinema": cinema_name,
                "schedule": schedule,
                "link": film_link,
            }
        )

    logger.info(f"{len(movies)} films récupérés pour '{cinema_name}'.")
    return movies


def scrape_all_cinemas(cinemas_config: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, Any]]:
    """
    Permet de scraper plusieurs cinémas configurés.

    :param cinemas_config: Liste de dicts [{"name": "Nom", "url": "https://..."}]
    :return: Liste agrégée de tous les films trouvés en salle.
    """
    if not cinemas_config:
        # Configuration par défaut / démonstration
        return scrape_cinema_example(url=None, cinema_name="Cinéma du Quartier")

    all_movies = []
    for cinema in cinemas_config:
        name = cinema.get("name", "Cinéma")
        url = cinema.get("url")
        cinema_movies = scrape_cinema_example(url=url, cinema_name=name)
        all_movies.extend(cinema_movies)

    return all_movies


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = scrape_cinema_example()
    for item in results:
        print(f"- {item['title']} @ {item['cinema']} [{item['schedule']}] ({item['link']})")
