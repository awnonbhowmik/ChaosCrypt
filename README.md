# ChaosCrypt

**Teaching Stream Cipher Failure Modes with Classical Number-Theoretic Primitives**

> An intentionally insecure educational stream cipher that combines the Middle-Square PRNG,
> the Cantor Pairing Function, and the Chinese Remainder Theorem to demonstrate classical
> cryptographic failure modes in a single, self-contained Python package.

---

## Overview

ChaosCrypt is an **educational tool**, not a security primitive. It is designed to help students
and practitioners understand:

- Why a short-period PRNG makes a stream cipher trivially breakable via known-plaintext attack (KPA)
- How a non-uniform keystream fails a chi-squared uniformity test
- Why weak diffusion means a 1-bit key change propagates poorly (violates the avalanche criterion)
- How the Chinese Remainder Theorem can be used for *n*-of-*n* threshold key splitting

The cipher pipeline is:

```
Plaintext  →  Cantor Pairing (encode chars to integers)
           →  Middle-Square + LCG keystream XOR  (encrypt)
           →  CRT key splitting  (share the seed)
```

## Repository Structure

```
ChaosCrypt/
├── chaoscrypt/          # Python package
│   ├── __init__.py      # Public API
│   ├── __main__.py      # Demo: python -m chaoscrypt
│   ├── cipher.py        # encrypt() / decrypt()
│   ├── cantor.py        # Cantor pairing encode/decode
│   ├── crt.py           # CRT key split / reconstruct
│   └── prng.py          # Middle-Square + LCG keystream
├── analysis.py          # Four security-failure experiments
├── figures.py           # Generate journal-quality PDF figures
├── figures/             # Output directory for figures
│   ├── keystream_uniformity.pdf
│   ├── period_distribution.pdf
│   └── avalanche.pdf
├── paper/               # LaTeX source for the arXiv paper
│   ├── main.tex
│   ├── refs.bib
│   ├── PRIMEarxiv.sty
│   └── chaoscrypt_arxiv.zip   # Submission-ready archive
└── requirements.txt
```

## Installation

```bash
git clone https://github.com/awnonbhowmik/ChaosCrypt.git
cd ChaosCrypt
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Quick demo

```bash
python -m chaoscrypt
```

### Python API

```python
from chaoscrypt import encrypt, decrypt

result  = encrypt("Hello, ChaosCrypt!", seed=1729)
plaintext = decrypt(
    result["ciphertext"],
    result["original_length"],
    seed=1729,
)
print(plaintext)  # Hello, ChaosCrypt!
```

### CRT key splitting

```python
from chaoscrypt import crt_split_key, crt_reconstruct

shares, moduli = crt_split_key(1729, n=3)
recovered_seed  = crt_reconstruct(shares, moduli)
```

## Experiments

Run all four security-failure analyses:

```bash
python analysis.py
```

Experiments performed:

| # | Experiment | What it shows |
|---|-----------|---------------|
| 1 | Period survey | Most seeds cycle with λ ≤ 50; 4.8 % are fixed points (λ = 1) |
| 2 | Keystream uniformity | χ² = 2299 (9 d.f.), p ≈ 0 — far from uniform |
| 3 | Known-plaintext attack | Full keystream recovered with one plaintext–ciphertext pair |
| 4 | Avalanche / diffusion | Mean bit-flip fraction ≈ 0.21, well below the ideal 0.50 |

## Figures

Generate all figures (saved as PDFs to `figures/`):

```bash
python figures.py
```

## Paper

The accompanying paper is available in `paper/` and on arXiv:

> Awnon Bhowmik. *Teaching Stream Cipher Failure Modes with Classical
> Number-Theoretic Primitives.* 2025.

To compile the paper locally (requires a TeX Live installation):

```bash
cd paper
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

The file `paper/chaoscrypt_arxiv.zip` is ready for direct upload to arXiv.

## ⚠ Security Warning

**Do not use ChaosCrypt to protect real data.** It is broken by design:

- The Middle-Square PRNG has a maximum period of 50 for 4-digit seeds with the default parameters.
- A known-plaintext attack recovers the keystream immediately.
- The keystream is highly non-uniform.
- Seed diffusion is poor.

## License

MIT License — see [LICENSE](LICENSE) for details.

## Author

Awnon Bhowmik — [awnonbhowmik@outlook.com](mailto:awnonbhowmik@outlook.com)  
GitHub: [https://github.com/awnonbhowmik/ChaosCrypt](https://github.com/awnonbhowmik/ChaosCrypt)
