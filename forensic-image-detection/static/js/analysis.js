// static/js/analysis.js
document.addEventListener('DOMContentLoaded', function () {
    const analysisPageDiv = document.querySelector('.analysis-page');
    if (!analysisPageDiv) return;

    const analysisId = analysisPageDiv.dataset.analysisId;
    
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const analysisStatusElem = document.getElementById('analysisStatus');
    const currentStageNumberElem = document.getElementById('currentStageNumber');
    const totalStageNumberElem = document.getElementById('totalStageNumber');
    const currentStageNameElem = document.getElementById('currentStageName');
    const etaValueElem = document.getElementById('etaValue');
    const stagesListElem = document.getElementById('stagesList');
    const analysisErrorDetailsElem = document.getElementById('analysisErrorDetails');
    const errorMessageTextElem = document.getElementById('errorMessageText');

    let estimatedTotalTime = 120; // Default, akan diupdate jika ada dari server

    function updateStageUI(stageNumber, totalStages, stageName, stageStatus) {
        const stageItem = document.getElementById(`stage-${stageNumber}`);
        if (stageItem) {
            const icon = stageItem.querySelector('.stage-icon');
            const statusLabel = stageItem.querySelector('.stage-status-label');
            
            stageItem.className = `stage-item status-${stageStatus}`; // Reset class
            statusLabel.textContent = stageStatus.charAt(0).toUpperCase() + stageStatus.slice(1);

            if (stageStatus === 'completed') icon.textContent = '✓';
            else if (stageStatus === 'active') icon.textContent = '⟳';
            else if (stageStatus === 'error') icon.textContent = '⚠';
            else icon.textContent = '○';
        }
    }
    
    function updateAllStagesUI(stagesData) {
        if (!stagesListElem || !stagesData) return;
        stagesListElem.innerHTML = ''; // Kosongkan list lama

        const totalStagesNum = stagesData.length > 0 ? stagesData[stagesData.length-1].id : 17; // Ambil total stages dari data terakhir atau default

        stagesData.forEach(stage => {
            const li = document.createElement('li');
            li.className = `stage-item status-${stage.status}`;
            li.id = `stage-${stage.id}`;
            
            let iconChar = '○';
            if (stage.status === 'completed') iconChar = '✓';
            else if (stage.status === 'active') iconChar = '⟳';
            else if (stage.status === 'error') iconChar = '⚠';

            li.innerHTML = `
                <span class="stage-icon">${iconChar}</span>
                <span class="stage-name">[${stage.id}/${totalStagesNum}] ${stage.name}</span>
                <span class="stage-status-label">${stage.status.charAt(0).toUpperCase() + stage.status.slice(1)}</span>
            `;
            stagesListElem.appendChild(li);
        });
    }


    function updateUI(data) {
        if (progressFill) progressFill.style.width = `${data.progress}%`;
        if (progressText) progressText.textContent = `${parseFloat(data.progress).toFixed(1)}%`;
        if (analysisStatusElem) {
            analysisStatusElem.textContent = data.status.charAt(0).toUpperCase() + data.status.slice(1);
            analysisStatusElem.className = `status-${data.status.toLowerCase()}`;
        }
        if (currentStageNumberElem) currentStageNumberElem.textContent = data.current_stage_num;
        if (totalStageNumberElem && data.total_stages_num) totalStageNumberElem.textContent = data.total_stages_num;
        if (currentStageNameElem) currentStageNameElem.textContent = data.current_stage_name || 'Memproses...';
        
        if (data.estimated_time) estimatedTotalTime = data.estimated_time;
        
        const remainingTime = Math.max(0, estimatedTotalTime * (1 - data.progress / 100));
        if (etaValueElem) {
            if (data.status === 'completed' || data.status === 'error') {
                etaValueElem.textContent = "-";
            } else {
                const minutes = Math.floor(remainingTime / 60);
                const seconds = Math.floor(remainingTime % 60);
                etaValueElem.textContent = `${minutes}m ${seconds}s`;
            }
        }
        
        // Update individual stage status (jika data stages dikirim)
        // Ini perlu helper dari backend untuk membuat list UI stages yang benar
        // Kita akan asumsikan 'get_analysis_stages' dari Python helper
        // menghasilkan struktur yang sesuai dan dikirim dalam 'data.ui_stages_list'
        if (data.ui_stages_list && Array.isArray(data.ui_stages_list)) {
            updateAllStagesUI(data.ui_stages_list);
        }


        if (data.status === 'error') {
            if(analysisErrorDetailsElem) analysisErrorDetailsElem.style.display = 'block';
            if(errorMessageTextElem) errorMessageTextElem.textContent = data.error_message || "Terjadi kesalahan tidak diketahui.";
        } else {
            if(analysisErrorDetailsElem) analysisErrorDetailsElem.style.display = 'none';
        }
    }

    if (analysisId && window.socket) {
        // Join room untuk analisis spesifik ini
        window.socket.emit('join_analysis_room', { analysis_id: analysisId });

        window.socket.on('analysis_update', (data) => {
            if (data.id === analysisId) {
                console.log('Analysis update received:', data);
                updateUI(data);
            }
        });

        window.socket.on('analysis_complete', (data) => {
            if (data.id === analysisId) {
                console.log('Analysis complete:', data);
                updateUI(data); // Update UI terakhir kali
                showDynamicAlert('success', `Analisis untuk file "${data.original_filename}" telah selesai! Mengarahkan ke halaman hasil...`, 3000);
                setTimeout(() => {
                    window.location.href = `/results/${analysisId}`;
                }, 3000);
            }
        });

        window.socket.on('analysis_error', (data) => {
            if (data.id === analysisId) {
                console.error('Analysis error:', data);
                updateUI(data); // Update UI untuk menunjukkan error
                showDynamicAlert('danger', `Analisis gagal: ${data.error_message || 'Kesalahan tidak diketahui.'}`);
            }
        });
        
        // Polling sebagai fallback jika WebSocket bermasalah atau untuk inisialisasi awal
        // Tapi karena kita emit status saat join, ini mungkin tidak terlalu dibutuhkan.
        // Bisa di-disable jika WebSocket sudah stabil.
        function pollStatus() {
            fetch(`/api/analysis/status/${analysisId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error("Polling error:", data.error);
                        if(analysisErrorDetailsElem) analysisErrorDetailsElem.style.display = 'block';
                        if(errorMessageTextElem) errorMessageTextElem.textContent = data.error;
                        return; // Stop polling on error
                    }
                    
                    // Ambil juga ui_stages_list via API jika perlu.
                    // Untuk sekarang, kita update UI utama saja dari polling.
                    // data.ui_stages_list akan diisi oleh socket event.
                    updateUI(data);

                    if (data.status === 'completed') {
                        console.log('Polling: Analysis complete.');
                         showDynamicAlert('success', `Analisis untuk file "${data.original_filename}" telah selesai! Mengarahkan ke halaman hasil...`, 3000);
                        setTimeout(() => {
                            window.location.href = `/results/${analysisId}`;
                        }, 3000);
                    } else if (data.status !== 'error') {
                        setTimeout(pollStatus, 5000); // Poll every 5 seconds
                    } else {
                        console.log('Polling: Analysis error.');
                        showDynamicAlert('danger', `Analisis gagal: ${data.error_message || 'Kesalahan tidak diketahui.'}`);
                    }
                })
                .catch(err => {
                    console.error('Polling request failed:', err);
                     setTimeout(pollStatus, 10000); // Retry after longer delay
                });
        }
        // pollStatus(); // Mulai polling jika diperlukan
        // Sebaiknya, data awal sudah ada dari render_template, dan update via WebSocket.

    } else {
        if (!analysisId) console.error('Analysis ID not found in data attribute.');
        if (!window.socket) console.error('Socket.IO not available.');
    }
});