// Mobile Menu and Navbar Scripts
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');
    const mobileMenuClose = document.getElementById('mobileMenuClose');
    const mobileMenu = document.getElementById('mobileMenu');
    const mainNav = document.getElementById('mainNav');

    if (mobileMenuToggle && mobileMenuClose && mobileMenu) {
        mobileMenuToggle.addEventListener('click', () => {
            mobileMenu.classList.remove('translate-x-full');
        });

        mobileMenuClose.addEventListener('click', () => {
            mobileMenu.classList.add('translate-x-full');
        });
    }

    // Navbar Scroll Effect
    if (mainNav) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 20) {
                mainNav.classList.add('py-2');
                const navContainer = mainNav.querySelector('.container div');
                if (navContainer) {
                    navContainer.classList.remove('bg-white/10', 'border-white/20');
                    navContainer.classList.add('bg-slate-900/90', 'border-white/10', 'py-2');
                }
            } else {
                mainNav.classList.remove('py-2');
                const navContainer = mainNav.querySelector('.container div');
                if (navContainer) {
                    navContainer.classList.add('bg-white/10', 'border-white/20');
                    navContainer.classList.remove('bg-slate-900/90', 'border-white/10', 'py-2');
                }
            }
        });
    }
});