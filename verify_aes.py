from sbox_data import AES_SBOX, SBOX_K44
from aes_engine import AES, encrypt_text
import binascii

def test_aes_engine():
    key = b'1234567890123456'
    plaintext = b'Hello World! 123' # 16 bytes exactly suitable for single block test without padding logic dependency in encrypt_block, but encrypt_text handles padding.

    print("Testing Standard AES S-box...")
    idx1 = encrypt_text(plaintext, key, AES_SBOX)
    print(f"Ciphertext (Standard): {binascii.hexlify(idx1)}")

    print("\nTesting Proposed S-box K44...")
    idx2 = encrypt_text(plaintext, key, SBOX_K44)
    print(f"Ciphertext (K44): {binascii.hexlify(idx2)}")
    
    assert idx1 != idx2, "Ciphertexts should differ with different S-boxes!"
    print("\nSUCCESS: S-boxes produced different outputs.")

if __name__ == "__main__":
    test_aes_engine()
