"""
CipherVault Pro — Cryptographic Utilities
Provides AES-256 (EAX), Blowfish (EAX), and 3DES (CBC+HMAC) encryption
with PBKDF2-HMAC-SHA256 key derivation.

All functions return / accept raw bytes for the payload so callers can
base64-encode for storage or transport as needed.
"""

import os
import hmac as hmac_lib
import hashlib
import struct
import base64
from typing import Tuple

from Crypto.Cipher import AES, Blowfish, DES3
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256, HMAC


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PBKDF2_ITERATIONS = 200_000
SALT_SIZE = 32          # bytes
AES_KEY_SIZE = 32       # 256 bits
BLOWFISH_KEY_SIZE = 56  # 448 bits (max) — 56 bytes
DES3_KEY_SIZE = 24      # 192 bits (3 × 64-bit DES keys)
TAG_SIZE = 16           # bytes — EAX authentication tag (AES)
BLOWFISH_TAG_SIZE = 8  # bytes — EAX tag for Blowfish (block-size limited)
HMAC_SIZE = 32          # bytes — SHA-256 HMAC for 3DES


# ---------------------------------------------------------------------------
# Key derivation
# ---------------------------------------------------------------------------

def derive_key(passphrase: str, salt: bytes, key_len: int) -> bytes:
    """Derive a cryptographic key from a passphrase using PBKDF2-HMAC-SHA256."""
    return PBKDF2(
        passphrase.encode("utf-8"),
        salt,
        dkLen=key_len,
        count=PBKDF2_ITERATIONS,
        prf=lambda p, s: HMAC.new(p, s, SHA256).digest(),
    )


# ---------------------------------------------------------------------------
# AES-256 in EAX mode (authenticated encryption)
# ---------------------------------------------------------------------------

def aes_encrypt(plaintext: bytes, passphrase: str) -> bytes:
    """
    Encrypt *plaintext* with AES-256-EAX.

    Payload layout:
        [4 bytes: salt_len][salt][nonce][tag][ciphertext]
    """
    salt = get_random_bytes(SALT_SIZE)
    key = derive_key(passphrase, salt, AES_KEY_SIZE)
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)

    # Pack: salt_len (4 B) | salt | nonce (16 B) | tag (16 B) | ciphertext
    packed = struct.pack(">I", SALT_SIZE) + salt + cipher.nonce + tag + ciphertext
    return packed


def aes_decrypt(payload: bytes, passphrase: str) -> bytes:
    """Decrypt an AES-256-EAX payload produced by :func:`aes_encrypt`."""
    offset = 0
    salt_len = struct.unpack(">I", payload[offset:offset + 4])[0]
    offset += 4
    salt = payload[offset:offset + salt_len]
    offset += salt_len
    nonce = payload[offset:offset + 16]
    offset += 16
    tag = payload[offset:offset + TAG_SIZE]
    offset += TAG_SIZE
    ciphertext = payload[offset:]

    key = derive_key(passphrase, salt, AES_KEY_SIZE)
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    return plaintext


# ---------------------------------------------------------------------------
# Blowfish in EAX mode (authenticated encryption via PyCryptodome)
# ---------------------------------------------------------------------------

def blowfish_encrypt(plaintext: bytes, passphrase: str) -> bytes:
    """
    Encrypt *plaintext* with Blowfish-EAX.

    Blowfish key: 56 bytes (448 bits — maximum).
    Payload layout identical to AES variant.
    """
    salt = get_random_bytes(SALT_SIZE)
    key = derive_key(passphrase, salt, BLOWFISH_KEY_SIZE)
    nonce = get_random_bytes(16)  # explicit 16-byte nonce for EAX mode
    cipher = Blowfish.new(key, Blowfish.MODE_EAX, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)

    # Pack: salt_len | salt | nonce (16 B) | tag (16 B) | ciphertext
    packed = struct.pack(">I", SALT_SIZE) + salt + nonce + tag + ciphertext
    return packed


def blowfish_decrypt(payload: bytes, passphrase: str) -> bytes:
    """Decrypt a Blowfish-EAX payload produced by :func:`blowfish_encrypt`."""
    offset = 0
    salt_len = struct.unpack(">I", payload[offset:offset + 4])[0]
    offset += 4
    salt = payload[offset:offset + salt_len]
    offset += salt_len

    # Blowfish nonce: 16 bytes (explicit in encrypt)
    nonce = payload[offset:offset + 16]
    offset += 16
    tag = payload[offset:offset + BLOWFISH_TAG_SIZE]
    offset += BLOWFISH_TAG_SIZE
    ciphertext = payload[offset:]

    key = derive_key(passphrase, salt, BLOWFISH_KEY_SIZE)
    cipher = Blowfish.new(key, Blowfish.MODE_EAX, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    return plaintext


# ---------------------------------------------------------------------------
# Triple DES — CBC + HMAC-SHA256 (Encrypt-then-MAC)
# ---------------------------------------------------------------------------
_DES3_BLOCK = 8  # bytes


def _pad(data: bytes, block_size: int) -> bytes:
    """PKCS#7 padding."""
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len] * pad_len)


def _unpad(data: bytes) -> bytes:
    """Remove PKCS#7 padding."""
    pad_len = data[-1]
    if pad_len < 1 or pad_len > _DES3_BLOCK:
        raise ValueError("Invalid padding")
    return data[:-pad_len]


def des3_encrypt(plaintext: bytes, passphrase: str) -> bytes:
    """
    Encrypt *plaintext* with 3DES-CBC + HMAC-SHA256 (Encrypt-then-MAC).

    Payload layout:
        [4 B: salt_len][salt][iv (8 B)][hmac (32 B)][ciphertext]
    """
    salt = get_random_bytes(SALT_SIZE)
    # Derive two sub-keys: encryption key (24 B) + MAC key (32 B)
    key_material = derive_key(passphrase, salt, DES3_KEY_SIZE + HMAC_SIZE)
    enc_key = key_material[:DES3_KEY_SIZE]
    mac_key = key_material[DES3_KEY_SIZE:]

    iv = get_random_bytes(_DES3_BLOCK)
    padded = _pad(plaintext, _DES3_BLOCK)

    cipher = DES3.new(enc_key, DES3.MODE_CBC, iv=iv)
    ciphertext = cipher.encrypt(padded)

    # MAC over iv || ciphertext
    mac = hmac_lib.new(mac_key, iv + ciphertext, hashlib.sha256).digest()

    packed = struct.pack(">I", SALT_SIZE) + salt + iv + mac + ciphertext
    return packed


def des3_decrypt(payload: bytes, passphrase: str) -> bytes:
    """Decrypt a 3DES-CBC+HMAC payload produced by :func:`des3_encrypt`."""
    offset = 0
    salt_len = struct.unpack(">I", payload[offset:offset + 4])[0]
    offset += 4
    salt = payload[offset:offset + salt_len]
    offset += salt_len
    iv = payload[offset:offset + _DES3_BLOCK]
    offset += _DES3_BLOCK
    mac_received = payload[offset:offset + HMAC_SIZE]
    offset += HMAC_SIZE
    ciphertext = payload[offset:]

    key_material = derive_key(passphrase, salt, DES3_KEY_SIZE + HMAC_SIZE)
    enc_key = key_material[:DES3_KEY_SIZE]
    mac_key = key_material[DES3_KEY_SIZE:]

    # Verify MAC before decrypting (prevents padding oracle)
    mac_expected = hmac_lib.new(mac_key, iv + ciphertext, hashlib.sha256).digest()
    if not hmac_lib.compare_digest(mac_received, mac_expected):
        raise ValueError("MAC verification failed — wrong passphrase or tampered data")

    cipher = DES3.new(enc_key, DES3.MODE_CBC, iv=iv)
    padded = cipher.decrypt(ciphertext)
    return _unpad(padded)


# ---------------------------------------------------------------------------
# Unified interface
# ---------------------------------------------------------------------------

ALGORITHMS = {
    "AES-256": (aes_encrypt, aes_decrypt),
    "Blowfish": (blowfish_encrypt, blowfish_decrypt),
    "3DES": (des3_encrypt, des3_decrypt),
}


def encrypt_data(plaintext: bytes, passphrase: str, algorithm: str = "AES-256") -> bytes:
    """Encrypt *plaintext* using the named algorithm. Returns raw bytes."""
    if algorithm not in ALGORITHMS:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    enc_fn, _ = ALGORITHMS[algorithm]
    return enc_fn(plaintext, passphrase)


def decrypt_data(payload: bytes, passphrase: str, algorithm: str = "AES-256") -> bytes:
    """Decrypt *payload* using the named algorithm. Returns raw bytes."""
    if algorithm not in ALGORITHMS:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    _, dec_fn = ALGORITHMS[algorithm]
    return dec_fn(payload, passphrase)


def encrypt_b64(plaintext: bytes, passphrase: str, algorithm: str = "AES-256") -> str:
    """Encrypt and return base64-encoded string (safe for DB storage)."""
    raw = encrypt_data(plaintext, passphrase, algorithm)
    return base64.b64encode(raw).decode("ascii")


def decrypt_b64(b64_payload: str, passphrase: str, algorithm: str = "AES-256") -> bytes:
    """Decode base64 then decrypt."""
    raw = base64.b64decode(b64_payload.encode("ascii"))
    return decrypt_data(raw, passphrase, algorithm)
