<p align="center"><img src="docs/engispeak-logo.svg" alt="EngiSpeak" width="420"></p>

# EngiSpeak

Plateforme web qui accompagne les étudiants ingénieurs pendant **un mois** pour progresser en anglais et en prise de parole en public. La roadmap suit la *English Public Speaking Masterclass* : 4 semaines, 12 sessions construites autour d'un TED Talk (à analyser, puis un défi oral), et une prise filmée chaque dimanche.

MVP volontairement simple, mais architecturé comme une application cloud-native prête pour Azure :

| Exigence | Implémentation |
|---|---|
| 2 composants de calcul | `web-app` (FastAPI + Jinja/Tailwind CDN) et `worker` (rappels quotidiens, logs JSON) |
| Stockage 1 : progression | SQLAlchemy : SQLite en local, PostgreSQL en prod, ou Azure Table Storage |
| Stockage 2 : ressources | Azure Blob Storage via `azure-storage-blob` + `DefaultAzureCredential` (Managed Identity), fallback dossier local |
| 12-Factor & sécurité | Toute la config en variables d'environnement, aucun secret en dur, lecture optionnelle depuis Key Vault |
| Conteneurs & CI/CD | 2 Dockerfiles (multi-stage, utilisateur non-root, healthcheck), `docker-compose.yml`, GitHub Actions (ruff + pytest + build) |

## Architecture

```
                ┌──────────────────────────┐
  Navigateur ──▶│  web-app (FastAPI)       │──▶ Azure Blob Storage (fiches)
                │  /, /weeks/n, /resources │       via Managed Identity
                │  /api/..., /health       │
                └────────────┬─────────────┘
                             │ progression
                             ▼
                 PostgreSQL / Azure Table / SQLite
                             ▲
                ┌────────────┴─────────────┐
                │  worker (Python)         │──▶ logs JSON (Azure Monitor)
                │  rappels quotidiens      │
                └──────────────────────────┘
```

## Arborescence

```
engispeak/
├── engispeak/                 # Code partagé par les deux services
│   ├── config.py              # Settings 12-Factor + lecture Key Vault optionnelle
│   ├── logging_utils.py       # Logs structurés JSON
│   ├── roadmap.py             # Contenu pédagogique (4 semaines, 16 étapes)
│   ├── progress.py            # Logique de progression (sans I/O, testable)
│   └── storage/
│       ├── progress_store.py  # Stockage 1 : SQL (SQLite/PostgreSQL) ou Azure Table
│       └── resource_store.py  # Stockage 2 : Azure Blob ou dossier local
├── web/
│   ├── app.py                 # Service 1 : FastAPI (pages HTML + API JSON + /health)
│   ├── templates/             # Jinja2 + Tailwind CDN
│   └── Dockerfile
├── worker/
│   ├── worker.py              # Service 2 : rappels motivants + suivi de progression
│   └── Dockerfile
├── resources/                 # Fiches mémo (fallback local / source pour l'upload Blob)
├── scripts/upload_resources.py
├── tests/                     # pytest : routes, /health, logique de progression, worker
├── .github/workflows/ci.yml
├── docker-compose.yml
├── .env.example
├── requirements.txt / requirements-worker.txt / requirements-dev.txt
└── pyproject.toml             # Config ruff + pytest
```

## Démarrage rapide (sans Docker)

Prérequis : Python 3.11+.

```bash
python -m venv .venv && source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env

# Service 1 : web-app sur http://localhost:8000
uvicorn web.app:create_app --factory --reload

# Service 2 : worker (un seul cycle, dans un autre terminal)
WORKER_RUN_ONCE=true python -m worker.worker
```

Sans aucune variable Azure, l'application utilise SQLite (`./data/engispeak.db`) et sert les fiches du dossier `resources/`.

## Démarrage avec Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

- web-app : http://localhost:8000 (healthcheck sur `/health`)
- worker : un cycle toutes les 60 s en local (`WORKER_INTERVAL_SECONDS`), visible avec `docker compose logs -f worker`
- PostgreSQL 16 : la progression survit aux redémarrages (volume `pgdata`)

## Variables d'environnement

| Variable | Défaut | Rôle |
|---|---|---|
| `APP_ENV` | `local` | Nom de l'environnement |
| `LOG_LEVEL` | `INFO` | Niveau de log |
| `PROGRESS_BACKEND` | `sql` | `sql` ou `azure_table` |
| `DATABASE_URL` | SQLite local | Ex. `postgresql+psycopg://user:pwd@host:5432/engispeak` |
| `AZURE_TABLE_ENDPOINT` | – | Requis si `PROGRESS_BACKEND=azure_table` |
| `AZURE_TABLE_NAME` | `progress` | Nom de la table |
| `AZURE_STORAGE_ACCOUNT_URL` | – | Active Azure Blob ; vide = fallback local |
| `AZURE_STORAGE_CONTAINER` | `resources` | Conteneur des fiches |
| `LOCAL_RESOURCES_DIR` | `./resources` | Dossier du fallback local |
| `KEY_VAULT_URL` | – | Si défini et `DATABASE_URL` vide, la chaîne est lue dans Key Vault |
| `DATABASE_URL_SECRET_NAME` | `database-url` | Nom du secret dans Key Vault |
| `AZURE_CLIENT_ID` | – | Managed Identity user-assigned (lu par `DefaultAzureCredential`) |
| `WORKER_INTERVAL_SECONDS` | `86400` | Intervalle entre deux cycles du worker |
| `WORKER_RUN_ONCE` | `false` | `true` pour une tâche planifiée (cron / Container Apps Job) |
| `INACTIVITY_DAYS_THRESHOLD` | `2` | Jours sans activité avant un rappel « inactif » |

## Authentification Azure (Managed Identity)

Aucune clé de compte ni chaîne de connexion n'est utilisée pour Blob, Table ou Key Vault : le code passe par `DefaultAzureCredential`, qui choisit automatiquement :

- en production : la **Managed Identity** de l'App Service / Container App ;
- en local : la session `az login` (ou les variables `AZURE_CLIENT_ID` / `AZURE_TENANT_ID` / `AZURE_CLIENT_SECRET`).

Rôles RBAC à attribuer à l'identité :

| Ressource | Rôle |
|---|---|
| Compte de stockage (Blob) | `Storage Blob Data Reader` (web-app) |
| Compte de stockage (Table) | `Storage Table Data Contributor` |
| Key Vault | `Key Vault Secrets User` |

Pour publier les fiches dans le conteneur Blob :

```bash
az login
AZURE_STORAGE_ACCOUNT_URL=https://<compte>.blob.core.windows.net python -m scripts.upload_resources
```

## Endpoints

| Méthode | Route | Description |
|---|---|---|
| GET | `/health` | Liveness (200), pour le Load Balancer et Azure Monitor |
| GET | `/ready` | Readiness : vérifie la base (503 si indisponible) |
| GET | `/` | Connexion par identifiant, puis tableau de bord |
| GET | `/weeks/{n}` | Détail d'une semaine, validation des étapes |
| POST | `/steps/{step_id}/toggle` | Coche / décoche une étape |
| GET | `/resources`, `/resources/{name}` | Liste et téléchargement des fiches |
| GET | `/api/roadmap` | Roadmap en JSON |
| GET | `/api/students/{id}/progress` | Progression d'un étudiant |
| PUT | `/api/students/{id}/steps/{step_id}` | `{"completed": true}` |

La documentation OpenAPI est disponible sur `/docs`.

## Qualité

```bash
ruff check . && ruff format --check .
pytest
```

La CI GitHub Actions exécute le lint, les tests, puis construit les deux images Docker à chaque push et pull request.

## Limites du MVP et suites possibles

- L'identifiant étudiant n'est pas une authentification : prochaine étape, Microsoft Entra ID.
- Les rappels du worker sont simulés (logs) : brancher Azure Communication Services pour de vrais e-mails.
- Tailwind est chargé par CDN : passer à un build Tailwind pour la production.
- Infrastructure as Code : décrire App Service / Container Apps, Storage, Key Vault et les rôles RBAC en Terraform.
