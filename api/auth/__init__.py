"""
Authentication Package

JWT-based authentication for the API.
"""

from api.auth.password import hash_password, verify_password
from api.auth.jwt import create_access_token, decode_access_token
from api.auth.middleware import get_current_user, get_current_admin_user

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "get_current_user",
    "get_current_admin_user",
]
