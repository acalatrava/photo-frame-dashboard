from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_VERSION = "0.1.0"
# Origin that the Android kiosk uses for its bundled web assets (see kiosk MainActivity).
KIOSK_ORIGIN = "http://appassets.homehq.invalid"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="HOMEHQ_", env_file=".env", extra="ignore")

    data_dir: Path = Path("/data")
    port: int = 8787
    # Extra browser origins allowed by CORS (comma separated). The kiosk origin is always allowed.
    cors_origins: str = ""
    # "auto" sets the Secure flag only when the request arrived over HTTPS, "true"/"false" force it.
    cookie_secure: str = "auto"
    # Initial admin account. When the password is empty a random one is generated on first start.
    admin_user: str = "admin"
    admin_password: str = ""
    # Optional base64 Fernet key. When empty one is generated inside the data volume.
    secret_key: str = ""
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    pairing_ttl_seconds: int = 600
    mdns_enabled: bool = False
    mdns_hostname: str = ""
    log_level: str = "INFO"
    photo_max_upload_mb: int = 40
    # Trust X-Forwarded-Proto/For from a reverse proxy.
    trust_proxy: bool = False
    public_dashboard: bool = True

    @property
    def cors_list(self) -> list[str]:
        extra = [o.strip().rstrip("/") for o in self.cors_origins.split(",") if o.strip()]
        return [KIOSK_ORIGIN, *extra]

    @property
    def db_path(self) -> Path:
        return self.data_dir / "db" / "homehq.sqlite3"

    @property
    def secrets_dir(self) -> Path:
        return self.data_dir / "secrets"

    @property
    def photos_dir(self) -> Path:
        return self.data_dir / "photos"

    @property
    def recordings_dir(self) -> Path:
        return self.data_dir / "recordings"

    @property
    def logs_dir(self) -> Path:
        return self.data_dir / "logs"


@lru_cache
def get_settings() -> Settings:
    return Settings()
