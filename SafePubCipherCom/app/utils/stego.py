"""
CipherVault Pro — Steganography Utilities
Two complementary strategies:

1. LSB (Least-Significant-Bit) — embeds arbitrary bytes into R/G/B channels,
   1 bit per channel.  Robust, handles any payload size within image capacity.

2. Morse-Pixel — maps each character to a Morse sequence, encodes the sequence
   as a cumulative pixel offset, and colours those pixels red (255, 0, 0).
   Inspired by the SafePub/CipherCom project.  Useful for demonstration; LSB
   is preferred for larger payloads.

Both strategies include a length prefix so extraction knows where to stop.
"""

import io
import math
import struct
from PIL import Image


# ---------------------------------------------------------------------------
# Morse code table (extended for base64 alphabet)
# ---------------------------------------------------------------------------
MORSE_TABLE = {
    'a': '.', 'b': '-', 'c': '..', 'd': '.-', 'e': '-.', 'f': '--',
    'g': '...', 'h': '..-', 'i': '.-.', 'j': '.--', 'k': '-..', 'l': '-.-',
    'm': '--.', 'n': '---', 'o': '....', 'p': '...-', 'q': '..-.',
    'r': '..--', 's': '.-..', 't': '.-.-', 'u': '.--.',  'v': '.---',
    'w': '-...', 'x': '-..-', 'y': '-.-.', 'z': '-.--', 'A': '--..',
    'B': '--.-', 'C': '---.', 'D': '----', 'E': '.....', 'F': '...._',
    'G': '...-.', 'H': '...--', 'I': '..-..', 'J': '..-.-', 'K': '..--.',
    'L': '..---', 'M': '......--.', 'N': '......---', 'O': '.-.-.', 'P': '.-.--',
    'Q': '.--..', 'R': '.--.-', 'S': '.---.', 'T': '.----', 'U': '-....',
    'V': '-...-', 'W': '-..-.', 'X': '-..--', 'Y': '-..-.', 'Z': '-.-.-',
    '0': '-.--.', '1': '-.---', '2': '--...', '3': '--..-', '4': '--.-.',
    '5': '--.--', '6': '---..', '7': '---.', '8': '----.', '9': '-----',
    '+': '/.--.', '=': '/.--', '/': './.-.', '\n': '..//-', ' ': '../..',
    '\r': '../-', '.': '....-.', ',': '....--', '?': '...-..', "'": '...-.-',
    '(': '...--.', ')': '...---', '[': '..-...', ']': '..-..-', ':': '..-.-.',
    ';': '..-.--', '-': '..--.-', '_': '..--.-', '"': '..---.', '$': '..----',
    '!': '..--..', '@': '..--.-', '#': '..--..',
}

REVERSE_MORSE = {v: k for k, v in MORSE_TABLE.items()}


# ---------------------------------------------------------------------------
# LSB steganography (preferred, handles large payloads)
# ---------------------------------------------------------------------------

def _to_bits(data: bytes):
    """Yield individual bits from a bytes object, MSB first."""
    for byte in data:
        for i in range(7, -1, -1):
            yield (byte >> i) & 1


def _from_bits(bits):
    """Reconstruct bytes from an iterable of bits (MSB first)."""
    result = bytearray()
    buf = 0
    count = 0
    for bit in bits:
        buf = (buf << 1) | bit
        count += 1
        if count == 8:
            result.append(buf)
            buf = 0
            count = 0
    return bytes(result)


def lsb_embed(image_bytes: bytes, payload: bytes) -> bytes:
    """
    Embed *payload* into the LSB of the RGB channels of *image_bytes* (PNG).

    Layout in image:
        First 32 bits  → payload length (big-endian uint32)
        Next N bits     → payload bytes

    Returns the modified image as PNG bytes.
    Raises ValueError if the image is too small to hold the payload.
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    pixels = list(img.getdata())
    capacity_bits = len(pixels) * 3  # R, G, B — 1 bit each

    length_prefix = struct.pack(">I", len(payload))
    full_data = length_prefix + payload
    bits = list(_to_bits(full_data))

    if len(bits) > capacity_bits:
        raise ValueError(
            f"Image too small: need {len(bits)} bits, have {capacity_bits} bits "
            f"({len(bits) // 8} bytes payload, {capacity_bits // 8} bytes capacity)."
        )

    new_pixels = []
    bit_idx = 0
    for r, g, b in pixels:
        if bit_idx < len(bits):
            r = (r & 0xFE) | bits[bit_idx]; bit_idx += 1
        if bit_idx < len(bits):
            g = (g & 0xFE) | bits[bit_idx]; bit_idx += 1
        if bit_idx < len(bits):
            b = (b & 0xFE) | bits[bit_idx]; bit_idx += 1
        new_pixels.append((r, g, b))

    out_img = Image.new("RGB", img.size)
    out_img.putdata(new_pixels)
    buf = io.BytesIO()
    out_img.save(buf, format="PNG")
    return buf.getvalue()


def lsb_extract(image_bytes: bytes) -> bytes:
    """
    Extract a payload previously embedded by :func:`lsb_embed`.

    Returns raw payload bytes.
    Raises ValueError if the length prefix is invalid.
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    pixels = list(img.getdata())

    # Extract first 32 bits to get length
    channel_bits = []
    for r, g, b in pixels:
        channel_bits += [r & 1, g & 1, b & 1]

    length_bytes = _from_bits(channel_bits[:32])
    payload_len = struct.unpack(">I", length_bytes)[0]

    if payload_len == 0 or payload_len > len(channel_bits) // 8:
        raise ValueError("No valid LSB payload found in this image.")

    total_bits_needed = 32 + payload_len * 8
    payload_bytes = _from_bits(channel_bits[32:total_bits_needed])
    return payload_bytes


def lsb_capacity(image_bytes: bytes) -> int:
    """Return maximum payload bytes the image can hold via LSB."""
    img = Image.open(io.BytesIO(image_bytes))
    w, h = img.size
    # 3 channels, 1 bit each, minus 4-byte length prefix
    return (w * h * 3 // 8) - 4


# ---------------------------------------------------------------------------
# Morse-Pixel steganography (demo / educational)
# ---------------------------------------------------------------------------
_MORSE_IMG_WIDTH = 800


def morse_embed(payload_str: str) -> bytes:
    """
    Encode a string as Morse-pixel art image.

    Each character → Morse sequence → cumulative pixel sum →
    paint that pixel red on a black canvas.

    Returns PNG bytes of the generated image.
    """
    letters = list(payload_str)
    pix_sum = 0
    white_pixels = []

    for char in letters:
        code = MORSE_TABLE.get(char)
        if code is None:
            # Skip unknown characters
            continue
        for mc in code:
            pix_sum += ord(mc)
            white_pixels.append(pix_sum)
        pix_sum += 32  # inter-character gap
        white_pixels.append(pix_sum)

    if not white_pixels:
        raise ValueError("No encodable characters found in payload.")

    W = _MORSE_IMG_WIDTH
    H = int(white_pixels[-1] / W) + 2

    img = Image.new("RGB", (W, H), "black")
    pixels = img.load()

    for wp in white_pixels:
        y = wp // W
        x = wp % W
        if 0 <= x < W and 0 <= y < H:
            pixels[x, y] = (255, 0, 0)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def morse_extract(image_bytes: bytes) -> str:
    """
    Extract the string previously encoded by :func:`morse_embed`.

    Returns the decoded string.
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    W, H = img.size
    pixels = img.load()

    last_off = 0
    _letter = ""
    answer = ""

    for y in range(H):
        for x in range(W):
            if pixels[x, y] == (255, 0, 0):
                offset = y * W + x - last_off
                last_off = y * W + x
                char = chr(offset)
                if char == " ":
                    letter = REVERSE_MORSE.get(_letter, "?")
                    answer += letter
                    _letter = ""
                elif char == "\n":
                    letter = REVERSE_MORSE.get(_letter, "?")
                    answer += letter + "\n"
                    _letter = ""
                else:
                    _letter += char

    if _letter:
        letter = REVERSE_MORSE.get(_letter, "?")
        answer += letter

    return answer


# ---------------------------------------------------------------------------
# Capacity helper
# ---------------------------------------------------------------------------

def image_capacity_info(image_bytes: bytes) -> dict:
    """Return capacity info dict for a given image."""
    img = Image.open(io.BytesIO(image_bytes))
    w, h = img.size
    lsb_cap = lsb_capacity(image_bytes)
    return {
        "width": w,
        "height": h,
        "pixels": w * h,
        "lsb_capacity_bytes": lsb_cap,
        "lsb_capacity_kb": round(lsb_cap / 1024, 2),
    }
