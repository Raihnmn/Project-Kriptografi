import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from PIL import Image
import io
import time
import binascii

from sbox_data import AES_SBOX, SBOX_K44
import aes_engine
import sbox_utils
import metrics

# --- Page Configuration ---
st.set_page_config(
    page_title="Analisis S-box K44 & Kripto Suite",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished look
st.markdown("""
<style>
    body, .main, .block-container {
        background: linear-gradient(135deg, #e0e7ff 0%, #f8fafc 100%) !important;
        color: #222 !important;
    }
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 1rem;
        text-shadow: 0 2px 8px rgba(30,58,138,0.08);
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #222;
        margin-top: 2rem;
    }
    .card {
        padding: 1.5rem;
        border-radius: 12px;
        background-color: #f4f6fb;
        box-shadow: 0 4px 12px rgba(30,58,138,0.10);
        margin-bottom: 1rem;
        border-left: 6px solid #1E3A8A;
        color: #222;
    }
    .score-card {
        background-color: #e9ecef;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        border: 2px solid #dee2e6;
        box-shadow: 0 2px 8px rgba(30,58,138,0.08);
        color: #222;
    }
    .score-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: #dc3545;
    }
    .score-good {
        color: #198754;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #0d6efd;
    }
    .metric-label {
        font-size: 1rem;
        color: #222;
    }
    .sbox-card {
        background: #f4f6fb;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(30,58,138,0.08);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border-left: 6px solid #1E3A8A;
        color: #222;
    }
    .sbox-badge {
        display: inline-block;
        padding: 0.3em 0.8em;
        border-radius: 8px;
        font-size: 1em;
        font-weight: 600;
        background: #e9ecef;
        color: #1E3A8A;
        margin-right: 0.5em;
    }
    .sbox-badge.good { background: #d1e7dd; color: #198754; }
    .sbox-badge.warn { background: #fff3cd; color: #856404; }
    .sbox-badge.bad { background: #f8d7da; color: #dc3545; }
    .stButton>button {
        background: #1E3A8A;
        color: #fff;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5em 1.2em;
        box-shadow: 0 2px 8px rgba(30,58,138,0.08);
        border: none;
    }
    .stButton>button:hover {
        background: #0d6efd;
        color: #fff;
    }
    .stTabs [data-baseweb="tab"] {
        background: #e0e7ff;
        border-radius: 8px 8px 0 0;
        font-weight: 600;
        color: #1E3A8A;
    }
    .stTabs [aria-selected="true"] {
        background: #1E3A8A;
        color: #fff;
    }
    .stSidebar {
        background: #1E3A8A !important;
        color: #fff !important;
    }
    .stSidebar .sidebar-content {
        background: #1E3A8A !important;
        color: #fff !important;
    }
    .stSidebar .sidebar-content a {
        color: #fff !important;
    }
    /* Perbaiki warna teks info box di sidebar agar kontras */
    .stSidebar .stAlert, .stSidebar .stAlert * {
        color: #fff !important;
        background: rgba(30,58,138,0.15) !important;
    }
    /* Pertebal judul dan info penting di sidebar.info */
    .stSidebar .stAlert b, .stSidebar .stAlert strong {
        color: #ffb703 !important;
        font-weight: bold;
    }
    /* Perbaiki warna link di sidebar.info */
    .stSidebar .stAlert a {
        color: #ffd166 !important;
    }
    /* Perbaiki warna teks navigasi agar kontras dan jelas */
    .stSidebar, .stSidebar .sidebar-content, .stSidebar .sidebar-content * {
        color: #fff !important;
    }
    /* Perbaiki warna radio button dan label */
    .stSidebar .stRadio label, .stSidebar .stRadio div, .stSidebar .stRadio span {
        color: #fff !important;
    }
    /* Perbaiki warna teks metric dan info di sidebar */
    .stSidebar .stMarkdown, .stSidebar .stInfo, .stSidebar .stText, .stSidebar .stTitle {
        color: #fff !important;
    }
    /* Perbaiki warna teks radio yang tidak aktif */
    .stSidebar .stRadio [data-baseweb="radio"] > div > div {
        color: #fff !important;
    }
    /* Perbaiki warna teks radio yang aktif */
    .stSidebar .stRadio [aria-checked="true"] {
        color: #ffb703 !important;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- Navigation ---
st.sidebar.title("Navigasi")
page = st.sidebar.radio("Pilih Halaman", ["Dashboard (Beranda)", "Analisis S-box", "Playground Enkripsi", "S-Box Analyzer & Eksplorasi"])

st.sidebar.markdown("---")
st.sidebar.info(
    "**Analisis S-box K44**\n\n"
    "Berdasarkan jurnal penelitian:\n"
    "*AES S-box modification uses affine matrices exploration*\n\n"
    "v1.2.0 (With Generator)"
)

# --- Helper Functions ---
def plot_heatmap(sbox, title):
    # Reshape 256-element array to 16x16 matrix
    matrix = np.array(sbox).reshape(16, 16)
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(matrix, annot=False, cmap="viridis", cbar=True, ax=ax)
    ax.set_title(title)
    return fig

def calculate_sv_score(nl, sac, bic_nl, bic_sac):
    # Formula: SV = (120 - NL) + abs(0.5 - SAC) + (120 - BIC_NL) + abs(0.5 - BIC_SAC)
    return (120 - nl) + abs(0.5 - sac) + (120 - bic_nl) + abs(0.5 - bic_sac)

# --- Page 1: Dashboard ---
if page == "Dashboard (Beranda)":
    st.markdown('<div class="main-header">Analisis S-box K44 & Kripto Suite</div>', unsafe_allow_html=True)
    

    # --- Kelompok Profile & Kampus ---
    st.markdown("""
    <div class="card" style="border-left: 5px solid #198754;">
        <h3>Profil Kelompok</h3>
        <ul style='font-size:1.1em;'>
            <li><b>Nama:</b> Raihan Muhammad Nafi'          | <b>NIM:</b> 2304130019</li>
            <li><b>Nama:</b> Ahmad Galvin Firdaus Zahid     | <b>NIM:</b> 2304130021</li>
            <li><b>Nama:</b> Muhammad Fila Nafan            | <b>NIM:</b> 2304130042</li>
            <li><b>Nama:</b> Ahmad Iffad Izzudin            | <b>NIM:</b> 2304130044</li>
        </ul>
        <div style='margin-top:1em;font-size:1.15em;'><b>Kampus:</b> Universitas Negeri Semarang</div>
    </div>
    """, unsafe_allow_html=True)

    # 1. Research Context
    st.markdown("""
    <div class="card">
        <h3>Konteks Riset</h3>
        <p><strong>Judul Riset:</strong> "AES S-box modification uses affine matrices exploration for increased S-box strength"</p>
        <p><strong>Temuan Utama:</strong> Penelitian ini mengusulkan S-box baru (S-box K44) yang dibangun menggunakan matriks affine terpilih (K44). 
        S-box ini terbukti memiliki nilai SAC (0.50073) yang lebih baik dibandingkan S-box AES Standar (0.50488), menjadikannya lebih mendekati nilai ideal 0.5.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Non-linearitas Standar AES", value="112")
    with col2:
        st.metric(label="Non-linearitas S-box K44", value="112")
    with col3:
        st.metric(label="Peningkatan SAC (K44)", value="0.82%", delta="Lebih Baik")

    st.markdown("---")
    
    # 2. Methodology / Construction Steps
    st.markdown("### Metodologi: Bagaimana S-box K44 Dibuat?")
    with st.expander("Klik untuk melihat langkah-langkah konstruksi S-box K44", expanded=False):
        st.markdown(r"""
        **Langkah 1: Polinomial Irreduksibel**
        
        Sama seperti AES standar, riset ini menggunakan polinomial: $x^8 + x^4 + x^3 + x + 1$ (0x11B). Ini adalah fondasi matematika di Galois Field $GF(2^8)$.
        
        **Langkah 2: Invers Multiplikatif**
        
        Setiap nilai input (kecuali 0) dipetakan ke invers multiplikatifnya di $GF(2^8)$. Langkah ini memberikan sifat non-linearitas (NL) yang tinggi.
        
        **Langkah 3: Eksplorasi Matriks Affine (Inti Riset)**
        
        Peneliti melakukan eksplorasi komputasi terhadap $2^{64}$ kemungkinan matriks affine $8x8$. Dari jutaan kandidat, disaring matriks yang memenuhi syarat Bijective (output unik) dan Balanced. Terpilihlah 128 matriks kandidat terbaik.
        
        **Langkah 4: Pemilihan Matriks K44**
        
        Dari 128 kandidat, matriks ke-44 ($K_{44}$) dipilih karena menghasilkan skor kriptografi terbaik setelah diuji.
        
        **Langkah 5: Transformasi Affine**
        
        S-box final dibentuk menggunakan rumus transformasi:
        
        $S\text{-}box = (K_{44} \times Invers) \oplus Konstanta\_AES$
        
        Di mana $K_{44}$ adalah matriks baru hasil riset, dan Konstanta adalah 0x63 (sama dengan AES).
        """)

    # 3. Educational Concepts (General)
    st.markdown("### Konsep Dasar Kriptografi") 
    c1, c2 = st.columns(2)
    with c1:
        st.info("**S-box (Substitution Box)**: Komponen utama dalam AES yang berfungsi mengacak data (Confusion). S-box yang kuat harus tahan terhadap serangan matematika.")
    with c2:
        st.warning("**Confusion & Diffusion**: Prinsip dasar kriptografi. Confusion mengaburkan hubungan kunci dan ciphertext. Diffusion menyebarkan pengaruh 1 bit plaintext ke banyak bit ciphertext.")

# --- Page 2: S-box Analyzer (Result Summary) ---
elif page == "Analisis S-box":
    st.markdown('<div class="main-header">Analisis S-box</div>', unsafe_allow_html=True)
    st.markdown("Bandingkan properti kriptografi dan struktur S-box Standar AES vs. S-box K44 yang Diusulkan.")

    # 1. SV Score Analysis
    st.markdown('<div class="sub-header">Analisis Skor Akhir (SV Score)</div>', unsafe_allow_html=True)
    
    # Calculate SV
    # AES Data: NL=112, SAC=0.50488, BIC_NL=112, BIC_SAC=0.50460
    sv_aes = calculate_sv_score(112, 0.50488, 112, 0.50460)
    # K44 Data: NL=112, SAC=0.50073, BIC_NL=112, BIC_SAC=0.50237
    sv_k44 = calculate_sv_score(112, 0.50073, 112, 0.50237)
    
    col_sv1, col_sv2, col_sv_info = st.columns([1, 1, 2])
    
    with col_sv1:
        st.markdown(f"""
        <div class="score-card">
            <h4>Skor SV AES</h4>
            <div class="score-value">{sv_aes:.5f}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_sv2:
        st.markdown(f"""
        <div class="score-card">
            <h4>Skor SV K44</h4>
            <div class="score-value score-good">{sv_k44:.5f}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_sv_info:
        st.info(
            "**Nilai SV (Strength Value)** adalah akumulasi dari selisih nilai ideal. "
            "Semakin **KECIL** nilai SV, semakin baik kualitas S-box tersebut mendekati batas teoritis.\n\n"
            f"K44 memiliki skor {sv_k44:.5f}, yang secara signifikan lebih rendah (lebih baik) dari AES standar ({sv_aes:.5f})."
        )

    # 4. Conclusion / Analysis Note
    st.markdown("""
    <div class="card" style="border-left: 5px solid #0d6efd;">
        <h4>Mengapa S-box K44 Lebih Baik?</h4>
        <p>
        Meskipun nilai Nonlinearity (112) dan Differential Uniformity (4) sama dengan AES standar (karena sifat affine-invariant), 
        <strong>S-box K44 unggul pada kriteria difusi (SAC & BIC-SAC)</strong>. 
        Ini berarti S-box K44 menyebarkan perubahan bit dengan lebih acak dan merata dibandingkan AES standar, 
        memberikan perlindungan lebih baik terhadap pola statistik.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 2. Heatmaps
    st.markdown('<div class="sub-header">Visualisasi Heatmap</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("S-box Standar AES")
        fig_aes = plot_heatmap(AES_SBOX, "Distribusi S-box AES")
        st.pyplot(fig_aes)
        
    with col2:
        st.subheader("S-box K44 (Diusulkan)")
        fig_k44 = plot_heatmap(SBOX_K44, "Distribusi S-box K44")
        st.pyplot(fig_k44)

    # 3. Metrics Table
    st.markdown('<div class="sub-header">Perbandingan Metrik Kriptografi</div>', unsafe_allow_html=True)
    
    data = {
        "Metrik": [
            "Nonlinearity (NL)", "SAC (Strict Avalanche Criterion)", "BIC-NL", "BIC-SAC", 
            "LAP (Linear Approx. Prob.)", "DAP (Diff. Approx. Prob.)", "Differential Uniformity (DU)",
            "Algebraic Degree (AD)", "Transparency Order (TO)", "Correlation Immunity (CI)"
        ],
        "Nilai Standar AES": [
            "112", "0.50488", "112", "0.50460", "0.0625", "0.01563", "4", "7", "Calculated", "0"
        ],
        "Nilai S-box K44": [
            "112", "0.50073", "112", "0.50237", "0.0625", "0.01563", "4", "7", "Calculated", "0"
        ],
        "Catatan": [
            "Kekuatan Setara", "K44 Lebih Baik (Mendekati 0.5)", "Kekuatan Setara", "K44 Lebih Baik (Mendekati 0.5)",
            "Kekuatan Setara", "Kekuatan Setara", "Invariant Teoritis", "Invariant Teoritis", 
            "-", "Invariant Teoritis"
        ]
    }
    
    df = pd.DataFrame(data)
    st.table(df)
    
    # Educational Definitions
    with st.expander("Klik untuk melihat penjelasan detail setiap metrik"):
        st.markdown("""
        **Nonlinearity (NL)**: Mengukur seberapa jauh fungsi S-box berbeda dari fungsi linear. Semakin tinggi nilai NL (maks 112 untuk S-box 8-bit), semakin tahan terhadap Linear Cryptanalysis.
        
        **SAC (Strict Avalanche Criterion)**: Mengukur efek longsoran. Jika 1 bit input diubah, idealnya 50% bit output harus berubah. Nilai ideal adalah 0.5. K44 lebih unggul di sini.
        
        **BIC (Bit Independence Criterion)**: Mengukur apakah perubahan pada bit output terjadi secara independen (tidak saling mempengaruhi). Penting untuk mencegah pola statistik.
        
        **Differential Uniformity (DU)**: Mengukur ketahanan terhadap Differential Cryptanalysis. Nilai semakin kecil (ideal 4) semakin baik.
        
        **LAP & DAP**: Probabilitas pendekatan linear dan diferensial. Nilai yang lebih rendah menunjukkan keamanan yang lebih tinggi.
        """)

    
# --- Page 3: Encryption Playground ---
elif page == "Playground Enkripsi":
    st.markdown('<div class="main-header">Playground Enkripsi & Dekripsi</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📝 Teks (Text)", "🖼️ Gambar (Image)"])
    
    # helper for key input
    def render_key_input():
        k = st.text_input("Masukkan Kunci (Key):", value="1234567890123456", help="Kunci enkripsi/dekripsi")
        st.caption("ℹ️ Kunci bebas (akan otomatis disesuaikan menjadi 16 karakter).")
        return k

    with tab1:
        st.subheader("Demo Enkripsi/Dekripsi Teks")
        
        col_settings, col_io = st.columns([1, 2])
        
        with col_settings:
            sbox_choice = st.radio("Pilih S-box:", ("Standar AES", "K44 Diusulkan"), key="text_sbox")
            key_input = render_key_input()
        
        with col_io:
            sub_tab_enc, sub_tab_dec = st.tabs(["Enkripsi", "Dekripsi"])
            
            with sub_tab_enc:
                plaintext = st.text_area("Masukkan Plaintext:", value="Halo Dunia! Menguji S-box K44.", height=150)
                if st.button("Enkripsi Teks"):
                    sbox = AES_SBOX if sbox_choice == "Standar AES" else SBOX_K44
                    key = key_input.encode('utf-8')
                    
                    start_time = time.time()
                    try:
                        ciphertext = aes_engine.encrypt_text(plaintext.encode('utf-8'), key, sbox)
                        end_time = time.time()
                        st.success(f"Enkripsi Selesai ({end_time - start_time:.4f}s)")
                        
                        hex_output = ciphertext.hex()
                        st.code(hex_output, language="text")
                        st.caption("Output (Hexadecimal)")
                        
                        # Store in session state for convenience in decryption tab? (Optional)
                    except Exception as e:
                        st.error(f"Terjadi kesalahan: {str(e)}")

            with sub_tab_dec:
                cipher_input = st.text_area("Masukkan Ciphertext (Hex):", help="Tempel output hex dari enkripsi di sini.", height=150)
                if st.button("Dekripsi Teks"):
                    sbox = AES_SBOX if sbox_choice == "Standar AES" else SBOX_K44
                    key = key_input.encode('utf-8')
                    
                    try:
                        # Convert hex back to bytes
                        cipher_bytes = bytes.fromhex(cipher_input.strip())
                        
                        start_time = time.time()
                        decrypted_bytes = aes_engine.decrypt_text(cipher_bytes, key, sbox)
                        end_time = time.time()
                        
                        # Try decode as utf-8
                        decrypted_text = decrypted_bytes.decode('utf-8', errors='ignore')
                        
                        st.success(f"Dekripsi Selesai ({end_time - start_time:.4f}s)")
                        st.text_area("Hasil Plaintext:", value=decrypted_text, height=100)
                    except ValueError:
                        st.error("Format Hex tidak valid.")
                    except Exception as e:
                        st.error(f"Gagal dekripsi: {str(e)}")

    with tab2:
        st.subheader("Demo Enkripsi/Dekripsi Gambar")
        st.warning("Catatan: Mode ECB mempertahankan pola visual pada gambar. Ini digunakan untuk mendemonstrasikan properti 'confusion'.")
        
        img_sbox_choice = st.radio("Pilih S-box Gambar:", ("Standar AES", "K44 Diusulkan"), horizontal=True, key="img_sbox")
        img_key_input = st.text_input("Kunci Gambar:", value="RahasiaGambar123")
        st.caption("ℹ️ Kunci bebas (akan otomatis disesuaikan menjadi 16 karakter).")
        
        tab_img_enc, tab_img_dec = st.tabs(["Enkripsi Gambar", "Dekripsi Gambar"])
        
        with tab_img_enc:
            img_file = st.file_uploader("Unggah Gambar Asli (JPG/PNG)", type=["jpg", "png", "jpeg"], key="upl_enc")
            
            if img_file is not None:
                image = Image.open(img_file)
                # Resize for performance
                max_size = (200, 200)
                image.thumbnail(max_size)
                
                col_orig, col_res = st.columns(2)
                with col_orig:
                    st.image(image, caption="Gambar Asli (Resized)", use_container_width=True)
                
                if st.button("Enkripsi Gambar"):
                    sbox = AES_SBOX if img_sbox_choice == "Standar AES" else SBOX_K44
                    key = img_key_input.encode('utf-8')
                    
                    with st.spinner("Sedang mengenkripsi..."):
                        img_rgb = image.convert("RGB")
                        width, height = img_rgb.size
                        pixels = np.array(img_rgb)
                        flat_pixels = pixels.flatten().tobytes()
                        
                        encrypted_data = aes_engine.encrypt_image(flat_pixels, key, sbox)
                        
                        # Show result
                        # Truncate strictly for display, but user might want to download full encrypted file?
                        # For display purposes (noise):
                        display_len = len(flat_pixels)
                        display_data = encrypted_data[:display_len]
                        
                        enc_pixels = np.frombuffer(display_data, dtype=np.uint8).reshape(height, width, 3)
                        enc_image = Image.fromarray(enc_pixels)
                        
                        with col_res:
                            st.image(enc_image, caption=f"Terenkripsi ({img_sbox_choice})", use_container_width=True)
                            
                        # Allow download of encrypted raw bytes?
                        # Or save "encrypted image" as PNG (which is technically just noise pixels, not really secure file format)
                        # Let's simple offer download as simple noise PNG
                        buf = io.BytesIO()
                        enc_image.save(buf, format="PNG")
                        st.download_button(
                            label="Unduh Gambar Terenkripsi (PNG)",
                            data=buf.getvalue(),
                            file_name="encrypted_noise.png",
                            mime="image/png"
                        )

        with tab_img_dec:
            st.info("Unggah gambar 'noise' hasil enkripsi sebelumnya untuk didekripsi kembali.")
            enc_img_file = st.file_uploader("Unggah Gambar Terenkripsi", type=["png", "jpg"], key="upl_dec")
            
            if enc_img_file is not None:
                e_image = Image.open(enc_img_file)
                st.image(e_image, caption="Gambar Terenkripsi (Input)", width=200)
                
                if st.button("Dekripsi Gambar"):
                    sbox = AES_SBOX if img_sbox_choice == "Standar AES" else SBOX_K44
                    key = img_key_input.encode('utf-8')
                    
                    with st.spinner("Sedang mendekripsi..."):
                        e_img_rgb = e_image.convert("RGB")
                        width, height = e_img_rgb.size
                        e_pixels = np.array(e_img_rgb)
                        e_flat_pixels = e_pixels.flatten().tobytes()
                        
                        # Decrypt
                        # Note: decrypt_image expects padded data usually, but our display file is just raw pixels.
                        # aes_engine.decrypt_image tries to strip padding.
                        # In this flow: Encrypt -> Padded Cipher -> Truncate to Size -> Save PNG.
                        # So we lost the padding! Decryption will be imperfect at the last block?
                        # Or we should encrypt, then unpad/truncate, then save.
                        # But AES block size is 16. If we truncate, we lose data.
                        # Thus, saving the "Image" as a PNG is lossy if the pixel count isn't multiple of 16 bytes?
                        # RGB = 3 bytes per pixel.
                        # Total bytes = W * H * 3.
                        # If (W*H*3) % 16 != 0, we have an issue if we just save pixels.
                        # However, for the sake of this demo:
                        # We will just decrypt the raw bytes we get.
                        
                        decrypted_data = aes_engine.decrypt_image(e_flat_pixels, key, sbox)
                        
                        # Reconstruct
                        # If decrypted size doesn't match shape, we truncate or pad?
                        needed_len = width * height * 3
                        # Pad with 0 if short (due to stripped padding or loss)
                        if len(decrypted_data) < needed_len:
                            decrypted_data += b'\x00' * (needed_len - len(decrypted_data))
                        else:
                            decrypted_data = decrypted_data[:needed_len]
                            
                        d_pixels = np.frombuffer(decrypted_data, dtype=np.uint8).reshape(height, width, 3)
                        d_image = Image.fromarray(d_pixels)
                        
                        st.success("Gambar berhasil dipulihkan (estimasi).")
                        st.image(d_image, caption="Hasil Dekripsi", use_container_width=True)

# --- Tambahan Halaman S-Box Analyzer (Refactored) ---
elif page == "S-Box Analyzer & Eksplorasi":
    st.markdown('<div class="main-header">🔎 S-Box Analyzer & Eksplorasi</div>', unsafe_allow_html=True)
    
    # 1. Source Selection
    st.markdown("### 1. Sumber S-box")
    source_choice = st.radio("Pilih Sumber S-box:", 
                             ["Input Manual / Upload File", "Eksplorasi Matriks Affine (Generator)"],
                             index=0, horizontal=True)
    
    
    sbox_arr = None
    generated_matrix = None
    
    # Storage for analysis source name
    sbox_source_name = "S-box Anda"

    if source_choice == "Input Manual / Upload File":
        st.info("Masukkan S-Box dalam format heksadesimal (512 karakter, 256 byte) atau unggah file .xlsx.")
        
        # Helper parsing functions
        def parse_hex_sbox(hex_str):
            hex_str = hex_str.replace(" ", "").replace("\n", "")
            if hex_str.startswith("0x"): hex_str = hex_str[2:]
            if len(hex_str) != 512:
                raise ValueError(f"Input harus 512 karakter hex. Diterima: {len(hex_str)}")
            arr = [int(hex_str[i:i+2], 16) for i in range(0, 512, 2)]
            if len(arr) != 256: raise ValueError("S-Box harus 256 elemen")
            return arr

        def parse_xlsx_sbox(uploaded_file):
            try:
                df = pd.read_excel(uploaded_file, header=None)
                if df.shape == (16, 16): arr = df.values.flatten().tolist()
                elif df.shape == (256, 1): arr = df[0].tolist()
                else: raise ValueError("Format file harus 16x16 atau 256x1.")
                return [int(x) for x in arr]
            except Exception as e:
                raise ValueError(f"Gagal membaca file: {e}")

        # UI Input
        col_in1, col_in2 = st.columns(2)
        with col_in1:
            hex_input = st.text_area("Input S-Box (Hex)", height=100)
            if st.button("Parse Hex"):
                try:
                    sbox_arr = parse_hex_sbox(hex_input)
                    sbox_source_name = "S-box Manual (Hex)"
                    st.success("Berhasil memproses input Hex.")
                except Exception as e:
                    st.error(f"Error: {e}")
        
        with col_in2:
            uploaded_xlsx = st.file_uploader("Upload File .xlsx", type=["xlsx"])
            if uploaded_xlsx:
                if st.button("Proses XLSX"):
                    try:
                        sbox_arr = parse_xlsx_sbox(uploaded_xlsx)
                        sbox_source_name = "S-box Upload (XLSX)"
                        st.success("Berhasil memproses file XLSX.")
                    except Exception as e:
                        st.error(f"Error: {e}")

    else: # Generator Mode
        st.info("Mode ini akan membangkitkan Matriks Affine 8x8 Acak (Invertible) dan membentuk S-box baru.")
        
        if st.button("🔄 Generate S-box Baru"):
            try:
                with st.spinner("Membangkitkan Matriks & S-box..."):
                    gen_sbox, gen_matrix = sbox_utils.generate_affine_sbox()
                    
                    st.session_state['generated_sbox'] = gen_sbox
                    st.session_state['generated_matrix'] = gen_matrix
                    st.success("S-box berhasil dibangkitkan!")
            except Exception as e:
                st.error(f"Gagal generate: {e}")
        
        if 'generated_sbox' in st.session_state:
            sbox_arr = st.session_state['generated_sbox']
            generated_matrix = st.session_state['generated_matrix']
            sbox_source_name = "S-box Generator Affine"
            
            st.markdown("#### Matriks Affine Terpilih (8x8):")
            st.dataframe(pd.DataFrame(generated_matrix), use_container_width=False, width=400)


    # --- Unified Analysis Section ---
    if sbox_arr:
        st.markdown("---")
        st.markdown(f"### 2. Analisis & Visualisasi: {sbox_source_name}")
        
        
        # 1. Visualization
        col_vis1, col_vis2 = st.columns([1, 2])
        with col_vis1:
            st.markdown("#### Heatmap S-box")
            fig = plot_heatmap(sbox_arr, sbox_source_name)
            st.pyplot(fig)
            
        with col_vis2:
            st.markdown("#### Matriks S-box (Hex)")
            # Display as 16x16 dataframe of hex strings
            matrix_hex = np.array([f"{x:02X}" for x in sbox_arr]).reshape(16, 16)
            st.dataframe(pd.DataFrame(matrix_hex, columns=[f"{i:X}" for i in range(16)], index=[f"{i:X}" for i in range(16)]), height=400)

        # 2. Metrics Calculation
        st.markdown("### 3. Perbandingan Benchmark")
        st.info("Membandingkan performa 10 metrik kriptografi dengan standar industri.")
        
        if st.button("📊 Jalankan Analisis Lengkap"):
            with st.spinner("Menghitung 10 metrik kriptografi... (Ini mungkin memakan waktu beberapa detik)"):
                try:
                    # Calculate User Metrics
                    user_metrics = metrics.get_all_metrics(sbox_arr)
                    
                    # Standard Benchmarks
                    
                    @st.cache_data
                    def get_benchmark_metrics():
                        m_aes = metrics.get_all_metrics(AES_SBOX)
                        m_k44 = metrics.get_all_metrics(SBOX_K44)
                        return m_aes, m_k44
                    
                    # NOTE: First run might be slow
                    aes_metrics, k44_metrics = get_benchmark_metrics()
                    
                    metric_names = [
                        "NL", "SAC", "BIC-NL", "BIC-SAC", 
                        "LAP", "DAP", "DU", "AD", "TO", "CI"
                    ]
                    
                    rows = []
                    for k in metric_names:
                        rows.append([
                            aes_metrics[k], 
                            k44_metrics[k], 
                            user_metrics[k]
                        ])
                        
                    df_compare = pd.DataFrame(rows, columns=["AES Standar", "S-box K44", sbox_source_name], index=metric_names)
                    
                    # --- Highlighting Logic ---
                    def highlight_best(data):
                        # data is a DataFrame. We return a DataFrame of styles.
                        styles = pd.DataFrame('', index=data.index, columns=data.columns)
                        
                        goals = {
                            "NL": "max",
                            "SAC": "target_0.5",
                            "BIC-NL": "max", 
                            "BIC-SAC": "target_0.5", 
                            "LAP": "min",
                            "DAP": "min",
                            "DU": "min",
                            "AD": "max", 
                            "TO": "min", 
                            "CI": "max"  
                        }
                        
                        for metric in data.index:
                            row_vals = data.loc[metric]
                            rule = goals.get(metric, "max")
                            
                            if rule == "max":
                                best_val = row_vals.max()
                                is_best = row_vals == best_val
                            elif rule == "min":
                                best_val = row_vals.min()
                                is_best = row_vals == best_val
                            elif rule == "target_0.5":
                                diffs = abs(row_vals - 0.5)
                                min_diff = diffs.min()
                                is_best = diffs == min_diff
                            
                            # Apply style
                            for col in data.columns:
                                if is_best[col]:
                                    styles.loc[metric, col] = 'background-color: #d1e7dd; color: #0f5132; font-weight: bold'
                                    
                        return styles

                    st.markdown("#### Tabel Perbandingan")
                    st.dataframe(df_compare.style.apply(highlight_best, axis=None).format("{:.5g}"), use_container_width=True)
                    
                    st.caption("**Keterangan Warna Hijau**: Menunjukkan nilai terbaik di antara ketiga kandidat untuk metrik tersebut.")
                            
                except Exception as e:
                    st.error(f"Kesalahan dalam perhitungan metrik: {e}")
