function initSorting() {
    const table = document.querySelector('table');
    if (!table) return;
    const headers = table.querySelectorAll('.sortable');
    
    headers.forEach(header => {
        header.addEventListener('click', function() {
            const column = parseInt(this.getAttribute('data-column'));
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            // Toggle sort direction
            const isAscending = this.classList.contains('asc');
            headers.forEach(h => h.classList.remove('asc', 'desc'));
            this.classList.toggle('asc', !isAscending);
            this.classList.toggle('desc', isAscending);
            
            // Sort rows
            rows.sort((a, b) => {
                const aText = a.cells[column].textContent.trim().toLowerCase();
                const bText = b.cells[column].textContent.trim().toLowerCase();
                
                if (isAscending) {
                    return aText.localeCompare(bText);
                } else {
                    return bText.localeCompare(aText);
                }
            });
            
            // Re-append sorted rows
            rows.forEach(row => tbody.appendChild(row));
        });
    });
}

document.addEventListener('DOMContentLoaded', function() {
    initSorting();

    // Maintain scroll position for pagination
    const scrollPosition = sessionStorage.getItem('monitoring_cetak_scroll_position');
    if (scrollPosition) {
        // Small delay to ensure page is fully loaded
        setTimeout(() => {
            window.scrollTo(0, parseInt(scrollPosition));
            sessionStorage.removeItem('monitoring_cetak_scroll_position');
        }, 100);
    }

    // Store scroll position before navigation
    const paginationLinks = document.querySelectorAll('#pagination-controls a');
    paginationLinks.forEach(link => {
        link.addEventListener('click', function() {
            sessionStorage.setItem('monitoring_cetak_scroll_position', window.scrollY.toString());
        });
    });
});

// Handle perPageSelect change
document.getElementById('perPageSelect').addEventListener('change', function() {
    const perPage = this.value;
    const url = new URL(window.location);
    url.searchParams.set('per_page', perPage);
    url.searchParams.set('page', '1'); // Reset to first page when changing per_page
    window.location.href = url.toString();
});

// Function to update filters
function updateFilters() {
    const searchInput = document.getElementById('searchInput');
    const kecamatanFilter = document.getElementById('kecamatanFilter');
    const statusFilter = document.getElementById('statusFilter');
    const kondisiFilter = document.getElementById('kondisiFilter');
    const operatorFilter = document.getElementById('operatorFilter');
    
    const searchTerm = searchInput ? searchInput.value.trim() : '';
    const kecamatanVal = kecamatanFilter ? kecamatanFilter.value : '';
    const statusVal = statusFilter ? statusFilter.value : '';
    const kondisiVal = kondisiFilter ? kondisiFilter.value : '';
    const operatorVal = operatorFilter ? operatorFilter.value : '';
    
    const url = new URL(window.location);
    if (searchTerm) {
        url.searchParams.set('search', searchTerm);
    } else {
        url.searchParams.delete('search');
    }
    
    if (kecamatanVal) {
        url.searchParams.set('kecamatan', kecamatanVal);
    } else {
        url.searchParams.delete('kecamatan');
    }
    
    if (statusVal) {
        url.searchParams.set('status', statusVal);
    } else {
        url.searchParams.delete('status');
    }

    if (kondisiVal) {
        url.searchParams.set('kondisi', kondisiVal);
    } else {
        url.searchParams.delete('kondisi');
    }
    
    if (operatorVal) {
        url.searchParams.set('operator', operatorVal);
    } else {
        url.searchParams.delete('operator');
    }
    
    url.searchParams.set('page', '1'); // Reset to first page when filtering
    window.location.href = url.toString();
}

const searchInput = document.getElementById('searchInput');
if (searchInput) {
    searchInput.addEventListener('input', function() {
        // Debounce search input to avoid too many requests
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(updateFilters, 500);
    });
}

const kecamatanFilter = document.getElementById('kecamatanFilter');
if (kecamatanFilter) kecamatanFilter.addEventListener('change', updateFilters);

const statusFilter = document.getElementById('statusFilter');
if (statusFilter) statusFilter.addEventListener('change', updateFilters);

const kondisiFilter = document.getElementById('kondisiFilter');
if (kondisiFilter) kondisiFilter.addEventListener('change', updateFilters);

const operatorFilter = document.getElementById('operatorFilter');
if (operatorFilter) operatorFilter.addEventListener('change', updateFilters);
