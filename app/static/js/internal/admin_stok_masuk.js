function openAddModal() {
    document.getElementById('addStokModal').classList.remove('hidden');
}

function closeAddModal() {
    document.getElementById('addStokModal').classList.add('hidden');
}

function openEditModal(button) {
    const id = button.dataset.id;
    const jumlah = button.dataset.jumlah;
    const tanggal = button.dataset.tanggal;
    const keterangan = button.dataset.keterangan;
    
    document.getElementById('edit_transaksi_id').value = id;
    document.getElementById('edit_jumlah').value = jumlah;
    document.getElementById('edit_tanggal').value = tanggal;
    document.getElementById('edit_keterangan').value = keterangan;
    document.getElementById('editModal').classList.remove('hidden');
}

function closeEditModal() {
    document.getElementById('editModal').classList.add('hidden');
}

function openViewModal(button) {
    const id = button.dataset.id;
    const waktuInput = button.dataset.time;
    const sumber = button.dataset.sumber;
    const jumlah = button.dataset.jumlah;
    const petugas = button.dataset.user;
    const keterangan = button.dataset.keterangan;
    
    document.getElementById('viewTransaksiId').innerText = '#' + id;
    document.getElementById('viewWaktuInput').innerText = waktuInput + ' WIB';
    document.getElementById('viewSumber').innerText = sumber;
    document.getElementById('viewJumlah').innerText = jumlah + ' Keping';
    document.getElementById('viewPetugas').innerText = petugas;
    document.getElementById('viewKeterangan').innerText = keterangan || '-';
    document.getElementById('viewModal').classList.remove('hidden');
}

function closeViewModal() {
    document.getElementById('viewModal').classList.add('hidden');
}

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
});
