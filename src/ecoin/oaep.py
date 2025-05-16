"""
Produces a two ways chaotic function.

f(M, r):
1. Compute $𝑋 = 𝑀 ⊕ G(𝑟)$
2. Compute $𝑌 = 𝑟 ⊕ H(𝑋)$
3.  Return (𝑋,𝑌)

f(x, y):
1. Compute $𝑟 = 𝑌 ⊕ H(𝑋)$
2. Compute $𝑀 = 𝑋 ⊕ G(𝑟)
3. Return (𝑀,𝑟)

We use SHAKE256 as a Hash function.
"""

from Crypto.Hash import SHAKE256
import operator


def enc(m: bytes, r: bytes) -> tuple[bytes, bytes]:
    xof = SHAKE256.new(r)
    gr = xof.read(len(m))
    x = bytes(map(operator.xor, m, gr))
    xof = SHAKE256.new(x)
    hx = xof.read(len(r))
    y = bytes(map(operator.xor, r, hx))
    return (x, y)  # NOTE: x is m bytes, y is r bytes


def dec(x: bytes, y: bytes) -> tuple[bytes, bytes]:
    xof = SHAKE256.new(x)
    hx = xof.read(len(y))
    r = bytes(map(operator.xor, y, hx))
    xof = SHAKE256.new(r)
    gr = xof.read(len(x))
    m = bytes(map(operator.xor, x, gr))
    return (m, r)
