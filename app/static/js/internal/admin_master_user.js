function openAddModal() {
    document.getElementById('addUserModal').classList.remove('hidden');
}

function closeAddModal() {
    document.getElementById('addUserModal').classList.add('hidden');
}

function openEditModal(button) {
    const id = button.dataset.id;
    const username = button.dataset.username;
    const role = button.dataset.role;
    
    document.getElementById('edit_user_id').value = id;
    document.getElementById('edit_username').value = username;
    document.getElementById('edit_role').value = role;
    // Set nama_lengkap
    fetch(`/admin/get_user_details/${id}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('edit_nama_lengkap').value = data.nama_lengkap || '';
            if (data.kecamatan_id) {
                document.getElementById('edit_kecamatan_id').value = data.kecamatan_id;
            }
        });
    toggleKecamatanField(); // Set initial visibility
    document.getElementById('editUserModal').classList.remove('hidden');
}

function closeEditModal() {
    document.getElementById('editUserModal').classList.add('hidden');
}

function openViewModal(button) {
    const id = button.dataset.id;
    const username = button.dataset.username;
    const namaLengkap = button.dataset.nama;
    const role = button.dataset.role;
    const createdAt = button.dataset.created;
    const lastLogin = button.dataset.lastLogin;

    document.getElementById('viewUserId').innerText = '#' + id;
    document.getElementById('viewUsername').innerText = username;
    document.getElementById('viewNamaLengkap').innerText = namaLengkap;
    document.getElementById('viewRole').innerText = role === 'admin_dinas' ? 'Admin Dinas' : 'Operator Kecamatan';
    document.getElementById('viewCreatedAt').innerText = createdAt || '-';
    document.getElementById('viewLastLogin').innerText = lastLogin || '-';
    document.getElementById('viewUserModal').classList.remove('hidden');
}

function closeViewModal() {
    document.getElementById('viewUserModal').classList.add('hidden');
}

function resetPassword(button) {
    const id = button.dataset.id;
    const username = button.dataset.username;
    Swal.fire({
        title: 'Reset Password',
        text: `Yakin reset password untuk ${username}? Password akan diset sama dengan username.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Ya, Reset!',
        cancelButtonText: 'Batal'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(`/admin/reset_password/${id}`, { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    Swal.fire(
                        'Berhasil!',
                        data.message,
                        'success'
                    ).then(() => {
                        if (data.success) location.reload();
                    });
                });
        }
    });
}

function toggleKecamatanField() {
    const role = document.getElementById('edit_role').value;
    const kecamatanField = document.getElementById('kecamatanField');
    const kecamatanSelect = document.getElementById('edit_kecamatan_id');
    
    if (role === 'admin_dinas') {
        kecamatanField.style.display = 'none';
        kecamatanSelect.required = false;
        kecamatanSelect.value = '';
    } else {
        kecamatanField.style.display = 'block';
        kecamatanSelect.required = true;
    }
}

function toggleKecamatanFieldAdd() {
    const role = document.querySelector('#addUserModal select[name="role"]').value;
    const kecamatanField = document.getElementById('kecamatanFieldAdd');
    const kecamatanSelect = document.querySelector('#addUserModal select[name="kecamatan_id"]');
    
    if (role === 'admin_dinas') {
        kecamatanField.style.display = 'none';
        kecamatanSelect.required = false;
        kecamatanSelect.value = '';
    } else {
        kecamatanField.style.display = 'block';
        kecamatanSelect.required = true;
    }
}

// Search and Filter Functions - Now handled server-side
// Removed client-side filtering functions

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

    const addUserBtn = document.getElementById('addUserBtn');
    
    if (addUserBtn) {
        addUserBtn.onclick = function() {
            openAddModal();
            toggleKecamatanFieldAdd(); // Set initial state
        };
    }

    const addUserModal = document.getElementById('addUserModal');
    const editUserModal = document.getElementById('editUserModal');
    const viewUserModal = document.getElementById('viewUserModal');

    if (addUserModal) {
        addUserModal.addEventListener('click', function(e) {
            if (e.target === this) closeAddModal();
        });
    }
    if (editUserModal) {
        editUserModal.addEventListener('click', function(e) {
            if (e.target === this) closeEditModal();
        });
    }
    if (viewUserModal) {
        viewUserModal.addEventListener('click', function(e) {
            if (e.target === this) closeViewModal();
        });
    }

    // Maintain scroll position for pagination
    const scrollPosition = sessionStorage.getItem('master_user_scroll_position');
    if (scrollPosition) {
        // Small delay to ensure page is fully loaded
        setTimeout(() => {
            window.scrollTo(0, parseInt(scrollPosition));
            sessionStorage.removeItem('master_user_scroll_position');
        }, 100);
    }

    // Store scroll position before navigation
    const paginationLinks = document.querySelectorAll('#pagination-controls a');
    paginationLinks.forEach(link => {
        link.addEventListener('click', function() {
            sessionStorage.setItem('master_user_scroll_position', window.scrollY.toString());
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
    const searchTerm = document.getElementById('searchInput').value.trim();
    const roleFilter = document.getElementById('roleFilter').value;
    
    const url = new URL(window.location);
    if (searchTerm) {
        url.searchParams.set('search', searchTerm);
    } else {
        url.searchParams.delete('search');
    }
    
    if (roleFilter) {
        url.searchParams.set('role', roleFilter);
    } else {
        url.searchParams.delete('role');
    }
    
    url.searchParams.set('page', '1'); // Reset to first page when filtering
    window.location.href = url.toString();
}

document.getElementById('searchInput').addEventListener('input', function() {
    // Debounce search input to avoid too many requests
    clearTimeout(this.searchTimeout);
    this.searchTimeout = setTimeout(updateFilters, 500);
});

document.getElementById('roleFilter').addEventListener('change', updateFilters);
