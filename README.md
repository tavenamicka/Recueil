# Recueil

Recueil est une application web self-hosted qui transforme vos exports WhatsApp en bibliothèque organisée.

Déposez un export de discussion (`.txt`) : les liens sont extraits, leurs titres récupérés automatiquement et classés parmi 15 catégories. Importez les médias (photos, vidéos, audios) : vignettes générées, durées extraites, dates retrouvées depuis les noms de fichiers WhatsApp. Le tout est ensuite consultable dans une interface claire — recherche, filtres par catégorie et par dates, favoris, ajout manuel de liens depuis n'importe quelle source.

Pensée pour un usage familial ou en petit groupe : les inscriptions sont soumises à validation par un administrateur, les réinitialisations de mot de passe sont supervisées, et chaque étape déclenche une notification email. L'interface respecte les contrastes WCAG AA et se pilote entièrement au clavier.

## Fonctionnalités

- Import d'exports WhatsApp (`.txt`) avec suivi de progression
- Extraction des liens, scraping des titres (`og:title` / `<title>`), catégorisation automatique
- Import de médias avec vignettes (Pillow/ffmpeg) et durée (ffprobe)
- Recherche, filtres catégorie/dates, favoris, pagination "Charger plus"
- Édition des titres, recatégorisation, suppression avec confirmation
- Multi-utilisateurs avec validation admin et notifications email (SMTP)
- Accessibilité : contrastes WCAG AA, navigation clavier, focus-trap dans les modales

## Stack

- **Backend** : FastAPI, SQLAlchemy, Alembic, PostgreSQL
- **Frontend** : Vue 3 (Composition API), vue-router, Tailwind CSS, Vite
- **Déploiement** : Docker Compose (Nginx sert le frontend et proxifie `/api` et `/media`)
- **Tests** : 82 tests pytest (parsing, endpoints, auth, imports)

## Démarrage rapide

```bash
cp .env.example .env       # renseigner SECRET_KEY, ADMIN_EMAIL, ADMIN_PASSWORD…
docker compose up -d
docker compose run --rm backend alembic upgrade head   # migrations (obligatoire au 1er lancement)
```

L'application est accessible sur `http://localhost:8090` (backend seul sur `:8091`). Le compte admin est créé automatiquement au démarrage à partir de `ADMIN_EMAIL`/`ADMIN_PASSWORD`.

En développement : `npm run dev` dans `frontend/` (port `5174`, proxy `/api` et `/media` vers le backend via `vite.config.js`).

## Tests

```bash
docker compose exec backend pytest
```

Les tests d'endpoints tournent sur une base dédiée `recueil_test` (créée automatiquement, jamais la base réelle) et un répertoire média jetable.

## Structure

```
.
├── backend/            # FastAPI (API, modèles, migrations Alembic, tests)
├── frontend/           # Vue 3 + Tailwind (build Vite servi par Nginx)
└── docker-compose.yml  # db (PostgreSQL) + backend + frontend
```
