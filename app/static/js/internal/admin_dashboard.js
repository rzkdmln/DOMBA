// Static date and time display with WIB timezone (updated every minute, without seconds)
function setDateTime() {
    const now = new Date();
    const clock = document.getElementById('currentTime');
    if (clock) {
        const day = String(now.getDate()).padStart(2, '0');
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const year = now.getFullYear();
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        clock.innerHTML = `${day}/${month}/${year}<br>Pukul ${hours}:${minutes} WIB`;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    setDateTime();
    
    // Update time every minute (not every second)
    setInterval(setDateTime, 60000); // 60 seconds = 1 minute
    
    // Auto-refresh dashboard data every minute
    setInterval(function() {
        location.reload();
    }, 60000); // Refresh page every minute to update data

    // Maintain scroll position for pagination
    const scrollPosition = sessionStorage.getItem('dashboard_scroll_position');
    if (scrollPosition) {
        // Small delay to ensure page is fully loaded
        setTimeout(() => {
            window.scrollTo(0, parseInt(scrollPosition));
            sessionStorage.removeItem('dashboard_scroll_position');
        }, 100);
    }

    // Store scroll position before navigation
    const paginationLinks = document.querySelectorAll('#pagination-controls a');
    paginationLinks.forEach(link => {
        link.addEventListener('click', function() {
            sessionStorage.setItem('dashboard_scroll_position', window.scrollY.toString());
        });
    });

    // Handle sorting
    const sortableHeaders = document.querySelectorAll('.sortable-header');
    const urlParams = new URLSearchParams(window.location.search);
    const currentSortBy = urlParams.get('sort_by') || 'jumlah_ktp';
    const currentSortOrder = urlParams.get('sort_order') || 'desc';

    // Update sort icons based on current sorting
    sortableHeaders.forEach(header => {
        const column = header.dataset.column;
        const sortIcons = header.querySelector('.sort-icons');
        const ascIcon = sortIcons.querySelector('.sort-asc');
        const descIcon = sortIcons.querySelector('.sort-desc');

        if (column === currentSortBy) {
            if (currentSortOrder === 'asc') {
                ascIcon.classList.remove('opacity-30');
                ascIcon.classList.add('opacity-100', 'text-blue-600');
                descIcon.classList.add('opacity-30');
                descIcon.classList.remove('opacity-100', 'text-blue-600');
            } else {
                descIcon.classList.remove('opacity-30');
                descIcon.classList.add('opacity-100', 'text-blue-600');
                ascIcon.classList.add('opacity-30');
                ascIcon.classList.remove('opacity-100', 'text-blue-600');
            }
        } else {
            ascIcon.classList.add('opacity-30');
            ascIcon.classList.remove('opacity-100', 'text-blue-600');
            descIcon.classList.add('opacity-30');
            descIcon.classList.remove('opacity-100', 'text-blue-600');
        }
    });

    // Add click handlers for sorting
    sortableHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const column = this.dataset.column;
            const url = new URL(window.location);
            
            // If clicking the same column, toggle sort order
            if (url.searchParams.get('sort_by') === column) {
                const currentOrder = url.searchParams.get('sort_order') || 'desc';
                url.searchParams.set('sort_order', currentOrder === 'asc' ? 'desc' : 'asc');
            } else {
                // If clicking different column, set to descending (default for stock)
                url.searchParams.set('sort_by', column);
                url.searchParams.set('sort_order', column === 'jumlah_ktp' ? 'desc' : 'asc');
            }
            
            // Reset to first page when sorting
            url.searchParams.set('page', '1');
            
            // Store scroll position
            sessionStorage.setItem('dashboard_scroll_position', window.scrollY.toString());
            
            window.location.href = url.toString();
        });
    });
});

// Handle Unified Filtering (Live Search & Status)
const applyFilters = () => {
    const url = new URL(window.location);
    const searchVal = document.getElementById('searchInput').value;
    const statusVal = document.getElementById('statusFilter').value;
    const perPageVal = document.getElementById('perPageSelect').value;

    url.searchParams.set('search', searchVal);
    url.searchParams.set('status', statusVal);
    url.searchParams.set('per_page', perPageVal);
    url.searchParams.set('page', '1');
    
    // Smooth transition
    sessionStorage.setItem('dashboard_scroll_position', window.scrollY.toString());
    window.location.href = url.toString();
};

// Debounce for Search Input
let searchTimer;
const debounceFilter = () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(applyFilters, 600);
};

// Handle perPageSelect change
const perPageSelect = document.getElementById('perPageSelect');
if (perPageSelect) {
    perPageSelect.addEventListener('change', applyFilters);
}

// Handle Search Input (Live Search)
const searchInput = document.getElementById('searchInput');
if (searchInput) {
    searchInput.addEventListener('input', debounceFilter);
    // Also handle Enter as immediate
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') applyFilters();
    });
}

// Handle Status Filter Change
const statusFilter = document.getElementById('statusFilter');
if (statusFilter) {
    statusFilter.addEventListener('change', applyFilters);
}
