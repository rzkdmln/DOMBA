// Allow dismissing SweetAlert2 by clicking outside or pressing ESC by default
(function() {
    if (typeof Swal !== 'undefined') {
        const _orig = Swal.fire;
        Swal.fire = function(...args) {
            try {
                if (args.length === 1 && typeof args[0] === 'object') {
                    const opts = args[0];
                    opts.allowOutsideClick = opts.allowOutsideClick === undefined ? true : opts.allowOutsideClick;
                    opts.allowEscapeKey = opts.allowEscapeKey === undefined ? true : opts.allowEscapeKey;
                    opts.allowEnterKey = opts.allowEnterKey === undefined ? true : opts.allowEnterKey;
                    return _orig.call(this, opts);
                } else {
                    const [title, text, icon] = args;
                    const opts = {
                        title: title || '',
                        text: text || undefined,
                        icon: icon || undefined,
                        allowOutsideClick: true,
                        allowEscapeKey: true,
                        allowEnterKey: true
                    };
                    return _orig.call(this, opts);
                }
            } catch (e) {
                return _orig.apply(this, args);
            }
        };
    }
})();

document.addEventListener('DOMContentLoaded', function() {
    const alertData = document.getElementById('sweetalert-data');
    if (alertData) {
        const category = alertData.dataset.category;
        const message = alertData.dataset.message;
        const dashboardUrl = alertData.dataset.dashboardUrl;

        if (category === 'success') {
            Swal.fire({
                title: 'Berhasil!',
                text: message,
                icon: 'success',
                timer: 1500,
                timerProgressBar: true,
                showConfirmButton: false
            }).then(() => {
                if (dashboardUrl) window.location.href = dashboardUrl;
            });
        } else if (category === 'warning') {
            Swal.fire({
                title: 'Peringatan!',
                text: message,
                icon: 'warning',
                confirmButtonText: 'Ubah Password',
                confirmButtonColor: '#f59e0b'
            });
        } else if (category === 'error') {
            Swal.fire({
                title: 'Error!',
                text: message,
                icon: 'error',
                confirmButtonText: 'Coba Lagi',
                confirmButtonColor: '#ef4444'
            });
        }
    }

    // Form Loading State
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn && !this.hasAttribute('data-no-loading')) {
                const originalText = submitBtn.innerHTML;
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin mr-3"></i>Memproses...';
            }
        });
    });

    // Password Reveal
    document.querySelectorAll('.toggle-password').forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.dataset.target;
            const input = document.querySelector(`input[name="${targetId}"]`) || document.getElementById(targetId);
            const icon = this.querySelector('i');
            
            if (input) {
                const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
                input.setAttribute('type', type);
                if (icon) {
                    icon.classList.toggle('fa-eye');
                    icon.classList.toggle('fa-eye-slash');
                }
            }
        });
    });
});
