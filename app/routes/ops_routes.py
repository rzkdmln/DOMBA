# pyright: reportCallIssue=false
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user  # type: ignore
from app.extensions import db
from app.models import DetailCetak, Stok, Transaksi
from sqlalchemy.orm import joinedload
from app.utils import get_gmt7_time, validate_cetak_data, process_stok_pengurangan
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO
import re

ops_bp = Blueprint('operator', __name__)

@ops_bp.route('/dashboard')
@login_required
def dashboard():
    # Ambil stok kecamatan saat ini
    stok = Stok.query.filter_by(kecamatan_id=current_user.kecamatan_id).first()
    
    # Ambil 5 cetakan terakhir (dibatasi untuk dashboard)
    recent_cetak = DetailCetak.query.options(joinedload(DetailCetak.user), joinedload(DetailCetak.kecamatan))\
        .filter_by(kecamatan_id=current_user.kecamatan_id)\
        .order_by(DetailCetak.tanggal_cetak.desc()).limit(5).all()
        
    # Hitung total hari ini
    today = get_gmt7_time().date()
    total_hari_ini = DetailCetak.query.filter_by(kecamatan_id=current_user.kecamatan_id)\
        .filter(db.func.date(DetailCetak.tanggal_cetak) == today).count()

    # Ambil 5 transaksi terakhir untuk kecamatan ini (dibatasi untuk dashboard)
    recent_transactions = Transaksi.query.options(joinedload(Transaksi.user), joinedload(Transaksi.kecamatan))\
        .filter_by(kecamatan_id=current_user.kecamatan_id)\
        .order_by(Transaksi.created_at.desc()).limit(5).all()

    return render_template('operator/dashboard.html', 
                          stok=stok, 
                          recent_cetak=recent_cetak,
                          total_hari_ini=total_hari_ini,
                          recent_transactions=recent_transactions)

@ops_bp.route('/export-my-cetak')
@login_required
def export_my_cetak():
    cetaks = DetailCetak.query.filter_by(kecamatan_id=current_user.kecamatan_id).all()
    
    data = []
    for c in cetaks:
        data.append({
            'Waktu Cetak': c.tanggal_cetak.strftime('%Y-%m-%d %H:%M:%S'),
            'NIK': c.nik,
            'Nama Lengkap': c.nama_lengkap,
            'Jenis Cetak': c.jenis_cetak or '-',
            'Registrasi IKD': 'Ya' if c.registrasi_ikd else 'Tidak',
            'Status Cetak': c.status_cetak,
            'Keterangan Gagal': c.keterangan_gagal or '-',
            'Status Ambil': 'Sudah' if c.status_ambil else 'Belum',
            'Waktu Ambil': c.tanggal_ambil.strftime('%Y-%m-%d %H:%M:%S') if c.tanggal_ambil else '-',
            'Penerima': c.penerima or '-',
        })
    
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Data Cetak Saya')
    
    output.seek(0)
    filename = f"laporan_cetak_{current_user.username}_{get_gmt7_time().strftime('%Y%m%d')}.xlsx"
    return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@ops_bp.route('/lapor-pakai', methods=['GET', 'POST'])
@login_required
def lapor_pakai():
    if request.method == 'POST':
        nik = request.form.get('nik')
        nama = request.form.get('nama_lengkap')
        jenis_cetak = request.form.get('jenis_cetak')
        registrasi_ikd_val = request.form.get('registrasi_ikd')
        registrasi_ikd = registrasi_ikd_val == 'true' if registrasi_ikd_val is not None else None
        status_cetak = request.form.get('status_cetak', 'BERHASIL')
        keterangan_gagal = request.form.get('keterangan_gagal')
        
        # Validasi menggunakan utility
        is_valid, error_msg = validate_cetak_data(nik, nama, jenis_cetak, registrasi_ikd_val)
        if not is_valid and error_msg:
            flash(error_msg, 'danger')
            return redirect(url_for('operator.lapor_pakai'))
        
        # 1. Buat object detail cetak
        new_record = DetailCetak(
            nik=nik,
            nama_lengkap=nama,
            jenis_cetak=jenis_cetak,
            registrasi_ikd=registrasi_ikd,
            user_id=current_user.id,
            kecamatan_id=current_user.kecamatan_id,
            status_cetak=status_cetak,
            keterangan_gagal=keterangan_gagal if status_cetak == 'GAGAL' else None
        )
        
        # 2. Proses stok dan transaksi menggunakan utility (Asumsi lapor pakai ini khusus KTP-el)
        success, message = process_stok_pengurangan(
            current_user.kecamatan_id, 
            current_user.id, 
            status_cetak, 
            new_record
        )
        
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
            
        return redirect(url_for('operator.lapor_pakai'))

    # GET request
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Validate per_page options
    if per_page not in [10, 20, 50]:  # Only allow these options for operator
        per_page = 10
    
    # Define history_query before pagination
    history_query = DetailCetak.query.filter_by(kecamatan_id=current_user.kecamatan_id)\
        .filter(DetailCetak.status_ambil == False)\
        .order_by(DetailCetak.tanggal_cetak.desc())
    
    # Get history with pagination using Flask-SQLAlchemy paginate
    pagination = history_query.paginate(page=page, per_page=per_page, error_out=False)
    history = pagination.items
    total_cetak = pagination.total
    
    # Format pagination info to match existing structure
    pagination_info = {
        'page': pagination.page,
        'per_page': pagination.per_page,
        'total_pages': pagination.pages,
        'total_records': pagination.total,
        'has_prev': pagination.has_prev,
        'has_next': pagination.has_next,
        'prev_page': pagination.prev_num,
        'next_page': pagination.next_num
    }
        
    stok = Stok.query.filter_by(kecamatan_id=current_user.kecamatan_id).first()
    
    return render_template('operator/lapor_pakai.html', history=history, stok=stok, total_cetak=total_cetak, pagination_info=pagination_info)

@ops_bp.route('/monitoring-cetak')
@login_required
def monitoring_cetak():
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Get filter parameters
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '')
    kondisi_filter = request.args.get('kondisi', '')
    
    # Validate per_page options
    if per_page not in [10, 20, 50, 0]:
        per_page = 10
    
    # Build query filtered by current user's kecamatan
    cetaks_query = DetailCetak.query.options(joinedload(DetailCetak.user), joinedload(DetailCetak.kecamatan))\
        .filter_by(kecamatan_id=current_user.kecamatan_id)
    
    # Apply search filter
    if search:
        cetaks_query = cetaks_query.filter(
            db.or_(
                DetailCetak.nama_lengkap.ilike(f'%{search}%'),
                DetailCetak.nik.ilike(f'%{search}%')
            )
        )
    
    # Apply status ambil filter
    if status_filter:
        if status_filter == 'diambil':
            cetaks_query = cetaks_query.filter(DetailCetak.status_ambil == True)
        elif status_filter == 'pending':
            cetaks_query = cetaks_query.filter(DetailCetak.status_ambil == False)

    # Apply kondisi cetak filter
    if kondisi_filter:
        cetaks_query = cetaks_query.filter(DetailCetak.status_cetak == kondisi_filter)
    
    # Order by tanggal_cetak desc
    cetaks_query = cetaks_query.order_by(DetailCetak.tanggal_cetak.desc())
    
    # Get cetaks with pagination
    if per_page == 0:
        cetaks = cetaks_query.all()
        pagination_info = None
    else:
        # Paginated query using Flask-SQLAlchemy paginate
        pagination = cetaks_query.paginate(page=page, per_page=per_page, error_out=False)
        cetaks = pagination.items
        
        # Format pagination info to match existing structure
        pagination_info = {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total_pages': pagination.pages,
            'total_records': pagination.total,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
            'prev_page': pagination.prev_num,
            'next_page': pagination.next_num
        }
    
    return render_template('admin/monitoring_cetak.html', 
                         cetaks=cetaks, 
                         pagination_info=pagination_info,
                         search=search,
                         status_filter=status_filter,
                         kondisi_filter=kondisi_filter,
                         is_operator=True,
                         kecamatan_name=current_user.kecamatan.nama_kecamatan)

@ops_bp.route('/update-status-ambil/<int:id>', methods=['POST'])
@login_required
def update_status_ambil(id):
    record = DetailCetak.query.get_or_404(id)
    
    # Pastikan operator hanya bisa update data kecamatannya sendiri
    if record.kecamatan_id != current_user.kecamatan_id:
        flash('Unauthorized!', 'danger')
        return redirect(url_for('operator.lapor_pakai'))
        
    status = request.form.get('status') == 'true'
    hubungan = request.form.get('hubungan')
    penerima = request.form.get('penerima')
    tanggal_custom = request.form.get('tanggal_custom')
    waktu_custom = request.form.get('waktu_custom')
    use_now = request.form.get('use_now') == 'on'
    
    # Validasi penerima
    if not penerima or not re.match(r'^[A-Z\s\'\-]+$', penerima):
        flash('Nama pengambil hanya boleh huruf kapital, spasi, dash, atau kutip!', 'danger')
        return redirect(url_for('operator.lapor_pakai'))
    
    record.status_ambil = status
    record.hubungan = hubungan
    record.penerima = penerima
    if status:
        if use_now:
            record.tanggal_ambil = get_gmt7_time()
        else:
            if tanggal_custom and waktu_custom:
                tanggal_waktu = f"{tanggal_custom} {waktu_custom}"
                record.tanggal_ambil = datetime.strptime(tanggal_waktu, '%Y-%m-%d %H:%M')
            else:
                flash('Tanggal dan waktu harus diisi jika tidak menggunakan waktu sekarang!', 'danger')
                return redirect(url_for('operator.lapor_pakai'))
    else:
        record.tanggal_ambil = None
        record.hubungan = None
        record.penerima = None
        
    db.session.commit()
    flash('Status pengambilan berhasil diperbarui', 'success')
    return redirect(url_for('operator.lapor_pakai'))

@ops_bp.route('/update-cetak/<int:id>', methods=['POST'])
@login_required
def update_cetak(id):
    record = DetailCetak.query.get_or_404(id)
    
    # Pastikan operator hanya bisa update data kecamatannya sendiri
    if record.kecamatan_id != current_user.kecamatan_id:
        flash('Unauthorized!', 'danger')
        return redirect(url_for('operator.lapor_pakai'))
    
    nik = request.form.get('nik')
    nama = request.form.get('nama_lengkap')
    jenis_cetak = request.form.get('jenis_cetak')
    registrasi_ikd = request.form.get('registrasi_ikd') == 'true'
    status_cetak = request.form.get('status_cetak')
    keterangan_gagal = request.form.get('keterangan_gagal')
    
    # Checkbox status_ambil
    status_ambil = request.form.get('status_ambil') == 'on'
    hubungan = request.form.get('hubungan')
    penerima = request.form.get('penerima')
    
    if not nik or not nama or not jenis_cetak or request.form.get('registrasi_ikd') is None:
        flash('Semua data wajib diisi, termasuk status Registrasi IKD!', 'danger')
        return redirect(url_for('operator.lapor_pakai'))
    
    # Validasi NIK: 16 digit angka
    if not re.match(r'^\d{16}$', nik):
        flash('NIK harus terdiri dari 16 digit angka!', 'danger')
        return redirect(url_for('operator.lapor_pakai'))
    
    # Validasi Nama Lengkap: huruf kapital, spasi, dash, kutip
    if not re.match(r'^[A-Z\s\'\-]+$', nama):
        flash('Nama Lengkap hanya boleh huruf kapital, spasi, dash, atau kutip!', 'danger')
        return redirect(url_for('operator.lapor_pakai'))
    
    # Update data dasar
    record.nik = nik
    record.nama_lengkap = nama
    record.jenis_cetak = jenis_cetak
    record.registrasi_ikd = registrasi_ikd
    record.status_cetak = status_cetak
    
    if status_cetak == 'GAGAL':
        record.keterangan_gagal = keterangan_gagal
        # Jika gagal, otomatis tidak diambil
        record.status_ambil = False
        record.tanggal_ambil = None
        record.hubungan = None
        record.penerima = None
    else:
        record.keterangan_gagal = None
        # Handle status pengambilan
        if status_ambil:
            # Jika sebelumnya belum diambil, set waktu sekarang
            if not record.status_ambil:
                record.tanggal_ambil = get_gmt7_time()
            
            # Validasi penerima jika diambil
            if not penerima or not re.match(r'^[A-Z\s\'\-]+$', penerima):
                flash('Nama pengambil harus valid (Huruf Kapital)!', 'danger')
                return redirect(url_for('operator.lapor_pakai'))
                
            record.status_ambil = True
            record.hubungan = hubungan
            record.penerima = penerima
        else:
            record.status_ambil = False
            record.tanggal_ambil = None
            record.hubungan = None
            record.penerima = None

    db.session.commit()
    flash('Data cetakan berhasil diperbarui', 'success')
    return redirect(url_for('operator.lapor_pakai'))

@ops_bp.route('/delete-cetak/<int:id>', methods=['GET'])
@login_required
def delete_cetak(id):
    record = DetailCetak.query.get_or_404(id)
    
    # Pastikan operator hanya bisa delete data kecamatannya sendiri
    if record.kecamatan_id != current_user.kecamatan_id:
        flash('Unauthorized!', 'danger')
        return redirect(url_for('operator.lapor_pakai'))
    
    # Jika belum diambil, kembalikan stok
    if not record.status_ambil:
        stok = Stok.query.filter_by(kecamatan_id=current_user.kecamatan_id).first()
        if stok:
            stok.jumlah_ktp += 1
            # Catat transaksi pengembalian
            transaksi = Transaksi(
                kecamatan_id=current_user.kecamatan_id,
                user_id=current_user.id,
                jenis_transaksi='PENGEMBALIAN',
                jumlah_ktp=1,
                jumlah_kia=0
            )
            db.session.add(transaksi)
    
    db.session.delete(record)
    db.session.commit()
    flash('Data cetakan berhasil dihapus', 'success')
    return redirect(url_for('operator.lapor_pakai'))

@ops_bp.route('/profil', methods=['GET', 'POST'])
@login_required
def profil():
    from werkzeug.security import generate_password_hash
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            nama_lengkap = request.form.get('nama_lengkap')
            
            # Validasi nama lengkap
            if not nama_lengkap:
                flash('Nama lengkap tidak boleh kosong!', 'danger')
                return redirect(url_for('operator.profil'))
            
            # Validasi format nama lengkap
            if not re.match(r'^[A-Z\s\'\-]+$', nama_lengkap):
                flash('Nama lengkap hanya boleh huruf kapital, spasi, dash, atau kutip!', 'danger')
                return redirect(url_for('operator.profil'))
            
            # Update nama lengkap
            current_user.nama_lengkap = nama_lengkap
            db.session.commit()
            flash('Nama lengkap berhasil diperbarui!', 'success')
            
        elif action == 'change_password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            # Validasi input
            if not current_password or not new_password or not confirm_password:
                flash('Semua field password harus diisi!', 'danger')
                return redirect(url_for('operator.profil'))
            
            # Validasi password baru dan konfirmasi
            if new_password != confirm_password:
                flash('Password baru dan konfirmasi password tidak cocok!', 'danger')
                return redirect(url_for('operator.profil'))
            
            # Validasi panjang password minimal
            if len(new_password) < 6:
                flash('Password baru minimal 6 karakter!', 'danger')
                return redirect(url_for('operator.profil'))
            
            # Validasi password saat ini
            from werkzeug.security import check_password_hash
            if not check_password_hash(current_user.password_hash, current_password):
                flash('Password saat ini salah!', 'danger')
                return redirect(url_for('operator.profil'))
            
            # Update password
            current_user.password_hash = generate_password_hash(new_password, method='pbkdf2:sha256:600000')
            db.session.commit()
            flash('Password berhasil diperbarui!', 'success')
    
    return render_template('operator/profil.html')