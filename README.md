# Dairyboard 🥛 - Sistem Deteksi Anomali & Rekomendasi Mitigasi Kualitas Susu

Dairyboard adalah platform dasbor pemantauan berbasis AI (Machine Learning) dan Sistem Pakar (*Rule-Based*) yang dirancang untuk mendeteksi anomali pada proses kontrol kualitas (QC) susu di lini produksi pabrik secara *real-time*.

Aplikasi ini telah dimigrasi dari Streamlit menjadi aplikasi berbasis **Flask Web Server** dengan antarmuka yang responsif.

---

## 🛠️ Metodologi Pengembangan & Alur Kerja Sistem

### 1. Rekayasa Data Runtun Waktu (*Data Synthesis dari Milk.csv*)
* **Sumber Data Referensi**: Profil awal data referensi diambil dari dataset kualitas susu publik di Kaggle: [Milk Quality Prediction Dataset](https://www.kaggle.com/datasets/cpluzshrijayan/milkquality/data).
* **Berdasarkan Distribusi Statistik**: Data historis dibangkitkan secara sintetis dengan merujuk pada profil distribusi statistik riil (Nilai Tengah/Mean, Simpangan Baku/Standard Deviation, dan Probabilitas Rasio) dari data referensi tersebut khusus pada kondisi operasional susu normal.
* **Struktur Dataset**: Menghasilkan dataset berformat deret waktu (*time-series*) yang dilengkapi kolom `Timestamp` beserta sensor IoT pendukung: `pH`, `Temprature` (Suhu), `Taste`, `Odor`, `Fat`, `Turbidity`, dan `Colour`.
* **Penyuntikan Skenario Anomali**: Untuk menguji keandalan deteksi sistem, beberapa titik data anomali ekstrem dan kombinasi aneh (multivariat) disuntikkan secara sengaja ke dalam database simulasi operasional.

### 2. Deteksi Anomali Berbasis Kecerdasan Buatan (*Machine Learning*)
* **Algoritma Isolation Forest**: Sistem menggunakan algoritma *Isolation Forest* yang dilatih secara *unsupervised* untuk mempelajari profil batas "susu normal".
* **Deteksi Multivariat**: Model mampu mengidentifikasi anomali yang tidak kasat mata secara langsung (misal: kondisi di mana suhu dan pH secara individual tampak normal, namun kombinasinya melanggar batas korelasi fisik susu yang sehat).

### 3. Mesin Rekomendasi Tindakan (*Knowledge Base / Expert System*)
* **Sistem Pakar Berbasis Aturan (Rule-Based)**: Ketika modul *Machine Learning* menandai suatu batch sebagai anomali (`status_anomali = -1`), mesin pakar akan memeriksa data sensor terkait terhadap batas-batas SOP pabrik.
* **Analisis Akar Masalah & Mitigasi**: Menentukan **Akar Masalah (*Root Cause*)** secara spesifik (misal: "Suhu pasteurisasi terlampau tinggi" atau "Kontaminasi zat asam") dan langsung mengeluarkan instruksi **Tindakan Mitigasi (SOP)** konkret untuk teknisi di lapangan.

### 4. Dasbor Interaktif & Business Intelligence
* Dashboard modern berbasis web dibangun menggunakan Flask (backend) dan HTML/CSS/JavaScript murni (frontend).
* Dilengkapi visualisasi tren sensor interaktif menggunakan **Chart.js** yang diperhalus menggunakan font tipografi **Inter** dengan kontras tinggi untuk kenyamanan pemantauan operator pabrik.

---

## 🌟 Fitur Utama Dasbor

1. **Metrik KPI Real-Time dengan Highlight Kontras**:
   * **Total Batch Diproses**: Menampilkan jumlah data log berjalan dalam rentang filter.
   * **Tingkat Keandalan Produksi**: Dilengkapi highlight **merah solid** (`X Anomali Ditemukan -- Y%`) bila ada anomali untuk menarik perhatian instan operator.
   * **Status Batch Terkini**: Menampilkan status QC batch paling baru, lengkap dengan highlight **kuning solid** (`Cek Panel Rekomendasi`) jika batch terkini bermasalah.
2. **Grafik Tren Runtun Waktu dengan Filter Kapsul**:
   * Filter cepat interaktif: **24 Jam**, **7 Hari**, **30 Hari**, dan **Semua**.
   * Integrasi sinkronisasi dua arah: mengklik tab filter waktu otomatis memperbarui kalender filter tanggal di sidebar, begitu pula sebaliknya.
3. **Simulator Pengujian Mandiri (`/simulator`)**:
   * Halaman simulator terisolasi untuk menguji sampel susu secara manual menggunakan slider sensor IoT tanpa merusak data historis berjalan.
4. **Log Data Operasional Lengkap**:
   * Tabel interaktif dengan selector limit data (10, 50, 100, Semua) serta penyorotan baris anomali dengan warna merah muda halus.

---

## 💻 Spesifikasi Teknologi

* **Backend / Analisis**: Python 3.9+, Flask, Pandas, Scikit-Learn, Joblib.
* **Frontend**: HTML5, Vanilla CSS3 (Custom Dark Gray), Vanilla JavaScript (ES6+), Chart.js (Visualisasi).
* **Serverless Deployment**: Dikonfigurasi untuk dideploy ke **Vercel** (`vercel.json`).
