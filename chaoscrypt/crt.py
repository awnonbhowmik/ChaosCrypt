"""
Chinese Remainder Theorem — Key Splitting
==========================================
Used in ChaosCrypt to distribute the PRNG seed across multiple residues.

A secret value k split under moduli [m1, …, mn] produces shares
[k mod m1, …, k mod mn].  Any holder of all shares can reconstruct k
via CRT; partial knowledge of shares does not reveal k, provided the
product M = ∏mᵢ exceeds k.

This implements a simple (n-of-n) threshold scheme: all shares are
required for reconstruction.

Reference: Hardy & Wright (1979). An Introduction to the Theory of Numbers.
"""

from functools import reduce


def _extended_gcd(a, b):
    """Extended Euclidean Algorithm: returns (gcd, x, y) where a·x + b·y = gcd."""
    if a == 0:
        return b, 0, 1
    gcd, x1, y1 = _extended_gcd(b % a, a)
    return gcd, y1 - (b // a) * x1, x1


def _mod_inverse(a, m):
    """
    Modular multiplicative inverse of a mod m.

    Raises ValueError if gcd(a, m) ≠ 1 (inverse does not exist).
    """
    gcd, x, _ = _extended_gcd(a % m, m)
    if gcd != 1:
        raise ValueError(f"Modular inverse does not exist: gcd({a}, {m}) = {gcd}")
    return x % m


def crt_split_key(value, moduli):
    """
    Express value as CRT residues (secret shares).

    Parameters
    ----------
    value  : int       — integer to split (e.g. PRNG seed)
    moduli : list[int] — pairwise-coprime moduli; their product must exceed value

    Returns
    -------
    list[int]  — residues [value mod m1, …, value mod mn]
    """
    return [value % m for m in moduli]


def crt_reconstruct(residues, moduli):
    """
    Reconstruct an integer from its CRT residues.

    Solves the system  x ≡ rᵢ (mod mᵢ)  for all i,
    returning the unique solution in [0, M) where M = ∏mᵢ.

    Parameters
    ----------
    residues : list[int] — remainders [r1, …, rn]
    moduli   : list[int] — pairwise-coprime moduli [m1, …, mn]

    Returns
    -------
    (int, int)  — (solution x, product M)
    """
    M = reduce(lambda a, b: a * b, moduli)
    x = 0
    for r_i, m_i in zip(residues, moduli):
        M_i = M // m_i
        x += r_i * _mod_inverse(M_i, m_i) * M_i
    return x % M, M
