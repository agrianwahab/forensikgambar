// static/js/charts.js
// Namespace untuk fungsi chart
const ForensicCharts = {
    // Contoh fungsi render chart sederhana jika diperlukan di UI
    // Kebanyakan visualisasi forensik akan berupa gambar dari backend (Python)

    renderSimpleBarChart: function(canvasId, labels, data, chartLabel = 'Data') {
        const ctx = document.getElementById(canvasId);
        if (!ctx || typeof Chart === 'undefined') { // Perlu Chart.js di-include di base.html jika mau pakai ini
            console.warn(`Canvas with id ${canvasId} not found or Chart.js not loaded.`);
            return;
        }
        new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: chartLabel,
                    data: data,
                    backgroundColor: 'rgba(59, 130, 246, 0.5)', // --forensic-primary transparan
                    borderColor: 'rgba(59, 130, 246, 1)', // --forensic-primary
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { color: '#BCCCDC' }, // --forensic-text-secondary
                        grid: { color: 'rgba(188, 204, 220, 0.1)' }
                    },
                    x: {
                        ticks: { color: '#BCCCDC' },
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: {
                        labels: { color: '#BCCCDC' }
                    }
                }
            }
        });
    },

    // Fungsi lain untuk chart bisa ditambahkan di sini
    // Misalnya, pie chart untuk distribusi hasil analisis, dll.
};

// Contoh penggunaan bisa dipanggil dari file JS lain seperti app.js atau results.js
// jika ada elemen canvas di HTML dan data tersedia.
// Misal di results.js:
// ForensicCharts.renderSimpleBarChart('myChartCanvas', ['Authentic', 'Copy-Move', 'Splicing'], [70, 20, 10]);