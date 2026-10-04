# 🎬 Letterboxd Cinema Alert

Système d'alerte automatisé hébergé sur **GitHub Actions** qui compare votre Watchlist [Letterboxd](https://letterboxd.com/) avec la programmation de cinémas indépendants et vous prévient par e-mail dès qu'un film passe en salle.

---

## 📁 Architecture du projet

```text
.
├── .github/
│   └── workflows/
│       └── cinema_alert.yml   # Workflow d'automatisation GitHub Actions (cron hebdo)
├── letterboxd.py              # Extraction de la Watchlist via flux RSS
├── scraper.py                 # Scraping des programmes des cinémas (BeautifulSoup)
├── notifier.py                # Envoi d'alertes par e-mail HTML/Texte (SMTP Gmail)
├── main.py                    # Orchestration, normalisation des titres et matching
├── requirements.txt           # Dépendances Python du projet
├── .env.example               # Exemple de variables d'environnement pour test local
└── .gitignore
```

---

## ⚙️ Configuration des Secrets GitHub (Indispensable)

Dans votre dépôt GitHub :
1. Allez dans l'onglet **Settings** du dépôt.
2. Dans le menu de gauche, rendez-vous dans **Secrets and variables** > **Actions**.
3. Cliquez sur le bouton vert **New repository secret** et ajoutez les variables suivantes :

| Nom du Secret | Description | Exemple |
| :--- | :--- | :--- |
| `LETTERBOXD_USERNAME` | Votre nom d'utilisateur Letterboxd | `mon_pseudo` |
| `GMAIL_SENDER` | Votre adresse e-mail Gmail expéditrice | `mon_adresse@gmail.com` |
| `GMAIL_APP_PASSWORD` | Mot de passe d'application Google (16 caractères) | `abcd efgh ijkl mnop` |
| `RECIPIENT_EMAIL` | Adresse e-mail recevant l'alerte (peut être la même) | `mon_adresse@gmail.com` |
| `CINEMA_URL` *(Optionnel)* | URL personnalisée du cinéma à scraper | `https://moncinema.fr/programme` |

> 💡 **Comment générer le mot de passe d'application Gmail ?**
> 1. Rendez-vous sur votre compte Google : [myaccount.google.com/security](https://myaccount.google.com/security).
> 2. Activez l'**authentification à deux facteurs** si ce n'est pas déjà fait.
> 3. Allez dans la section **Mots de passe des applications** (ou recherchez "Mots de passe d'application" dans la barre de recherche en haut).
> 4. Donnez un nom (ex: `GitHub Actions Letterboxd`) puis copiez le mot de passe de 16 caractères généré dans le secret `GMAIL_APP_PASSWORD`.

---

## 🚀 Exécution & Tests

### En local :
1. Créez un fichier `.env` basé sur `.env.example` :
   ```bash
   cp .env.example .env
   ```
2. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
3. Lancez le script :
   ```bash
   python main.py
   ```

### Sur GitHub Actions :
- Le workflow tourne automatiquement chaque **mercredi à 06:00 UTC** (07h00 en hiver / 08h00 en été en France).
- Vous pouvez le déclencher manuellement à tout moment dans l'onglet **Actions** > **Cinema Letterboxd Alert** > **Run workflow**.
# Projet-letterboxd
