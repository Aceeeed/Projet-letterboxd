import os
import re
import sys
import logging
import unicodedata
from typing import List, Dict, Any, Tuple

# Chargement facultatif des variables d'environnement depuis un fichier .env (développement local)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from letterboxd import fetch_letterboxd_watchlist
from scraper import scrape_all_cinemas, scrape_cinema_example
from notifier import send_email_alert

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("CinemaAlertMain")


def normalize_title(text: str) -> str:
    """
    Normalise un titre de film pour une comparaison robuste :
    - Minuscule
    - Suppression des accents / diacritiques (NFKD)
    - Suppression de la ponctuation et caractères spéciaux
    - Réduction des espaces multiples

    Exemple : "2001: A Space Odyssey" -> "2001 a space odyssey"
              "L'Armée des 12 singes !" -> "l armee des 12 singes"
    """
    if not text:
        return ""

    # Minuscule
    text = text.lower()

    # Décomposition unicode et suppression des accents
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))

    # Remplacement des apostrophes et tirets par des espaces
    text = re.sub(r"['’\-–—]", " ", text)

    # Suppression de toute la ponctuation restante
    text = re.sub(r"[^\w\s]", "", text)

    # Nettoyage des espaces
    text = re.sub(r"\s+", " ", text).strip()

    return text


def compare_titles(watchlist_title: str, cinema_title: str) -> bool:
    """
    Vérifie si deux titres correspondent en utilisant la normalisation.
    Prend en compte l'égalité stricte normalisée ou l'inclusion mutuelle
    si les titres ont une longueur suffisante.
    """
    norm_w = normalize_title(watchlist_title)
    norm_c = normalize_title(cinema_title)

    if not norm_w or not norm_c:
        return False

    # Correspondance exacte après normalisation
    if norm_w == norm_c:
        return True

    # Tolérance pour les sous-titres ou préfixes (ex: "Dune" vs "Dune: Deuxième Partie")
    # appliquée seulement si la chaîne la plus courte est assez longue (> 4 caractères)
    if len(norm_w) >= 5 and len(norm_c) >= 5:
        if norm_w in norm_c or norm_c in norm_w:
            return True

    return False


def find_matching_movies(
    watchlist: List[Dict[str, Any]], cinema_movies: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Compare les films de la Watchlist et les films à l'affiche.

    :return: Liste des correspondances enrichies.
    """
    matches = []
    seen_combinations = set()

    for watch_item in watchlist:
        watch_title = watch_item.get("title", "")

        for cinema_item in cinema_movies:
            cinema_title = cinema_item.get("title", "")

            if compare_titles(watch_title, cinema_title):
                combo_key = (watch_title.lower(), cinema_item.get("cinema", ""), cinema_item.get("schedule", ""))
                if combo_key in seen_combinations:
                    continue
                seen_combinations.add(combo_key)

                match_entry = {
                    "watchlist_title": watch_title,
                    "watchlist_year": watch_item.get("year"),
                    "letterboxd_link": watch_item.get("link"),
                    "cinema_title": cinema_title,
                    "cinema": cinema_item.get("cinema", "Cinéma"),
                    "schedule": cinema_item.get("schedule", "Voir programmation"),
                    "cinema_link": cinema_item.get("link", ""),
                }
                matches.append(match_entry)
                logger.info(f"✨ Match trouvé : '{watch_title}' @ {match_entry['cinema']}")

    return matches


def main() -> int:
    logger.info("=== Démarrage du système d'alerte Cinéma / Letterboxd ===")

    # Récupération des variables d'environnement
    letterboxd_user = os.getenv("LETTERBOXD_USERNAME")
    sender_email = os.getenv("GMAIL_SENDER")
    sender_password = os.getenv("GMAIL_APP_PASSWORD")
    recipient_email = os.getenv("RECIPIENT_EMAIL") or sender_email
    cinema_url = os.getenv("CINEMA_URL")

    if not letterboxd_user:
        logger.error("Variable LETTERBOXD_USERNAME non configurée. Arrêt.")
        return 1

    # 1. Récupération de la Watchlist Letterboxd
    try:
        watchlist = fetch_letterboxd_watchlist(letterboxd_user)
    except Exception as e:
        logger.error(f"Impossible de récupérer la Watchlist Letterboxd : {e}")
        return 1

    if not watchlist:
        logger.warning(f"La Watchlist de '{letterboxd_user}' est vide ou inaccessible.")
        return 0

    # 2. Récupération de la programmation des cinémas
    try:
        if cinema_url:
            cinema_movies = scrape_cinema_example(url=cinema_url, cinema_name="Cinéma Cible")
        else:
            cinema_movies = scrape_all_cinemas()
    except Exception as e:
        logger.error(f"Erreur lors du scraping des cinémas : {e}")
        return 1

    if not cinema_movies:
        logger.warning("Aucun film récupéré depuis les cinémas.")
        return 0

    # 3. Comparaison et recherche de correspondances
    matches = find_matching_movies(watchlist, cinema_movies)
    logger.info(f"Total de correspondances trouvées : {len(matches)}")

    # 4. Envoi de l'e-mail d'alerte si des films ont été trouvés
    if matches:
        if not sender_email or not sender_password:
            logger.warning(
                "GMAIL_SENDER ou GMAIL_APP_PASSWORD manquant. "
                "Affichage des correspondances dans la console sans envoi d'email."
            )
            for m in matches:
                print(f" -> {m['watchlist_title']} ({m['cinema']}) - {m['schedule']}")
            return 0

        success = send_email_alert(
            sender_email=sender_email,
            sender_password=sender_password,
            recipient_email=recipient_email,
            matches=matches,
        )
        if not success:
            logger.error("Échec de l'envoi de la notification.")
            return 1
    else:
        logger.info("Aucun film de votre Watchlist ne passe au cinéma cette semaine. Aucune notification requise.")

    logger.info("=== Traitement terminé avec succès ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
