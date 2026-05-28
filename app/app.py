# File: app/app.py

import streamlit as st
import pandas as pd
import joblib
import os
from datetime import datetime
from recommender import analyze_anomaly

st.set_page_config(page_title="Dairy Intelligence Dashboard", layout="wide", page_icon="🥛")

# 1. Update Path File
PATH_DATA = "data/milk_syntethic_timeseries.csv"
PATH_MODEL = "model/iforest_model.pkl"

st.title("🥛 Industrial Dashboard: Real-Time Anomaly Detection")
st.markdown("Dashboard ini memantau sensor operasional secara runtun waktu (*time-series*) dan memberikan rekomendasi mitigasi berbasis AI.")

@st.cache_data
def load_data():
    if os.path.exists(PATH_DATA):
        df = pd.read_csv(PATH_DATA, parse_dates=['Timestamp'])
        return df
    return None

@st.cache_resource
def load_model():
    if os.path.exists(PATH_MODEL):
        return joblib.load(PATH_MODEL)
    return None

df_raw = load_data()
model = load_model()

if df_raw is None or model is None:
    st.error("⚠️ File Data atau Model tidak ditemukan.")
else:
    # --- FITUR BARU: SIDEBAR UNTUK FILTER WAKTU ---
    st.sidebar.header("⚙️ Kontrol & Filter")
    st.sidebar.markdown("Gunakan panel ini untuk menyaring data operasional pabrik.")
    
    # Mengambil tanggal paling awal dan paling akhir dari dataset
    min_date = df_raw['Timestamp'].min().date()
    max_date = df_raw['Timestamp'].max().date()
    
    # Widget kalender untuk rentang waktu
    rentang_tanggal = st.sidebar.date_input(
        "Pilih Rentang Analisis:",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Logika Filtering Data
    if len(rentang_tanggal) == 2:
        start_date, end_date = rentang_tanggal
        # Konversi ke format datetime pandas, pastikan end_date mencakup hingga jam 23:59
        mask = (df_raw['Timestamp'] >= pd.to_datetime(start_date)) & \
               (df_raw['Timestamp'] <= pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1))
        df = df_raw.loc[mask].copy()
    else:
        # Jika user baru memilih 1 tanggal (sedang mengklik), gunakan data hari itu saja
        df = df_raw[df_raw['Timestamp'].dt.date == rentang_tanggal[0]].copy()
        
    st.sidebar.success(f"Menampilkan {len(df)} batch data pada rentang waktu terpilih.")
    
    # Jika hasil filter kosong
    if df.empty:
        st.warning("⚠️ Tidak ada data pabrik pada rentang tanggal tersebut. Silakan atur ulang filter di sidebar.")
    else:
        # AI melakukan Prediksi pada data yang sudah di-filter
        fitur_sensor = ['pH', 'Temprature', 'Taste', 'Odor', 'Fat ', 'Turbidity', 'Colour']
        df['status_anomali'] = model.predict(df[fitur_sensor])
        df['status_text'] = df['status_anomali'].map({1: 'Normal', -1: 'Anomali'})
        
        total_data = len(df)
        total_anomali = len(df[df['status_anomali'] == -1])
        persen_anomali = round((total_anomali / total_data) * 100, 2) if total_data > 0 else 0
        
        # --- KPI METRICS ---
        st.markdown("### 📊 Key Performance Indicators (KPI)")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Batch Tersaring", total_data)
        col2.metric("Alarm Anomali (Terfilter)", total_anomali, delta=f"{persen_anomali}% Failure Rate", delta_color="inverse")
        
        data_terkini = df.iloc[-1]
        status_sekarang = "🔴 BAHAYA" if data_terkini['status_anomali'] == -1 else "🟢 AMAN"
        col3.metric("Status Pabrik (Akhir Periode)", status_sekarang)
        
        st.divider()

        # --- GRAFIK RUNTUN WAKTU ---
        st.markdown("### 📈 Tren Suhu Operasional (Time-Series)")
        df_chart = df.set_index('Timestamp')
        st.line_chart(df_chart['Temprature'], height=300, color="#2ecc71")
        st.caption("*Catatan Visual: Jika terjadi lonjakan drastis pada grafik di atas, sistem akan memicu kartu rekomendasi di bawah ini.*")
        
        st.divider()

        # --- PANEL REKOMENDASI KNOWLEDGE WORKER ---
        st.markdown("### 🚨 Panel Rekomendasi Tindakan (Knowledge Base)")
        df_anomali = df[df['status_anomali'] == -1].reset_index(drop=True)
        
        if not df_anomali.empty:
            pilihan_batch = st.selectbox(
                "Pilih Histori Waktu Anomali untuk Dianalisis:", 
                df_anomali.index, 
                format_func=lambda x: f"Waktu Kejadian: {df_anomali.loc[x, 'Timestamp'].strftime('%d %b %Y, %H:%M')} (Suhu: {df_anomali.loc[x, 'Temprature']}°C)"
            )
            
            baris_terpilih = df_anomali.loc[pilihan_batch]
            masalah, rekomendasi = analyze_anomaly(baris_terpilih)
            
            with st.container(border=True):
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
            st.success("🎉 Luar biasa! Pada rentang waktu ini tidak ada anomali yang terdeteksi.")

        st.divider()
        st.markdown("### 📋 Log Sensor Raw Data")
        st.dataframe(df[['Timestamp', 'pH', 'Temprature', 'Odor', 'Turbidity', 'status_text']], use_container_width=True)