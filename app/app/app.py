# File: app/app.py

import streamlit as st
import pandas as pd
import joblib
import os
from recommender import analyze_anomaly

# Konfigurasi Halaman (Harus dipanggil pertama kali)
st.set_page_config(page_title="Dairy Intelligence Dashboard", layout="wide", page_icon="🥛")

# Tentukan Path File (Menggunakan path relatif dari root folder)
PATH_DATA = "data/milknew.csv"
PATH_MODEL = "model/iforest_model.pkl"

# Header Dashboard
st.title("🥛 Industrial Dashboard: Sistem Deteksi Anomali & Rekomendasi")
st.markdown("Dashboard ini dirancang untuk membantu **Knowledge Worker** mendeteksi kegagalan proses secara *real-time* dan memberikan rekomendasi tindakan strategis.")

# --- LOAD DATA & MODEL ---
@st.cache_data
def load_data():
    if os.path.exists(PATH_DATA):
        return pd.read_csv(PATH_DATA)
    return None

@st.cache_resource
def load_model():
    if os.path.exists(PATH_MODEL):
        return joblib.load(PATH_MODEL)
    return None

df = load_data()
model = load_model()

if df is None or model is None:
    st.error("⚠️ File Data atau Model tidak ditemukan. Pastikan Anda menjalankan perintah 'streamlit run app/app.py' dari folder utama proyek.")
else:
    # Fitur Sensor (Sama seperti saat training)
    fitur_sensor = ['pH', 'Temprature', 'Taste', 'Odor', 'Fat ', 'Turbidity', 'Colour']
    
    # Lakukan Prediksi
    df['status_anomali'] = model.predict(df[fitur_sensor])
    df['status_text'] = df['status_anomali'].map({1: 'Normal', -1: 'Anomali'})
    
    # Hitung KPI
    total_data = len(df)
    total_anomali = len(df[df['status_anomali'] == -1])
    persen_anomali = round((total_anomali / total_data) * 100, 2)
    
    # --- BAGIAN 1: KPI METRICS ---
    st.markdown("### 📊 Key Performance Indicators (KPI)")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Batch Diproses", total_data)
    col2.metric("Batch Anomali Terdeteksi", total_anomali, delta=f"{persen_anomali}% Risk", delta_color="inverse")
    col3.metric("Rata-rata Suhu Pabrik", f"{round(df['Temprature'].mean(), 1)} °C")
    
    st.divider()

    # --- BAGIAN 2: KNOWLEDGE WORKER ACTION PANEL ---
    st.markdown("### 🚨 Panel Rekomendasi Tindakan")
    
    # Filter data yang anomali saja
    df_anomali = df[df['status_anomali'] == -1].reset_index(drop=True)
    
    if not df_anomali.empty:
        # Biarkan user memilih batch mana yang mau dianalisis
        pilihan_batch = st.selectbox("Pilih Batch Anomali untuk Dianalisis:", df_anomali.index, format_func=lambda x: f"Batch Error #{x} (Suhu: {df_anomali.loc[x, 'Temprature']}°C, pH: {df_anomali.loc[x, 'pH']})")
        
        baris_terpilih = df_anomali.loc[pilihan_batch]
        masalah, rekomendasi = analyze_anomaly(baris_terpilih)
        
        # Tampilkan dalam bentuk kartu informasi
        with st.container():
            col_masalah, col_solusi = st.columns(2)
            
            with col_masalah:
                st.error("**Akar Masalah (Root Cause):**")
                for m in masalah:
                    st.write(f"- {m}")
                    
            with col_solusi:
                st.success("**Rekomendasi Tema Industri (Solusi):**")
                for r in rekomendasi:
                    st.write(f"- **{r}**")
    else:
        st.success("🎉 Luar biasa! Saat ini tidak ada anomali yang terdeteksi di pabrik.")

    st.divider()
    
    # --- BAGIAN 3: DATA TABEL PREVIEW ---
    st.markdown("### 📋 Log Data Sensor (B.I Report Preview)")
    st.dataframe(df[['pH', 'Temprature', 'Odor', 'Turbidity', 'status_text']].head(100), use_container_width=True)