# File: app/recommender.py

def analyze_anomaly(row):
    """
    Fungsi ini menganalisis baris data sensor yang anomali
    dan mengembalikan daftar masalah (Root Cause) serta rekomendasi tindakan teknis (SOP).
    """
    masalah = []
    rekomendasi = []
    
    # 1. Parameter Kimia (pH) - Normal susu sapi: 6.5 - 6.7
    if row['pH'] < 6.4: 
        masalah.append("pH Drop (< 6.4): Susu mulai asam. Indikasi fermentasi laktat akibat aktivitas bakteri tinggi.")
        rekomendasi.append("Tindakan Cepat: Isolasi batch tangki ini. Lakukan uji mikrobiologi segera.")
        rekomendasi.append("Investigasi: Periksa apakah ada jeda waktu terlalu lama sebelum pendinginan.")
    elif row['pH'] > 6.8: 
        masalah.append("pH Basa (> 6.8): Ketidakwajaran kimiawi. Kemungkinan mastitis parah pada bahan baku atau kontaminasi kimia.")
        rekomendasi.append("Tindakan Cepat: Tahan rilis produk (Hold Release). Ambil sampel untuk uji residu antibiotik dan kimia.")
        rekomendasi.append("Investigasi: Audit log sistem pembersihan CIP (Cleaning-in-Place). Cek apakah pembilasan soda api kurang bersih.")
        
    # 2. Parameter Termal (Suhu) 
    if row['Temprature'] >= 50: 
        masalah.append(f"Suhu Ekstrem ({row['Temprature']}°C): Kegagalan fatal pada sistem pendingin (Chiller/Heat Exchanger).")
        rekomendasi.append("Tindakan Cepat: Hentikan aliran pipa ke tangki utama. Aktifkan pendingin cadangan.")
        rekomendasi.append("Investigasi: Tim Maintenance wajib memeriksa kebocoran freon atau kerusakan kompresor Chiller.")
    elif 40 <= row['Temprature'] < 50:
        masalah.append(f"Suhu Warning ({row['Temprature']}°C): Anomali fluktuasi termal. Beban pendinginan tidak stabil.")
        rekomendasi.append("Tindakan Cepat: Lakukan pengecekan fisik pada panel suhu mesin. Tambahkan durasi sirkulasi pendinginan.")
        
    # 3. Parameter Organoleptik & Fisik
    if row['Odor'] == 0: 
        masalah.append("Uji Sensorik: Terdeteksi bau menyimpang.")
        rekomendasi.append("Tindakan Cepat: Reject batch ini ke IPAL jika hasil lab mengonfirmasi pembusukan.")
        
    if row['Turbidity'] == 1: 
        masalah.append("Uji Fisik: Kekeruhan abnormal. Indikasi awal penggumpalan protein (curdling) atau filtrasi kotor.")
        rekomendasi.append("Investigasi: Cek dan bersihkan saringan utama (Filter Strainer). Periksa tekanan pompa dorong.")

    # 4. Parameter Organoleptik Lanjutan & Komposisi
    if row['Taste'] == 0: 
        masalah.append("Uji Rasa: Terdeteksi penyimpangan.")
        rekomendasi.append("Tindakan Cepat: Lakukan uji organoleptik ulang oleh panelis bersertifikat. Blokir batch dari pengemasan.")
        rekomendasi.append("Investigasi: Periksa potensi percampuran dengan air bilasan di dalam pipa distribusi.")
        
    if row['Fat '] == 0:
        masalah.append("Komposisi: Kadar lemak terdeteksi rendah.")
        rekomendasi.append("Tindakan Cepat: Alihkan rute aliran susu ini ke tangki produksi Susu Rendah Lemak (Low-Fat/Skim).")
        rekomendasi.append("Investigasi: Evaluasi kualitas bahan baku dari peternak (potensi pengenceran air).")

    # 5. Parameter Visual (Warna)
    if row['Colour'] < 255: 
        masalah.append(f"Uji Visual: Warna tidak standar/kusam (Skala: {row['Colour']}). Indikasi kontaminasi fisik, air kotor, atau mastitis (darah).")
        rekomendasi.append("Tindakan Cepat: Reject batch sepenuhnya. Lakukan sanitasi total (CIP) pada seluruh jalur pipa yang dilewati.")
        
    # 6. Fallback (Anomali Multivariat dari Isolation Forest yang tidak tertangkap aturan tunggal di atas)
    if not masalah:
        masalah.append("Sistem AI mendeteksi penyimpangan pola multivariat (kombinasi aneh antar sensor).")
        rekomendasi.append("Tindakan Cepat: Ambil sampel manual untuk uji lab lengkap secara menyeluruh (Kimia & Fisik).")
        rekomendasi.append("Investigasi: Minta teknisi instrumen melakukan kalibrasi ulang pada sensor IoT di lini produksi ini.")

    # Menghapus duplikat rekomendasi jika ada (menjaga urutan tetap rapi)
    rekomendasi_unik = []
    for rec in rekomendasi:
        if rec not in rekomendasi_unik:
            rekomendasi_unik.append(rec)
    
    return masalah, rekomendasi_unik