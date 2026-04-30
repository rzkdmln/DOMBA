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
    
    // Load existing documents
    loadEditDocuments(id);
    
    document.getElementById('editModal').classList.remove('hidden');
}

function loadEditDocuments(transaksiId) {
    const existingDocsDiv = document.getElementById('editExistingDocs');
    existingDocsDiv.innerHTML = '<p class="text-slate-400 text-sm">Memuat dokumen...</p>';
    
    fetch(`/admin/view_dokumen/${transaksiId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                existingDocsDiv.innerHTML = '';
                
                if (data.dokumen.length === 0) {
                    existingDocsDiv.innerHTML = '<p class="text-slate-400 text-sm italic">Tidak ada dokumen.</p>';
                } else {
                    data.dokumen.forEach(doc => {
                        const docItem = document.createElement('div');
                        docItem.className = 'flex items-center justify-between p-3 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors';
                        docItem.innerHTML = `
                            <div class="flex items-center space-x-3">
                                <div class="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                                    <i class="fa-solid fa-file-pdf text-purple-600 text-sm"></i>
                                </div>
                                <div>
                                    <p class="font-semibold text-slate-800 text-sm">${doc.nama_file}</p>
                                    <p class="text-[0.65rem] text-slate-500">${doc.ukuran_file}</p>
                                </div>
                            </div>
                            <div class="flex items-center space-x-2">
                                <a href="/admin/serve_dokumen/${doc.id}" target="_blank" class="px-3 py-1.5 bg-purple-600 text-white rounded-lg text-xs font-semibold hover:bg-purple-700 transition-colors">
                                    <i class="fa-solid fa-eye"></i>
                                </a>
                                <button onclick="deleteDocument(${doc.id}, ${transaksiId})" class="px-3 py-1.5 bg-rose-500 text-white rounded-lg text-xs font-semibold hover:bg-rose-600 transition-colors">
                                    <i class="fa-solid fa-trash"></i>
                                </button>
                            </div>
                        `;
                        existingDocsDiv.appendChild(docItem);
                    });
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            existingDocsDiv.innerHTML = '<p class="text-rose-500 text-sm">Gagal memuat dokumen.</p>';
        });
}

function deleteDocument(docId, transaksiId) {
    Swal.fire({
        title: 'Hapus Dokumen?',
        text: 'Dokumen yang dihapus tidak dapat dikembalikan.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'Ya, Hapus',
        cancelButtonText: 'Batal'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(`/admin/delete_dokumen/${docId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire({
                        title: 'Berhasil!',
                        text: 'Dokumen berhasil dihapus.',
                        icon: 'success',
                        confirmButtonColor: '#3b82f6'
                    });
                    loadEditDocuments(transaksiId);
                } else {
                    Swal.fire({
                        title: 'Gagal!',
                        text: data.message || 'Gagal menghapus dokumen.',
                        icon: 'error',
                        confirmButtonColor: '#ef4444'
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                Swal.fire({
                    title: 'Gagal!',
                    text: 'Terjadi kesalahan saat menghapus dokumen.',
                    icon: 'error',
                    confirmButtonColor: '#ef4444'
                });
            });
        }
    });
}

function deleteStokMasuk(button) {
    const transaksiId = button.dataset.id;
    
    Swal.fire({
        title: 'Hapus Transaksi?',
        text: 'Data transaksi yang dihapus tidak dapat dikembalikan.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'Ya, Hapus',
        cancelButtonText: 'Batal'
    }).then((result) => {
        if (result.isConfirmed) {
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = `/admin/delete_stok_masuk/${transaksiId}`;
            
            const csrfToken = document.querySelector('input[name="csrf_token"]');
            if (csrfToken) {
                const csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrf_token';
                csrfInput.value = csrfToken.value;
                form.appendChild(csrfInput);
            }
            
            document.body.appendChild(form);
            form.submit();
        }
    });
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

function viewDokumen(button) {
    const transaksiId = button.dataset.id;

    fetch(`/admin/view_dokumen/${transaksiId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const dokumenList = document.getElementById('dokumenList');
                dokumenList.innerHTML = '';

                if (data.dokumen.length === 0) {
                    dokumenList.innerHTML = '<p class="text-slate-400 text-sm italic">Tidak ada dokumen.</p>';
                } else {
                    data.dokumen.forEach(doc => {
                        const docItem = document.createElement('div');
                        docItem.className = 'p-3 bg-slate-50 rounded-xl hover:bg-purple-50 cursor-pointer transition-colors border-2 border-transparent hover:border-purple-200';
                        docItem.innerHTML = `
                            <div class="flex items-center space-x-3">
                                <div class="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0">
                                    <i class="fa-solid fa-file-pdf text-purple-600 text-sm"></i>
                                </div>
                                <div class="flex-1 min-w-0">
                                    <p class="font-semibold text-slate-800 text-sm truncate">${doc.nama_file}</p>
                                    <p class="text-[0.65rem] text-slate-500">${doc.ukuran_file}</p>
                                </div>
                            </div>
                        `;
                        docItem.onclick = () => previewPDF(doc.id, doc.nama_file);
                        dokumenList.appendChild(docItem);
                    });
                }

                // Reset preview area
                document.getElementById('pdfPreviewFrame').classList.add('hidden');
                document.getElementById('pdfPreviewArea').classList.remove('hidden');
                document.getElementById('pdfPreviewHeader').classList.add('hidden');

                document.getElementById('dokumenModal').classList.remove('hidden');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Gagal memuat dokumen.');
        });
}

function previewPDF(docId, docName) {
    const pdfPreviewFrame = document.getElementById('pdfPreviewFrame');
    const pdfPreviewArea = document.getElementById('pdfPreviewArea');
    const pdfPreviewHeader = document.getElementById('pdfPreviewHeader');
    const pdfPreviewTitle = document.getElementById('pdfPreviewTitle');

    // Show header with document name
    pdfPreviewTitle.textContent = docName;
    pdfPreviewHeader.classList.remove('hidden');

    // Hide placeholder and show iframe
    pdfPreviewArea.classList.add('hidden');
    pdfPreviewFrame.classList.remove('hidden');

    // Set iframe source to PDF
    pdfPreviewFrame.src = `/admin/serve_dokumen/${docId}`;
}

function closeDokumenModal() {
    document.getElementById('dokumenModal').classList.add('hidden');
    document.getElementById('pdfPreviewFrame').classList.add('hidden');
    document.getElementById('pdfPreviewArea').classList.remove('hidden');
    document.getElementById('pdfPreviewHeader').classList.add('hidden');
    document.getElementById('pdfPreviewFrame').src = '';
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
    const dokumenModal = document.getElementById('dokumenModal');

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

    if (dokumenModal) {
        dokumenModal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeDokumenModal();
            }
        });
    }
});
