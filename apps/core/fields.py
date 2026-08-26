import os
import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken
from django.db import models
from django.conf import settings

def get_fernet_cipher():
    """
    Returns a Fernet cipher initialized with FIELD_ENCRYPTION_KEY or
    derived deterministically from SECRET_KEY.
    """
    raw_key = os.getenv('FIELD_ENCRYPTION_KEY', getattr(settings, 'FIELD_ENCRYPTION_KEY', None))
    if not raw_key:
        # Deterministically derive 32-byte urlsafe base64 key from SECRET_KEY as fallback
        secret = settings.SECRET_KEY.encode('utf-8')
        derived = hashlib.sha256(secret).digest()
        raw_key = base64.urlsafe_b64encode(derived).decode('utf-8')
    elif isinstance(raw_key, str):
        # Validate or pad to valid Fernet key
        try:
            Fernet(raw_key.encode('utf-8') if isinstance(raw_key, str) else raw_key)
        except Exception:
            derived = hashlib.sha256(raw_key.encode('utf-8')).digest()
            raw_key = base64.urlsafe_b64encode(derived).decode('utf-8')

    return Fernet(raw_key.encode('utf-8') if isinstance(raw_key, str) else raw_key)

def encrypt_value(value: str) -> str:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    if value == "":
        return ""
    cipher = get_fernet_cipher()
    encrypted_bytes = cipher.encrypt(value.encode('utf-8'))
    return encrypted_bytes.decode('utf-8')

def decrypt_value(value: str) -> str:
    if value is None or value == "":
        return value
    if not isinstance(value, str):
        return value
    
    # Check if value matches Fernet token format (starts with standard prefix 'gAAAAA')
    if not value.startswith('gAAAAA'):
        # Legacy/plaintext value
        return value

    cipher = get_fernet_cipher()
    try:
        decrypted_bytes = cipher.decrypt(value.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except (InvalidToken, Exception):
        # If decryption fails (e.g. not encrypted or corrupt), return raw string
        return value


class EncryptedTextField(models.TextField):
    """
    TextField that automatically encrypts data before storing in the database
    and decrypts it upon retrieval into Python.
    """
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return decrypt_value(value)

    def to_python(self, value):
        if isinstance(value, str):
            return decrypt_value(value)
        return value

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is None or value == "":
            return value
        return encrypt_value(value)


class EncryptedCharField(models.CharField):
    """
    CharField that stores data encrypted at rest.
    Uses TextField or sufficiently large CharField to store Fernet ciphertext.
    """
    def __init__(self, *args, **kwargs):
        # Fernet ciphertext expands length, so default to 1024 or max_length
        kwargs['max_length'] = max(kwargs.get('max_length', 255), 1024)
        super().__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return decrypt_value(value)

    def to_python(self, value):
        if isinstance(value, str):
            return decrypt_value(value)
        return value

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is None or value == "":
            return value
        return encrypt_value(value)
