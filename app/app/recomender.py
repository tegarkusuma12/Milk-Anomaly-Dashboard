# File: app/recommender.py

def analyze_anomaly(row):
    """
    Fungsi ini menganalisis baris data sensor yang anomali
    dan mengembalikan daftar masalah serta rekomendasi tema industri.
    """
    masalah = []
    rekomendasi = []
    
    # 1. Parameter Kimia (pH)
    if row['pH'] < 6.4: 
        masalah.append("pH < 6.4: Asiditas tinggi (Risiko fermentasi bakteri)")
        rekomendasi.append("Tema: Audit & Otomatisasi Sanitasi CIP (Cleaning in Place)")
    elif row['pH'] > 6.8: 
        masalah.append("pH > 6.8: Basa tidak wajar (Cek residu bahan pembersih / Mastitis)")
        rekomendasi.append("Tema: Sistem Deteksi Kontaminasi Kimia Berbasis IoT")
        
    # 2. Parameter Termal (Suhu)
    if row['Temprature'] >= 50: 
        masalah.append("Suhu Kritis (>=50°C): Kegagalan total sistem pendingin tangki")
        rekomendasi.append("Tema: Predictive Maintenance pada Heat Exchanger")
    elif 40 <= row['Temprature'] < 50:
        masalah.append("Suhu Warning (40-49°C): Fluktuasi termal terdeteksi")
        rekomendasi.append("Tema: Optimasi Logistik Cold Chain & A/B Testing Sensor Suhu")
        
    # 3. Parameter Organoleptik & Fisik
    if row['Odor'] == 0: 
        masalah.append("Uji Organoleptik Gagal: Terdeteksi bau menyimpang")
        rekomendasi.append("Tema: Quality Control Otomatis & Standar Zero Defect")
        
    if row['Turbidity'] == 1: 
        masalah.append("Fisik: Kekeruhan tinggi (Indikasi penggumpalan protein/filtrasi buruk)")
        rekomendasi.append("Tema: Upgrade Sistem Ultra-Filtrasi (Lean Production)")

    # Fallback jika mesin mendeteksi anomali dari kombinasi fitur lain
    if not masalah:
        masalah.append("Kombinasi sensor multivariat tidak wajar terdeteksi oleh AI.")
        rekomendasi.append("Tema: Investigasi Menyeluruh & Kalibrasi Ulang Sensor")

    # Menghapus duplikat tema jika ada
    rekomendasi = list(set(rekomendasi))
    
    return masalah, rekomendasi