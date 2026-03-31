"""
Middle-Square + LCG Hybrid PRNG
================================
Keystream generator for the ChaosCrypt cipher.

The Middle-Square method (von Neumann, 1949) squares the current value
and extracts the middle 4 digits of the 8-digit result.  Its well-known
failure mode is collapse to zero; the Linear Congruential Generator (LCG)
acts as a rescue mechanism and cycle-escape mechanism.
"""


def _lcg_step(x, a, b, m):
    """One LCG step: x_{n+1} = (a·x + b) mod m."""
    return (a * x + b) % m


def middle_square_lcg(seed, a, b, m, n):
    """
    Generate a keystream of n integers.

    Parameters
    ----------
    seed : int  — 4-digit starting seed (1000–9999)
    a    : int  — LCG multiplier
    b    : int  — LCG increment (must be > 0)
    m    : int  — LCG modulus (must be > 2^12 = 4096)
    n    : int  — number of values to generate

    Returns
    -------
    list[int] of length n
    """
    sequence = []
    number = seed
    seen = set()

    while len(sequence) < n:
        # Cycle detected — escape via LCG and reset tracker
        if number in seen:
            number = _lcg_step(number, a, b, m)
            seen.clear()

        seen.add(number)
        sequence.append(number)

        # Middle-Square step: square, zero-pad to 8 digits, take positions [2:6]
        number = int(str(number * number).zfill(8)[2:6])

        # Zero-collapse guard
        if number == 0:
            number = _lcg_step(0, a, b, m)

    return sequence
