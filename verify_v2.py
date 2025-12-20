from sbox_data import AES_SBOX, SBOX_K44
from aes_engine import AES, encrypt_text, decrypt_text, process_key
import binascii

def test_features():
    print("--- 1. Testing Key Processing ---")
    k1 = "short"
    k2 = "thiskeyiswaytoolongforaes128"
    pk1 = process_key(k1)
    pk2 = process_key(k2)
    print(f"Input: '{k1}' -> Key: {pk1}, Len: {len(pk1)}")
    print(f"Input: '{k2}' -> Key: {pk2}, Len: {len(pk2)}")
    assert len(pk1) == 16
    assert len(pk2) == 16
    assert pk1.endswith(b'0')

    print("\n--- 2. Testing Encryption & Decryption (Round Trip) ---")
    plaintext_str = "Selamat Pagi Dunia! Test K44."
    key_str = "kunci_rahasia_12" # 16 chars
    
    print(f"Plaintext: {plaintext_str}")
    
    # Encrypt
    cipher = encrypt_text(plaintext_str.encode('utf-8'), key_str, SBOX_K44)
    print(f"Ciphertext (Hex): {cipher.hex()}")
    
    # Decrypt
    decrypted_bytes = decrypt_text(cipher, key_str, SBOX_K44)
    decrypted_str = decrypted_bytes.decode('utf-8')
    print(f"Decrypted: {decrypted_str}")
    
    assert plaintext_str == decrypted_str, "Decryption failed to restore original text!"
    print("SUCCESS: Decryption verified.")

if __name__ == "__main__":
    test_features()
