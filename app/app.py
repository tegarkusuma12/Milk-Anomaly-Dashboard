# File: app/app.py

import os
import sys

# Tambahkan direktori 'app' ke path pencarian modul Python agar Vercel dapat mengimpor recommender.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, jsonify, request
import pandas as pd
import joblib
import numpy as np
from datetime import datetime
from recommender import analyze_anomaly

app = Flask(__name__, template_folder='templates', static_folder='static')

# Path File Absolut agar aman saat di-deploy ke Vercel (karena CWD serverless function bisa berbeda)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH_DATA = os.path.join(BASE_DIR, "data", "milk_syntethic_timeseries.csv")
PATH_MODEL = os.path.join(BASE_DIR, "model", "iforest_model_grid.pkl")

# Load model dan data secara global saat start-up
def init_resources():
    model = None
    df_raw = None
    if os.path.exists(PATH_MODEL):
        model = joblib.load(PATH_MODEL)
    if os.path.exists(PATH_DATA):
        df_raw = pd.read_csv(PATH_DATA, parse_dates=['Timestamp'])
    return model, df_raw

model, df_raw = init_resources()

def run_anomaly_detection(df):
    """Menjalankan sistem deteksi anomali hibrida (AI + Pakar) pada dataframe"""
    if df.empty:
        return df
        
    fitur_sensor = ['pH', 'Temprature', 'Taste', 'Odor', 'Fat ', 'Turbidity', 'Colour']
    
    # AI (Isolation Forest)
    df['status_anomali'] = model.predict(df[fitur_sensor])
    
    # Sistem Pakar Override
    batas_kritis = (
        (df['pH'] < 6.4) |          # Asam ekstrem 
        (df['pH'] > 7.0) |          # Basa ekstrem 
        (df['Temprature'] >= 50)    # Suhu ekstrem 
    )
    
    df['status_anomali'] = np.where(batas_kritis, -1, df['status_anomali'])
    df['status_text'] = df['status_anomali'].map({1: 'Normal', -1: 'Anomali'})
    return df

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulator')
def simulator():
    return render_template('simulator.html')

@app.route('/api/data', methods=['GET'])
def get_data():
    if df_raw is None or model is None:
        return jsonify({"error": "File data atau model tidak ditemukan."}), 500
    
    # Prediksi seluruh data terlebih dahulu agar status_anomali terisi
    df_processed = run_anomaly_detection(df_raw.copy())
    
    # Urutan waktu
    df_processed = df_processed.sort_values('Timestamp', ascending=True)
    
    # Ambil filter tanggal & range
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    time_range = request.args.get('range', '7d')
    
    min_date = df_processed['Timestamp'].min().date()
    max_date = df_processed['Timestamp'].max().date()
    
    if start_date_str and end_date_str:
        try:
            start_date = pd.to_datetime(start_date_str)
            end_date = pd.to_datetime(end_date_str) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            mask = (df_processed['Timestamp'] >= start_date) & (df_processed['Timestamp'] <= end_date)
            df_filtered = df_processed.loc[mask].copy()
        except Exception:
            df_filtered = df_processed.copy()
    else:
        # Filter berdasarkan range relatif terhadap waktu kejadian TERAKHIR di dataset
        latest_timestamp = df_processed['Timestamp'].max()
        if time_range == '24h':
            df_filtered = df_processed[df_processed['Timestamp'] >= latest_timestamp - pd.Timedelta(hours=24)].copy()
        elif time_range == '7d':
            df_filtered = df_processed[df_processed['Timestamp'] >= latest_timestamp - pd.Timedelta(days=7)].copy()
        elif time_range == '30d':
            df_filtered = df_processed[df_processed['Timestamp'] >= latest_timestamp - pd.Timedelta(days=30)].copy()
        else: # 'all'
            df_filtered = df_processed.copy()
            
    # Tentukan range tanggal yang saat ini aktif ditampilkan
    active_start = df_filtered['Timestamp'].min().strftime('%Y-%m-%d') if not df_filtered.empty else min_date.strftime('%Y-%m-%d')
    active_end = df_filtered['Timestamp'].max().strftime('%Y-%m-%d') if not df_filtered.empty else max_date.strftime('%Y-%m-%d')
        
    if df_filtered.empty:
        return jsonify({
            "kpis": {
                "total_data": 0,
                "tingkat_keandalan": 100.0,
                "total_anomali": 0,
                "persen_anomali": 0.0,
                "status_sekarang": "N/A",
                "delta_teks": "Tidak ada data"
            },
            "chart_data": [],
            "logs": [],
            "anomalies": [],
            "date_range": {
                "min": min_date.strftime('%Y-%m-%d'),
                "max": max_date.strftime('%Y-%m-%d')
            }
        })
        
    # Perhitungan KPI
    total_data = len(df_filtered)
    total_anomali = len(df_filtered[df_filtered['status_anomali'] == -1])
    persen_anomali = round((total_anomali / total_data) * 100, 2) if total_data > 0 else 0.0
    tingkat_keandalan = round(100.0 - persen_anomali, 1)
    
    # Status Terkini (batch terakhir)
    data_terkini = df_filtered.iloc[-1]
    if data_terkini['status_anomali'] == -1:
        status_sekarang = "🔍 Butuh Mitigasi"
        delta_teks = "Cek Panel Rekomendasi"
    else:
        status_sekarang = "✅ Lolos QC"
        delta_teks = "Standar Terpenuhi"
        
    kpis = {
        "total_data": int(total_data),
        "tingkat_keandalan": float(tingkat_keandalan),
        "total_anomali": int(total_anomali),
        "persen_anomali": float(persen_anomali),
        "status_sekarang": status_sekarang,
        "delta_teks": delta_teks
    }
    
    # Format data untuk grafik (Chart.js)
    chart_data = []
    for _, row in df_filtered.iterrows():
        chart_data.append({
            "timestamp": row['Timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            "pH": float(row['pH']),
            "temperature": float(row['Temprature']),
            "status_anomali": int(row['status_anomali'])
        })
        
    # Format data untuk Raw Logs (limit 150 baris terakhir agar render tidak lambat, diurutkan descending)
    df_logs = df_filtered.sort_values('Timestamp', ascending=False)
    logs = []
    for idx, row in df_logs.iterrows():
        logs.append({
            "index": int(idx),
            "timestamp": row['Timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            "pH": float(row['pH']),
            "temperature": float(row['Temprature']),
            "odor": int(row['Odor']),
            "turbidity": int(row['Turbidity']),
            "fat": int(row['Fat ']),
            "taste": int(row['Taste']),
            "colour": int(row['Colour']),
            "status_anomali": int(row['status_anomali']),
            "status_text": str(row['status_text'])
        })
        
    # List anomali untuk dropdown panel rekomendasi
    df_anomali = df_filtered[df_filtered['status_anomali'] == -1].sort_values('Timestamp', ascending=False)
    anomalies = []
    for idx, row in df_anomali.iterrows():
        anomalies.append({
            "index": int(idx),
            "timestamp": row['Timestamp'].strftime('%d %b %Y, %H:%M'),
            "pH": float(row['pH']),
            "temperature": float(row['Temprature'])
        })
        
    return jsonify({
        "kpis": kpis,
        "chart_data": chart_data,
        "logs": logs,
        "anomalies": anomalies,
        "date_range": {
            "min": min_date.strftime('%Y-%m-%d'),
            "max": max_date.strftime('%Y-%m-%d')
        },
        "active_range": {
            "start": active_start,
            "end": active_end
        }
    })

@app.route('/api/anomaly-details/<int:index>', methods=['GET'])
def get_anomaly_details(index):
    if df_raw is None:
        return jsonify({"error": "Data belum dimuat"}), 500
        
    try:
        row = df_raw.iloc[index].to_dict()
        masalah, rekomendasi = analyze_anomaly(row)
        return jsonify({
            "timestamp": df_raw.loc[index, 'Timestamp'].strftime('%d %b %Y, %H:%M'),
            "pH": float(row['pH']),
            "temperature": float(row['Temprature']),
            "masalah": masalah,
            "rekomendasi": rekomendasi
        })
    except Exception as e:
        return jsonify({"error": f"Gagal memproses data indeks {index}: {str(e)}"}), 400

@app.route('/api/predict-simulator', methods=['POST'])
def predict_simulator():
    if model is None:
        return jsonify({"error": "Model tidak siap"}), 500
        
    data = request.json
    try:
        # Validasi & konversi data sensor
        ph = float(data.get('pH', 6.6))
        temp = float(data.get('Temprature', 37.0))
        taste = int(data.get('Taste', 1))
        odor = int(data.get('Odor', 1))
        fat = int(data.get('Fat ', 1)) # Note the space
        turbidity = int(data.get('Turbidity', 0))
        colour = int(data.get('Colour', 255))
        
        # Buat array input untuk model (urutan harus sama dengan fitur_sensor)
        # fitur_sensor = ['pH', 'Temprature', 'Taste', 'Odor', 'Fat ', 'Turbidity', 'Colour']
        input_data = np.array([[ph, temp, taste, odor, fat, turbidity, colour]])
        
        # Prediksi AI
        ai_pred = int(model.predict(input_data)[0])
        
        # Sistem pakar override
        is_pakar_anomaly = (ph < 6.4) or (ph > 7.0) or (temp >= 50.0)
        status_anomali = -1 if (is_pakar_anomaly or ai_pred == -1) else 1
        status_text = 'Anomali' if status_anomali == -1 else 'Normal'
        
        # Buat row dict untuk penganalisis anomali
        row_dict = {
            'pH': ph,
            'Temprature': temp,
            'Taste': taste,
            'Odor': odor,
            'Fat ': fat,
            'Turbidity': turbidity,
            'Colour': colour
        }
        
        masalah = []
        rekomendasi = []
        if status_anomali == -1:
            masalah, rekomendasi = analyze_anomaly(row_dict)
            
        return jsonify({
            "status_anomali": status_anomali,
            "status_text": status_text,
            "masalah": masalah,
            "rekomendasi": rekomendasi
        })
        
    except Exception as e:
        return jsonify({"error": f"Gagal melakukan simulasi: {str(e)}"}), 400

if __name__ == '__main__':
    # Pastikan file static dan templates dibaca dengan benar
    app.run(host='0.0.0.0', port=5000, debug=True)