// static/js/app.js
document.addEventListener('DOMContentLoaded', function() {
    // Navbar toggler for mobile
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarMenu = document.querySelector('.navbar-menu');

    if (navbarToggler && navbarMenu) {
        navbarToggler.addEventListener('click', () => {
            navbarMenu.classList.toggle('active');
            const isExpanded = navbarMenu.classList.contains('active');
            navbarToggler.setAttribute('aria-expanded', isExpanded);
        });
    }

    // Close flash messages
    document.querySelectorAll('.alert .close-alert').forEach(button => {
        button.addEventListener('click', (event) => {
            const alert = event.target.closest('.alert');
            if (alert) {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 300); // Remove after fade out
            }
        });
    });
    // Auto-hide flash messages
    setTimeout(() => {
        document.querySelectorAll('.flash-messages-container .alert').forEach(alert => {
            if (alert.style.opacity !== '0') { // Don't try to hide already closing alerts
                 alert.style.opacity = '0';
                 setTimeout(() => alert.remove(), 600);
            }
        });
    }, 7000); // Hide after 7 seconds

    // Modal handling
    const openModalButtons = document.querySelectorAll('[data-toggle="modal"]');
    const closeModalButtons = document.querySelectorAll('[data-dismiss="modal"], .close-modal');

    openModalButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetModalId = button.getAttribute('data-target');
            const modal = document.querySelector(targetModalId);
            if (modal) modal.classList.add('active');
        });
    });

    closeModalButtons.forEach(button => {
        button.addEventListener('click', () => {
            const modal = button.closest('.modal');
            if (modal) modal.classList.remove('active');
        });
    });

    // Close modal when clicking outside of modal-content
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (event) => {
            if (event.target === modal) { // Clicked on modal backdrop
                modal.classList.remove('active');
            }
        });
    });
    
    // Close modal with Escape key
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            const activeModal = document.querySelector('.modal.active');
            if (activeModal) {
                activeModal.classList.remove('active');
            }
        }
    });


    // SocketIO connection
    // const socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);
    // Namespace default '/' biasanya otomatis, jadi bisa io() saja
    const socket = io();


    socket.on('connect', () => {
        console.log('Socket.IO Connected');
    });

    socket.on('disconnect', () => {
        console.log('Socket.IO Disconnected');
    });

    socket.on('error', (data) => {
        console.error('Socket.IO Error:', data.message);
        showDynamicAlert('danger', `Error: ${data.message}`);
    });

    // Expose socket for other JS files if needed (atau gunakan event bus)
    window.socket = socket;

});

// Helper function to show dynamic alerts
function showDynamicAlert(type, message, duration = 5000) {
    const placeholder = document.getElementById('dynamicAlertPlaceholder');
    if (!placeholder) return;

    const alertId = `dynAlert-${Date.now()}`;
    let icon = 'ℹ';
    if (type === 'success') icon = '✓';
    else if (type === 'danger' || type === 'error') icon = '⚠'; // Allow 'error' as type
    else if (type === 'warning') icon = '!';
    
    // Ensure type is one of the valid alert classes
    const validTypes = ['primary', 'secondary', 'success', 'danger', 'warning', 'info', 'light', 'dark'];
    const alertClassType = validTypes.includes(type) ? type : (type === 'error' ? 'danger' : 'info');


    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${alertClassType} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.id = alertId;

    alertDiv.innerHTML = `
        <span class="alert-icon">${icon}</span>
        ${message}
        <button type="button" class="close-alert" data-dismiss="alert" aria-label="Close">&times;</button>
    `;
    
    placeholder.appendChild(alertDiv);

    const closeButton = alertDiv.querySelector('.close-alert');
    closeButton.addEventListener('click', () => {
        alertDiv.style.opacity = '0';
        setTimeout(() => alertDiv.remove(), 300);
    });

    if (duration) {
        setTimeout(() => {
             if (document.getElementById(alertId)) { // Check if still exists
                alertDiv.style.opacity = '0';
                setTimeout(() => alertDiv.remove(), 300);
            }
        }, duration);
    }
}

// Helper to format file size
function formatFileSize(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}