import numpy as np
from sbox_data import AES_SBOX

# S-box Construction Constants
AES_MODULUS = 0x11B  # x^8 + x^4 + x^3 + x + 1
AES_CONSTANT = 0x63

def gf_inv(a):
    """Calculates multiplicative inverse in GF(2^8) with AES modulus."""
    if a == 0:
        return 0
    # Extended Euclidean Algorithm
    b = AES_MODULUS
    x0, x1 = 0, 1
    # We need to treat these as polynomials over GF(2).
    # Since we don't have a library like pyfinite easily available without pip,
    # we'll use a pre-computed inverse table for performance and reliability,
    # OR implement a table generator. The table is static for AES GF field.
    return _INV_TABLE[a]

def _generate_inv_table():
    # Brute force or efficient generation
    # Since AES uses a specific field, we can use the exponent/log tables method 
    # or just brute force finding x such that (a * x) % mod == 1 in GF(2)
    # Actually, for 256 values, a simple generator is fast enough.
    inv = [0] * 256
    # 0 maps to 0
    for i in range(1, 256):
        for j in range(1, 256):
            if _gf_mult(i, j) == 1:
                inv[i] = j
                break
    return inv

def _gf_mult(a, b):
    # GF(2^8) multiplication
    p = 0
    mod = 0x11B
    for _ in range(8):
        if b & 1:
            p ^= a
        if a & 0x80:
            a = (a << 1) ^ mod
        else:
            a <<= 1
        b >>= 1
    return p & 0xFF

# Cache the inverse table
_INV_TABLE = _generate_inv_table()

def generate_random_affine_matrix():
    """Generates a random 8x8 invertible binary matrix."""
    while True:
        # Generate random 8x8 matrix (entries 0 or 1)
        matrix = np.random.randint(0, 2, size=(8, 8), dtype=int)
        
        # Check determinant in GF(2)
        # Det must be odd (1) for invertibility in GF(2)
        det = int(np.round(np.linalg.det(matrix))) % 2
        if det == 1:
            return matrix

def affine_transform(byte_val, matrix, constant=0x63):
    """Applies affine transformation: A*x + c."""
    # Convert byte to bit vector (LSB first or MSB first? AES usually treats LSB as top in polynomial, 
    # but standard vector notation treats index 0. 
    # AES S-box def: b' = M * b + c.
    # We will assume column vector convention used in standard AES literature.
    
    # Get bits: [b0, b1, ... b7]
    bits = [(byte_val >> i) & 1 for i in range(8)]
    
    # Matrix multiply
    # result_bits[i] = XOR( matrix[i][j] * bits[j] )
    new_bits = [0] * 8
    for i in range(8):
        acc = 0
        for j in range(8):
            acc ^= (matrix[i][j] & bits[j])
        
        # Add constant part
        c_bit = (constant >> i) & 1
        new_bits[i] = acc ^ c_bit
        
    # Reconstruct byte
    res = 0
    for i in range(8):
        res |= (new_bits[i] << i)
    return res

def generate_sbox_from_matrix(matrix):
    """Generates an S-box using the provided affine matrix."""
    sbox = [0] * 256
    for x in range(256):
        # 1. Multiplicative Inverse
        inv_x = gf_inv(x)
        # 2. Affine Transformation
        s_val = affine_transform(inv_x, matrix)
        sbox[x] = s_val
    return sbox

def generate_affine_sbox():
    """
    Wrapper to generate a random valid affine S-box.
    Returns: (sbox_list, matrix_numpy)
    """
    matrix = generate_random_affine_matrix()
    sbox = generate_sbox_from_matrix(matrix)
    return sbox, matrix
