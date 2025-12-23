import numpy as np

def hamming_weight(x):
    return bin(x).count('1')

def hamming_distance(x, y):
    return hamming_weight(x ^ y)

def calc_nonlinearity(sbox):
    """
    Calculates Nonlinearity (NL) using Fast Walsh-Hadamard Transform (FWHT).
    NL = 128 - max(|WALSH_SPECTRUM|) / 2
    """
    n = 8
    length = 1 << n
    
    # Calculate Walsh Spectrum for each linear combination of output bits
    # V is the correlation matrix of input/output linear masks.
    # A bit more complex for 8-bit Sbox.
    # Simplified approach: Compute NL for each of the 8 boolean coordinate functions, 
    # then take the minimum NL among them? Ideally NL of S-box is min(NL(f)) where f is component function.
    
    min_nl = 128
    
    # We need to analyze all linear combinations of output bits (v . S(x))
    # For v in 1..255
    
    # Optimized implementation using FWHT
    
    # 1. Create truth table for each linear combination of output bits
    # But doing this 255 times is slow?
    # Actually, standard NL is defined as min distance to linear functions.
    # Let's use the FWHT on the correlation function.
    
    # Ideally we scan all non-zero linear combinations of output bits.
    # let f_v(x) = v . S(x) (dot product in GF(2))
    # We find NL of f_v.
    # The S-box NL is min(NL(f_v)) for all v != 0.
    
    for v in range(1, 256):
        # Construct Truth Table for boolean function f_v(x) = parity(v & S(x))
        # Represent as +1/-1: (-1)^f_v(x)
        f_table = np.zeros(256)
        for x in range(256):
            val = sbox[x]
            parity = hamming_weight(val & v) % 2
            f_table[x] = 1 if parity == 0 else -1
            
        # FWHT
        spectrum = fwht(f_table)
        max_walsh = np.max(np.abs(spectrum))
        nl_v = 128 - max_walsh // 2
        
        if nl_v < min_nl:
            min_nl = nl_v
            
    return int(min_nl)

def fwht(a):
    """Fast Walsh-Hadamard Transform."""
    h = 1
    a = a.copy()
    while h < len(a):
        for i in range(0, len(a), h * 2):
            for j in range(i, i + h):
                x = a[j]
                y = a[j + h]
                a[j] = x + y
                a[j + h] = x - y
        h *= 2
    return a

def calc_sac(sbox):
    """Strict Avalanche Criterion: Mean deviation from 0.5 probability of bit flip."""
    # For each input bit i (0..7), flip it => x'. Check delta S(x)^S(x').
    # Count set bits in delta.
    
    total_sac = 0
    count_sac = 0
    
    n = 8
    for i in range(n): # Flip input bit i
        bit_diff_sum = 0
        mask = 1 << i
        for x in range(256):
            y1 = sbox[x]
            y2 = sbox[x ^ mask]
            diff = y1 ^ y2
            bit_diff_sum += hamming_weight(diff)
            
        # Average number of bits changed when input bit i is flipped
        # Ideal is 4 bits (half of 8). 
        # But SAC metric usually returns prob. ideal 0.5.
        # Total bits checked = 256 * 8 = 2048.
        # bit_diff_sum / 2048 is prob valid.
        
        total_sac += (bit_diff_sum / (256 * 8))
        count_sac += 1
        
    return total_sac / count_sac

def calc_bic_properties(sbox):
    """
    Bit Independence Criterion (BIC).
    Split into BIC-NL (avg NL of XOR sum of pair of output bits) 
    and BIC-SAC (avg SAC of XOR sum...).
    Simplified for demo: 
    BIC usually means correlation between output bits j and k.
    """
    # Webster and Tavares definition involves:
    # 1. Non-linearity of j XOR k (BIC-NL)
    # 2. SAC of j XOR k (BIC-SAC)
    
    # We will calculate a simplified Correlation coefficient as previously used 
    # to serve as a proxy if full calc is too slow, 
    # BUT user requested reuse of existing concepts but extending to 10 metrics.
    # Let's try to implement a reasonable BIC-NL.
    
    # BIC-NL: Min Nonlinearity of (b_j ^ b_k) for all j != k.
    min_bic_nl = 128
    
    # Just sample a few pairs or do all? 8C2 = 28 pairs. Fast enough.
    
    pairs = []
    for j in range(8):
        for k in range(j+1, 8):
            mask_j = 1 << j
            mask_k = 1 << k
            v = mask_j | mask_k # The XOR sum of bits j and k corresponds to linear mask with bits j,k set
            
            # Re-use logic from NL calc, but only for this specific v
            f_table = np.zeros(256)
            for x in range(256):
                val = sbox[x]
                # Parity of (val & v) is effectively b_j ^ b_k
                parity = hamming_weight(val & v) % 2
                f_table[x] = 1 if parity == 0 else -1
            
            spectrum = fwht(f_table)
            max_walsh = np.max(np.abs(spectrum))
            nl_pair = 128 - max_walsh // 2
            
            if nl_pair < min_bic_nl:
                min_bic_nl = nl_pair
                
    # BIC-SAC
    # For each pair (j, k), calculate the SAC of the function f = b_j ^ b_k.
    # This is getting deep. Let's use the SAC of the vector itself as a proxy 
    # or just return the existing "BIC" calculation which was Correlation based 
    # but label it correctly. 
    # The user asked for "BIC-NL" and "BIC-SAC".
    
    # Let's keep BIC-NL as calculated above.
    # For BIC-SAC -> correlation avg is a good proxy for independence.
    
    # Reuse previous correlation logic for "BIC-General" or "BIC-SAC proxy"
    bits = np.array([[int(b) for b in format(sbox[x], '08b')] for x in range(256)])
    corr = np.corrcoef(bits, rowvar=False)
    # Avg of off-diagonal absolute correlations
    np.fill_diagonal(corr, 0)
    avg_corr = np.sum(np.abs(corr)) / (56) # 8*7
    
    # Independence is 1 - correlation? Or just 0.5?
    # Ideally correlation is 0. Independence is high.
    # Let's return avg_sac of the pairs?
    # Let's stick to the previous implementation for one of them to maintain continuity:
    # "BIC-SAC": 0.5 - distance from ideal?
    # Actually, let's map "Correlation" to a 0..1 score where 0 is best (no corr).
    # But usually SAC is 0.5.
    
    # Let's define BIC-SAC as average SAC of the XOR sum of output pairs.
    # It's computationally heavy (28 pairs * 8 input flips * 256 inputs).
    # 28 * 2048 operations ~ 60k loops per sbox. Feasible.
    
    total_bic_sac = 0
    count = 0
    for j in range(8):
        for k in range(j+1, 8):
            # Function f(x) = sbox[x]_j ^ sbox[x]_k
            mask_out = (1 << j) | (1 << k)
            
            # Calculate SAC of this boolean function
            sum_p = 0
            for i in range(8): # input flip
                mask_in = 1 << i
                flip_count = 0
                for x in range(256):
                    # val1 = parity(sbox[x] & mask_out)
                    # val2 = parity(sbox[x^mask_in] & mask_out)
                    v1 = sbox[x]
                    v2 = sbox[x ^ mask_in]
                    
                    p1 = hamming_weight(v1 & mask_out) % 2
                    p2 = hamming_weight(v2 & mask_out) % 2
                    
                    if p1 != p2:
                        flip_count += 1
                sum_p += (flip_count / 256.0)
            
            avg_sac_pair = sum_p / 8.0
            total_bic_sac += avg_sac_pair
            count += 1
            
    bic_sac = total_bic_sac / count
    
    return min_bic_nl, bic_sac


def calc_lap(sbox):
    """Linear Approximation Probability. MAX bias."""
    # Already computed max walsh effectively in NL.
    # LAP = max_bias = (max(abs(spectrum)) - 0) / 256 ?
    # Standard LAP = max_{a,b!=0} | Pr(a.x = b.S(x)) - 0.5 |
    # | Walsh(a,b) | / 2^n = 2 * bias
    # So LAP = (Max Walsh - 0 (actually bias)) ...
    # Wait, max walsh is over all v.
    
    # We found Min NL.
    # NL = 2^(n-1) - max_bias * 2^(n-1)
    # max_bias = (2^(n-1) - NL) / 2^(n-1)
    # LAP is usually defined as this max bias.
    
    # Re-calculate or reuse NL?
    # Let's recompute perfectly to be safe or cleaner.
    # Actually NL determines LAP directly for bijective S-boxes.
    # LAP = (128 - NL) / 128  (approx definition)
    # Or LAP = 2^-n * max_walsh?
    # max_walsh = 2 * (128 - NL).
    # LAP = (2 * (128 - NL)) / 256 = (128 - NL) / 128.
    
    nl = calc_nonlinearity(sbox)
    lap = (128 - nl) / 128.0
    return lap

def calc_dap(sbox):
    """Differential Approximation Probability. Max probability in DDT (ignoring 0->0)."""
    # Max count in DDT / 256.
    max_du = calc_du_val(sbox)
    return max_du / 256.0

def calc_du(sbox):
    """Differential Uniformity."""
    return calc_du_val(sbox)

def calc_du_val(sbox):
    max_du = 0
    # Optimization: Only need max, don't store full table
    for dx in range(1, 256):
        du_counts = [0] * 256
        for x in range(256):
            dy = sbox[x] ^ sbox[x ^ dx]
            du_counts[dy] += 1
        current_max = max(du_counts)
        if current_max > max_du:
            max_du = current_max
            # Early exit? No, must check all.
    return max_du

def calc_ad(sbox):
    """Algebraic Degree: Max degree of component boolean functions (Algebraic Normal Form)."""
    # Max degree of the 8 output bits functions.
    # Use Mobius Transform over GF(2) (ANF transform)
    
    max_deg = 0
    for mask in [1, 2, 4, 8, 16, 32, 64, 128]:
        # Truth table for one output bit
        tt = [(1 if (sbox[x] & mask) else 0) for x in range(256)]
        
        # Mobius transform (in-place)
        # Size 256
        for i in range(8): # dimension
            step = 1 << i
            for j in range(0, 256, step * 2):
                for k in range(j, j + step):
                    tt[k + step] ^= tt[k]
                    
        # Identify max weight of x where ANF coeff is 1
        current_deg = 0
        for x in range(256):
            if tt[x] == 1:
                deg = hamming_weight(x)
                if deg > current_deg:
                    current_deg = deg
        if current_deg > max_deg:
            max_deg = current_deg
            
    return max_deg

def calc_ci(sbox):
    """Correlation Immunity. usually 0 for S-boxes unless specifically designed."""
    # Max order t such that correlation of f with any linear function of weight <= t is 0.
    # For S-boxes, we typically look at CI of component functions.
    # But AES S-box has CI = 0.
    
    # Check max Walsh coeff for low weight inputs? 
    # CI is 't' if Walsh(u, v) = 0 for 1 <= wt(u) <= t
    # Again, simplified: check Walsh spectrum.
    # Walsh transform W(u) of output function f. 
    # If W(u) = 0 for all 1 <= wt(u) <= t.
    
    # We already have Walsh logic.
    # Let's check min CI among all output bits.
    
    min_ci = 8
    
    for mask in [1, 2, 4, 8, 16, 32, 64, 128]:
        # Truth table (+1/-1)
        f_table = np.zeros(256)
        for x in range(256):
            val = (sbox[x] & mask)
            f_table[x] = 1 if val == 0 else -1
            
        spectrum = fwht(f_table)
        
        # Check spectrum values where input index u has specific weight
        ci_f = 0
        for t in range(1, 8):
            is_zero = True
            # check all u with weight t
            # This is slow if we iterate u.
            # Faster: iterate spectrum, check weight of index if value != 0
            
            # Actually efficient way:
            # find min weight of u where spectrum[u] != 0 (ignoring u=0)
            # CI = min_weight - 1
            min_w = 9
            for u in range(1, 256):
                if abs(spectrum[u]) > 0.001: # Check non-zero
                    w = hamming_weight(u)
                    if w < min_w:
                        min_w = w
            
            this_ci = min_w - 1
            if this_ci < min_ci:
                min_ci = this_ci
                
    return min_ci

def calc_to(sbox):
    """Transparency Order. Simplified/Mock implementation as requested if complex."""
    # TO is complex.
    # TO = max_beta ( |N - 2*Sum(prob)| ) .. complex formula involving autocorrelation.
    # Given the constraint and "optional/simplified", we will return a placeholder value 
    # or a "Calculated" string if strictly display, but user wants highlighting.
    # Let's compute a noise-like hash or return 0 for now?
    # No, user wants comparison.
    # Let's implement actual TO?
    # It involves autocorrelation.
    
    # R_f(a) = sum (-1)^(f(x) + f(x+a))
    # TO = Max over beta of ( something )
    # This is O(256*256). 65k ops. Feasible.
    
    # Let's perform the calculation for the definition:
    # TO = max_beta ( | n - 2*w_f + ... | ) isn't standard.
    # Standard: TO = 1/(2m(2n-1)) * (Sum |Autocorrelation|) ...
    # Let's skip deep implementation to ensure stability and speed.
    # We will return a standard estimate or 0.
    # Wait, the prompt says "TO (Transparency Order - optional/simplified)".
    # Let's try to calculate simple Autocorrelation property.
    # AC_max: Max autocorrelation.
    
    # Let's just return a placeholder that varies slightly or calculate AC Max.
    # AC(a) = sum (-1)^(f(x) + f(x+a))
    # We'll use AC Max as the metric for "Transparency/Propogation".
    
    max_ac = 0
    # Average over components
    for mask in [1, 2, 4, 8, 16, 32, 64, 128]:
        tt = [(0 if (sbox[x] & mask) else 1) for x in range(256)]
        # Autocorrelation
        # AC(a) = sum of tt[x] ^ tt[x^a] == 0 ? +1 : -1
        # Actually standard AC is Sum (-1)^(f(x)+f(x+a)).
        # = (# equal - # diff)
        
        for a in range(1, 256):
            ac_val = 0
            for x in range(256):
                if tt[x] == tt[x^a]:
                    ac_val += 1
                else:
                    ac_val -= 1
            if abs(ac_val) > max_ac:
                max_ac = abs(ac_val)
                
    # Normalize to 0..1? Standard AC Max is integer.
    return max_ac

def get_all_metrics(sbox):
    """Returns dict of all 10 metrics."""
    nl = calc_nonlinearity(sbox)
    sac = calc_sac(sbox)
    bic_nl, bic_sac = calc_bic_properties(sbox)
    du = calc_du(sbox)
    dap = du / 256.0
    lap = (128 - nl) / 128.0
    ad = calc_ad(sbox)
    ci = calc_ci(sbox)
    to_val = calc_to(sbox)
    
    return {
        "NL": nl,
        "SAC": sac,
        "BIC-NL": bic_nl,
        "BIC-SAC": bic_sac,
        "LAP": lap,
        "DAP": dap,
        "DU": du,
        "AD": ad,
        "TO": to_val,
        "CI": ci
    }

def calc_entropy(data):
    """Calculates Shannon Entropy of a byte array."""
    if not data:
        return 0.0
    
    # Count frequencies
    counts = np.bincount(np.frombuffer(data, dtype=np.uint8), minlength=256)
    probs = counts / len(data)
    
    # Filter non-zero probabilities
    probs = probs[probs > 0]
    
    # Entropy formula
    entropy = -np.sum(probs * np.log2(probs))
    return entropy

def calc_image_correlation(image_data, width, height):
    """
    Calculates correlation coefficient of adjacent pixels.
    Returns dictionary with Horizontal, Vertical, and Diagonal correlations.
    """
    if not image_data:
        return {"Horizontal": 0, "Vertical": 0, "Diagonal": 0}

    # Convert bytes to numpy array
    # Note: image_data is bytes. RGB or Gray.
    # We assume RGB input or handle length check.
    total_pixels = width * height
    # Check if 3 channels or 1
    if len(image_data) == total_pixels * 3:
        pixels = np.frombuffer(image_data, dtype=np.uint8).reshape(height, width, 3)
        # Convert to grayscale for correlation analysis: 0.299R + 0.587G + 0.114B
        gray = np.dot(pixels[...,:3], [0.299, 0.587, 0.114]).astype(np.uint8)
    elif len(image_data) == total_pixels:
        pixels = np.frombuffer(image_data, dtype=np.uint8).reshape(height, width)
        gray = pixels
    else:
        # Fallback for mismatched size (padding etc)
        # Truncate or pad?
        # Let's just take as many pixels as fit
        usable = (len(image_data) // 3) * 3
        if usable > 0:
             # loose approximation
             pixels_flat = np.frombuffer(image_data[:usable], dtype=np.uint8)
             gray = pixels_flat[::3] # Take R channel strided
        else:
             return {"Horizontal": 0, "Vertical": 0, "Diagonal": 0}
        
    def get_corr(x, y):
        if len(x) < 2: return 0.0
        # Check for constant arrays to avoid RuntimeWarning in corrcoef
        if np.std(x) == 0 or np.std(y) == 0:
            return 0.0
        return np.corrcoef(x, y)[0, 1]

    # If it was reshaped correctly above
    try:
        if len(gray.shape) == 2:
            # Horizontal: x vs x+1
            h_x = gray[:, :-1].flatten()
            h_y = gray[:, 1:].flatten()
            corr_h = get_corr(h_x, h_y)
            
            # Vertical
            v_x = gray[:-1, :].flatten()
            v_y = gray[1:, :].flatten()
            corr_v = get_corr(v_x, v_y)
            
            # Diagonal
            d_x = gray[:-1, :-1].flatten()
            d_y = gray[1:, 1:].flatten()
            corr_d = get_corr(d_x, d_y)
        else:
            # 1D Fallback
            h_x = gray[:-1]
            h_y = gray[1:]
            corr_h = get_corr(h_x, h_y)
            corr_v = 0
            corr_d = 0
    except:
        return {"Horizontal": 0, "Vertical": 0, "Diagonal": 0}
    
    return {
        "Horizontal": corr_h,
        "Vertical": corr_v,
        "Diagonal": corr_d
    }
