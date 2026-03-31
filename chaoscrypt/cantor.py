"""
Cantor Pairing Function
========================
Bijective mapping ℕ × ℕ → ℕ used to pre-process plaintext in ChaosCrypt.

Each pair of consecutive ASCII values is encoded into a single integer
before XOR with the keystream, changing the numerical structure of the
message and making frequency analysis on raw byte values harder.

Reference: Cantor, G. (1878). Ein Beitrag zur Mannigfaltigkeitslehre.
"""

import numpy as np


def cantor_pair(k1, k2):
    """
    Map (k1, k2) ∈ ℕ² to a unique z ∈ ℕ.

    Formula:  z = ½ (k1 + k2)(k1 + k2 + 1) + k2
    """
    return int(0.5 * (k1 + k2) * (k1 + k2 + 1) + k2)


def cantor_unpair(z):
    """
    Recover (k1, k2) from z (inverse of cantor_pair).

    Uses the closed-form inverse:
        w  = ⌊(√(8z + 1) − 1) / 2⌋
        k2 = z − (w² + w) / 2
        k1 = w − k2
    """
    w = int(np.floor((np.sqrt(8 * z + 1) - 1) / 2))
    t = (w * w + w) // 2
    k2 = z - t
    k1 = w - k2
    return (k1, k2)


def encode_message(text):
    """
    Convert plaintext to a list of Cantor-paired blocks.

    Consecutive ASCII values are paired: (ord(c0), ord(c1)) → z0, etc.
    A null byte (0x00) is appended if the message has odd length.

    Returns
    -------
    (list[int], int)  — (blocks, original_length)
    """
    ascii_vals = [ord(c) for c in text]
    original_length = len(ascii_vals)
    if len(ascii_vals) % 2 != 0:
        ascii_vals.append(0)
    blocks = [cantor_pair(ascii_vals[i], ascii_vals[i + 1])
              for i in range(0, len(ascii_vals), 2)]
    return blocks, original_length


def decode_message(blocks, original_length):
    """
    Recover plaintext from a list of Cantor-valued blocks.

    Padding introduced by encode_message() is stripped via original_length.
    """
    ascii_vals = []
    for z in blocks:
        k1, k2 = cantor_unpair(z)
        ascii_vals.extend([k1, k2])
    return ''.join(chr(v) for v in ascii_vals[:original_length])
