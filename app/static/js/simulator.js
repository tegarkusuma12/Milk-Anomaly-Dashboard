/* File: app/static/js/simulator.js */

document.addEventListener("DOMContentLoaded", () => {
    initSliders();
    setupSimulatorListener();
});

// 1. Sinkronisasi slider dengan teks nilai di halaman Simulator
function initSliders() {
    const simPh = document.getElementById("sim_ph");
    const valPh = document.getElementById("val_ph");
    if (simPh && valPh) {
        simPh.addEventListener("input", (e) => {
            valPh.textContent = parseFloat(e.target.value).toFixed(2);
        });
    }

    const simTemp = document.getElementById("sim_temp");
    const valTemp = document.getElementById("val_temp");
    if (simTemp && valTemp) {
        simTemp.addEventListener("input", (e) => {
            valTemp.textContent = parseFloat(e.target.value).toFixed(1) + "°C";
        });
    }

    const simColour = document.getElementById("sim_colour");
    const valColour = document.getElementById("val_colour");
    if (simColour && valColour) {
        simColour.addEventListener("input", (e) => {
            valColour.textContent = e.target.value;
        });
    }
}

// 2. Setup event listener form simulasi sensor
function setupSimulatorListener() {
    const form = document.getElementById("page_simulator_form");
    if (!form) return;

    form.addEventListener("submit", (e) => {
        e.preventDefault();

        // Ambil data input dari form
        const payload = {
            "pH": parseFloat(document.getElementById("sim_ph").value),
            "Temprature": parseFloat(document.getElementById("sim_temp").value),
            "Taste": parseInt(document.getElementById("sim_taste").value),
            "Odor": parseInt(document.getElementById("sim_odor").value),
            "Fat ": parseInt(document.getElementById("sim_fat").value), // Note space
            "Turbidity": parseInt(document.getElementById("sim_turbidity").value),
            "Colour": parseInt(document.getElementById("sim_colour").value)
        };

        // Kirim via AJAX POST ke API
        fetch('/api/predict-simulator', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(res => {
            if (!res.ok) throw new Error("Gagal melakukan prediksi");
            return res.json();
        })
        .then(data => {
            // Sembunyikan placeholder, tampilkan hasil aktual
            document.getElementById("placeholder_result").style.display = "none";
            const actualResult = document.getElementById("actual_result");
            actualResult.style.display = "flex";

            const badge = document.getElementById("sim_result_badge");
            const detailsGrid = document.getElementById("sim_details_grid");
            const pillBadge = document.getElementById("status_pill_badge");

            // Update status text
            badge.textContent = `BATCH STATUS: ${data.status_text.toUpperCase()}`;
            pillBadge.textContent = data.status_text;

            if (data.status_anomali === -1) {
                // Anomali terdeteksi
                badge.className = "result-badge-page badge-sim-anomali";
                pillBadge.className = "badge badge-danger";
                detailsGrid.style.display = "grid";

                // Isi Root Causes
                const rootList = document.getElementById("sim_root_cause_list");
                rootList.innerHTML = '';
                data.masalah.forEach(m => {
                    const li = document.createElement("li");
                    li.textContent = m;
                    rootList.appendChild(li);
                });

                // Isi SOP Mitigasi
                const mitList = document.getElementById("sim_mitigation_list");
                mitList.innerHTML = '';
                data.rekomendasi.forEach(r => {
                    const li = document.createElement("li");
                    li.innerHTML = `<strong>${r}</strong>`;
                    mitList.appendChild(li);
                });
            } else {
                // Normal
                badge.className = "result-badge-page badge-sim-normal";
                pillBadge.className = "badge color-green";
                detailsGrid.style.display = "none";

                // Jika normal, set pill badge agar berwarna hijau
                pillBadge.style.backgroundColor = "var(--color-green-soft)";
                pillBadge.style.color = "#34d399";
                pillBadge.style.border = "1px solid rgba(16, 185, 129, 0.2)";
            }
        })
        .catch(err => {
            console.error(err);
            alert("Terjadi kesalahan simulasi: " + err.message);
        });
    });
}
