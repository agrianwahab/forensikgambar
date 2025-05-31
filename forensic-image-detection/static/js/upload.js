// static/js/upload.js
document.addEventListener('DOMContentLoaded', function () {
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    const dropzone = document.getElementById('dropzone');
    const imagePreview = document.getElementById('imagePreview');
    const previewPlaceholder = document.getElementById('previewPlaceholder');
    const fileInfoPreview = document.getElementById('fileInfoPreview');
    const filenameDisplay = document.getElementById('filenameDisplay');
    const filesizeDisplay = document.getElementById('filesizeDisplay');
    const filetypeDisplay = document.getElementById('filetypeDisplay');
    const dimensionsDisplay = document.getElementById('dimensionsDisplay');
    const submitAnalysisBtn = document.getElementById('submitAnalysisBtn');

    if (!uploadForm || !fileInput || !dropzone) {
        // console.warn('Upload elements not found on this page.');
        return;
    }

    dropzone.addEventListener('click', () => fileInput.click());

    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            handleFile(fileInput.files[0]);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) {
            handleFile(fileInput.files[0]);
        }
    });

    function handleFile(file) {
        if (!file) return;

        // Validasi sisi client (opsional, karena ada validasi server)
        const allowedTypes = ['image/jpeg', 'image/png', 'image/bmp', 'image/tiff', 'image/webp'];
        const maxSizeMB = 16; // Sesuaikan dengan MAX_CONTENT_LENGTH
        
        if (!allowedTypes.includes(file.type)) {
            showDynamicAlert('danger', `Tipe file tidak didukung: ${file.type}. Pilih JPG, PNG, BMP, TIFF, atau WEBP.`);
            resetFileInput();
            return;
        }
        if (file.size > maxSizeMB * 1024 * 1024) {
            showDynamicAlert('danger', `Ukuran file terlalu besar (maks ${maxSizeMB}MB).`);
            resetFileInput();
            return;
        }

        filenameDisplay.textContent = file.name;
        filesizeDisplay.textContent = formatFileSize(file.size);
        filetypeDisplay.textContent = file.type;
        
        fileInfoPreview.style.display = 'block';
        previewPlaceholder.style.display = 'none';
        imagePreview.style.display = 'block';
        dimensionsDisplay.style.display = 'inline';


        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.src = e.target.result;
            const img = new Image();
            img.onload = () => {
                dimensionsDisplay.textContent = `${img.width} x ${img.height} px`;
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
        submitAnalysisBtn.disabled = false;
    }
    
    function resetFileInput() {
        fileInput.value = ''; // Kosongkan input file
        fileInfoPreview.style.display = 'none';
        imagePreview.style.display = 'none';
        previewPlaceholder.style.display = 'block';
        filenameDisplay.textContent = '-';
        filesizeDisplay.textContent = '-';
        filetypeDisplay.textContent = '-';
        dimensionsDisplay.style.display = 'none';
        dimensionsDisplay.textContent = '-';
        submitAnalysisBtn.disabled = true;
    }


    uploadForm.addEventListener('submit', function(event) {
        // Biarkan default action form (POST ke Flask route) berjalan
        // Validasi dasar bisa ditambahkan di sini jika diperlukan sebelum submit
        if (!fileInput.files.length) {
            event.preventDefault(); // Hentikan submit jika tidak ada file
            showDynamicAlert('warning', 'Silakan pilih file gambar terlebih dahulu.');
            return;
        }
        
        // Tampilkan loading state pada tombol submit
        if (submitAnalysisBtn) {
            submitAnalysisBtn.disabled = true;
            submitAnalysisBtn.innerHTML = '<span class="spinner"></span> Mengunggah & Memproses...';
        }
    });
});