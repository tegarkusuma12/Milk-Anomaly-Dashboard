/* File: app/static/js/dashboard.js */

// Global Chart variables
let tempChart = null;
let phChart = null;
let currentDataLogs = []; // Tempat menyimpan log lengkap saat ini untuk diekspor & dipotong

document.addEventListener("DOMContentLoaded", () => {
    // Jalankan inisialisasi awal dashboard utama
    fetchDashboardData();
    setupEventListeners();
});

// 1. Fetch Data Dashboard dari API Backend Flask
function fetchDashboardData(startDate = '', endDate = '', range = '') {
    let url = '/api/data';
    const params = [];
    if (startDate && endDate) {
        params.push(`start_date=${startDate}`);
        params.push(`end_date=${endDate}`);
    } else {
        const activeRange = range || document.querySelector(".chart-tab-btn.active")?.dataset.range || '24h';
        params.push(`range=${activeRange}`);
    }
    url += '?' + params.join('&');

    // Set loading state untuk tabel
    document.getElementById("table_body").innerHTML = `
        <tr>
            <td colspan="9" class="text-center placeholder-text">Memuat data sensor...</td>
        </tr>
    `;

    fetch(url)
        .then(response => {
            if (!response.ok) throw new Error("Gagal memuat data dari server");
            return response.json();
        })
        .then(data => {
            // Simpan seluruh data log mentah
            currentDataLogs = data.logs;
            
            // Set input filter tanggal sesuai range aktif dari server
            if (data.active_range) {
                document.getElementById("start_date").value = data.active_range.start;
                document.getElementById("end_date").value = data.active_range.end;
            }
            
            // Tetapkan batasan kalender min-max
            if (data.date_range) {
                document.getElementById("start_date").min = data.date_range.min;
                document.getElementById("start_date").max = data.date_range.max;
                document.getElementById("end_date").min = data.date_range.min;
                document.getElementById("end_date").max = data.date_range.max;
            }

            // Update KPI Cards
            updateKPIs(data.kpis);

            // Render/Update Charts
            renderCharts(data.chart_data);

            // Update Anomaly Selector Dropdown
            populateAnomalySelector(data.anomalies);

            // Update Log Sensor Table dengan limitasi awal (default dropdown)
            updateLogsTable();
        })
        .catch(err => {
            console.error(err);
            alert("Terjadi kesalahan sistem: " + err.message);
        });
}

// 2. Update Metrik KPI di UI
function updateKPIs(kpis) {
    document.getElementById("kpi_val_total").textContent = kpis.total_data.toLocaleString();
    
    const reliabilityVal = document.getElementById("kpi_val_reliability");
    reliabilityVal.textContent = kpis.tingkat_keandalan.toFixed(1) + "%";
    
    // Warnai subtext keandalan jika tingkat keandalannya di bawah 95%
    const subReliability = document.getElementById("kpi_sub_reliability");
    subReliability.textContent = `${kpis.total_anomali} Anomali Ditemukan (${kpis.persen_anomali}%)`;
    if (kpis.tingkat_keandalan < 95.0) {
        reliabilityVal.style.color = "var(--color-amber)";
    } else {
        reliabilityVal.style.color = "var(--color-green)";
    }

    const valStatus = document.getElementById("kpi_val_status");
    const subStatus = document.getElementById("kpi_sub_status");
    valStatus.textContent = kpis.status_sekarang;
    subStatus.textContent = kpis.delta_teks;
    
    // Ganti background card status batch terkini berdasarkan kondisi
    const statusCard = document.getElementById("kpi_status");
    if (kpis.status_sekarang.includes("QC")) {
        valStatus.style.color = "var(--color-green)";
        statusCard.style.borderColor = "rgba(52, 211, 153, 0.2)";
    } else if (kpis.status_sekarang.includes("Mitigasi")) {
        valStatus.style.color = "var(--color-red)";
        statusCard.style.borderColor = "rgba(248, 113, 113, 0.2)";
    } else {
        valStatus.style.color = "var(--text-primary)";
        statusCard.style.borderColor = "var(--border-color)";
    }
}

// 3. Render Visualisasi Chart.js (Suhu & pH) dengan Highlight Anomali
function renderCharts(chartData) {
    const labels = chartData.map(d => d.timestamp);
    const temps = chartData.map(d => d.temperature);
    const phs = chartData.map(d => d.pH);
    
    // Titik anomali (kecil)
    const tempPointRadii = chartData.map(d => d.status_anomali === -1 ? 3 : 0);
    const tempPointColors = chartData.map(d => d.status_anomali === -1 ? 'rgba(248, 113, 113, 1)' : 'transparent');
    
    const phPointRadii = chartData.map(d => d.status_anomali === -1 ? 3 : 0);
    const phPointColors = chartData.map(d => d.status_anomali === -1 ? 'rgba(248, 113, 113, 1)' : 'transparent');

    const chartOptions = (title, unit = '') => ({
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
            mode: 'index',
            intersect: false,
        },
        plugins: {
            legend: { display: false },
            tooltip: {
                backgroundColor: 'rgba(26, 27, 30, 0.95)',
                titleFont: { family: 'Inter', size: 12 },
                bodyFont: { family: 'Inter', size: 12 },
                titleColor: '#ffffff',
                bodyColor: '#e4e4e7',
                borderColor: 'rgba(255,255,255,0.1)',
                borderWidth: 1,
                callbacks: {
                    label: function(context) {
                        let label = context.dataset.label || '';
                        if (label) {
                            label += ': ';
                        }
                        if (context.parsed.y !== null) {
                            label += context.parsed.y + unit;
                        }
                        const idx = context.dataIndex;
                        if (chartData[idx].status_anomali === -1) {
                            label += ' [ANOMALI]';
                        }
                        return label;
                    }
                }
            }
        },
        scales: {
            x: {
                grid: { color: 'rgba(255, 255, 255, 0.08)' },
                ticks: {
                    color: '#e4e4e7',
                    font: { family: 'Inter', size: 10 },
                    maxTicksLimit: 12,
                    callback: function(val, index) {
                        const label = labels[index] || '';
                        if (label.length > 11) {
                            return label.substring(5, 16);
                        }
                        return label;
                    }
                }
            },
            y: {
                grid: { color: 'rgba(255, 255, 255, 0.08)' },
                ticks: {
                    color: '#e4e4e7',
                    font: { family: 'Inter', size: 11 }
                }
            }
        }
    });

    // Custom Plugin untuk garis kritis pH
    const phCriticalLinesPlugin = {
        id: 'phCriticalLines',
        afterDraw(chart) {
            const { ctx, chartArea: { left, right }, scales: { y } } = chart;
            ctx.save();
            ctx.strokeStyle = 'rgba(248, 113, 113, 0.6)';
            ctx.lineWidth = 1.2;
            ctx.setLineDash([4, 4]);

            // Garis bawah 6.4
            const y64 = y.getPixelForValue(6.4);
            if (y64 >= chart.chartArea.top && y64 <= chart.chartArea.bottom) {
                ctx.beginPath();
                ctx.moveTo(left, y64);
                ctx.lineTo(right, y64);
                ctx.stroke();
                ctx.fillStyle = '#fca5a5';
                ctx.font = '10px Inter';
                ctx.fillText('Batas Asam Kritis (6.4)', right - 130, y64 - 5);
            }

            // Garis atas 7.0
            const y70 = y.getPixelForValue(7.0);
            if (y70 >= chart.chartArea.top && y70 <= chart.chartArea.bottom) {
                ctx.beginPath();
                ctx.moveTo(left, y70);
                ctx.lineTo(right, y70);
                ctx.stroke();
                ctx.fillStyle = '#fca5a5';
                ctx.font = '10px Inter';
                ctx.fillText('Batas Basa Kritis (7.0)', right - 130, y70 - 5);
            }
            ctx.restore();
        }
    };

    // Custom Plugin untuk garis kritis Suhu (50°C)
    const tempCriticalLinesPlugin = {
        id: 'tempCriticalLines',
        afterDraw(chart) {
            const { ctx, chartArea: { left, right }, scales: { y } } = chart;
            ctx.save();
            ctx.strokeStyle = 'rgba(248, 113, 113, 0.6)';
            ctx.lineWidth = 1.2;
            ctx.setLineDash([4, 4]);

            // Garis kritis 50°C
            const y50 = y.getPixelForValue(50.0);
            if (y50 >= chart.chartArea.top && y50 <= chart.chartArea.bottom) {
                ctx.beginPath();
                ctx.moveTo(left, y50);
                ctx.lineTo(right, y50);
                ctx.stroke();
                ctx.fillStyle = '#fca5a5';
                ctx.font = '10px Inter';
                ctx.fillText('Batas Suhu Ekstrem (50.0°C)', right - 160, y50 - 5);
            }
            ctx.restore();
        }
    };

    // 1. Render atau Update Grafik Suhu
    if (tempChart) {
        tempChart.data.labels = labels;
        tempChart.data.datasets[0].data = temps;
        tempChart.data.datasets[0].pointRadius = tempPointRadii;
        tempChart.data.datasets[0].pointBackgroundColor = tempPointColors;
        tempChart.update();
    } else {
        const ctxTemp = document.getElementById('tempChart').getContext('2d');
        tempChart = new Chart(ctxTemp, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Suhu Sensor',
                    data: temps,
                    borderColor: '#10b981',
                    borderWidth: 2,
                    tension: 0.1,
                    pointRadius: tempPointRadii,
                    pointBackgroundColor: tempPointColors,
                    pointBorderColor: '#fff',
                    pointBorderWidth: 1,
                    fill: true,
                    backgroundColor: 'rgba(16, 185, 129, 0.02)'
                }]
            },
            options: chartOptions('Sensor Suhu (°C)', '°C'),
            plugins: [tempCriticalLinesPlugin]
        });
    }

    // 2. Render atau Update Grafik pH
    if (phChart) {
        phChart.data.labels = labels;
        phChart.data.datasets[0].data = phs;
        phChart.data.datasets[0].pointRadius = phPointRadii;
        phChart.data.datasets[0].pointBackgroundColor = phPointColors;
        phChart.update();
    } else {
        const ctxPh = document.getElementById('phChart').getContext('2d');
        phChart = new Chart(ctxPh, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'pH Sensor',
                    data: phs,
                    borderColor: '#3b82f6',
                    borderWidth: 2,
                    tension: 0.1,
                    pointRadius: phPointRadii,
                    pointBackgroundColor: phPointColors,
                    pointBorderColor: '#fff',
                    pointBorderWidth: 1,
                    fill: true,
                    backgroundColor: 'rgba(59, 130, 246, 0.02)'
                }]
            },
            options: chartOptions('Sensor Keasaman (pH)'),
            plugins: [phCriticalLinesPlugin]
        });
    }
}

// 4. Mengisi Dropdown List Anomali
function populateAnomalySelector(anomalies) {
    const selector = document.getElementById("anomaly_selector");
    const badge = document.getElementById("anom_badge");
    
    badge.textContent = `${anomalies.length} Anomali`;
    
    // Kosongkan selector
    selector.innerHTML = '';
    
    if (anomalies.length === 0) {
        selector.innerHTML = '<option value="">-- Tidak ada anomali terdeteksi --</option>';
        document.getElementById("root_cause_list").innerHTML = `
            <li class="placeholder-text" style="color: #34d399 !important;">
                🎉 Lolos Uji Kontrol. Seluruh parameter sensor dalam rentang normal aman.
            </li>`;
        document.getElementById("mitigation_list").innerHTML = `
            <li class="placeholder-text" style="color: #34d399 !important;">
                Tidak ada tindakan mitigasi yang diperlukan. Pertahankan kinerja chiller dan SOP pembersihan.
            </li>`;
        return;
    }
    
    const defaultOpt = document.createElement("option");
    defaultOpt.value = "";
    defaultOpt.textContent = `-- Pilih salah satu (${anomalies.length} kejadian) --`;
    selector.appendChild(defaultOpt);
    
    anomalies.forEach((anom) => {
        const opt = document.createElement("option");
        opt.value = anom.index;
        opt.textContent = `${anom.timestamp} (Suhu: ${anom.temperature}°C, pH: ${anom.pH})`;
        selector.appendChild(opt);
    });
}

// 5. Logika Pemotongan Baris Tabel (Revisi: Limitasi Show 10, 50, 100, All)
function updateLogsTable() {
    const limitSelect = document.getElementById("row_limit_select");
    const limitVal = parseInt(limitSelect.value);
    
    let slicedLogs = currentDataLogs;
    if (limitVal !== -1) {
        slicedLogs = currentDataLogs.slice(0, limitVal);
    }
    
    populateTable(slicedLogs);
}

// 6. Mengisi Tabel Log Sensor Aktual
function populateTable(logs) {
    const tableBody = document.getElementById("table_body");
    tableBody.innerHTML = '';

    if (logs.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center placeholder-text">Tidak ada data log sensor.</td>
            </tr>
        `;
        return;
    }

    logs.forEach(log => {
        const row = document.createElement("tr");
        if (log.status_anomali === -1) {
            row.classList.add("row-anomaly");
        }

        const isOdorNormal = log.odor === 1 ? "Normal" : "Abnormal";
        const isTurbNormal = log.turbidity === 0 ? "Normal" : "Abnormal";
        const isFatNormal = log.fat === 1 ? "Normal" : "Abnormal";
        const isTasteNormal = log.taste === 1 ? "Normal" : "Abnormal";

        const statusBadgeClass = log.status_anomali === 1 ? "status-pill-normal" : "status-pill-anomali";

        row.innerHTML = `
            <td>${log.timestamp}</td>
            <td><strong>${log.pH.toFixed(2)}</strong></td>
            <td><strong>${log.temperature.toFixed(1)}</strong></td>
            <td>${isOdorNormal}</td>
            <td>${isTurbNormal}</td>
            <td>${isFatNormal}</td>
            <td>${isTasteNormal}</td>
            <td>${log.colour}</td>
            <td><span class="status-pill ${statusBadgeClass}">${log.status_text}</span></td>
        `;
        tableBody.appendChild(row);
    });
}

// 7. Pengaturan Event Listener Interaksi UI
function setupEventListeners() {
    const tabButtons = document.querySelectorAll(".chart-tab-btn");

    // A. Filter Rentang Tanggal (Sidebar)
    document.getElementById("btn_apply_filter").addEventListener("click", () => {
        const startDate = document.getElementById("start_date").value;
        const endDate = document.getElementById("end_date").value;
        if (!startDate || !endDate) {
            alert("Harap tentukan tanggal mulai dan tanggal selesai filter!");
            return;
        }
        
        // Nonaktifkan semua tab karena beralih ke filter tanggal kustom
        tabButtons.forEach(b => b.classList.remove("active"));
        
        fetchDashboardData(startDate, endDate);
    });

    // B. Filter Sumbu Waktu Tab (Grafik)
    tabButtons.forEach(btn => {
        btn.addEventListener("click", (e) => {
            // Nonaktifkan semua tab
            tabButtons.forEach(b => b.classList.remove("active"));
            // Aktifkan tab yang diklik
            e.target.classList.add("active");
            
            const range = e.target.dataset.range;
            fetchDashboardData('', '', range);
        });
    });

    // B. Dropdown Selector Anomali
    document.getElementById("anomaly_selector").addEventListener("change", (e) => {
        const idx = e.target.value;
        if (!idx) {
            document.getElementById("root_cause_list").innerHTML = '<li class="placeholder-text">Pilih batch anomali di atas untuk memunculkan analisis akar masalah.</li>';
            document.getElementById("mitigation_list").innerHTML = '<li class="placeholder-text">Pilih batch anomali di atas untuk memunculkan instruksi SOP.</li>';
            return;
        }

        fetch(`/api/anomaly-details/${idx}`)
            .then(res => {
                if (!res.ok) throw new Error("Gagal mengambil detail anomali");
                return res.json();
            })
            .then(data => {
                // Render Root Cause
                const rootList = document.getElementById("root_cause_list");
                rootList.innerHTML = '';
                data.masalah.forEach(m => {
                    const li = document.createElement("li");
                    li.textContent = m;
                    rootList.appendChild(li);
                });

                // Render Mitigasi
                const mitList = document.getElementById("mitigation_list");
                mitList.innerHTML = '';
                data.rekomendasi.forEach(r => {
                    const li = document.createElement("li");
                    li.innerHTML = `<strong>${r}</strong>`;
                    mitList.appendChild(li);
                });
            })
            .catch(err => {
                console.error(err);
                alert("Gagal memuat rekomendasi: " + err.message);
            });
    });

    // C. Dropdown Limitasi Baris Tabel (Revisi)
    document.getElementById("row_limit_select").addEventListener("change", updateLogsTable);

    // D. Ekspor CSV (Mengekspor seluruh data yang ter-load, bukan hanya yang terpotong di tabel)
    document.getElementById("btn_export").addEventListener("click", () => {
        if (currentDataLogs.length === 0) {
            alert("Tidak ada data untuk diekspor!");
            return;
        }

        // Header CSV
        let csvContent = "data:text/csv;charset=utf-8,";
        csvContent += "Timestamp,pH,Suhu,Bau,Kekeruhan,Lemak,Rasa,Warna,Status Anomali,Status Teks\n";

        // Tambahkan baris data
        currentDataLogs.forEach(log => {
            const isOdorNormal = log.odor === 1 ? "Normal" : "Abnormal";
            const isTurbNormal = log.turbidity === 0 ? "Normal" : "Abnormal";
            const isFatNormal = log.fat === 1 ? "Normal" : "Abnormal";
            const isTasteNormal = log.taste === 1 ? "Normal" : "Abnormal";

            const row = [
                log.timestamp,
                log.pH,
                log.temperature,
                isOdorNormal,
                isTurbNormal,
                isFatNormal,
                isTasteNormal,
                log.colour,
                log.status_anomali,
                log.status_text
            ].join(",");
            csvContent += row + "\n";
        });

        // Buat tautan unduhan
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        
        const timestampStr = new Date().toISOString().substring(0, 10);
        link.setAttribute("download", `log_sensor_susu_${timestampStr}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });
}
