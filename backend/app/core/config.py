from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://recueil:recueil@db:5432/recueil"
    media_root: str = "/data/media"
    app_name: str = "Recueil"
    # "production" ferme /docs, /redoc, /openapi.json (à activer avant toute exposition publique)
    environment: str = "development"

    secret_key: str = "change-me-in-production"
    admin_email: str = "admin@recueil.local"
    admin_password: str = "changeme123"

    # SMTP vide = notifications désactivées (log seulement, pas d'envoi)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True


settings = Settings()
