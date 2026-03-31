"""
Run the ChaosCrypt demo:  python -m chaoscrypt
"""

from .cipher import encrypt, decrypt
from .cantor import encode_message
from .crt    import crt_reconstruct
from .prng   import middle_square_lcg


def main():
    print("=" * 60)
    print("  ChaosCrypt — Educational Hybrid Cipher Demo")
    print("=" * 60)

    # ── Key ────────────────────────────────────────────────────────
    seed = 1729   # Ramanujan number — a nod to number theory
    a, b, m = 113, 697, 65536

    # Pairwise-coprime moduli; product = 255255 > 9999 so seed is recoverable
    crt_moduli = [3, 5, 7, 11, 13, 17]

    plaintext = "Hello, ChaosCrypt!"

    print(f"\n[KEY]")
    print(f"  seed = {seed},  a = {a},  b = {b},  m = {m}")
    print(f"  CRT moduli = {crt_moduli}")

    # ── Encryption ─────────────────────────────────────────────────
    result = encrypt(plaintext, seed, a, b, m, split_moduli=crt_moduli)

    print(f"\n[PLAINTEXT]\n  {plaintext!r}")

    blocks, _ = encode_message(plaintext)
    print(f"\n[CANTOR-ENCODED BLOCKS]\n  {blocks}")

    ks = middle_square_lcg(seed, a, b, m, len(blocks))
    print(f"\n[KEYSTREAM]\n  {ks}")

    print(f"\n[CIPHERTEXT  (Cantor blocks XOR keystream)]\n  {result['ciphertext']}")

    print(f"\n[CRT KEY SHARES]")
    for mod, share in zip(crt_moduli, result['crt_shares']):
        print(f"  {seed} mod {mod:2d}  =  {share}")

    # ── Key reconstruction via CRT ─────────────────────────────────
    recovered_seed, M = crt_reconstruct(result['crt_shares'], crt_moduli)
    print(f"\n[CRT RECONSTRUCTION]\n  Recovered seed = {recovered_seed}  (product M = {M})")

    # ── Decryption ─────────────────────────────────────────────────
    recovered = decrypt(result['ciphertext'], result['original_length'],
                        recovered_seed, a, b, m)

    print(f"\n[DECRYPTED]\n  {recovered!r}")
    print(f"\n[MATCH] {'OK — Success' if recovered == plaintext else 'FAIL — Mismatch'}")
    print("=" * 60)


if __name__ == '__main__':
    main()
