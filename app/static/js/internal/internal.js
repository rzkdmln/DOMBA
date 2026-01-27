// SweetAlert2 Configuration
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

// UI Scripts
document.addEventListener('DOMContentLoaded', function() {
    // Handle SweetAlert2 messages
    const alertData = document.getElementById('sweetalert-data');
    if (alertData) {
        const category = alertData.dataset.category;
        const message = alertData.dataset.message;

        const swalConfig = {
            timer: 3000,
            timerProgressBar: true,
            showConfirmButton: category !== 'success',
            allowOutsideClick: true,
            allowEscapeKey: true
        };

        if (category === 'success') {
            Swal.fire({
                ...swalConfig,
                title: 'Berhasil!',
                text: message,
                icon: 'success'
            });
        } else if (category === 'error') {
            Swal.fire({
                ...swalConfig,
                title: 'Error!',
                text: message,
                icon: 'error',
                confirmButtonColor: '#dc2626'
            });
        } else if (category === 'warning') {
            Swal.fire({
                ...swalConfig,
                title: 'Peringatan!',
                text: message,
                icon: 'warning',
                confirmButtonColor: '#d97706'
            });
        } else {
            Swal.fire({
                ...swalConfig,
                title: 'Informasi',
                text: message,
                icon: 'info',
                confirmButtonColor: '#2563eb'
            });
        }
    }

    // Dropdown Handlers
    const userBtn = document.getElementById('userDropdownButton');
    const userMenu = document.getElementById('userDropdownMenu');

    if (userBtn && userMenu) {
        userBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            userMenu.classList.toggle('hidden');
        });

        document.addEventListener('click', () => {
            userMenu.classList.add('hidden');
        });
    }

    // Mobile Menu Toggle Functionality
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');
    const mobileSidebarOverlay = document.getElementById('mobileSidebarOverlay');

    if (mobileMenuToggle && mobileSidebarOverlay) {
        function toggleMobileMenu() {
            const sidebar = document.getElementById('sidebar');
            const isOpen = !sidebar.classList.contains('-translate-x-full');
            
            if (isOpen) {
                // Close mobile menu
                sidebar.classList.add('-translate-x-full');
                mobileSidebarOverlay.classList.remove('active');
            } else {
                // Open mobile menu
                sidebar.classList.remove('-translate-x-full');
                mobileSidebarOverlay.classList.add('active');
            }
        }

        mobileMenuToggle.addEventListener('click', toggleMobileMenu);
        mobileSidebarOverlay.addEventListener('click', toggleMobileMenu);
    }

    // Sidebar Toggle Functionality
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const mainWrapper = document.getElementById('mainWrapper');

    // Create overlay for mobile
    const overlay = document.createElement('div');
    overlay.id = 'sidebarOverlay';
    overlay.className = 'fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-[999] hidden opacity-0 transition-opacity duration-300';
    document.body.appendChild(overlay);

    function toggleSidebar() {
        if (window.innerWidth >= 1024) {
            const isCollapsed = document.documentElement.classList.toggle('sidebar-collapsed');
            localStorage.setItem('sidebar-collapsed', isCollapsed);
        } else {
            sidebar.classList.toggle('-translate-x-full');
            if (!sidebar.classList.contains('-translate-x-full')) {
                overlay.classList.remove('hidden');
                setTimeout(() => overlay.classList.add('opacity-100'), 10);
            } else {
                overlay.classList.remove('opacity-100');
                setTimeout(() => overlay.classList.add('hidden'), 300);
            }
        }
    }

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', toggleSidebar);
    }

    // Initial State for Mobile
    if (window.innerWidth < 1024) {
        sidebar.classList.add('-translate-x-full');
    }

    // Close sidebar when clicking overlay
    overlay.addEventListener('click', () => {
        sidebar.classList.add('-translate-x-full');
        overlay.classList.remove('opacity-100');
        setTimeout(() => overlay.classList.add('hidden'), 300);
    });

    // Handle window resize
    window.addEventListener('resize', function() {
        if (window.innerWidth >= 1024) {
            sidebar.classList.remove('-translate-x-full');
            overlay.classList.add('hidden');
            overlay.classList.remove('opacity-100');
        } else {
            sidebar.classList.add('-translate-x-full');
        }
    });
});