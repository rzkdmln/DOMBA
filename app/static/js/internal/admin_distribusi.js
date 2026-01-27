function openEditModal(id, jumlah, kecamatan_id, kecamatan_nama) {
    document.getElementById('edit_transaksi_id').value = id;
    document.getElementById('edit_jumlah').value = jumlah;
    document.getElementById('edit_kecamatan_id').value = kecamatan_id;
    document.getElementById('editModal').classList.remove('hidden');
}

function closeEditModal() {
    document.getElementById('editModal').classList.add('hidden');
}

function openViewModal(id, tujuan, tanggal, alokasi, status) {
    document.getElementById('viewDistribusiId').innerText = '#' + id;
    document.getElementById('viewTujuan').innerText = tujuan;
    document.getElementById('viewTanggal').innerText = tanggal + ' WIB';
    document.getElementById('viewAlokasi').innerText = alokasi + ' Keping';
    document.getElementById('viewStatus').innerText = status;
    document.getElementById('viewModal').classList.remove('hidden');
}

function closeViewModal() {
    document.getElementById('viewModal').classList.add('hidden');
}

// Helper to open view modal using button dataset (avoids inline JS with templating)
function openViewModalFromButton(btn) {
    const id = btn.dataset.id;
    const tujuan = btn.dataset.kecamatan;
    const tanggal = btn.dataset.tanggal;
    const alokasi = btn.dataset.jumlah;
    const status = btn.dataset.status;
    openViewModal(id, tujuan, tanggal, alokasi, status);
}

// Helper to open edit modal using button dataset
function openEditModalFromButton(btn) {
    const id = btn.dataset.id;
    const jumlah = btn.dataset.jumlah;
    const kecamatanId = btn.dataset.kecamatanId || btn.dataset.kecamatan_id;
    const kecamatanNama = btn.dataset.kecamatan;
    openEditModal(id, jumlah, kecamatanId, kecamatanNama);
}

// Table sorting functionality helper
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

    const editModal = document.getElementById('editModal');
    const viewModal = document.getElementById('viewModal');

    if (editModal) {
        editModal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeEditModal();
            }
        });
    }

    if (viewModal) {
        viewModal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeViewModal();
            }
        });
    }

    // Handle kecamatan stock display
    const kecamatanSelect = document.querySelector('select[name="kecamatan_id"]');
    const sisaStokContainer = document.getElementById('sisa_stok_container');
    const sisaStokField = document.getElementById('sisa_stok');
    
    if (kecamatanSelect && sisaStokContainer && sisaStokField) {
        kecamatanSelect.addEventListener('change', function() {
            const kecamatanId = this.value;
            
            if (kecamatanId) {
                // Fetch stock data
                fetch(`/admin/get_kecamatan_stock/${kecamatanId}`)
                    .then(response => response.json())
                    .then(data => {
                        const jumlah = data.jumlah_ktp || 0;
                        sisaStokField.value = jumlah.toLocaleString('id-ID') + ' Keping';
                        sisaStokField.classList.remove('bg-slate-100', 'text-slate-400');
                        sisaStokField.classList.add('bg-emerald-50', 'text-emerald-700');
                    })
                    .catch(error => {
                        console.error('Error fetching stock:', error);
                        sisaStokField.value = 'Error memuat data';
                        sisaStokField.classList.remove('bg-slate-100', 'text-slate-400');
                        sisaStokField.classList.add('bg-red-50', 'text-red-700');
                    });
            } else {
                // Reset to placeholder when no kecamatan selected
                sisaStokField.value = '';
                sisaStokField.placeholder = 'Pilih kecamatan dahulu';
                sisaStokField.classList.remove('bg-emerald-50', 'text-emerald-700', 'bg-red-50', 'text-red-700');
                sisaStokField.classList.add('bg-slate-100', 'text-slate-400');
            }
        });
    }

    // Check if we need to restore scroll position
    const scrollPosition = sessionStorage.getItem('distribusi_scroll_position');
    if (scrollPosition) {
        // Small delay to ensure page is fully loaded
        setTimeout(() => {
            window.scrollTo(0, parseInt(scrollPosition));
            sessionStorage.removeItem('distribusi_scroll_position');
        }, 100);
    }

    // Store scroll position before navigation
    const paginationLinks = document.querySelectorAll('#pagination-controls a');
    paginationLinks.forEach(link => {
        link.addEventListener('click', function() {
            sessionStorage.setItem('distribusi_scroll_position', window.scrollY.toString());
        });
    });

    // Handle sorting for sebaran tab
    const sortableHeaders = document.querySelectorAll('.sortable-header');
    const urlParams = new URLSearchParams(window.location.search);
    const currentSortBy = urlParams.get('sort_by') || 'jumlah_ktp';
    const currentSortOrder = urlParams.get('sort_order') || 'desc';

    // Update sort icons based on current sorting
    sortableHeaders.forEach(header => {
        const column = header.dataset.column;
        const sortIcons = header.querySelector('.sort-icons');
        if (!sortIcons) return;
        
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
            sessionStorage.setItem('distribusi_scroll_position', window.scrollY.toString());
            
            window.location.href = url.toString();
        });
    });

    // Handle per page selector for sebaran tab
    const perPageSelect = document.getElementById('perPageSelect');
    if (perPageSelect) {
        perPageSelect.addEventListener('change', function() {
            const perPage = this.value;
            const url = new URL(window.location);
            url.searchParams.set('per_page', perPage);
            url.searchParams.set('page', '1'); // Reset to first page when changing per_page
            window.location.href = url.toString();
        });
    }

    // Filter functionality for stock status (only for sebaran tab)
    const activeTab = urlParams.get('tab') || 'distribusi';
    
    if (activeTab === 'sebaran') {
        const filterButton = document.getElementById('filterButton');
        const filterDropdown = document.getElementById('filterDropdown');
        const filterIndicator = document.getElementById('filterIndicator');
        
        // Get current filter from URL
        const currentFilter = urlParams.get('filter') || 'all';
        
        // Update filter UI based on current filter
        updateFilterUI(currentFilter);
        
        // Toggle dropdown
        if (filterButton) {
            filterButton.addEventListener('click', function(e) {
                e.stopPropagation();
                if (filterDropdown) filterDropdown.classList.toggle('hidden');
            });
        }
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (filterButton && filterDropdown && !filterButton.contains(e.target) && !filterDropdown.contains(e.target)) {
                filterDropdown.classList.add('hidden');
            }
        });
        
        // Apply initial filter to table rows
        applyTableFilter(currentFilter);
    }
});

function closeEditStockModal() {
    document.getElementById('editStockModal').classList.add('hidden');
}

function confirmEditStock(event) {
    event.preventDefault();
    const form = event.target;
    const kecamatanName = document.getElementById('editStockKecamatanName').value;
    const newStock = document.getElementById('editStockJumlah').value;
    
    Swal.fire({
        title: 'Konfirmasi Update Stok',
        text: `Apakah Anda yakin ingin mengubah stok blangko untuk ${kecamatanName} menjadi ${newStock} keping?`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Ya, Update',
        cancelButtonText: 'Batal'
    }).then((result) => {
        if (result.isConfirmed) {
            form.submit();
        }
    });
}

function applyFilter(filterType) {
    const url = new URL(window.location);
    url.searchParams.set('filter', filterType);
    url.searchParams.set('page', '1'); // Reset to first page when filtering
    
    // Store scroll position
    sessionStorage.setItem('distribusi_scroll_position', window.scrollY.toString());
    
    window.location.href = url.toString();
}

function updateFilterUI(activeFilter) {
    const filterOptions = document.querySelectorAll('.filter-option');
    const filterIndicator = document.getElementById('filterIndicator');
    
    filterOptions.forEach(option => {
        const checkIcon = option.querySelector('.filter-check');
        if (checkIcon) {
            if (option.dataset.filter === activeFilter) {
                checkIcon.classList.remove('hidden');
                option.classList.add('bg-indigo-50', 'text-indigo-700');
            } else {
                checkIcon.classList.add('hidden');
                option.classList.remove('bg-indigo-50', 'text-indigo-700');
            }
        }
    });
    
    // Show indicator if filter is active
    if (filterIndicator) {
        if (activeFilter !== 'all') {
            filterIndicator.classList.remove('hidden');
        } else {
            filterIndicator.classList.add('hidden');
        }
    }
}

function applyTableFilter(filterType) {
    const tableRows = document.querySelectorAll('#stockTable tbody tr');
    
    tableRows.forEach(row => {
        const statusBadge = row.querySelector('td:last-child span');
        let shouldShow = true;
        
        if (statusBadge) {
            const statusText = statusBadge.textContent.trim().toLowerCase();
            
            switch(filterType) {
                case 'tersedia':
                    shouldShow = statusText === 'tersedia';
                    break;
                case 'terbatas':
                    shouldShow = statusText === 'terbatas';
                    break;
                case 'habis':
                    shouldShow = statusText === 'habis';
                    break;
                case 'all':
                default:
                    shouldShow = true;
                    break;
            }
        }
        
        if (shouldShow) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// Modal functions for distribution log
function openViewModalFromButton(btn) {
    const id = btn.dataset.id;
    const kecamatan = btn.dataset.kecamatan;
    const tanggal = btn.dataset.tanggal;
    const jumlah = btn.dataset.jumlah;
    const status = btn.dataset.status;
    
    // Create modal content
    const modalContent = `
        <div class="p-6">
            <div class="flex items-center justify-between mb-6">
                <h3 class="text-xl font-bold text-slate-800">Detail Distribusi</h3>
                <button onclick="closeModal()" class="text-slate-400 hover:text-slate-600">
                    <i class="fa-solid fa-times"></i>
                </button>
            </div>
            <div class="space-y-4">
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-bold text-slate-500 mb-1">ID Transaksi</label>
                        <p class="text-slate-800 font-semibold">#${id}</p>
                    </div>
                    <div>
                        <label class="block text-sm font-bold text-slate-500 mb-1">Status</label>
                        <span class="px-3 py-1 bg-emerald-100 text-emerald-600 text-sm font-bold rounded-full">${status}</span>
                    </div>
                </div>
                <div>
                    <label class="block text-sm font-bold text-slate-500 mb-1">Tujuan</label>
                    <p class="text-slate-800 font-semibold">${kecamatan}</p>
                </div>
                <div>
                    <label class="block text-sm font-bold text-slate-500 mb-1">Tanggal & Waktu</label>
                    <p class="text-slate-800 font-semibold">${tanggal} WIB</p>
                </div>
                <div>
                    <label class="block text-sm font-bold text-slate-500 mb-1">Jumlah Dikirim</label>
                    <p class="text-2xl font-black text-indigo-600">${jumlah} Keping</p>
                </div>
            </div>
        </div>
    `;
    
    showModal(modalContent);
}

function openEditModalFromButton(btn) {
    const id = btn.dataset.id;
    const jumlah = btn.dataset.jumlah;
    const kecamatanId = btn.dataset.kecamatanId || btn.dataset.kecamatan_id;
    const kecamatan = btn.dataset.kecamatan;
    
    // Create modal content
    const modalContent = `
        <div class="p-6">
            <div class="flex items-center justify-between mb-6">
                <h3 class="text-xl font-bold text-slate-800">Edit Distribusi</h3>
                <button onclick="closeModal()" class="text-slate-400 hover:text-slate-600">
                    <i class="fa-solid fa-times"></i>
                </button>
            </div>
            <form action="/admin/edit_distribusi" method="POST" class="space-y-4">
                <input type="hidden" name="transaksi_id" value="${id}">
                <div>
                    <label class="block text-sm font-bold text-slate-500 mb-2">Kecamatan</label>
                    <input type="text" value="${kecamatan}" class="w-full px-3 py-2 border border-slate-200 rounded-lg bg-slate-50" readonly>
                </div>
                <div>
                    <label class="block text-sm font-bold text-slate-500 mb-2">Jumlah Baru</label>
                    <input type="number" name="jumlah_baru" value="${jumlah}" min="1" class="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500" required>
                </div>
                <div class="flex justify-end space-x-3 pt-4">
                    <button type="button" onclick="closeModal()" class="px-4 py-2 border border-slate-200 text-slate-600 rounded-lg hover:bg-slate-50">Batal</button>
                    <button type="submit" class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">Simpan</button>
                </div>
            </form>
        </div>
    `;
    
    showModal(modalContent);
}

function showModal(content) {
    // Create modal overlay
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    modal.innerHTML = `
        <div class="bg-white rounded-2xl shadow-xl max-w-md w-full mx-4">
            ${content}
        </div>
    `;
    document.body.appendChild(modal);
    
    // Close modal when clicking outside
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeModal();
        }
    });
}

function closeModal() {
    const modal = document.querySelector('.fixed.inset-0.bg-black');
    if (modal) {
        modal.remove();
    }
}
