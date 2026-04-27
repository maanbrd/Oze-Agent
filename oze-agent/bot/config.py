import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SECRET_ENV_NAMES = (
    "TELEGRAM_BOT_TOKEN",
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GOOGLE_CLIENT_SECRET",
    "SUPABASE_KEY",
    "SUPABASE_SERVICE_KEY",
    "SUPABASE_JWT_SECRET",
    "ENCRYPTION_KEY",
    "PRZELEWY24_API_KEY",
    "PRZELEWY24_CRC",
    "SENTRY_DSN",
    "GMAIL_SMTP_PASSWORD",
)


def _clean_env(name: str, default: str = "") -> str:
    return (os.getenv(name, default) or "").strip()


class Config:
    # Core
    ENV = os.getenv("ENV", "dev")
    TIMEZONE = os.getenv("TIMEZONE", "Europe/Warsaw")

    # Telegram
    TELEGRAM_BOT_TOKEN = _clean_env("TELEGRAM_BOT_TOKEN")

    # AI
    ANTHROPIC_API_KEY = _clean_env("ANTHROPIC_API_KEY")
    OPENAI_API_KEY = _clean_env("OPENAI_API_KEY")

    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = _clean_env("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "")

    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = _clean_env("SUPABASE_KEY")
    SUPABASE_SERVICE_KEY = _clean_env("SUPABASE_SERVICE_KEY")
    SUPABASE_JWT_SECRET = _clean_env("SUPABASE_JWT_SECRET")

    # Security
    ENCRYPTION_KEY = _clean_env("ENCRYPTION_KEY")

    # Payments
    PRZELEWY24_MERCHANT_ID = os.getenv("PRZELEWY24_MERCHANT_ID", "")
    PRZELEWY24_API_KEY = _clean_env("PRZELEWY24_API_KEY")
    PRZELEWY24_CRC = _clean_env("PRZELEWY24_CRC")

    # Pricing
    ACTIVATION_FEE_PLN = int(os.getenv("ACTIVATION_FEE_PLN", "199"))
    ACTIVATION_FEE_PROMO_PLN = int(os.getenv("ACTIVATION_FEE_PROMO_PLN", "20"))
    MONTHLY_SUBSCRIPTION_PLN = int(os.getenv("MONTHLY_SUBSCRIPTION_PLN", "49"))
    YEARLY_SUBSCRIPTION_PLN = int(os.getenv("YEARLY_SUBSCRIPTION_PLN", "350"))

    # Monitoring
    SENTRY_DSN = _clean_env("SENTRY_DSN")
    ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID", "")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")

    # URLs
    BASE_URL = os.getenv("BASE_URL", "")
    DASHBOARD_URL = os.getenv("DASHBOARD_URL", "")
    ADMIN_URL = os.getenv("ADMIN_URL", "")

    # Email
    GMAIL_SMTP_USER = os.getenv("GMAIL_SMTP_USER", "")
    GMAIL_SMTP_PASSWORD = _clean_env("GMAIL_SMTP_PASSWORD")

    @classmethod
    def warn_secret_whitespace(cls) -> None:
        """Log secret env vars with surrounding whitespace without exposing values."""
        for name in SECRET_ENV_NAMES:
            raw = os.getenv(name, "")
            if raw and raw != raw.strip():
                logger.warning(
                    "Config: env var %s has leading/trailing whitespace; "
                    "using stripped value (raw_len=%d stripped_len=%d)",
                    name,
                    len(raw),
                    len(raw.strip()),
                )

    @classmethod
    def validate_phase_a(cls) -> list[str]:
        """Return list of missing env vars required for Phase A (bot)."""
        required = {
            "TELEGRAM_BOT_TOKEN": cls.TELEGRAM_BOT_TOKEN,
            "ANTHROPIC_API_KEY": cls.ANTHROPIC_API_KEY,
            "OPENAI_API_KEY": cls.OPENAI_API_KEY,
            "SUPABASE_URL": cls.SUPABASE_URL,
            "SUPABASE_KEY": cls.SUPABASE_KEY,
            "SUPABASE_SERVICE_KEY": cls.SUPABASE_SERVICE_KEY,
            "ENCRYPTION_KEY": cls.ENCRYPTION_KEY,
            "GOOGLE_CLIENT_ID": cls.GOOGLE_CLIENT_ID,
            "GOOGLE_CLIENT_SECRET": cls.GOOGLE_CLIENT_SECRET,
            "BASE_URL": cls.BASE_URL,
        }
        return [k for k, v in required.items() if not v]
