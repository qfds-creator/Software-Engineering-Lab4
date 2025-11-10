"""
encryption.py - Key derivation (PBKDF2-HMAC-SHA256) + AES-GCM AEAD encryption
File format (binary):
  4 bytes magic: b'FA1\x00'
  16 bytes salt
  12 bytes nonce
  remaining: ciphertext (AES-GCM tag included)
"""
import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from typing import Tuple

MAGIC = b"FA1\x00"
SALT_SIZE = 16
NONCE_SIZE = 12
ITERATIONS = 200_000  # PBKDF2 iterations


def derive_key(password: str, salt: bytes, iterations: int = ITERATIONS) -> bytes:
    if isinstance(password, str):
        password = password.encode("utf-8")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
        backend=default_backend()
    )
    return kdf.derive(password)


def encrypt(plaintext: bytes, password: str) -> bytes:
    # generate salt + nonce
    salt = os.urandom(SALT_SIZE)
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    nonce = os.urandom(NONCE_SIZE)
    ct = aesgcm.encrypt(nonce, plaintext, None)
    return MAGIC + salt + nonce + ct


def decrypt(blob: bytes, password: str) -> bytes:
    if not blob.startswith(MAGIC):
        raise ValueError("Invalid file format (magic mismatch)")
    pos = len(MAGIC)
    salt = blob[pos:pos + SALT_SIZE]; pos += SALT_SIZE
    nonce = blob[pos:pos + NONCE_SIZE]; pos += NONCE_SIZE
    ct = blob[pos:]
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    pt = aesgcm.decrypt(nonce, ct, None)
    return pt


def hash_password_hex(password: str) -> str:
    # SHA256 hex; use for applock password storage (we still derive encryption key from password separately)
    from cryptography.hazmat.primitives import hashes
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(password.encode("utf-8"))
    return digest.finalize().hex()