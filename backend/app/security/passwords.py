"""Standard-library PBKDF2 password hashing; no plaintext password persistence."""
import base64
import hashlib
import hmac
import secrets

ITERATIONS = 600_000


def hash_password(password: str) -> str:
    if not 12 <= len(password) <= 256:
        raise ValueError('Password must be between 12 and 256 characters')
    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, ITERATIONS)
    return f'pbkdf2_sha256${ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(derived).decode()}'


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt, signature = encoded.split('$')
        if algorithm != 'pbkdf2_sha256' or int(rounds) < 600_000 or int(rounds) > 1_200_000:
            return False
        derived = hashlib.pbkdf2_hmac('sha256', password.encode(), base64.b64decode(salt, validate=True), int(rounds))
        return hmac.compare_digest(derived, base64.b64decode(signature, validate=True))
    except (ValueError, TypeError, UnicodeError):
        return False
