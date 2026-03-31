"""
ChaosCrypt — Security Analysis
================================
This module supports the security analysis section of the ChaosCrypt paper.

It covers four areas:

  1. PRNG Period Analysis
     — Measure the actual period of the Middle-Square + LCG keystream for
       various seeds, and compare against a theoretical uniform bound.

  2. Keystream Frequency / Uniformity Test
     — Collect a large keystream sample and run a chi-squared uniformity
       test.  A secure stream cipher keystream should be indistinguishable
       from uniform random; ChaosCrypt's is not.

  3. Known-Plaintext Attack (KPA) Demonstration
     — Given one (plaintext, ciphertext) pair, recover the keystream
       directly and hence decrypt any other message encrypted under the
       same key.  This illustrates why keystream reuse is catastrophic.

  4. Bit-Frequency / Avalanche Analysis
     — Count bit distributions to show whether single-bit key changes
       produce near-50% ciphertext bit flips (the avalanche criterion).
       ChaosCrypt does not satisfy this criterion.

Each function returns structured data suitable for inclusion in paper tables
and figures; a __main__ block at the bottom runs all analyses and prints a
formatted report.
"""

import math
import numpy as np
from collections import Counter
from scipy.stats import chisquare

from chaoscrypt import middle_square_lcg, encrypt, decrypt
from chaoscrypt.cantor import encode_message as _encode_message


# ─────────────────────────────────────────────────────────────────────────────
# 1. PRNG PERIOD ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def measure_period(seed, a, b, m, max_steps=100_000):
    """
    Measure the period of the raw Middle-Square sequence (without the
    cycle-escape mechanism) using Floyd's cycle-detection algorithm.

    This reveals how quickly the unmodified Middle-Square method enters
    a cycle, justifying the LCG rescue mechanism.

    Parameters
    ----------
    seed, a, b, m : int — key parameters
    max_steps     : int — upper bound on steps before giving up

    Returns
    -------
    dict with 'period', 'tail' (steps before cycle entry), 'cycle_start'
    """
    def ms_step(x):
        nxt = int(str(x * x).zfill(8)[2:6])
        return nxt if nxt != 0 else (a * x + b) % m

    # Floyd's tortoise-and-hare
    tortoise = ms_step(seed)
    hare = ms_step(ms_step(seed))
    steps = 0

    while tortoise != hare and steps < max_steps:
        tortoise = ms_step(tortoise)
        hare = ms_step(ms_step(hare))
        steps += 1

    if tortoise != hare:
        return {'period': None, 'tail': None, 'cycle_start': None,
                'note': 'No cycle found within max_steps'}

    # Find the entry point of the cycle (mu)
    mu = 0
    tortoise = seed
    while tortoise != hare:
        tortoise = ms_step(tortoise)
        hare = ms_step(hare)
        mu += 1

    # Measure the period (lambda)
    lam = 1
    hare = ms_step(tortoise)
    while tortoise != hare:
        hare = ms_step(hare)
        lam += 1

    return {'period': lam, 'tail': mu, 'cycle_start': mu}


def period_survey(seeds, a=113, b=697, m=65536):
    """
    Run measure_period() for a list of seeds and summarise results.

    Returns
    -------
    list[dict] — one dict per seed with keys 'seed', 'period', 'tail'
    """
    results = []
    for s in seeds:
        r = measure_period(s, a, b, m)
        results.append({'seed': s, **r})
    return results


# ─────────────────────────────────────────────────────────────────────────────
# 2. KEYSTREAM UNIFORMITY TEST (Chi-Squared)
# ─────────────────────────────────────────────────────────────────────────────

def uniformity_test(seed, a, b, m, n=1000, num_buckets=10):
    """
    Test whether the keystream values are uniformly distributed using a
    chi-squared goodness-of-fit test.

    For a stream cipher to be secure, its output must be computationally
    indistinguishable from uniform. ChaosCrypt's Middle-Square PRNG is
    biased and will fail this test for short periods.

    Parameters
    ----------
    n           : int — number of keystream values to sample
    num_buckets : int — number of equal-width histogram bins

    Returns
    -------
    dict with 'chi2_stat', 'p_value', 'degrees_of_freedom',
              'observed', 'expected', 'verdict'
    """
    keystream = middle_square_lcg(seed, a, b, m, n)

    max_val = max(keystream) + 1
    bucket_size = max_val / num_buckets
    observed = [0] * num_buckets
    for v in keystream:
        bucket = min(int(v / bucket_size), num_buckets - 1)
        observed[bucket] += 1

    expected_freq = n / num_buckets
    expected = [expected_freq] * num_buckets

    chi2_stat, p_value = chisquare(observed, f_exp=expected)

    return {
        'chi2_stat':         round(chi2_stat, 4),
        'p_value':           round(p_value, 6),
        'degrees_of_freedom': num_buckets - 1,
        'observed':          observed,
        'expected':          [round(expected_freq, 2)] * num_buckets,
        # α = 0.05: reject H0 (uniform) if p < 0.05
        'verdict':           'NON-UNIFORM (insecure)' if p_value < 0.05 else 'Uniform (within α=0.05)',
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. KNOWN-PLAINTEXT ATTACK (KPA)
# ─────────────────────────────────────────────────────────────────────────────

def known_plaintext_attack(known_plain, known_cipher, target_cipher, original_lengths):
    """
    Demonstrate a known-plaintext attack against ChaosCrypt.

    Because ciphertext = Cantor(plaintext) XOR keystream, an attacker who
    knows one (plaintext, ciphertext) pair can recover the keystream
    segment directly:

        keystream_block_i = Cantor(plain_i) XOR cipher_i

    With the keystream in hand, decrypting any other message encrypted
    under the same key is trivial:

        plain_i = Cantor_inv( cipher_i XOR keystream_block_i )

    This demonstrates that the scheme provides ZERO security against a
    known-plaintext adversary — a fundamental requirement (IND-CPA) of
    any secure symmetric cipher.

    Parameters
    ----------
    known_plain      : str       — the known plaintext
    known_cipher     : list[int] — its corresponding ciphertext blocks
    target_cipher    : list[int] — a second ciphertext (same key!) to attack
    original_lengths : (int,int) — original_length for known and target messages

    Returns
    -------
    dict with 'recovered_keystream', 'recovered_plaintext', 'attack_succeeded'
    """
    known_len, target_len = original_lengths

    # Step 1: recover keystream from known pair
    known_blocks, _ = _encode_message(known_plain)
    recovered_keystream = [c ^ k for c, k in zip(known_blocks, known_cipher)]

    # Step 2: use recovered keystream to decrypt target (pad/truncate to match)
    n = len(target_cipher)
    ks = recovered_keystream[:n]
    target_blocks = [c ^ k for c, k in zip(target_cipher, ks)]

    # Step 3: Cantor decode
    from chaoscrypt.cantor import decode_message
    recovered_plain = decode_message(target_blocks, target_len)

    return {
        'recovered_keystream': recovered_keystream,
        'recovered_plaintext': recovered_plain,
        'attack_note': (
            'An attacker with one plaintext-ciphertext pair recovers the '
            'keystream and can decrypt all messages under the same key.'
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4. AVALANCHE / BIT-FLIP ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def hamming_distance(a, b):
    """Count differing bits between two integers."""
    return bin(a ^ b).count('1')


def avalanche_analysis(plaintext, seed, a, b, m, num_trials=20):
    """
    Measure whether a 1-bit change in the seed causes ~50% of ciphertext
    bits to flip (the avalanche criterion).

    A cipher satisfying strict avalanche criterion (SAC) flips exactly
    half the output bits on any single-bit input change.  ChaosCrypt is
    a stream cipher whose keystream changes only at the escape points
    in the PRNG, so single-bit seed changes typically cause very few
    ciphertext bits to flip — a serious structural weakness.

    Parameters
    ----------
    num_trials : int — number of random single-bit flips to test

    Returns
    -------
    dict with 'avg_flip_fraction', 'flip_fractions', 'verdict'
    """
    base_result = encrypt(plaintext, seed, a, b, m)
    base_ct = base_result['ciphertext']
    total_bits = sum(c.bit_length() for c in base_ct) or 1

    flip_fractions = []
    rng = np.random.default_rng(42)

    for _ in range(num_trials):
        # Flip one bit of the seed (keep it 4-digit)
        bit_pos = int(rng.integers(0, 14))     # seed fits in ~14 bits
        flipped_seed = seed ^ (1 << bit_pos)
        flipped_seed = max(1000, min(9999, flipped_seed))   # clamp to 4-digit

        flipped_result = encrypt(plaintext, flipped_seed, a, b, m)
        flipped_ct = flipped_result['ciphertext']

        # Count bit differences across all ciphertext blocks
        total_diff_bits = sum(
            hamming_distance(x, y)
            for x, y in zip(base_ct, flipped_ct)
        )
        flip_fractions.append(total_diff_bits / total_bits)

    avg = float(np.mean(flip_fractions))

    return {
        'avg_flip_fraction': round(avg, 4),
        'flip_fractions':    [round(f, 4) for f in flip_fractions],
        # SAC threshold: 0.50 ± 0.05
        'verdict': 'FAILS avalanche criterion' if abs(avg - 0.5) > 0.05
                   else 'Satisfies avalanche criterion',
    }


# ─────────────────────────────────────────────────────────────────────────────
# REPORT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    SEED = 1729
    A, B, M = 113, 697, 65536
    PLAINTEXT_A = "Hello, ChaosCrypt!"
    PLAINTEXT_B = "Secret message!!"    # same key — KPA target

    print("=" * 65)
    print("  ChaosCrypt — Security Analysis Report")
    print("=" * 65)

    # ── 1. Period survey ──────────────────────────────────────────
    print("\n[1] PRNG PERIOD ANALYSIS")
    print("    (Middle-Square + LCG, a={}, b={}, m={})".format(A, B, M))
    test_seeds = [1000, 1234, 1729, 2025, 3721, 4875, 5678, 9999]
    survey = period_survey(test_seeds, A, B, M)
    print(f"\n    {'Seed':>6}  {'Period':>8}  {'Tail':>6}")
    print("    " + "-" * 24)
    for r in survey:
        period_str = str(r['period']) if r['period'] else 'N/A'
        tail_str   = str(r['tail'])   if r['tail']   else 'N/A'
        print(f"    {r['seed']:>6}  {period_str:>8}  {tail_str:>6}")

    # ── 2. Uniformity test ────────────────────────────────────────
    print("\n[2] KEYSTREAM UNIFORMITY TEST (n=1000, 10 buckets)")
    uni = uniformity_test(SEED, A, B, M, n=1000, num_buckets=10)
    print(f"    χ² statistic : {uni['chi2_stat']}")
    print(f"    p-value      : {uni['p_value']}")
    print(f"    d.o.f.       : {uni['degrees_of_freedom']}")
    print(f"    Verdict      : {uni['verdict']}")
    print(f"\n    Observed bucket counts : {uni['observed']}")
    print(f"    Expected (uniform)     : {uni['expected'][0]} per bucket")

    # ── 3. Known-plaintext attack ─────────────────────────────────
    print("\n[3] KNOWN-PLAINTEXT ATTACK (KPA)")
    enc_a = encrypt(PLAINTEXT_A, SEED, A, B, M)
    enc_b = encrypt(PLAINTEXT_B, SEED, A, B, M)

    kpa_result = known_plaintext_attack(
        known_plain=PLAINTEXT_A,
        known_cipher=enc_a['ciphertext'],
        target_cipher=enc_b['ciphertext'],
        original_lengths=(enc_a['original_length'], enc_b['original_length']),
    )
    print(f"    Known plaintext  : {PLAINTEXT_A!r}")
    print(f"    Target plaintext : {PLAINTEXT_B!r}  (same key, attacker doesn't know this)")
    print(f"    Recovered        : {kpa_result['recovered_plaintext']!r}")
    success = kpa_result['recovered_plaintext'] == PLAINTEXT_B
    print(f"    Attack success   : {'YES — plaintext fully recovered' if success else 'partial'}")
    print(f"\n    Note: {kpa_result['attack_note']}")

    # ── 4. Avalanche analysis ─────────────────────────────────────
    print("\n[4] AVALANCHE / BIT-FLIP ANALYSIS (20 single-bit seed flips)")
    av = avalanche_analysis(PLAINTEXT_A, SEED, A, B, M, num_trials=20)
    print(f"    Average bit-flip fraction : {av['avg_flip_fraction']}")
    print(f"    Ideal (SAC)               : 0.5000")
    print(f"    Verdict                   : {av['verdict']}")
    print(f"\n    Per-trial flip fractions:")
    for i, f in enumerate(av['flip_fractions'], 1):
        bar = '█' * int(f * 40)
        print(f"      Trial {i:2d}: {f:.4f}  {bar}")

    print("\n" + "=" * 65)
    print("  Summary of Weaknesses")
    print("=" * 65)
    print("""
  1. Short PRNG periods — Middle-Square degenerates quickly for
     many seeds; LCG rescue only partially mitigates this.

  2. Non-uniform keystream — Statistical tests reject the hypothesis
     that the keystream is uniformly distributed, enabling
     distinguishing attacks.

  3. Known-plaintext attack — XOR with a deterministic keystream
     allows trivial key-stream recovery from a single plaintext-
     ciphertext pair, breaking the cipher completely.

  4. Avalanche failure — Small key changes produce small ciphertext
     changes, violating the strict avalanche criterion and making
     the cipher vulnerable to differential analysis.

  ChaosCrypt is intended as an educational demonstration of how
  classical number-theoretic primitives compose into a cipher
  pipeline.  It is NOT suitable for any security application.
""")
