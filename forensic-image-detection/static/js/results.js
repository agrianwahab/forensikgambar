// static/js/results.js
document.addEventListener('DOMContentLoaded', function () {
    const resultsPageDiv = document.querySelector('.results-page');
    if (!resultsPageDiv) return;

    // Logika untuk tab (jika ada implementasi tab di HTML)
    const tabButtons = resultsPageDiv.querySelectorAll('.result-tabs .tab-btn'); // Jika ada tab
    const visualizationPanes = resultsPageDiv.querySelectorAll('.visualization-pane'); // Jika ada pane

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Nonaktifkan semua tombol dan sembunyikan semua pane
            tabButtons.forEach(btn => btn.classList.remove('active'));
            visualizationPanes.forEach(pane => pane.style.display = 'none');

            // Aktifkan tombol yang diklik dan tampilkan pane yang sesuai
            button.classList.add('active');
            const targetPaneId = button.getAttribute('data-target'); // Misal: data-target="#elaPane"
            const targetPane = document.querySelector(targetPaneId);
            if (targetPane) {
                targetPane.style.display = 'block';
            }
            console.log(`Tab ${targetPaneId} activated.`);
        });
    });

    // Logika untuk tombol export (jika ada interaksi JS spesifik)
    // Contoh: Membuka modal konfirmasi sebelum download
    const exportButtons = resultsPageDiv.querySelectorAll('.export-options-section .btn');
    exportButtons.forEach(button => {
        button.addEventListener('click', (event) => {
            // event.preventDefault(); // Hentikan default action jika ingin konfirmasi dulu
            const exportType = button.textContent.match(/Export (\w+)/i);
            if (exportType && exportType[1]) {
                console.log(`Exporting as ${exportType[1].toUpperCase()}...`);
                // Jika ada konfirmasi modal:
                // showConfirmationModal(`Anda akan mengekspor hasil sebagai ${exportType[1].toUpperCase()}. Lanjutkan?`, () => {
                //     window.location.href = button.href; // Lanjutkan download
                // });
            }
        });
    });
    
    // Jika ada elemen chart yang perlu di-render di sisi client (menggunakan charts.js)
    // Contoh:
    // if (document.getElementById('someClientSideChart')) {
    //     const chartData = JSON.parse(document.getElementById('someClientSideChartData').textContent);
    //     ForensicCharts.renderSomeChart('someClientSideChart', chartData); // Asumsi ForensicCharts ada di charts.js
    // }
    
    console.log('Results page JavaScript loaded.');
});