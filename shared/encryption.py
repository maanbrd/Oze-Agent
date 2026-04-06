"""Fernet encryption for Google OAuth tokens stored in Supabase."""

from cryptography.fernet import Fernet

from bot.config import Config


def get_fernet() -> Fernet:
    return Fernet(Config.ENCRYPTION_KEY.encode())


def encrypt_token(token: str) -> str:
    return get_fernet().encrypt(token.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    return get_fernet().decrypt(encrypted.encode()).decode()


def generate_encryption_key() -> str:
    """Run once to generate ENCRYPTION_KEY for .env"""
    return Fernet.generate_key().decode()
