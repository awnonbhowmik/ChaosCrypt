"""
ChaosCrypt Cipher — Encrypt / Decrypt
======================================
Combines the three primitives into a stream cipher pipeline:

    Encrypt:  plaintext  →  Cantor encode  →  XOR keystream  →  ciphertext
    Decrypt:  ciphertext →  XOR keystream  →  Cantor decode  →  plaintext

Key = (seed, a, b, m) where seed is a 4-digit integer and (a, b, m) are
the LCG parameters.  Optionally, the seed can be split into CRT residues
for distribution across multiple key-holders.

NOTE: ChaosCrypt is an educational demonstration only.  See analysis.py
for a full characterisation of its security weaknesses.
"""

from .prng   import middle_square_lcg
from .cantor import encode_message, decode_message
from .crt    import crt_split_key


def encrypt(plaintext, seed, a, b, m, split_moduli=None):
    """
    Encrypt a plaintext string.

    Parameters
    ----------
    plaintext    : str        — message to encrypt
    seed         : int        — 4-digit PRNG seed
    a, b, m      : int        — LCG parameters (b > 0; m > 4095)
    split_moduli : list[int]  — optional pairwise-coprime moduli for CRT key
                                splitting; product must exceed seed value

    Returns
    -------
    dict:
        'ciphertext'      : list[int]       — encrypted blocks
        'original_length' : int             — required for correct decryption
        'crt_shares'      : list[int]|None  — CRT residues of seed
        'crt_moduli'      : list[int]|None  — corresponding moduli
    """
    blocks, original_length = encode_message(plaintext)
    keystream = middle_square_lcg(seed, a, b, m, len(blocks))
    ciphertext = [c ^ k for c, k in zip(blocks, keystream)]

    crt_shares = crt_split_key(seed, split_moduli) if split_moduli else None

    return {
        'ciphertext':       ciphertext,
        'original_length':  original_length,
        'crt_shares':       crt_shares,
        'crt_moduli':       split_moduli,
    }


def decrypt(ciphertext, original_length, seed, a, b, m):
    """
    Decrypt a ChaosCrypt ciphertext.

    If the seed was distributed as CRT shares, reconstruct it first:
        seed, _ = crt_reconstruct(shares, moduli)

    Parameters
    ----------
    ciphertext      : list[int] — from encrypt()['ciphertext']
    original_length : int       — from encrypt()['original_length']
    seed, a, b, m   : int       — key parameters

    Returns
    -------
    str — recovered plaintext
    """
    keystream = middle_square_lcg(seed, a, b, m, len(ciphertext))
    blocks = [c ^ k for c, k in zip(ciphertext, keystream)]
    return decode_message(blocks, original_length)
