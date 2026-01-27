const isAdmin = document.getElementById('role-data').dataset.isAdmin === 'true';

function openAmbilModal(button) {
    const id = button.dataset.id;
    const name = button.dataset.nama;
    const modal = document.getElementById('ambilModal');
    const form = document.getElementById('ambilForm');
    const nameDisplay = document.getElementById('modalWargaName');
    const hubunganSelect = document.getElementById('hubunganSelect');
    const penerimaInput = document.getElementById('penerimaInput');
    
    const baseUrl = isAdmin ? '/admin' : '/operator';
    if (form) form.action = `${baseUrl}/update-status-ambil/${id}`;
    if (nameDisplay) nameDisplay.innerText = `Warga: ${name}`;
    
    // Reset form
    if (hubunganSelect) hubunganSelect.value = '';
    if (penerimaInput) penerimaInput.value = '';
    
    const useNowCheckbox = document.getElementById('useNowCheckbox');
    if (useNowCheckbox) useNowCheckbox.checked = true;
    
    const customDateTime = document.getElementById('customDateTime');
    if (customDateTime) customDateTime.classList.add('hidden');
    
    if (modal) modal.classList.remove('hidden');
}

function closeAmbilModal() {
    const modal = document.getElementById('ambilModal');
    if (modal) modal.classList.add('hidden');
}

function openEditModal(button) {
    const id = button.dataset.id;
    const nik = button.dataset.nik;
    const nama = button.dataset.nama;
    const jenisCetak = button.dataset.jenisCetak;
    const registrasiIkd = button.dataset.registrasiIkd;
    const statusCetak = button.dataset.status;
    const keterangan = button.dataset.keterangan;
    const statusAmbil = button.dataset.ambil;
    const hubungan = button.dataset.hubungan;
    const penerima = button.dataset.penerima;

    const modal = document.getElementById('editModal');
    const form = document.getElementById('editForm');
    
    const baseUrl = isAdmin ? '/admin' : '/operator';
    if (form) form.action = `${baseUrl}/update-cetak/${id}`;
    
    document.getElementById('editNik').value = nik;
    document.getElementById('editNama').value = nama;
    document.getElementById('editJenisCetak').value = jenisCetak || '';
    
    // Set Registrasi IKD (Radio)
    if (registrasiIkd === 'true') {
        document.querySelector('input[name="registrasi_ikd"][value="true"]').checked = true;
    } else {
        document.querySelector('input[name="registrasi_ikd"][value="false"]').checked = true;
    }
    
    // Set Status Cetak (Radio)
    if (statusCetak === 'BERHASIL') {
        document.getElementById('editStatusBerhasil').checked = true;
    } else {
        document.getElementById('editStatusGagal').checked = true;
    }
    
    document.getElementById('editKeteranganGagal').value = keterangan || '';
    
    // Set Status Ambil (Checkbox)
    const statusAmbilBool = (statusAmbil === 'True' || statusAmbil === 'true');
    document.getElementById('editStatusAmbil').checked = statusAmbilBool;
    
    document.getElementById('editHubungan').value = hubungan || 'Yang Bersangkutan';
    document.getElementById('editPenerima').value = penerima || '';
    
    // Toggle containers
    toggleEditSections();
    
    if (modal) modal.classList.remove('hidden');
}

function toggleEditSections() {
    const isGagal = document.getElementById('editStatusGagal').checked;
    const gagalContainer = document.getElementById('editGagalReasonContainer');
    const ambilStatusContainer = document.getElementById('editAmbilStatusContainer');
    const ambilFormContainer = document.getElementById('editAmbilFormContainer');
    
    if (isGagal) {
        gagalContainer.classList.remove('hidden');
        ambilStatusContainer.classList.add('hidden');
        ambilFormContainer.classList.add('hidden');
    } else {
        gagalContainer.classList.add('hidden');
        ambilStatusContainer.classList.remove('hidden');
        toggleEditAmbilForm();
    }
}

function toggleEditAmbilForm() {
    const isAmbil = document.getElementById('editStatusAmbil').checked;
    const formContainer = document.getElementById('editAmbilFormContainer');
    
    if (isAmbil) {
        formContainer.classList.remove('hidden');
    } else {
        formContainer.classList.add('hidden');
    }
}

function closeEditModal() {
    const modal = document.getElementById('editModal');
    if (modal) modal.classList.add('hidden');
}

function openViewModal(button) {
    const id = button.dataset.id;
    const nik = button.dataset.nik;
    const nama = button.dataset.nama;
    const kecamatan = button.dataset.kecamatan;
    const jenisCetak = button.dataset.jenisCetak;
    const registrasiIkd = button.dataset.registrasiIkd;
    const waktuCetak = button.dataset.waktu;
    const kondisi = button.dataset.status; // BERHASIL or GAGAL
    const ambil = button.dataset.ambil; // true or false
    const hubungan = button.dataset.hubungan;
    const penerima = button.dataset.penerima;
    const waktuAmbil = button.dataset.waktuAmbil;
    const keterangan = button.dataset.keterangan;
    
    const kecamatanDiv = document.getElementById('viewKecamatan');
    const nikDiv = document.getElementById('viewNik');
    const namaDiv = document.getElementById('viewNama');
    const jenisCetakDiv = document.getElementById('viewJenisCetak');
    const registrasiIkdDiv = document.getElementById('viewRegistrasiIKD');
    const waktuCetakDiv = document.getElementById('viewWaktuCetak');
    const kondisiDiv = document.getElementById('viewKondisi');
    const statusDiv = document.getElementById('viewStatus');
    const keteranganDiv = document.getElementById('viewKeterangan');
    const gagalDetail = document.getElementById('gagalDetail');
    const statusAmbilDiv = document.getElementById('statusAmbilDiv');
    
    if (kecamatanDiv) kecamatanDiv.innerText = kecamatan;
    if (nikDiv) nikDiv.innerText = nik;
    if (namaDiv) namaDiv.innerText = nama;
    if (jenisCetakDiv) jenisCetakDiv.innerText = jenisCetak || '-';
    if (registrasiIkdDiv) registrasiIkdDiv.innerText = (registrasiIkd === 'true') ? 'Ya' : 'Tidak';
    if (waktuCetakDiv) waktuCetakDiv.innerText = waktuCetak + ' WIB';
    
    if (kondisiDiv) {
        kondisiDiv.innerText = kondisi;
        kondisiDiv.className = 'text-sm font-black ' + (kondisi === 'BERHASIL' ? 'text-emerald-600' : 'text-rose-600');
    }

    if (kondisi === 'GAGAL') {
        if (gagalDetail) gagalDetail.classList.remove('hidden');
        if (keteranganDiv) keteranganDiv.innerText = keterangan || 'Tanpa Keterangan';
        if (statusAmbilDiv) statusAmbilDiv.classList.add('hidden');
    } else {
        if (gagalDetail) gagalDetail.classList.add('hidden');
        if (statusAmbilDiv) statusAmbilDiv.classList.remove('hidden');
        if (statusDiv) statusDiv.innerText = ambil === 'true' || ambil === 'sudah' ? 'Sudah Diambil' : 'Belum Diambil';
    }
    
    const ambilDetail = document.getElementById('ambilDetail');
    if (kondisi === 'BERHASIL' && (ambil === 'true' || ambil === 'sudah')) {
        const hubunganDiv = document.getElementById('viewHubungan');
        const penerimaDiv = document.getElementById('viewPenerima');
        const waktuAmbilDiv = document.getElementById('viewWaktuAmbil');
        
        if (hubunganDiv) hubunganDiv.innerText = hubungan;
        if (penerimaDiv) penerimaDiv.innerText = penerima;
        if (waktuAmbilDiv) waktuAmbilDiv.innerText = waktuAmbil + ' WIB';
        if (ambilDetail) ambilDetail.classList.remove('hidden');
    } else {
        if (ambilDetail) ambilDetail.classList.add('hidden');
    }
    
    const modal = document.getElementById('viewModal');
    if (modal) modal.classList.remove('hidden');
}

function closeViewModal() {
    const modal = document.getElementById('viewModal');
    if (modal) modal.classList.add('hidden');
}

function toggleGagalReason(show) {
    const container = document.getElementById('gagalReasonContainer');
    const textarea = document.querySelector('textarea[name="keterangan_gagal"]');
    if (container) {
        if (show) {
            container.classList.remove('hidden');
        } else {
            container.classList.add('hidden');
            if (textarea) {
                textarea.value = '';
            }
        }
    }
}

function deleteCetak(button) {
    const id = button.dataset.id;
    Swal.fire({
        title: 'Hapus Cetakan?',
        text: 'Data cetakan akan dihapus permanen dan tidak dapat dikembalikan.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Ya, Hapus',
        cancelButtonText: 'Batal'
    }).then((result) => {
        if (result.isConfirmed) {
            const baseUrl = isAdmin ? '/admin' : '/operator';
            window.location.href = `${baseUrl}/delete-cetak/${id}`;
        }
    });
}

function validateForm() {
    const nik = document.querySelector('input[name="nik"]').value.trim();
    const namaLengkap = document.querySelector('input[name="nama_lengkap"]').value.trim();
    const jenisCetak = document.querySelector('select[name="jenis_cetak"]').value;
    const statusCetak = document.querySelector('input[name="status_cetak"]:checked');
    const registrasiIkd = document.querySelector('input[name="registrasi_ikd"]:checked');
    const keteranganGagal = document.querySelector('textarea[name="keterangan_gagal"]').value.trim();

    // Check NIK
    if (!nik) {
        Swal.fire({
            icon: 'error',
            title: 'NIK Wajib Diisi',
            text: 'Masukkan NIK 16 digit warga yang dicetak KTP-el nya.',
            confirmButtonColor: '#d33'
        });
        return false;
    }
    if (nik.length !== 16 || !/^\d{16}$/.test(nik)) {
        Swal.fire({
            icon: 'error',
            title: 'NIK Tidak Valid',
            text: 'NIK harus terdiri dari 16 digit angka.',
            confirmButtonColor: '#d33'
        });
        return false;
    }

    // Check Nama Lengkap
    if (!namaLengkap) {
        Swal.fire({
            icon: 'error',
            title: 'Nama Lengkap Wajib Diisi',
            text: 'Masukkan nama lengkap sesuai KTP.',
            confirmButtonColor: '#d33'
        });
        return false;
    }

    // Check Jenis Cetak
    if (!jenisCetak) {
        Swal.fire({
            icon: 'error',
            title: 'Jenis Cetak Wajib Dipilih',
            text: 'Pilih jenis cetak KTP-el.',
            confirmButtonColor: '#d33'
        });
        return false;
    }

    // Check Status Cetak
    if (!statusCetak) {
        Swal.fire({
            icon: 'error',
            title: 'Kondisi Hasil Cetak Wajib Dipilih',
            text: 'Pilih apakah hasil cetak BERHASIL atau GAGAL/RUSAK.',
            confirmButtonColor: '#d33'
        });
        return false;
    }

    // If GAGAL, check keterangan_gagal
    if (statusCetak.value === 'GAGAL' && !keteranganGagal) {
        Swal.fire({
            icon: 'error',
            title: 'Penyebab Gagal Wajib Diisi',
            text: 'Jelaskan penyebab hasil cetak gagal atau rusak.',
            confirmButtonColor: '#d33'
        });
        return false;
    }

    // Check Registrasi IKD
    if (!registrasiIkd) {
        Swal.fire({
            icon: 'error',
            title: 'Registrasi IKD Wajib Dipilih',
            text: 'Pilih apakah warga sudah registrasi IKD atau belum.',
            confirmButtonColor: '#d33'
        });
        return false;
    }

    return true;
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
            
            const isAscending = this.classList.contains('asc');
            headers.forEach(h => h.classList.remove('asc', 'desc'));
            this.classList.toggle('asc', !isAscending);
            this.classList.toggle('desc', isAscending);
            
            rows.sort((a, b) => {
                const aText = a.cells[column].textContent.trim().toLowerCase();
                const bText = b.cells[column].textContent.trim().toLowerCase();
                return isAscending ? aText.localeCompare(bText) : bText.localeCompare(aText);
            });
            
            rows.forEach(row => tbody.appendChild(row));
        });
    });
}

document.addEventListener('DOMContentLoaded', function() {
    initSorting();

    // Auto-fill nama jika "Yang Bersangkutan"
    const hubunganSelect = document.getElementById('hubunganSelect');
    if (hubunganSelect) {
        hubunganSelect.addEventListener('change', function() {
            const penerimaInput = document.getElementById('penerimaInput');
            const nameDisplay = document.getElementById('modalWargaName');
            if (nameDisplay && penerimaInput) {
                const namaWarga = nameDisplay.innerText.replace('Warga: ', '');
                if (this.value === 'Yang Bersangkutan') {
                    penerimaInput.value = namaWarga;
                } else {
                    penerimaInput.value = '';
                }
            }
        });
    }

    // Toggle custom date time
    const useNowCheckbox = document.getElementById('useNowCheckbox');
    if (useNowCheckbox) {
        useNowCheckbox.addEventListener('change', function() {
            const customDateTime = document.getElementById('customDateTime');
            if (customDateTime) {
                if (this.checked) {
                    customDateTime.classList.add('hidden');
                } else {
                    customDateTime.classList.remove('hidden');
                }
            }
        });
    }

    // Modal click-outside behavior
    const modals = ['ambilModal', 'editModal', 'viewModal'];
    modals.forEach(id => {
        const modal = document.getElementById(id);
        if (modal) {
            modal.addEventListener('click', function(e) {
                if (e.target === this) {
                    this.classList.add('hidden');
                }
            });
        }
    });

    // Maintain scroll position for pagination
    const scrollPosition = sessionStorage.getItem('lapor_pakai_scroll_position');
    if (scrollPosition) {
        setTimeout(() => {
            window.scrollTo(0, parseInt(scrollPosition));
            sessionStorage.removeItem('lapor_pakai_scroll_position');
        }, 100);
    }

    // Store scroll position before navigation
    const paginationLinks = document.querySelectorAll('#pagination-controls a');
    paginationLinks.forEach(link => {
        link.addEventListener('click', function() {
            sessionStorage.setItem('lapor_pakai_scroll_position', window.scrollY.toString());
        });
    });

    // Handle per page selector
    const perPageSelect = document.getElementById('perPageSelect');
    if (perPageSelect) {
        perPageSelect.addEventListener('change', function() {
            const perPage = this.value;
            const url = new URL(window.location);
            url.searchParams.set('per_page', perPage);
            url.searchParams.set('page', '1');
            window.location.href = url.toString();
        });
    }
});
