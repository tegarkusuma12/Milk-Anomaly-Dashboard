# File: app/app.py

import streamlit as st
import pandas as pd
import joblib
import os
import numpy as np 
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from datetime import datetime
from recommender import analyze_anomaly

st.set_page_config(page_title="Dairy Intelligence Dashboard", layout="wide", page_icon="🥛")

# 1. Update Path File
PATH_DATA = "data/milk_syntethic_timeseries.csv"
PATH_MODEL = "model/iforest_model_grid.pkl"

st.title("Dashboard Deteksi Anomali Susu dan Rekomendasi Mitigasi🥛")
st.markdown("Dashboard ini memantau sensor operasional secara runtun waktu (*time-series*) menggunakan kombinasi **Machine Learning** dan **SOP Sistem Pakar**.")

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
        # ==========================================
        # MESIN ANALISIS HIBRIDA (AI + PAKAR)
        # ==========================================
        fitur_sensor = ['pH', 'Temprature', 'Taste', 'Odor', 'Fat ', 'Turbidity', 'Colour']
        
        # FASE 1: AI melakukan Prediksi
        df['status_anomali'] = model.predict(df[fitur_sensor])
        
        # FASE 2: Sistem Pakar Mencegat Kerusakan Fatal
        batas_kritis = (
            (df['pH'] < 6.4) |          # Asam ekstrem 
            (df['pH'] > 7.0) |          # Basa ekstrem 
            (df['Temprature'] >= 50)    # Suhu ekstrem 
        )
        
        # FASE 3: Eksekusi Override Hibrida
        df['status_anomali'] = np.where(batas_kritis, -1, df['status_anomali'])
        
        # Mapping label untuk UI
        df['status_text'] = df['status_anomali'].map({1: 'Normal', -1: 'Anomali'})
        
        # ==========================================
        # METRIK & VISUALISASI
        # ==========================================
        total_data = len(df)
        total_anomali = len(df[df['status_anomali'] == -1])
        persen_anomali = round((total_anomali / total_data) * 100, 2) if total_data > 0 else 0
        
        # --- KPI METRICS ---
        st.markdown("### 📊 Key Performance Indicators (KPI)")
        col1, col2, col3 = st.columns(3)
        
        # Metrik 1: Total Produksi
        col1.metric("Total Batch Diproses", total_data)
        
        # Metrik 2: Tingkat Keandalan (Dibalik dari Failure Rate menjadi Success Rate)
        tingkat_keandalan = 100 - persen_anomali
        col2.metric(
            "Tingkat Keandalan Produksi", 
            f"{tingkat_keandalan:.1f}%", 
            delta=f" - {persen_anomali}% Anomali Ditemukan", 
            delta_color="normal"
        )
        
        # Metrik 3: Status Batch Terakhir dengan narasi yang lebih profesional
        data_terkini = df.iloc[-1]
        if data_terkini['status_anomali'] == -1:
            status_sekarang = "🔍 Butuh Mitigasi"
            warna_status = "normal"
            delta_teks = " - Cek Panel Rekomendasi"
        else:
            status_sekarang = "✅ Lolos QC"
            warna_status = "normal"
            delta_teks = "Standar Terpenuhi"
            
        col3.metric("Status Batch Terkini", status_sekarang, delta=delta_teks, delta_color=warna_status)

        # --- GRAFIK RUNTUN WAKTU (SUHU & pH) ---
        st.markdown("### 📈 Tren Sensor Operasional (Time-Series)")
        
        # Membuat kerangka grafik bertumpuk (2 baris, 1 kolom) dengan sumbu X (waktu) yang terhubung
        fig = make_subplots(
            rows=2, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.1,
            subplot_titles=("Sensor Suhu (°C)", "Sensor Keasaman (pH)")
        )
        
        # 1. Memasukkan Garis Suhu (Row 1)
        fig.add_trace(
            go.Scatter(
                x=df['Timestamp'], y=df['Temprature'], 
                mode='lines', name='Suhu',
                line=dict(color='#2ecc71', width=2),
                hovertemplate="<b>Suhu:</b> %{y}°C<extra></extra>"
            ), row=1, col=1
        )
        
        # 2. Memasukkan Garis pH (Row 2)
        fig.add_trace(
            go.Scatter(
                x=df['Timestamp'], y=df['pH'], 
                mode='lines', name='pH',
                line=dict(color='#3498db', width=2), # Warna biru untuk membedakan dari suhu
                hovertemplate="<b>pH:</b> %{y}<extra></extra>"
            ), row=2, col=1
        )
        
        # 3. Menambahkan Garis Batas Kritis (Threshold) khusus untuk pH
        fig.add_hline(y=7.0, line_dash="dot", line_color="#e74c3c", line_width=2, row=2, col=1, annotation_text="Batas Basa Kritis", annotation_position="top right")
        fig.add_hline(y=6.4, line_dash="dot", line_color="#e74c3c", line_width=2, row=2, col=1, annotation_text="Batas Asam Kritis", annotation_position="bottom right")
        
        # Kustomisasi Layout Keseluruhan
        fig.update_layout(
            hovermode="x unified",
            showlegend=False,
            height=500, # Tinggikan kanvas karena ada dua grafik
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        # Kustomisasi Sumbu X agar memunculkan Jam dan Tanggal di bagian paling bawah
        fig.update_xaxes(tickformat="%d %b\n%H:%M", row=2, col=1)
        
        st.plotly_chart(fig, use_container_width=True)
        st.caption("*Garis putus-putus merah pada grafik pH menunjukkan batas kritis (SOP Pabrik). Jika garis biru menembus batas tersebut, sistem pakar akan otomatis memicu mitigasi.*")
        
        st.divider()

        # --- PANEL REKOMENDASI KNOWLEDGE WORKER ---
        st.markdown("### 🚨 Panel Rekomendasi Tindakan")
        df_anomali = df[df['status_anomali'] == -1].reset_index(drop=True)
        
        if not df_anomali.empty:
            pilihan_batch = st.selectbox(
                "Pilih Histori Waktu Anomali untuk Dianalisis:", 
                df_anomali.index, 
                format_func=lambda x: f"Waktu Kejadian: {df_anomali.loc[x, 'Timestamp'].strftime('%d %b %Y, %H:%M')} (Suhu: {df_anomali.loc[x, 'Temprature']}°C, pH: {df_anomali.loc[x, 'pH']})"
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
                    st.success("**Rekomendasi Tindakan (Mitigasi):**")
                    for r in rekomendasi:
                        st.write(f"- **{r}**")
        else:
            st.success("Tidak ada anomali yang terdeteksi.")

        st.divider()
        st.markdown("### 📋 Log Sensor Raw Data")
        # Menampilkan tabel lengkap agar teknisi bisa melihat data detailnya
        st.dataframe(df[['Timestamp', 'pH', 'Temprature', 'Odor', 'Turbidity', 'Fat ', 'Colour', 'status_text']], use_container_width=True)