import copy

class AES:
    def __init__(self, key, sbox):
        self.key = key
        self.sbox = sbox
        self.nb = 4  # Number of columns (32-bit words) comprising the State. For AES-128, Nb = 4.
        self.nk = 4  # Number of 32-bit words comprising the Cipher Key. For AES-128, Nk = 4.
        self.nr = 10 # Number of rounds. For AES-128, Nr = 10.
        self.r_con = [
            0x00, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40,
            0x80, 0x1B, 0x36
        ]
        self.round_keys = self._key_expansion()

    def _sub_word(self, word):
        return [self.sbox[b] for b in word]

    def _rot_word(self, word):
        return word[1:] + word[:1]

    def _key_expansion(self):
        key_symbols = [b for b in self.key]
        w = [key_symbols[i:i+4] for i in range(0, len(key_symbols), 4)]

        for i in range(self.nk, self.nb * (self.nr + 1)):
            temp = w[i-1]
            if i % self.nk == 0:
                temp = self._sub_word(self._rot_word(temp))
                temp[0] = temp[0] ^ self.r_con[i // self.nk]
            
            w.append([a ^ b for a, b in zip(w[i-self.nk], temp)])
        
        # In this implementation, round_keys is a list of 4x4 matrices (list of lists)
        # However, for simplicity in add_round_key, let's keep it as flat list of words or convert later.
        # Actually, let's format it as a list of states (4x4 matrices)
        round_keys = []
        for i in range(0, len(w), 4):
            round_key = []
            # Transpose to get 4x4 column-major matrix state
            for row in range(4):
                round_key.append([w[i+col][row] for col in range(4)])
            round_keys.append(round_key)
        return round_keys

    def _sub_bytes(self, state):
        for r in range(4):
            for c in range(4):
                state[r][c] = self.sbox[state[r][c]]
        return state

    def _shift_rows(self, state):
        state[1] = state[1][1:] + state[1][:1]
        state[2] = state[2][2:] + state[2][:2]
        state[3] = state[3][3:] + state[3][:3]
        return state

    def _gmul(self, a, b):
        p = 0
        for _ in range(8):
            if b & 1:
                p ^= a
            hi_bit_set = a & 0x80
            a <<= 1
            if hi_bit_set:
                a ^= 0x1b
            b >>= 1
        return p & 0xFF

    def _mix_single_column(self, col):
        t = col[0] ^ col[1] ^ col[2] ^ col[3]
        u = col[0]
        col[0] ^= t ^ self._gmul(col[0] ^ col[1], 2)
        col[1] ^= t ^ self._gmul(col[1] ^ col[2], 2)
        col[2] ^= t ^ self._gmul(col[2] ^ col[3], 2)
        col[3] ^= t ^ self._gmul(col[3] ^ u, 2)
        return col

    def _mix_columns(self, state):
        for i in range(4):
            # Extract column
            col = [state[r][i] for r in range(4)]
            # Mix
            col = self._mix_single_column(col)
            # Put back
            for r in range(4):
                state[r][i] = col[r]
        return state

    def _add_round_key(self, state, round_idx):
        mk = self.round_keys[round_idx]
        for r in range(4):
            for c in range(4):
                state[r][c] ^= mk[r][c]
        return state

    def encrypt_block(self, plaintext):
        # Plaintext must be 16 bytes.
        # Initialize state as 4x4 matrix, column major
        state = [[0]*4 for _ in range(4)]
        for r in range(4):
            for c in range(4):
                state[r][c] = plaintext[r + 4*c]

        state = self._add_round_key(state, 0)

        for round in range(1, self.nr):
            state = self._sub_bytes(state)
            state = self._shift_rows(state)
            state = self._mix_columns(state)
            state = self._add_round_key(state, round)

        state = self._sub_bytes(state)
        state = self._shift_rows(state)
        state = self._add_round_key(state, self.nr)

        # Convert state back to list
        output = []
        for c in range(4):
            for r in range(4):
                output.append(state[r][c])
        return output

    # --- Decryption Primitives ---
    
    def _inv_sub_bytes(self, state):
        # Generate inverse sbox lazily or on init. 
        # For efficiency in this specific requested flow, we'll generate it here or pass it.
        # But better to have it in init if we were doing this properly. 
        # Given the constraints, let's generate it in __init__? 
        # No, let's generate it just-in-time or helper. 
        # Actually proper design: generate in __init__.
        # But since I can't easily change __init__ without replacing the whole file, I will generate it here.
        inv_sbox = [0] * 256
        for i, val in enumerate(self.sbox):
            inv_sbox[val] = i
            
        for r in range(4):
            for c in range(4):
                state[r][c] = inv_sbox[state[r][c]]
        return state

    def _inv_shift_rows(self, state):
        state[1] = state[1][-1:] + state[1][:-1]
        state[2] = state[2][-2:] + state[2][:-2]
        state[3] = state[3][-3:] + state[3][:-3]
        return state

    def _inv_mix_single_column(self, col):
        # Multipliers: 0e, 0b, 0d, 09
        # 14, 11, 13, 9
        u = self._gmul(col[0], 0x0e) ^ self._gmul(col[1], 0x0b) ^ self._gmul(col[2], 0x0d) ^ self._gmul(col[3], 0x09)
        v = self._gmul(col[0], 0x09) ^ self._gmul(col[1], 0x0e) ^ self._gmul(col[2], 0x0b) ^ self._gmul(col[3], 0x0d)
        w = self._gmul(col[0], 0x0d) ^ self._gmul(col[1], 0x09) ^ self._gmul(col[2], 0x0e) ^ self._gmul(col[3], 0x0b)
        x = self._gmul(col[0], 0x0b) ^ self._gmul(col[1], 0x0d) ^ self._gmul(col[2], 0x09) ^ self._gmul(col[3], 0x0e)
        return [u, v, w, x]

    def _inv_mix_columns(self, state):
        for i in range(4):
            col = [state[r][i] for r in range(4)]
            col = self._inv_mix_single_column(col)
            for r in range(4):
                state[r][i] = col[r]
        return state

    def decrypt_block(self, ciphertext):
        # Standard Inverse Cipher
        state = [[0]*4 for _ in range(4)]
        for r in range(4):
            for c in range(4):
                state[r][c] = ciphertext[r + 4*c]

        state = self._add_round_key(state, self.nr)
        
        state = self._inv_shift_rows(state)
        state = self._inv_sub_bytes(state)

        for round in range(self.nr - 1, 0, -1):
            state = self._add_round_key(state, round)
            state = self._inv_mix_columns(state)
            state = self._inv_shift_rows(state)
            state = self._inv_sub_bytes(state)

        state = self._add_round_key(state, 0)

        output = []
        for c in range(4):
            for r in range(4):
                output.append(state[r][c])
        return output

def process_key(user_input):
    """
    Ensures key is exactly 16 bytes.
    - If < 16: Pads with '0' (0x30).
    - If > 16: Truncates.
    """
    if isinstance(user_input, str):
        key_bytes = user_input.encode('utf-8')
    else:
        key_bytes = user_input
        
    if len(key_bytes) < 16:
        # Pad with '0' character bytes
        key_bytes += b'0' * (16 - len(key_bytes))
    elif len(key_bytes) > 16:
        key_bytes = key_bytes[:16]
        
    return key_bytes

def encrypt_text(text, key, sbox):
    key = process_key(key)
    # PKCS7 Padding
    pad_len = 16 - (len(text) % 16)
    padded_text = text + bytes([pad_len] * pad_len)
    
    aes = AES(key, sbox)
    encrypted = []
    
    for i in range(0, len(padded_text), 16):
        block = list(padded_text[i:i+16])
        encrypted_block = aes.encrypt_block(block)
        encrypted.extend(encrypted_block)
        
    return bytes(encrypted)

def decrypt_text(encrypted_bytes, key, sbox):
    key = process_key(key)
    aes = AES(key, sbox)
    decrypted = []
    
    for i in range(0, len(encrypted_bytes), 16):
        block = list(encrypted_bytes[i:i+16])
        decrypted_block = aes.decrypt_block(block)
        decrypted.extend(decrypted_block)
        
    # Remove PKCS7 Padding
    decrypted_bytes = bytes(decrypted)
    pad_len = decrypted_bytes[-1]
    # Basic validation of padding
    if pad_len < 1 or pad_len > 16:
        # In case of wrong key or sbox, padding might be garbage.
        # Ensure we don't crash, just return raw or empty?
        # Let's return raw if padding looks wrong, or try to strip.
        return decrypted_bytes
    
    # Check if all padding bytes are correct
    if decrypted_bytes[-pad_len:] == bytes([pad_len] * pad_len):
        return decrypted_bytes[:-pad_len]
    else:
        return decrypted_bytes

def encrypt_image(image_bytes, key, sbox):
    key = process_key(key)
    # Treat image bytes as a stream.
    pad_len = 16 - (len(image_bytes) % 16)
    padded_image = image_bytes + bytes([pad_len] * pad_len)
    
    aes = AES(key, sbox)
    encrypted = bytearray()
    
    for i in range(0, len(padded_image), 16):
        block = list(padded_image[i:i+16])
        encrypted_block = aes.encrypt_block(block)
        encrypted.extend(encrypted_block)
        
    return bytes(encrypted)

def decrypt_image(encrypted_bytes, key, sbox):
    key = process_key(key)
    aes = AES(key, sbox)
    decrypted = bytearray()
    
    for i in range(0, len(encrypted_bytes), 16):
        block = list(encrypted_bytes[i:i+16])
        decrypted_block = aes.decrypt_block(block)
        decrypted.extend(decrypted_block)
        
    # Strip PKCS7 padding
    # Note: For image demo we added padding, so we should remove it to get exact original file bytes.
    output = bytes(decrypted)
    pad_len = output[-1]
    if 1 <= pad_len <= 16 and output[-pad_len:] == bytes([pad_len] * pad_len):
        return output[:-pad_len]
    return output
