// Profil Page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Check if SweetAlert2 is available
    if (typeof Swal === 'undefined') {
        console.error('SweetAlert2 is not loaded. Please check your internet connection or CDN.');
        return;
    }

    // Password visibility toggle functionality
    initializePasswordToggles();

    // Auto-uppercase for nama lengkap
    initializeNamaLengkapAutoUppercase();

    // Password strength meter
    initializePasswordStrengthMeter();

    // Form validation with SweetAlert2 confirmation
    initializeFormValidation();
});

function initializePasswordToggles() {
    const toggleButtons = document.querySelectorAll('.toggle-password');

    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const input = document.getElementById(targetId);
            const icon = this.querySelector('i');

            if (!input || !icon) return;

            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
                this.setAttribute('title', 'Sembunyikan password');
            } else {
                input.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
                this.setAttribute('title', 'Tampilkan password');
            }
        });
    });
}

function initializeNamaLengkapAutoUppercase() {
    const namaLengkapInput = document.getElementById('nama_lengkap');

    if (namaLengkapInput) {
        namaLengkapInput.addEventListener('input', function() {
            // Convert to uppercase and remove invalid characters
            let value = this.value.toUpperCase();

            // Allow only letters, spaces, hyphens, and apostrophes
            value = value.replace(/[^A-Z\s\-']/g, '');

            // Prevent multiple consecutive spaces
            value = value.replace(/\s+/g, ' ');

            // Trim leading/trailing spaces
            value = value.trim();

            this.value = value;
        });

        // Also handle paste events
        namaLengkapInput.addEventListener('paste', function(e) {
            setTimeout(() => {
                let value = this.value.toUpperCase();
                value = value.replace(/[^A-Z\s\-']/g, '');
                value = value.replace(/\s+/g, ' ');
                this.value = value.trim();
            }, 0);
        });
    }
}

function initializeFormValidation() {
    // Profile update form validation with confirmation
    const profileForm = document.querySelector('form input[name="action"][value="update_profile"]');
    if (profileForm) {
        profileForm.closest('form').addEventListener('submit', function(e) {
            e.preventDefault(); // Prevent immediate submission
            
            const namaLengkap = document.getElementById('nama_lengkap');
            const currentValue = namaLengkap.value.trim();
            const originalValue = namaLengkap.getAttribute('data-original-value') || '';

            // Check if there are changes
            if (currentValue === originalValue) {
                Swal.fire({
                    title: 'Tidak Ada Perubahan',
                    text: 'Tidak ada perubahan yang perlu disimpan.',
                    icon: 'info',
                    confirmButtonText: 'OK',
                    confirmButtonColor: '#3B82F6'
                });
                return false;
            }

            // Validate input
            if (!currentValue) {
                showAlert('Nama lengkap tidak boleh kosong!', 'danger');
                namaLengkap.focus();
                return false;
            }

            if (!/^[A-Z\s\-']+$/.test(currentValue)) {
                showAlert('Nama lengkap hanya boleh huruf kapital, spasi, dash, atau kutip!', 'danger');
                namaLengkap.focus();
                return false;
            }

            // Show confirmation dialog
            Swal.fire({
                title: 'Konfirmasi Perubahan',
                text: `Apakah Anda yakin ingin mengubah nama lengkap menjadi "${currentValue}"?`,
                icon: 'question',
                showCancelButton: true,
                confirmButtonText: 'Ya, Simpan',
                cancelButtonText: 'Batal',
                confirmButtonColor: '#2563EB',
                cancelButtonColor: '#6B7280',
                reverseButtons: true
            }).then((result) => {
                if (result.isConfirmed) {
                    // Show loading
                    Swal.fire({
                        title: 'Menyimpan...',
                        text: 'Mohon tunggu sebentar',
                        allowOutsideClick: false,
                        showConfirmButton: false,
                        willOpen: () => {
                            Swal.showLoading();
                        }
                    });
                    
                    // Submit the form
                    this.submit();
                }
            });
        });
    }

    // Password change form validation with confirmation
    const passwordForm = document.querySelector('form input[name="action"][value="change_password"]');
    if (passwordForm) {
        passwordForm.closest('form').addEventListener('submit', function(e) {
            e.preventDefault(); // Prevent immediate submission
            
            const currentPassword = document.getElementById('current_password');
            const newPassword = document.getElementById('new_password');
            const confirmPassword = document.getElementById('confirm_password');

            // Validate input
            if (!currentPassword.value) {
                showAlert('Password saat ini harus diisi!', 'danger');
                currentPassword.focus();
                return false;
            }

            if (!newPassword.value) {
                showAlert('Password baru harus diisi!', 'danger');
                newPassword.focus();
                return false;
            }

            if (newPassword.value.length < 6) {
                showAlert('Password baru minimal 6 karakter!', 'danger');
                newPassword.focus();
                return false;
            }

            if (!confirmPassword.value) {
                showAlert('Konfirmasi password harus diisi!', 'danger');
                confirmPassword.focus();
                return false;
            }

            if (newPassword.value !== confirmPassword.value) {
                showAlert('Password baru dan konfirmasi password tidak cocok!', 'danger');
                confirmPassword.focus();
                return false;
            }

            // Show confirmation dialog
            Swal.fire({
                title: 'Konfirmasi Ubah Password',
                text: 'Apakah Anda yakin ingin mengubah password? Pastikan Anda mengingat password baru.',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'Ya, Ubah Password',
                cancelButtonText: 'Batal',
                confirmButtonColor: '#16A34A',
                cancelButtonColor: '#6B7280',
                reverseButtons: true
            }).then((result) => {
                if (result.isConfirmed) {
                    // Show loading
                    Swal.fire({
                        title: 'Mengubah Password...',
                        text: 'Mohon tunggu sebentar',
                        allowOutsideClick: false,
                        showConfirmButton: false,
                        willOpen: () => {
                            Swal.showLoading();
                        }
                    });
                    
                    // Submit the form
                    this.submit();
                }
            });
        });
    }
}

function showAlert(message, type) {
    // Use SweetAlert2 for consistency
    const icon = type === 'success' ? 'success' : 'error';
    const title = type === 'success' ? 'Berhasil' : 'Error';

    Swal.fire({
        title: title,
        text: message,
        icon: icon,
        confirmButtonText: 'OK',
        confirmButtonColor: type === 'success' ? '#16A34A' : '#DC2626'
    });
}

// Add some visual feedback for form interactions
document.addEventListener('focusin', function(e) {
    if (e.target.classList.contains('profil-input')) {
        e.target.parentElement.classList.add('focused');
    }
});

document.addEventListener('focusout', function(e) {
    if (e.target.classList.contains('profil-input')) {
        e.target.parentElement.classList.remove('focused');
    }
});

function initializePasswordStrengthMeter() {
    const newPasswordInput = document.getElementById('new_password');
    const strengthBar = document.getElementById('password-strength-bar');
    const strengthText = document.getElementById('password-strength-text');

    if (!newPasswordInput || !strengthBar || !strengthText) return;

    newPasswordInput.addEventListener('input', function() {
        const password = this.value;
        const strength = calculatePasswordStrength(password);
        
        updatePasswordStrengthDisplay(strength);
    });

    // Initial check
    updatePasswordStrengthDisplay(calculatePasswordStrength(newPasswordInput.value));
}

function calculatePasswordStrength(password) {
    let score = 0;
    const checks = {
        length: password.length >= 6,
        uppercase: /[A-Z]/.test(password),
        lowercase: /[a-z]/.test(password),
        numbers: /\d/.test(password),
        special: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)
    };

    // Calculate score based on criteria
    if (checks.length) score += 20;
    if (checks.uppercase) score += 20;
    if (checks.lowercase) score += 20;
    if (checks.numbers) score += 20;
    if (checks.special) score += 20;

    return {
        score: score,
        checks: checks
    };
}

function updatePasswordStrengthDisplay(strength) {
    const strengthBar = document.getElementById('password-strength-bar');
    const strengthText = document.getElementById('password-strength-text');
    
    if (!strengthBar || !strengthText) return;

    const score = strength.score;
    let level = '';
    let color = '';
    let width = '0%';

    if (score === 0) {
        level = 'Belum ada';
        color = 'bg-slate-300';
        width = '0%';
    } else if (score <= 40) {
        level = 'Lemah';
        color = 'bg-red-500';
        width = '25%';
    } else if (score <= 60) {
        level = 'Sedang';
        color = 'bg-yellow-500';
        width = '50%';
    } else if (score <= 80) {
        level = 'Kuat';
        color = 'bg-blue-500';
        width = '75%';
    } else {
        level = 'Sangat Kuat';
        color = 'bg-green-500';
        width = '100%';
    }

    strengthBar.style.width = width;
    strengthBar.className = `h-2 rounded-full transition-all duration-300 ${color}`;
    strengthText.textContent = level;
    strengthText.className = `text-xs font-bold ${score === 0 ? 'text-slate-400' : score <= 40 ? 'text-red-500' : score <= 60 ? 'text-yellow-600' : score <= 80 ? 'text-blue-600' : 'text-green-600'}`;
}