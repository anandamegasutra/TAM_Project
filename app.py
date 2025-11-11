import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
import io

# Mengimpor library tambahan
import semopy as sem
import pingouin as pg
import graphviz 
import numpy as np
import re 

# --- ### PERBAIKAN: MEMUAT CSS DARI FILE EKSTERNAL ### ---
def load_css(file_name):
    """Fungsi untuk memuat file CSS lokal"""
    try:
        with open(file_name) as f:
            css = f.read()
        return f"<style>{css}</style>"
    except FileNotFoundError:
        st.error(f"File CSS '{file_name}' tidak ditemukan. Pastikan file tersebut berada di folder yang sama dengan script Python.")
        return ""

# Terapkan CSS kustom dari file style.css
css_content = load_css("style.css")
if css_content:
    st.markdown(css_content, unsafe_allow_html=True)
# --- ### AKHIR PEMUATAN CSS ---


# --- Konfigurasi Halaman dan Data (Tidak Berubah) ---
st.set_page_config(
    page_title="Analisis TAM Grub info & Jual Beli Area Lede",
    layout="wide",
    initial_sidebar_state="auto"
)

DATA_FILE = "data/TAM_GroupFB_Jual_Beli_Area_Lede.csv"
os.makedirs("data", exist_ok=True)
os.makedirs("images", exist_ok=True) 

questions = {
    "Perceived Usefulness (PU)": [
        "Menggunakan grup ini memudahkan saya menemukan pembeli/barang dengan cepat",
        "Grup ini membantu saya mendapatkan informasi produk terkini",
        "Bertransaksi melalui grup ini meningkatkan efisiensi dan menghemat waktu saya",
    ],
    "Perceived Ease of Use (PEOU)": [
        "Proses membuat postingan/komentar di grup ini sederhana dan mudah",
        "Aplikasi Facebook selalu tersedia dan mudah diakses kapan saja",
        "Saya merasa tidak membutuhkan banyak usaha atau keahlian khusus untuk menggunakan grup ini",
    ],
    "Attitude Toward Using (ATU)": [
        "Saya memiliki pandangan positif terhadap penggunaan grup ini sebagai media transaksi",
        "Saya senang dan menyukai kemudahan yang ditawarkan grup ini",
        "Saya mempercayai informasi dan transaksi di grup ini",
    ],
    "Behavioral Intention (BI)": [
        "Saya berniat untuk terus menggunakan grup ini untuk aktivitas jual beli saya",
        "Saya pasti akan menjadikan grup ini tempat pertama yang saya kunjungi",
        "Saya akan secara rutin memeriksa postingan di grup ini",
    ],
    "Actual Technology Use (ATU_Real)": [
        "Saya aktif memposting atau mencari informasi minimal 5 kali seminggu",
        "Saya telah berhasil melakukan transaksi minimal [X kali] dalam sebulan",
        "Saya menghabiskan waktu rata-rata lebih dari 10 menit setiap hari untuk mengecek grup ini",
    ]
}

likert_scale_map = {
    1: "1 - Sangat Tidak Setuju",
    2: "2 - Tidak Setuju",
    3: "3 - Netral",
    4: "4 - Setuju",
    5: "5 - Sangat Setuju"
}

# --- Panel Admin dan Menu (Tidak Berubah) ---
st.sidebar.title("🔐 Admin Panel")
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

ADMIN_USER = "admin"
ADMIN_PASS = "ad1234"

is_admin = (username == ADMIN_USER and password == ADMIN_PASS)

if is_admin:
    menu = st.sidebar.radio("📌 Menu", ["Isi Kuesioner", "Lihat Hasil (Admin)"])
else:
    menu = "Isi Kuesioner"

# --- ### HALAMAN KUESIONER (Tampilan Scroll Sederhana) ### ---
if menu == "Isi Kuesioner":

    # --- TAMPILAN HEADER: Logo dan Judul satu baris (DIPERTAHANKAN) ---
    image_path = "images/logo_kelompok.png"
    
    col1, col2 = st.columns([1, 6], vertical_alignment="center")
    
    with col1:
        if os.path.exists(image_path):
            st.image(image_path, width=80) 
        else:
            st.warning("Logo Gagal Dimuat")

    with col2:
        st.title("Kuesioner TAM : Analisis Penerimaan Teknologi pada Grup FB Jual Beli Area Lede")
        st.caption("")
    # --- AKHIR TAMPILAN HEADER ---

    # Logika pembatasan responden (tidak berubah)
    try:
        if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
            current_df = pd.read_csv(DATA_FILE)
            num_responden_saat_ini = len(current_df)
            if num_responden_saat_ini >= 83:
                st.warning("🚨 **Batas jumlah responden (83 orang) telah tercapai.** Terima kasih atas partisipasi Anda. Kuesioner ini tidak lagi menerima jawaban baru.")
                st.stop()
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memeriksa jumlah responden: {e}")
        
    with st.expander("📖 Petunjuk Pengisian"):
        st.markdown("""
        Silakan isi kuesioner berikut berdasarkan pengalaman Anda menggunakan **Grup FB Jual Beli Area Lede dan sekitarnya**.
        Gunakan skala berikut untuk menjawab setiap pertanyaan:
        - **1 = Sangat Tidak Setuju**
        - **2 = Tidak Setuju**
        - **3 = Netral**
        - **4 = Setuju**
        - **5 = Sangat Setuju**
        """)

    nama = st.text_input("Nama Responden (opsional)")
    responses = {}
    
    # --- TAMPILAN KUESIONER (TANPA CARD) ---
    for indicator, qs in questions.items():
        
        if "Usefulness" in indicator: abbr = "PU"
        elif "Ease of Use" in indicator: abbr = "PEOU"
        elif "Attitude" in indicator: abbr = "ATU"
        elif "Intention" in indicator: abbr = "BI"
        elif "Actual" in indicator: abbr = "AU"
        else: abbr = indicator.split()[0]
        
        responses[indicator] = []
        for i, q in enumerate(qs):
            # Menampilkan pertanyaan radio (tanpa card)
            score = st.radio(
                q,
                options=[1, 2, 3, 4, 5],
                format_func=lambda x: likert_scale_map[x],
                index=None,
                key=f"{indicator}_{i}"
            )
            responses[indicator].append(score)
    # --- AKHIR TAMPILAN KUESIONER ---
    
    if st.button("💾 Simpan Jawaban"):
        # Logika validasi dan penyimpanan (tidak berubah)
        if any(score is None for scores in responses.values() for score in scores):
            st.error("⚠️ Harap isi semua pertanyaan sebelum menyimpan.")
        else:
            df_responses = {}
            for indicator, scores in responses.items():
                if "Usefulness" in indicator: abbr = "PU"
                elif "Ease of Use" in indicator: abbr = "PEOU"
                elif "Attitude" in indicator: abbr = "ATU"
                elif "Intention" in indicator: abbr = "BI"
                elif "Actual" in indicator: abbr = "AU"
                else: abbr = indicator.split()[0]
                
                for i, score in enumerate(scores):
                    df_responses[f"{abbr}_{i+1}"] = score

            df_new_row = pd.DataFrame([df_responses])
            df_new_row['Nama'] = nama if nama else f"Responden_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            try:
                old_df = pd.read_csv(DATA_FILE)
                df = pd.concat([old_df, df_new_row], ignore_index=True)
            except (FileNotFoundError, pd.errors.EmptyDataError):
                df = df_new_row 

            df.to_csv(DATA_FILE, index=False)
            st.success("✅ Jawaban berhasil disimpan! Terima kasih sudah berpartisipasi 🙏")

# --- ### HALAMAN ADMIN (TIDAK ADA PERUBAHAN) ### ---
elif menu == "Lihat Hasil (Admin)":
    st.title("📈 Dashboard Hasil Penelitian TAM")

    st.subheader("Pemuatan Data")
    st.info("Pilih sumber data yang ingin Anda analisis. Anda juga dapat mengelola data kuesioner di tab 'Data Mentah'.")
    
    data_source_option = st.radio(
        "Pilih Sumber Data:",
        ["Gunakan Data Kuesioner (Tersimpan)", "Upload File Baru (CSV/Excel)"],
        key="data_source_selector",
        horizontal=True
    )

    df = None 
    data_from_questionnaire = False

    if data_source_option == "Upload File Baru (CSV/Excel)":
        uploaded_file = st.file_uploader("Upload file .csv atau .xlsx", type=["csv", "xlsx"])
        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                elif uploaded_file.name.endswith('.xlsx'):
                    df = pd.read_excel(uploaded_file)
                st.success(f"Berhasil memuat file: {uploaded_file.name}")
            except Exception as e:
                st.error(f"Gagal membaca file: {e}")
    
    else: # "Gunakan Data Kuesioner (Tersimpan)"
        data_from_questionnaire = True
        try:
            if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
                df = pd.read_csv(DATA_FILE)
            else:
                st.warning("📂 File data kuesioner kosong atau belum ada. Silakan isi kuesioner terlebih dahulu.")
        except Exception as e:
            st.error(f"Gagal memuat data kuesioner: {e}")

    if df is None or df.empty:
        st.warning("Tidak ada data untuk dianalisis. Silakan pilih sumber data yang valid.")
        st.stop() 

    st.markdown("---")
    st.subheader("📊 Hasil Analisis") 

    tab1, tab2, tab3, tab4 = st.tabs([
        "🗃️ Data Mentah & Pengelolaan", 
        "🧪 Uji Instrumen (Validitas & Reliabilitas)", 
        "📉 Uji Hipotesis (SEM)", 
        "🔢 Analisis Deskriptif (Persentase)"
    ])

    with tab1:
        st.subheader("📂 Data Mentah Responden")
        st.dataframe(df)
        num_responden_tab1 = len(df)
        st.info(f"Jumlah responden saat ini: **{num_responden_tab1}** orang.")

        if data_from_questionnaire:
            st.markdown("---")
            st.subheader("🗑️ Hapus Baris Data")
            st.warning("Perhatian: Tindakan ini akan menghapus data secara **PERMANEN** dari file kuesioner.")
            st.write("Untuk menghindari kesalahan, data ditampilkan dengan 'ID Baris' (index). Pilih 'ID Baris' yang ingin Anda hapus.")

            df_with_index = df.reset_index().rename(columns={'index': 'ID Baris'})
            st.dataframe(df_with_index, use_container_width=True)

            indices_to_delete = st.multiselect(
                "Pilih 'ID Baris' yang akan dihapus:",
                df_with_index['ID Baris'].tolist() 
            )

            if st.button("Hapus Baris Terpilih Secara Permanen", key="delete_button"):
                if not indices_to_delete:
                    st.error("Anda belum memilih baris untuk dihapus.")
                else:
                    try:
                        df_new = df.drop(indices_to_delete)
                        df_new.to_csv(DATA_FILE, index=False)
                        st.success(f"Berhasil menghapus {len(indices_to_delete)} baris.")
                        st.info("Memuat ulang halaman untuk menampilkan data terbaru...")
                        st.rerun() 
                    except Exception as e:
                        st.error(f"Gagal menghapus data: {e}")

    try:
        df_numeric = df.select_dtypes(include=['number'])
        num_responden = len(df)
        MIN_RESPONDEN_ANALYSIS = 2
        MAX_RESPONDEN_ANALYSIS = 83
        analysis_allowed = (MIN_RESPONDEN_ANALYSIS < num_responden <= MAX_RESPONDEN_ANALYSIS)

        with tab2:
            st.subheader("STATISTIK DESKRIPTIF & UJI INSTRUMEN")

            if analysis_allowed:
                st.markdown("### Statistik Deskriptif per Item")
                st.write("Tabel ini menunjukkan rata-rata, standar deviasi, nilai minimum, dan maksimum untuk setiap item pertanyaan.")
                st.dataframe(df_numeric.describe().T)
                
                st.markdown("---")
                st.markdown("### Uji Validitas (Corrected Item-Total Correlation)")
                st.write("Item dianggap **valid** jika nilai 'r-hitung' (korelasi) lebih besar dari 'r-tabel' (umumnya **0.3**).")
                
                validity_results = []
                if num_responden > 2:
                    for indicator, qs in questions.items():
                        if "Usefulness" in indicator: abbr = "PU"
                        elif "Ease of Use" in indicator: abbr = "PEOU"
                        elif "Attitude" in indicator: abbr = "ATU"
                        elif "Intention" in indicator: abbr = "BI"
                        elif "Actual" in indicator: abbr = "AU"
                        else: abbr = indicator.split()[0]

                        cols = [f"{abbr}_{i+1}" for i in range(len(qs))]
                        cols_exist = [col for col in cols if col in df_numeric.columns]

                        if len(cols_exist) > 1:
                            total_score = df_numeric[cols_exist].sum(axis=1)
                            for item_col in cols_exist:
                                corrected_total = total_score - df_numeric[item_col]
                                correlation = df_numeric[item_col].corr(corrected_total)
                                status = "Valid" if correlation > 0.3 else "Tidak Valid"
                                validity_results.append({
                                    "Variabel": indicator, "Item": item_col,
                                    "r-hitung (Correlation)": f"{correlation:.3f}", "Keterangan": status
                                })
                        
                    validity_df = pd.DataFrame(validity_results)
                    st.table(validity_df)
                    if "Tidak Valid" in validity_df['Keterangan'].values:
                        st.warning("⚠️ **Terdapat item yang tidak valid.** Item ini sebaiknya ditinjau kembali atau dihapus dari analisis selanjutnya.")
                else:
                    st.info("Jumlah responden belum cukup untuk melakukan uji validitas.")

                st.markdown("---")
                st.markdown("### Uji Reliabilitas (Cronbach's Alpha)")
                st.write("Nilai diatas **0.7** umumnya dianggap reliabel.")
                reliability_results = []
                if num_responden > 1:
                    for indicator, qs in questions.items():
                        if "Usefulness" in indicator: abbr = "PU"
                        elif "Ease of Use" in indicator: abbr = "PEOU"
                        elif "Attitude" in indicator: abbr = "ATU"
                        elif "Intention" in indicator: abbr = "BI"
                        elif "Actual" in indicator: abbr = "AU"
                        else: abbr = indicator.split()[0]
                        
                        cols = [f"{abbr}_{i+1}" for i in range(len(qs))]
                        cols_exist = [col for col in cols if col in df_numeric.columns]
                        
                        if len(cols_exist) > 1:
                            alpha = pg.cronbach_alpha(data=df_numeric[cols_exist])
                            reliability_results.append({
                                "Variabel": indicator, "Cronbach's Alpha": f"{alpha[0]:.3f}",
                                "Keterangan": "Reliabel" if alpha[0] >= 0.7 else "Kurang Reliabel"
                            })
                    st.table(pd.DataFrame(reliability_results))
                else:
                    st.info("Jumlah responden belum cukup untuk melakukan uji reliabilitas.")
            
            else:
                st.warning(f"Jumlah responden ({num_responden}) harus di antara {MIN_RESPONDEN_ANALYSIS+1} dan {MAX_RESPONDEN_ANALYSIS} untuk melakukan analisis ini.")

        with tab3:
            st.subheader("UJI HIPOTESIS (Structural Equation Modeling - SEM)")
            st.write("Hipotesis **terdukung (signifikan)** jika `p-value` **< 0.05**.")

            if analysis_allowed:
                try:
                    model_desc = """
                    # Measurement Model
                    PU =~ PU_1 + PU_2 + PU_3
                    PEOU =~ PEOU_1 + PEOU_2 + PEOU_3
                    ATU =~ ATU_1 + ATU_2 + ATU_3
                    BI =~ BI_1 + BI_2 + BI_3
                    AU =~ AU_1 + AU_2 + AU_3
                    # Structural Model
                    PU ~ PEOU
                    ATU ~ PEOU + PU
                    BI ~ PU + ATU + PEOU
                    AU ~ BI
                    """
                    
                    model = sem.Model(model_desc)
                    results = model.fit(df_numeric)

                    st.markdown("### Hasil Uji Hipotesis")
                    estimates = model.inspect()
                    
                    structural_estimates = estimates[estimates['op'] == '~']
                    structural_estimates = structural_estimates[['lval', 'rval', 'Estimate', 'Std. Err', 'z-value', 'p-value']]
                    
                    structural_estimates['p-value'] = pd.to_numeric(structural_estimates['p-value'], errors='coerce')
                    structural_estimates['Keterangan'] = np.where(structural_estimates['p-value'] < 0.05, "Terdukung", "Tidak Terdukung")
                    
                    st.table(structural_estimates)

                    st.markdown("### Indeks Kecocokan Model (Goodness of Fit)")
                    stats = sem.calc_stats(model)
                    st.table(stats.T)
                    st.info("""
                    **Indeks Penting:**
                    - **CFI & TLI**: Semakin mendekati 1, semakin baik (> 0.90).
                    - **RMSEA**: Semakin mendekati 0, semakin baik (< 0.08).
                    """)

                    st.markdown("### Diagram Jalur (Path Diagram)")
                    try:
                        g = sem.semplot(model, "sem_model.png", plot_covs=True)
                        st.graphviz_chart(g)
                    except Exception as e:
                        st.warning(f"Gagal membuat visualisasi model. Error: {e}")

                except Exception as e:
                    st.error(f"❌ Terjadi kesalahan saat melakukan analisis SEM: {e}")
                    st.warning("Pastikan data Anda (terutama yang di-upload) memiliki nama kolom yang benar (PU_1, PEOU_1, dst.) dan tidak memiliki varians nol.")
            else:
                st.warning(f"Jumlah responden ({num_responden}) harus di antara {MIN_RESPONDEN_ANALYSIS+1} dan {MAX_RESPONDEN_ANALYSIS} untuk melakukan analisis SEM.")

        with tab4:
            st.subheader("ANALISIS DESKRIPTIF PERSENTASE")
            st.write("Analisis ini bertujuan untuk mengetahui tingkat pencapaian skor responden dibandingkan dengan skor idealnya.")

            if analysis_allowed:
                skor_maksimum_item = 5
                jumlah_responden = num_responden

                st.markdown("### Analisis Deskriptif per Variabel")
                st.write("Tabel ini merinci tingkat pencapaian skor untuk setiap variabel penelitian.")

                try:
                    variable_prefixes = sorted(list(set([re.match(r'([A-Za-z_]+)', col).group(1) for col in df_numeric.columns])))
                    variable_prefixes = [var for var in variable_prefixes if 'Unnamed' not in var]
                    hasil_per_variabel = []
                    for var in variable_prefixes:
                        cols_variabel = [col for col in df_numeric.columns if col.startswith(var)]
                        df_variabel = df_numeric[cols_variabel]
                        
                        jumlah_item_variabel = len(cols_variabel)
                        skor_total_sh_variabel = df_variabel.to_numpy().sum()
                        skor_kriterium_sk_variabel = skor_maksimum_item * jumlah_item_variabel * jumlah_responden
                        
                        persentase_p_variabel = (skor_total_sh_variabel * 100) / skor_kriterium_sk_variabel if skor_kriterium_sk_variabel > 0 else 0

                        if 81 <= persentase_p_variabel <= 100: kategori_variabel = "Sangat Baik"
                        elif 61 <= persentase_p_variabel < 81: kategori_variabel = "Baik"
                        elif 41 <= persentase_p_variabel < 61: kategori_variabel = "Cukup"
                        elif 21 <= persentase_p_variabel < 41: kategori_variabel = "Kurang"
                        else: kategori_variabel = "Sangat Kurang"
                        
                        hasil_per_variabel.append({
                            "Variabel": var, "Skor Total (SH)": int(skor_total_sh_variabel),
                            "Skor Ideal (SK)": int(skor_kriterium_sk_variabel),
                            "Persentase (%)": f"{persentase_p_variabel:.2f}", "Kategori": kategori_variabel
                        })

                    if hasil_per_variabel:
                        st.dataframe(pd.DataFrame(hasil_per_variabel), use_container_width=True)
                    else:
                        st.warning("Tidak dapat mengidentifikasi variabel dari nama kolom.")
                except Exception as e:
                    st.error(f"Terjadi kesalahan saat membuat tabel analisis per variabel: {e}")

                st.markdown("### Kesimpulan Analisis Deskriptif Keseluruhan")
                kolom_kuesioner_valid = [col for col in df_numeric.columns if re.match(r'([A-Z]+)_\d+', col)]
                jumlah_item = len(kolom_kuesioner_valid)
                
                skor_total_sh = df_numeric[kolom_kuesioner_valid].to_numpy().sum()
                skor_kriterium_sk = skor_maksimum_item * jumlah_item * jumlah_responden
                
                if skor_kriterium_sk > 0:
                    persentase_p = (skor_total_sh * 100) / skor_kriterium_sk

                    if 81 <= persentase_p <= 100: kategori, emoji = "Sangat Baik", "🎉"
                    elif 61 <= persentase_p < 81: kategori, emoji = "Baik", "👍"
                    elif 41 <= persentase_p < 61: kategori, emoji = "Cukup", "🙂"
                    elif 21 <= persentase_p < 41: kategori, emoji = "Kurang", "😕"
                    else: kategori, emoji = "Sangat Kurang", "😥"

                    st.write("Perhitungan berikut menggabungkan semua jawaban dari seluruh variabel untuk memberikan gambaran umum.")
                    col1, col2, col3 = st.columns(3)
                    col1.metric(label="Total Skor Kriterium (Ideal) - ∑SK", value=f"{int(skor_kriterium_sk):,}")
                    col2.metric(label="Total Skor Jawaban - ∑SH", value=f"{int(skor_total_sh):,}")
                    col3.metric(label="Persentase Pencapaian (P)", value=f"{persentase_p:.2f}%")

                    st.success(f"**Kesimpulan:** Secara keseluruhan, tanggapan responden masuk dalam kategori **{kategori}** {emoji}.")

                    with st.expander("Lihat Detail Rumus Perhitungan Keseluruhan"):
                        st.latex(r"P = \frac{\sum SH}{\sum SK} \times 100\%")
                        st.markdown(f"""
                            - **Skor Kriterium ($\sum SK$)**: `{skor_maksimum_item} (skor maks) × {jumlah_item} (item) × {jumlah_responden} (responden) = {int(skor_kriterium_sk)}`
                            - **Skor Total Jawaban ($\sum SH$)**: `{int(skor_total_sh)}`
                        """) 
                else:
                    st.info("Data tidak cukup untuk perhitungan keseluruhan.")
            
            else:
                st.warning(f"Jumlah responden ({num_responden}) harus di antara {MIN_RESPONDEN_ANALYSIS+1} dan {MAX_RESPONDEN_ANALYSIS} untuk melakukan analisis deskriptif.")
    
    except Exception as e:
        st.error(f"❌ Terjadi error saat memproses analisis: {e}")

        st.error("Pastikan data yang di-upload memiliki format kolom yang sama (PU_1, PU_2, PEOU_1, dst.) dengan data kuesioner.")

