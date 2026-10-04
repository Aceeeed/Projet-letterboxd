import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def generate_email_html(matches: List[Dict[str, Any]], recipient_name: str = "") -> str:
    """Génère le template HTML pour l'e-mail de notification."""
    movie_cards = ""
    for item in matches:
        title = item.get("watchlist_title", item.get("cinema_title", "Film inconnu"))
        year = f" ({item['watchlist_year']})" if item.get("watchlist_year") else ""
        cinema = item.get("cinema", "Cinéma")
        schedule = item.get("schedule", "Voir site")
        cinema_link = item.get("cinema_link", "")
        letterboxd_link = item.get("letterboxd_link", "")

        links_html = []
        if letterboxd_link:
            links_html.append(
                f'<a href="{letterboxd_link}" style="color: #40bcf4; text-decoration: none; font-weight: 500;">Fiche Letterboxd</a>'
            )
        if cinema_link:
            links_html.append(
                f'<a href="{cinema_link}" style="color: #00e054; text-decoration: none; font-weight: 500;">Séances cinéma &rarr;</a>'
            )
        links_rendered = " &nbsp;|&nbsp; ".join(links_html)

        movie_cards += f"""
        <div style="background-color: #202830; border-radius: 8px; padding: 16px; margin-bottom: 16px; border-left: 4px solid #00e054;">
            <h3 style="margin: 0 0 6px 0; color: #ffffff; font-size: 18px;">{title}{year}</h3>
            <p style="margin: 0 0 8px 0; color: #9ab; font-size: 14px;">
                <strong>Lieu :</strong> {cinema} <br/>
                <strong>Horaires :</strong> {schedule}
            </p>
            <div style="font-size: 13px;">
                {links_rendered}
            </div>
        </div>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Alerte Cinéma Letterboxd</title>
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #14181c; color: #9ab; margin: 0; padding: 24px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #1a2129; border-radius: 12px; padding: 28px; box-shadow: 0 4px 12px rgba(0,0,0,0.5);">
            <div style="text-align: center; border-bottom: 1px solid #2c3440; padding-bottom: 16px; margin-bottom: 24px;">
                <h1 style="color: #ffffff; margin: 0; font-size: 22px; letter-spacing: 0.5px;">🎬 Alerte Séances Cinéma</h1>
                <p style="color: #00e054; margin: 6px 0 0 0; font-size: 14px; font-weight: bold;">
                    {len(matches)} film(s) de votre Watchlist à l'affiche cette semaine !
                </p>
            </div>
            
            <p style="color: #bcd; font-size: 15px; line-height: 1.5;">
                Bonjour {recipient_name},<br>
                Voici les correspondances détectées entre votre Watchlist Letterboxd et la programmation de vos cinémas favoris :
            </p>

            <div style="margin-top: 20px;">
                {movie_cards}
            </div>

            <div style="margin-top: 30px; padding-top: 16px; border-top: 1px solid #2c3440; text-align: center; font-size: 12px; color: #678;">
                Généré automatiquement via GitHub Actions &bull; Letterboxd Watchlist Alert
            </div>
        </div>
    </body>
    </html>
    """
    return html_content


def generate_email_text(matches: List[Dict[str, Any]], recipient_name: str = "") -> str:
    """Génère le texte brut de secours pour l'e-mail."""
    lines = [
        f"Alerte Séances Cinéma ({len(matches)} film(s) trouvé(s))\n",
        f"Bonjour {recipient_name},\n",
        "Voici les films de votre Watchlist actuellement programmés :\n",
    ]
    for item in matches:
        title = item.get("watchlist_title", item.get("cinema_title", "Film"))
        year = f" ({item['watchlist_year']})" if item.get("watchlist_year") else ""
        cinema = item.get("cinema", "Cinéma")
        schedule = item.get("schedule", "Voir site")
        link = item.get("cinema_link", "")

        lines.append(f"- {title}{year}")
        lines.append(f"  Cinéma : {cinema}")
        lines.append(f"  Horaires : {schedule}")
        if link:
            lines.append(f"  Lien : {link}")
        lines.append("")

    return "\n".join(lines)


def send_email_alert(
    sender_email: str,
    sender_password: str,
    recipient_email: str,
    matches: List[Dict[str, Any]],
    smtp_host: str = "smtp.gmail.com",
    smtp_port: int = 465,
    use_ssl: bool = True,
) -> bool:
    """
    Envoie un e-mail via le serveur SMTP de Gmail.

    :param sender_email: Adresse Gmail de l'expéditeur.
    :param sender_password: Mot de passe d'application Google (16 caractères).
    :param recipient_email: Adresse e-mail du destinataire.
    :param matches: Liste des correspondances de films.
    :param smtp_host: Hôte SMTP (défaut : smtp.gmail.com).
    :param smtp_port: Port SMTP (465 pour SSL, 587 pour STARTTLS).
    :param use_ssl: True pour SSL direct (port 465), False pour STARTTLS (port 587).
    :return: True si l'e-mail a été envoyé avec succès, False sinon.
    """
    if not matches:
        logger.info("Aucun match à notifier. E-mail non envoyé.")
        return True

    if not sender_email or not sender_password or not recipient_email:
        logger.error("Identifiants e-mail manquants. Impossible d'envoyer l'alerte.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🎬 {len(matches)} film(s) de votre Watchlist au cinéma cette semaine !"
    msg["From"] = f"Letterboxd Alert <{sender_email}>"
    msg["To"] = recipient_email

    text_content = generate_email_text(matches)
    html_content = generate_email_html(matches)

    msg.attach(MIMEText(text_content, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        logger.info(f"Connexion au serveur SMTP {smtp_host}:{smtp_port}...")
        if use_ssl or smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=20) as server:
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipient_email, msg.as_string())
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipient_email, msg.as_string())

        logger.info(f"E-mail d'alerte envoyé avec succès à {recipient_email} !")
        return True
    except Exception as e:
        logger.error(f"Échec lors de l'envoi de l'e-mail : {e}")
        return False
