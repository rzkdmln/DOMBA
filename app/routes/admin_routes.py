from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from app.models import Kecamatan, Stok, Transaksi, User, DetailCetak, BackupSchedule, BackupLog
from app.extensions import db
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload
from app.utils import get_gmt7_time, admin_required, validate_cetak_data, process_stok_pengurangan
from app.forms import LaporPakaiForm
import pandas as pd
from io import BytesIO
from datetime import datetime
import json
import os
import re
from werkzeug.utils import secure_filename
from apscheduler.triggers.cron import CronTrigger

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Get parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', 'all')
    
    # Get sorting parameters
    sort_by = request.args.get('sort_by', 'jumlah_ktp')
    sort_order = request.args.get('sort_order', 'desc')
    
    # Validate per_page options
    if per_page not in [10, 20, 0]:
        per_page = 10
    
    # Get summary statistics
    total_kecamatan = Kecamatan.query.count()
    total_stok_ktp = db.session.query(func.sum(Stok.jumlah_ktp)).scalar() or 0
    total_stok_kia = db.session.query(func.sum(Stok.jumlah_kia)).scalar() or 0
    total_users = User.query.count()

    # Get recent transactions & cetaks
    recent_transactions = Transaksi.query.options(joinedload(Transaksi.kecamatan), joinedload(Transaksi.user))\
        .order_by(Transaksi.created_at.desc()).limit(10).all()

    recent_cetaks = DetailCetak.query.options(joinedload(DetailCetak.kecamatan), joinedload(DetailCetak.user))\
        .order_by(DetailCetak.tanggal_cetak.desc()).limit(10).all()

    # Base query for stock table
    stock_query = db.session.query(
        Kecamatan.nama_kecamatan,
        Stok.jumlah_ktp,
        Stok.jumlah_kia,
        Stok.last_updated
    ).join(Stok)
    
    # Apply search filter
    if search:
        stock_query = stock_query.filter(Kecamatan.nama_kecamatan.ilike(f'%{search}%'))
    
    # Apply status filter
    if status_filter == 'habis':
        stock_query = stock_query.filter(Stok.jumlah_ktp == 0)
    elif status_filter == 'terbatas':
        stock_query = stock_query.filter(Stok.jumlah_ktp > 0, Stok.jumlah_ktp <= 20)
    elif status_filter == 'tersedia':
        stock_query = stock_query.filter(Stok.jumlah_ktp > 20)

    # Apply sorting
    if sort_by == 'nama_kecamatan':
        stock_query = stock_query.order_by(Kecamatan.nama_kecamatan.asc() if sort_order == 'asc' else Kecamatan.nama_kecamatan.desc())
    else:
        stock_query = stock_query.order_by(Stok.jumlah_ktp.asc() if sort_order == 'asc' else Stok.jumlah_ktp.desc())

    if per_page == 0:
        stock_data = stock_query.all()
        pagination_info = None
    else:
        pagination = stock_query.paginate(page=page, per_page=per_page, error_out=False)
        stock_data = pagination.items
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

    # Low stock alerts (original logic for icons/alerts)
    all_stock_data = db.session.query(Kecamatan.nama_kecamatan, Stok.jumlah_ktp, Stok.jumlah_kia, Stok.last_updated).join(Stok).all()
    low_stock_alerts = [
        {'kecamatan': k, 'ktp': ktp, 'kia': kia, 'updated': u}
        for k, ktp, kia, u in all_stock_data if ktp < 100 or kia < 100
    ]

    return render_template('admin/dashboard.html',
                         total_kecamatan=total_kecamatan,
                         total_stok_ktp=total_stok_ktp,
                         total_stok_kia=total_stok_kia,
                         total_users=total_users,
                         recent_transactions=recent_transactions,
                         recent_cetaks=recent_cetaks,
                         stock_data=stock_data,
                         low_stock_alerts=low_stock_alerts,
                         pagination_info=pagination_info,
                         search=search,
                         status_filter=status_filter)


@admin_bp.route('/profil', methods=['GET', 'POST'])
@login_required
@admin_required
def profil():
    from werkzeug.security import generate_password_hash, check_password_hash

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_profile':
            nama_lengkap = (request.form.get('nama_lengkap') or '').strip()

            if not nama_lengkap:
                flash('Nama lengkap tidak boleh kosong!', 'danger')
                return redirect(url_for('admin.profil'))

            nama_lengkap = re.sub(r'\s+', ' ', nama_lengkap)

            if not re.match(r"^[A-Za-z\s\'\-]+$", nama_lengkap):
                flash('Nama lengkap hanya boleh huruf, spasi, dash, atau kutip!', 'danger')
                return redirect(url_for('admin.profil'))

            current_user.nama_lengkap = nama_lengkap
            db.session.commit()
            flash('Nama lengkap berhasil diperbarui!', 'success')

        elif action == 'change_password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            if not current_password or not new_password or not confirm_password:
                flash('Semua field password harus diisi!', 'danger')
                return redirect(url_for('admin.profil'))

            if new_password != confirm_password:
                flash('Password baru dan konfirmasi password tidak cocok!', 'danger')
                return redirect(url_for('admin.profil'))

            if len(new_password) < 6:
                flash('Password baru minimal 6 karakter!', 'danger')
                return redirect(url_for('admin.profil'))

            if not check_password_hash(current_user.password_hash, current_password):
                flash('Password saat ini salah!', 'danger')
                return redirect(url_for('admin.profil'))

            current_user.password_hash = generate_password_hash(new_password, method='pbkdf2:sha256:600000')
            db.session.commit()
            flash('Password berhasil diperbarui!', 'success')

    return render_template('internal/profil.html')

@admin_bp.route('/monitoring-cetak')
@login_required
@admin_required
def monitoring_cetak():
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Get filter parameters
    search = request.args.get('search', '').strip()
    kecamatan_filter = request.args.get('kecamatan', '')
    status_filter = request.args.get('status', '')
    operator_filter = request.args.get('operator', '')
    kondisi_filter = request.args.get('kondisi', '') # NEW: status_cetak
    
    # Validate per_page options
    if per_page not in [10, 20, 50, 0]:  # 0 means show all
        per_page = 10
    
    # Build query with filters
    cetaks_query = DetailCetak.query.options(joinedload(DetailCetak.user), joinedload(DetailCetak.kecamatan))
    
    # Apply search filter (name or NIK)
    if search:
        cetaks_query = cetaks_query.filter(
            or_(
                DetailCetak.nama_lengkap.ilike(f'%{search}%'),
                DetailCetak.nik.ilike(f'%{search}%')
            )
        )
    
    # Apply kecamatan filter
    if kecamatan_filter:
        cetaks_query = cetaks_query.filter(DetailCetak.kecamatan_id == kecamatan_filter)
    
    # Apply status ambil filter
    if status_filter:
        if status_filter == 'diambil':
            cetaks_query = cetaks_query.filter(DetailCetak.status_ambil == True)
        elif status_filter == 'pending':
            cetaks_query = cetaks_query.filter(DetailCetak.status_ambil == False)

    # Apply kondisi cetak filter (NEW)
    if kondisi_filter:
        cetaks_query = cetaks_query.filter(DetailCetak.status_cetak == kondisi_filter)
    
    # Apply operator filter
    if operator_filter:
        cetaks_query = cetaks_query.filter(DetailCetak.user_id == operator_filter)
    
    # Order by tanggal_cetak desc
    cetaks_query = cetaks_query.order_by(DetailCetak.tanggal_cetak.desc())
    
    # Get cetaks with pagination
    if per_page == 0:  # Show all
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
    
    # Get filter options - include all kecamatans including dinas
    kecamatans = Kecamatan.query.order_by(Kecamatan.nama_kecamatan).all()
    operators = User.query.order_by(User.username).all()  # Include all users (admin and operators)
    
    return render_template('admin/monitoring_cetak.html', 
                         cetaks=cetaks, 
                         kecamatans=kecamatans,
                         operators=operators,
                         pagination_info=pagination_info,
                         search=search,
                         kecamatan_filter=kecamatan_filter,
                         status_filter=status_filter,
                         kondisi_filter=kondisi_filter,
                         operator_filter=operator_filter,
                         is_operator=False)

@admin_bp.route('/input-data', methods=['GET', 'POST'])
@login_required
@admin_required
def input_data():
    form = LaporPakaiForm()
    
    # Ensure admin has a kecamatan_id (Dinas)
    if not current_user.kecamatan_id:
        dinas = Kecamatan.query.filter_by(kode_wilayah='32.05.00').first()
        if dinas:
            current_user.kecamatan_id = dinas.id
            db.session.commit()

    if form.validate_on_submit():
        nik = form.nik.data
        nama = form.nama_lengkap.data
        jenis_cetak = form.jenis_cetak.data
        registrasi_ikd = form.registrasi_ikd.data == 'true'
        status_cetak = form.status_cetak.data
        keterangan_gagal = form.keterangan_gagal.data
        
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
        
        # 2. Proses stok dan transaksi menggunakan utility
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
            
        return redirect(url_for('admin.input_data'))
    elif request.method == 'POST':
        # Flash first validation error if exists
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{error}", 'danger')
                break
            break

    # GET request
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status_filter = request.args.get('status', 'pending')
    
    # Define history_query based on status filter
    history_query = DetailCetak.query
    
    if status_filter == 'taken':
        history_query = history_query.filter(DetailCetak.status_ambil == True)
    else:
        history_query = history_query.filter(DetailCetak.status_ambil == False)
    
    history_query = history_query.order_by(DetailCetak.tanggal_cetak.desc())
    
    pagination = history_query.paginate(page=page, per_page=per_page, error_out=False)
    history = pagination.items
    total_cetak = pagination.total
    
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
    
    return render_template('internal/input_data.html', 
                         history=history, 
                         stok=stok, 
                         total_cetak=total_cetak, 
                         pagination_info=pagination_info,
                         is_admin=True)

@admin_bp.route('/update-status-ambil/<int:id>', methods=['POST'])
@login_required
@admin_required
def update_status_ambil(id):
    import re
    from datetime import timedelta
    record = DetailCetak.query.get_or_404(id)
        
    status = request.form.get('status') == 'true'
    hubungan = request.form.get('hubungan')
    penerima = request.form.get('penerima')
    tanggal_custom = request.form.get('tanggal_custom')
    waktu_custom = request.form.get('waktu_custom')
    use_now = request.form.get('use_now') == 'on'
    
    if not penerima or not re.match(r'^[A-Z\s\'\-]+$', penerima):
        flash('Nama pengambil tidak valid!', 'danger')
        return redirect(url_for('admin.input_data'))
    
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
    
    db.session.commit()
    flash('Status pengambilan diperbarui', 'success')
    return redirect(url_for('admin.input_data'))

@admin_bp.route('/update-cetak/<int:id>', methods=['POST'])
@login_required
@admin_required
def update_cetak(id):
    import re
    from datetime import timedelta
    record = DetailCetak.query.get_or_404(id)
    
    nik = request.form.get('nik')
    nama = request.form.get('nama_lengkap')
    jenis_cetak = request.form.get('jenis_cetak')
    registrasi_ikd = request.form.get('registrasi_ikd') == 'true'
    status_cetak = request.form.get('status_cetak')
    keterangan_gagal = request.form.get('keterangan_gagal')
    status_ambil = request.form.get('status_ambil') == 'on'
    hubungan = request.form.get('hubungan')
    penerima = request.form.get('penerima')
    
    if not nik or not nama or not jenis_cetak or request.form.get('registrasi_ikd') is None:
        flash('Semua field wajib diisi, termasuk status Registrasi IKD!', 'danger')
        return redirect(url_for('admin.input_data'))
    
    record.nik = nik
    record.nama_lengkap = nama
    record.jenis_cetak = jenis_cetak
    record.registrasi_ikd = registrasi_ikd
    record.status_cetak = status_cetak
    
    if status_cetak == 'GAGAL':
        record.keterangan_gagal = keterangan_gagal
        record.status_ambil = False
        record.tanggal_ambil = None
    else:
        record.keterangan_gagal = None
        if status_ambil:
            if not record.status_ambil:
                record.tanggal_ambil = get_gmt7_time()
            record.status_ambil = True
            record.hubungan = hubungan
            record.penerima = penerima
        else:
            record.status_ambil = False
            record.tanggal_ambil = None

    db.session.commit()
    flash('Data cetakan diperbarui', 'success')
    return redirect(url_for('admin.input_data'))

@admin_bp.route('/delete-cetak/<int:id>')
@login_required
@admin_required
def delete_cetak(id):
    record = DetailCetak.query.get_or_404(id)
    
    if not record.status_ambil:
        stok = Stok.query.filter_by(kecamatan_id=record.kecamatan_id).first()
        if stok:
            stok.jumlah_ktp += 1
    
    db.session.delete(record)
    db.session.commit()
    flash('Data cetakan dihapus', 'success')
    return redirect(url_for('admin.input_data'))

@admin_bp.route('/export-sebaran-stok')
@login_required
@admin_required
def export_sebaran_stok():
    # Similar to dashboard sebaran
    stock_data = db.session.query(
        Kecamatan.nama_kecamatan,
        Stok.jumlah_ktp,
        Stok.jumlah_kia,
        Stok.last_updated
    ).join(Stok).all()
    
    data = []
    for kecamatan, ktp, kia, updated in stock_data:
        data.append({
            'Kecamatan': kecamatan,
            'Sisa Stok KTP': ktp,
            'Update Terakhir': updated.strftime('%Y-%m-%d %H:%M:%S') if updated else '-'
        })
    
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sebaran Stok')
    
    output.seek(0)
    filename = f"sebaran_stok_{get_gmt7_time().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@admin_bp.route('/export-stok-masuk')
@login_required
@admin_required
def export_stok_masuk():
    recent_masuk = Transaksi.query.filter_by(jenis_transaksi='IN_FROM_PUSAT')\
        .order_by(Transaksi.created_at.desc()).all()
    
    data = []
    for log in recent_masuk:
        data.append({
            'Waktu Input': log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'Jumlah': log.jumlah_ktp,
            'Petugas': log.user.username
        })
    
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Riwayat Pengadaan')
    
    output.seek(0)
    filename = f"riwayat_pengadaan_{get_gmt7_time().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@admin_bp.route('/export-distribusi')
@login_required
@admin_required
def export_distribusi():
    recent_distribusi = Transaksi.query.filter_by(jenis_transaksi='DISTRIBUSI_TO_KEC')\
        .order_by(Transaksi.created_at.desc()).all()
    
    data = []
    for log in recent_distribusi:
        data.append({
            'Waktu Distribusi': log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'Tujuan': log.kecamatan.nama_kecamatan,
            'Alokasi': log.jumlah_ktp,
            'Petugas': log.user.username
        })
    
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Log Distribusi')
    
    output.seek(0)
    filename = f"log_distribusi_{get_gmt7_time().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@admin_bp.route('/export-cetak')
@login_required
@admin_required
def export_cetak():
    # Get filter parameters from query string (same filters as monitoring-cetak)
    search = request.args.get('search', '').strip()
    kecamatan_filter = request.args.get('kecamatan', '')
    status_filter = request.args.get('status', '')
    operator_filter = request.args.get('operator', '')
    kondisi_filter = request.args.get('kondisi', '')
    
    # Build query with filters (same logic as monitoring_cetak)
    cetaks_query = DetailCetak.query.join(User).join(Kecamatan)
    
    # Apply search filter (name or NIK)
    if search:
        cetaks_query = cetaks_query.filter(
            db.or_(
                DetailCetak.nama_lengkap.ilike(f'%{search}%'),
                DetailCetak.nik.ilike(f'%{search}%')
            )
        )
    
    # Apply kecamatan filter
    if kecamatan_filter:
        cetaks_query = cetaks_query.filter(DetailCetak.kecamatan_id == kecamatan_filter)
    
    # Apply status ambil filter
    if status_filter:
        if status_filter == 'diambil':
            cetaks_query = cetaks_query.filter(DetailCetak.status_ambil == True)
        elif status_filter == 'pending':
            cetaks_query = cetaks_query.filter(DetailCetak.status_ambil == False)
    
    # Apply kondisi cetak filter
    if kondisi_filter:
        cetaks_query = cetaks_query.filter(DetailCetak.status_cetak == kondisi_filter)
    
    # Apply operator filter
    if operator_filter:
        cetaks_query = cetaks_query.filter(DetailCetak.user_id == operator_filter)
    
    # Order by tanggal_cetak desc
    cetaks_query = cetaks_query.order_by(DetailCetak.tanggal_cetak.desc())
    
    # Get all matching cetaks
    cetaks = cetaks_query.all()
    
    data = []
    for c in cetaks:
        data.append({
            'Waktu Cetak': c.tanggal_cetak.strftime('%Y-%m-%d %H:%M:%S'),
            'Kecamatan': c.kecamatan.nama_kecamatan,
            'NIK': c.nik,
            'Nama Lengkap': c.nama_lengkap,
            'Jenis Cetak': c.jenis_cetak or 'KTP-EL',
            'Registrasi IKD': 'Ya' if c.registrasi_ikd else 'Tidak',
            'Kondisi': c.status_cetak,
            'Keterangan Gagal': c.keterangan_gagal or '-',
            'Status Ambil': 'Sudah Diambil' if c.status_ambil else 'Belum Diambil',
            'Waktu Ambil': c.tanggal_ambil.strftime('%Y-%m-%d %H:%M:%S') if c.tanggal_ambil else '-',
            'Hubungan': c.hubungan or '-',
            'Penerima': c.penerima or '-',
            'Operator': c.user.username
        })
    
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Data Cetak Wilayah')
    
    output.seek(0)
    filename = f"data_cetak_wilayah_{get_gmt7_time().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@admin_bp.route('/master_user')
@login_required
@admin_required
def master_user():
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Get filter parameters
    search = request.args.get('search', '').strip()
    role_filter = request.args.get('role', '')
    
    # Validate per_page options
    if per_page not in [10, 20, 0]:  # 0 means show all
        per_page = 10
    
    # Build query with filters
    users_query = User.query
    
    # Apply search filter (name or username)
    if search:
        users_query = users_query.filter(
            db.or_(
                User.nama_lengkap.ilike(f'%{search}%'),
                User.username.ilike(f'%{search}%')
            )
        )
    
    # Apply role filter
    if role_filter:
        if role_filter == 'admin':
            users_query = users_query.filter(User.role == 'admin_dinas')
        elif role_filter == 'operator':
            users_query = users_query.filter(User.role == 'operator_kecamatan')
    
    # Order by username
    users_query = users_query.order_by(User.username)
    
    # Get users with pagination
    if per_page == 0:  # Show all
        users = users_query.all()
        pagination_info = None
    else:
        # Paginated query using Flask-SQLAlchemy paginate
        pagination = users_query.paginate(page=page, per_page=per_page, error_out=False)
        users = pagination.items
        
        # Format pagination info
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
    
    kecamatans = Kecamatan.query.filter(Kecamatan.kode_wilayah != '32.05.00').order_by(Kecamatan.nama_kecamatan).all()
    
    # Calculate filtered stats for overview cards
    filtered_users_query = User.query
    
    # Apply same filters for stats
    if search:
        filtered_users_query = filtered_users_query.filter(
            db.or_(
                User.nama_lengkap.ilike(f'%{search}%'),
                User.username.ilike(f'%{search}%')
            )
        )
    
    if role_filter:
        if role_filter == 'admin':
            filtered_users_query = filtered_users_query.filter(User.role == 'admin_dinas')
        elif role_filter == 'operator':
            filtered_users_query = filtered_users_query.filter(User.role == 'operator_kecamatan')
    
    total_filtered_users = filtered_users_query.count()
    admin_count = filtered_users_query.filter(User.role == 'admin_dinas').count()
    operator_count = filtered_users_query.filter(User.role == 'operator_kecamatan').count()
    
    return render_template('admin/master_user.html', 
                         users=users, 
                         kecamatans=kecamatans, 
                         pagination_info=pagination_info,
                         search=search,
                         role_filter=role_filter,
                         total_filtered_users=total_filtered_users,
                         admin_count=admin_count,
                         operator_count=operator_count)

@admin_bp.route('/add_user', methods=['POST'])
@login_required
@admin_required
def add_user():
    raw_username = request.form.get('username')
    username = raw_username.lower() if raw_username else ''
    nama_lengkap = request.form.get('nama_lengkap')
    password = request.form.get('password')
    role = request.form.get('role')
    kecamatan_id = request.form.get('kecamatan_id')

    # Capitalize nama_lengkap
    if nama_lengkap:
        nama_lengkap = ' '.join(word.capitalize() for word in nama_lengkap.split())

    if not username or not password or not role:
        flash('Semua field harus diisi.', 'danger')
        return redirect(url_for('admin.master_user'))

    if User.query.filter_by(username=username).first():
        flash('Username sudah ada.', 'danger')
        return redirect(url_for('admin.master_user'))

    from werkzeug.security import generate_password_hash
    # Construct user by assigning attributes to avoid Pylance constructor warnings
    user = User()
    user.username = username
    user.nama_lengkap = nama_lengkap
    user.password_hash = generate_password_hash(password, method='pbkdf2:sha256:600000')
    user.role = role
    if role == 'operator_kecamatan' and kecamatan_id:
        user.kecamatan_id = kecamatan_id

    db.session.add(user)
    db.session.commit()

    flash('User berhasil ditambahkan.', 'success')
    return redirect(url_for('admin.master_user'))

@admin_bp.route('/edit_user', methods=['POST'])
@login_required
@admin_required
def edit_user():
    user_id = request.form.get('user_id')
    raw_username = request.form.get('username')
    username = raw_username.lower() if raw_username else ''
    nama_lengkap = request.form.get('nama_lengkap')
    role = request.form.get('role')
    kecamatan_id = request.form.get('kecamatan_id')

    # Capitalize nama_lengkap
    if nama_lengkap:
        nama_lengkap = ' '.join(word.capitalize() for word in nama_lengkap.split())

    user = User.query.get_or_404(user_id)

    # Check if username is taken by another user
    existing = User.query.filter_by(username=username).first()
    if existing and existing.id != user.id:
        flash('Username sudah ada.', 'danger')
        return redirect(url_for('admin.master_user'))

    user.username = username
    user.nama_lengkap = nama_lengkap
    user.role = role
    if role == 'operator_kecamatan' and kecamatan_id:
        user.kecamatan_id = kecamatan_id
    else:
        user.kecamatan_id = None

    db.session.commit()

    flash('User berhasil diupdate.', 'success')
    return redirect(url_for('admin.master_user'))

@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting current user
    if user.id == current_user.id:
        flash('Tidak bisa menghapus akun sendiri.', 'danger')
        return redirect(url_for('admin.master_user'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash('User berhasil dihapus.', 'success')
    return redirect(url_for('admin.master_user'))

@admin_bp.route('/reset_password/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    
    from werkzeug.security import generate_password_hash
    user.password_hash = generate_password_hash(user.username, method='pbkdf2:sha256:600000')
    
    db.session.commit()
    
    return {'success': True, 'message': f'Password untuk {user.username} berhasil direset ke username.'}

@admin_bp.route('/get_user_details/<int:user_id>')
@login_required
@admin_required
def get_user_details(user_id):
    user = User.query.get_or_404(user_id)
    return {'nama_lengkap': user.nama_lengkap, 'kecamatan_id': user.kecamatan_id}

@admin_bp.route('/stok_masuk', methods=['GET', 'POST'])
@login_required
@admin_required
def stok_masuk():
    if request.method == 'POST':
        jumlah = int(request.form.get('jumlah', 0))
        sumber = request.form.get('sumber', 'Pusat')
        keterangan = request.form.get('keterangan', '')
        
        if jumlah <= 0:
            flash('Jumlah harus lebih dari 0.', 'danger')
            return redirect(url_for('admin.stok_masuk'))
            
        # 1. Update Stok Gudang Dinas (kode_wilayah='32.05.00')
        dinas = Kecamatan.query.filter_by(kode_wilayah='32.05.00').first()
        if not dinas:
             # Create if missing (safety check)
             dinas = Kecamatan(nama_kecamatan='Dinas', kode_wilayah='32.05.00')
             db.session.add(dinas)
             db.session.flush()
             
        stok_dinas = Stok.query.filter_by(kecamatan_id=dinas.id).first()
        if not stok_dinas:
            stok_dinas = Stok(kecamatan_id=dinas.id, jumlah_ktp=0)
            db.session.add(stok_dinas)
            
        stok_dinas.jumlah_ktp += jumlah
        
        # 2. Add Transaksi Log
        transaksi = Transaksi(
            kecamatan_id=dinas.id,
            user_id=current_user.id,
            jenis_transaksi='IN_FROM_PUSAT',
            jumlah_ktp=jumlah,
            jumlah_kia=0,
            keterangan=keterangan
        )
        
        db.session.add(transaksi)
        db.session.commit()
        
        flash(f'Berhasil menambah {jumlah} blangko ke Dinas dari {sumber}.', 'success')
        return redirect(url_for('admin.stok_masuk'))

    # GET request
    dinas = Kecamatan.query.filter_by(kode_wilayah='32.05.00').first()
    recent_masuk = Transaksi.query.filter_by(jenis_transaksi='IN_FROM_PUSAT')\
        .order_by(Transaksi.created_at.desc()).limit(10).all()
        
    return render_template('admin/stok_masuk.html', 
                         recent_masuk=recent_masuk, 
                         today_date=get_gmt7_time().strftime('%Y-%m-%d'))

@admin_bp.route('/edit_stok_masuk', methods=['POST'])
@login_required
@admin_required
def edit_stok_masuk():
    transaksi_id = request.form.get('transaksi_id')
    jumlah_baru = int(request.form.get('jumlah', 0))
    tanggal_baru = request.form.get('tanggal')
    keterangan_baru = request.form.get('keterangan', '')
    
    transaksi = Transaksi.query.get_or_404(transaksi_id)
    if transaksi.jenis_transaksi != 'IN_FROM_PUSAT':
        flash('Transaksi ini tidak bisa diedit.', 'danger')
        return redirect(url_for('admin.stok_masuk'))
    
    selisih = jumlah_baru - transaksi.jumlah_ktp
    
    # Update stok Gudang Dinas
    dinas = Kecamatan.query.filter_by(kode_wilayah='32.05.00').first()
    stok_dinas = Stok.query.filter_by(kecamatan_id=dinas.id).first()
    if stok_dinas:
        stok_dinas.jumlah_ktp += selisih
    
    transaksi.jumlah_ktp = jumlah_baru
    transaksi.keterangan = keterangan_baru
    if tanggal_baru:
        transaksi.created_at = datetime.strptime(tanggal_baru + ' ' + transaksi.created_at.strftime('%H:%M:%S'), '%Y-%m-%d %H:%M:%S')
    
    db.session.commit()
    
    flash('Transaksi berhasil diupdate.', 'success')
    return redirect(url_for('admin.stok_masuk'))

@admin_bp.route('/delete_stok_masuk/<int:transaksi_id>', methods=['POST'])
@login_required
@admin_required
def delete_stok_masuk(transaksi_id):
    transaksi = Transaksi.query.get_or_404(transaksi_id)
    if transaksi.jenis_transaksi != 'IN_FROM_PUSAT':
        flash('Transaksi ini tidak bisa dihapus.', 'danger')
        return redirect(url_for('admin.stok_masuk'))
    
    # Kurangi stok Gudang Dinas secara atomik
    dinas = Kecamatan.query.filter_by(kode_wilayah='32.05.00').first()
    stok_dinas = Stok.query.filter_by(kecamatan_id=dinas.id).first()
    if stok_dinas:
        stok_dinas.jumlah_ktp = Stok.jumlah_ktp - transaksi.jumlah_ktp
    
    db.session.delete(transaksi)
    db.session.commit()
    
    flash('Transaksi berhasil dihapus.', 'success')
    return redirect(url_for('admin.stok_masuk'))

@admin_bp.route('/distribusi', methods=['GET', 'POST'])
@login_required
@admin_required
def distribusi():
    # Get tab parameter
    active_tab = request.args.get('tab', 'distribusi')  # Default to distribusi tab
    
    if request.method == 'POST':
        kecamatan_id = request.form.get('kecamatan_id')
        jumlah = int(request.form.get('jumlah', 0))
        
        dinas = Kecamatan.query.filter_by(kode_wilayah='32.05.00').first()
        stok_dinas = Stok.query.filter_by(kecamatan_id=dinas.id).first() if dinas else None

        if not kecamatan_id or jumlah <= 0:
            flash('Pilih kecamatan dan masukkan jumlah yang valid.', 'danger')
            return redirect(url_for('admin.distribusi'))
            
        if not stok_dinas or stok_dinas.jumlah_ktp < jumlah:
            flash(f'Stok di Dinas tidak mencukupi (Sisa: {stok_dinas.jumlah_ktp if stok_dinas else 0}).', 'danger')
            return redirect(url_for('admin.distribusi'))
        
        # 1. Kurangi Stok Gudang Dinas secara atomik
        stok_dinas.jumlah_ktp = Stok.jumlah_ktp - jumlah
        
        # 2. Tambah Stok Kecamatan Tujuan secara atomik
        stok_tujuan = Stok.query.filter_by(kecamatan_id=kecamatan_id).first()
        if not stok_tujuan:
            stok_tujuan = Stok(kecamatan_id=kecamatan_id, jumlah_ktp=jumlah)
            db.session.add(stok_tujuan)
        else:
            stok_tujuan.jumlah_ktp = Stok.jumlah_ktp + jumlah
        
        # 3. Add Transaksi Log (DISTRIBUSI_TO_KEC)
        transaksi = Transaksi(
            kecamatan_id=kecamatan_id,
            user_id=current_user.id,
            jenis_transaksi='DISTRIBUSI_TO_KEC',
            jumlah_ktp=jumlah,
            jumlah_kia=0
        )
        
        db.session.add(transaksi)
        db.session.commit()
        
        target_name = Kecamatan.query.get(kecamatan_id).nama_kecamatan
        flash(f'Berhasil mendistribusikan {jumlah} blangko ke {target_name}', 'success')
        return redirect(url_for('admin.distribusi'))

    # Filter out Gudang Dinas from target kecamatan list
    kecamatans = Kecamatan.query.filter(Kecamatan.kode_wilayah != '32.05.00').all()
    recent_distribusi = Transaksi.query.filter_by(jenis_transaksi='DISTRIBUSI_TO_KEC')\
        .order_by(Transaksi.created_at.desc()).limit(10).all()
        
    # Info Gudang Dinas
    dinas = Kecamatan.query.filter_by(kode_wilayah='32.05.00').first()
    stok_dinas = Stok.query.filter_by(kecamatan_id=dinas.id).first() if dinas else None
    
    total_terkirim_hari_ini = db.session.query(func.sum(Transaksi.jumlah_ktp))\
        .filter(Transaksi.jenis_transaksi == 'DISTRIBUSI_TO_KEC')\
        .filter(func.date(Transaksi.created_at) == get_gmt7_time().date()).scalar() or 0

    # Get stock distribution data for sebaran tab (similar to dashboard)
    # Get pagination parameters for sebaran tab
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Get sorting parameters for sebaran tab
    sort_by = request.args.get('sort_by', 'jumlah_ktp')  # Default: jumlah stok
    sort_order = request.args.get('sort_order', 'desc')  # Default: descending (terbanyak ke tersedikit)
    
    # Get filter parameter for sebaran tab
    filter_by = request.args.get('filter', 'all')  # Default: show all
    
    # Validate per_page options
    if per_page not in [10, 20, 0]:  # 0 means show all
        per_page = 10
    
    # Validate sorting options
    valid_sort_columns = ['nama_kecamatan', 'jumlah_ktp']
    if sort_by not in valid_sort_columns:
        sort_by = 'jumlah_ktp'
    if sort_order not in ['asc', 'desc']:
        sort_order = 'desc'
    
    # Get stock levels for all kecamatan with pagination (for sebaran tab)
    if per_page == 0:  # Show all
        stock_query = db.session.query(
            Kecamatan.id,
            Kecamatan.nama_kecamatan,
            Stok.jumlah_ktp,
            Stok.jumlah_kia,
            Stok.last_updated
        ).join(Stok)
        
        # Apply filter
        if filter_by == 'habis':
            stock_query = stock_query.filter(Stok.jumlah_ktp == 0)
        elif filter_by == 'terbatas':
            stock_query = stock_query.filter(Stok.jumlah_ktp > 0, Stok.jumlah_ktp <= 20)
        elif filter_by == 'tersedia':
            stock_query = stock_query.filter(Stok.jumlah_ktp > 20)
        # 'all' shows everything
        
        # Apply sorting
        if sort_by == 'nama_kecamatan':
            if sort_order == 'asc':
                stock_query = stock_query.order_by(Kecamatan.nama_kecamatan.asc())
            else:
                stock_query = stock_query.order_by(Kecamatan.nama_kecamatan.desc())
        elif sort_by == 'jumlah_ktp':
            if sort_order == 'asc':
                stock_query = stock_query.order_by(Stok.jumlah_ktp.asc())
            else:
                stock_query = stock_query.order_by(Stok.jumlah_ktp.desc())
        
        stock_data = stock_query.all()
        total_stock_records = len(stock_data)
        pagination_info = None
    else:
        # Paginated query
        stock_query = db.session.query(
            Kecamatan.id,
            Kecamatan.nama_kecamatan,
            Stok.jumlah_ktp,
            Stok.jumlah_kia,
            Stok.last_updated
        ).join(Stok)
        
        # Apply filter
        if filter_by == 'habis':
            stock_query = stock_query.filter(Stok.jumlah_ktp == 0)
        elif filter_by == 'terbatas':
            stock_query = stock_query.filter(Stok.jumlah_ktp > 0, Stok.jumlah_ktp <= 20)
        elif filter_by == 'tersedia':
            stock_query = stock_query.filter(Stok.jumlah_ktp > 20)
        # 'all' shows everything
        
        # Apply sorting
        if sort_by == 'nama_kecamatan':
            if sort_order == 'asc':
                stock_query = stock_query.order_by(Kecamatan.nama_kecamatan.asc())
            else:
                stock_query = stock_query.order_by(Kecamatan.nama_kecamatan.desc())
        elif sort_by == 'jumlah_ktp':
            if sort_order == 'asc':
                stock_query = stock_query.order_by(Stok.jumlah_ktp.asc())
            else:
                stock_query = stock_query.order_by(Stok.jumlah_ktp.desc())
        
        # Paginated query using Flask-SQLAlchemy paginate
        pagination = stock_query.paginate(page=page, per_page=per_page, error_out=False)
        stock_data = pagination.items
        
        # Format pagination info
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

    # Get low stock alerts (less than 100 for either KTP or KIA) - from all data
    all_stock_data = db.session.query(
        Kecamatan.nama_kecamatan,
        Stok.jumlah_ktp,
        Stok.jumlah_kia,
        Stok.last_updated
    ).join(Stok).all()
    
    low_stock_alerts = []
    for kecamatan, ktp, kia, updated in all_stock_data:
        if ktp < 100 or kia < 100:
            low_stock_alerts.append({
                'kecamatan': kecamatan,
                'ktp': ktp,
                'kia': kia,
                'updated': updated
            })

    return render_template('admin/distribusi.html', 
                         active_tab=active_tab,
                         kecamatans=kecamatans, 
                         recent_distribusi=recent_distribusi,
                         stok_dinas=stok_dinas,
                         total_terkirim_hari_ini=total_terkirim_hari_ini,
                         stock_data=stock_data,
                         low_stock_alerts=low_stock_alerts,
                         pagination_info=pagination_info,
                         filter_by=filter_by)

@admin_bp.route('/edit_distribusi', methods=['POST'])
@login_required
@admin_required
def edit_distribusi():
    transaksi_id = request.form.get('transaksi_id')
    jumlah_baru = int(request.form.get('jumlah', 0))
    kecamatan_id_baru = request.form.get('kecamatan_id')
    
    transaksi = Transaksi.query.get_or_404(transaksi_id)
    if transaksi.jenis_transaksi != 'DISTRIBUSI_TO_KEC':
        flash('Transaksi ini tidak bisa diedit.', 'danger')
        return redirect(url_for('admin.distribusi'))
    
    kecamatan_lama_id = transaksi.kecamatan_id
    selisih = jumlah_baru - transaksi.jumlah_ktp
    
    # Jika kecamatan berubah
    if kecamatan_id_baru and int(kecamatan_id_baru) != kecamatan_lama_id:
        # Kurangi stok dari kecamatan lama
        stok_lama = Stok.query.filter_by(kecamatan_id=kecamatan_lama_id).first()
        if stok_lama:
            stok_lama.jumlah_ktp -= transaksi.jumlah_ktp
        
        # Tambah stok ke kecamatan baru
        stok_baru = Stok.query.filter_by(kecamatan_id=int(kecamatan_id_baru)).first()
        if stok_baru:
            stok_baru.jumlah_ktp += jumlah_baru
        
        # Update transaksi
        transaksi.kecamatan_id = int(kecamatan_id_baru)
        
        # Update stok Gudang Dinas (karena distribusi ulang)
        dinas = Kecamatan.query.filter_by(kode_wilayah='32.05.00').first()
        stok_dinas = Stok.query.filter_by(kecamatan_id=dinas.id).first()
        if stok_dinas:
            # Stok dinas tetap sama karena hanya pindah kecamatan
            pass
    else:
        # Update stok Gudang Dinas
        dinas = Kecamatan.query.filter_by(kode_wilayah='32.05.00').first()
        stok_dinas = Stok.query.filter_by(kecamatan_id=dinas.id).first()
        if stok_dinas:
            stok_dinas.jumlah_ktp -= selisih  # Kurangi lebih banyak jika jumlah naik
        
        # Update stok kecamatan tujuan
        stok_tujuan = Stok.query.filter_by(kecamatan_id=transaksi.kecamatan_id).first()
        if stok_tujuan:
            stok_tujuan.jumlah_ktp += selisih
    
    transaksi.jumlah_ktp = jumlah_baru
    db.session.commit()
    
    flash('Distribusi berhasil diupdate.', 'success')
    return redirect(url_for('admin.distribusi'))

@admin_bp.route('/delete_distribusi/<int:transaksi_id>', methods=['POST'])
@login_required
@admin_required
def delete_distribusi(transaksi_id):
    transaksi = Transaksi.query.get_or_404(transaksi_id)
    if transaksi.jenis_transaksi != 'DISTRIBUSI_TO_KEC':
        flash('Transaksi ini tidak bisa dihapus.', 'danger')
        return redirect(url_for('admin.distribusi'))
    
    # Kembalikan stok ke Gudang Dinas
    dinas = Kecamatan.query.filter_by(kode_wilayah='32.05.00').first()
    stok_dinas = Stok.query.filter_by(kecamatan_id=dinas.id).first()
    if stok_dinas:
        stok_dinas.jumlah_ktp += transaksi.jumlah_ktp
    
    # Kurangi stok kecamatan
    stok_tujuan = Stok.query.filter_by(kecamatan_id=transaksi.kecamatan_id).first()
    if stok_tujuan:
        stok_tujuan.jumlah_ktp -= transaksi.jumlah_ktp
    
    db.session.delete(transaksi)
    db.session.commit()
    
    flash('Distribusi berhasil dihapus.', 'success')
    return redirect(url_for('admin.distribusi'))

@admin_bp.route('/get_kecamatan_stock/<int:kecamatan_id>')
@login_required
@admin_required
def get_kecamatan_stock(kecamatan_id):
    stok = Stok.query.filter_by(kecamatan_id=kecamatan_id).first()
    if stok:
        return {'jumlah_ktp': stok.jumlah_ktp}
    else:
        return {'jumlah_ktp': 0}

@admin_bp.route('/update_stock', methods=['POST'])
@login_required
@admin_required
def update_stock():
    kecamatan_id = request.form.get('kecamatan_id')
    jumlah_ktp = int(request.form.get('jumlah_ktp', 0))
    
    if not kecamatan_id or jumlah_ktp < 0:
        flash('Data tidak valid.', 'danger')
        return redirect(url_for('admin.distribusi'))
    
    # Update stok kecamatan
    stok = Stok.query.filter_by(kecamatan_id=kecamatan_id).first()
    if not stok:
        flash('Kecamatan tidak ditemukan.', 'danger')
        return redirect(url_for('admin.distribusi'))
    
    old_stock = stok.jumlah_ktp
    stok.jumlah_ktp = jumlah_ktp
    db.session.commit()
    
    # Create audit trail
    transaksi = Transaksi(
        kecamatan_id=kecamatan_id,
        user_id=current_user.id,
        jenis_transaksi='STOCK_ADJUSTMENT',
        jumlah_ktp=jumlah_ktp - old_stock,  # Positive for increase, negative for decrease
        jumlah_kia=0
    )
    db.session.add(transaksi)
    db.session.commit()
    
    flash(f'Stok blangko untuk {stok.kecamatan.nama_kecamatan} berhasil diperbarui menjadi {jumlah_ktp} keping.', 'success')
    return redirect(url_for('admin.distribusi'))

# ============================================================================
# DISASTER RECOVERY & BACKUP MANAGEMENT ENDPOINTS
# ============================================================================
# All backup endpoints are restricted to admin_dinas role only (@admin_required)
# Implementasi: Backup/Restore database dengan tracking & scheduling

@admin_bp.route('/backup')
@login_required
@admin_required
def backup_dashboard():
    """
    Main backup & restore management dashboard.
    Displays backup history, scheduling config, and upload area.
    """
    from app.models import BackupLog, BackupSchedule
    
    try:
        # Get backup history (latest 30)
        backups = BackupLog.query.filter(
            BackupLog.operation == 'BACKUP',
            BackupLog.status.in_(['SUCCESS', 'VERIFIED'])
        ).order_by(BackupLog.created_at.desc()).limit(30).all()
        
        # Get schedule configuration
        schedule = BackupSchedule.query.first()
        if not schedule:
            schedule = BackupSchedule(
                enabled=False,
                days_of_week='[0]',
                execution_time='02:00',
                backup_format='sql',
                retention_days=30
            )
            db.session.add(schedule)
            db.session.commit()
        
        import json
        days_enabled = json.loads(schedule.days_of_week) if schedule.days_of_week else [0]
        
        day_names = {0: 'Senin', 1: 'Selasa', 2: 'Rabu', 3: 'Kamis', 4: 'Jumat', 5: 'Sabtu', 6: 'Minggu'}
        selected_days = [day_names.get(d, '') for d in days_enabled if 0 <= d < 7]
        
        return render_template('admin/backup.html',
                             backups=backups,
                             schedule=schedule,
                             selected_days=', '.join(selected_days),
                             retention_days=schedule.retention_days)
    
    except Exception as e:
        flash(f'Error loading backup dashboard: {str(e)}', 'danger')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/backup/create', methods=['POST'])
@login_required
@admin_required
def backup_create():
    """
    Trigger manual database backup in specified format.
    
    POST params:
    - format: 'sql' or 'binary'
    """
    from app.services.backup_service import BackupService
    
    try:
        backup_format = request.form.get('format', 'sql')
        if backup_format not in ['sql', 'binary']:
            return {'success': False, 'error': 'Invalid format'}, 400
        
        service = BackupService()
        result = service.backup_database(format=backup_format, created_by_id=current_user.id)
        
        if result['success']:
            flash(f"✓ Backup berhasil dibuat: {result['filename']} ({result['message']})", 'success')
            return redirect(url_for('admin.backup_dashboard'))
        else:
            flash(f"✗ Backup gagal: {result['error']}", 'danger')
            return redirect(url_for('admin.backup_dashboard'))
    
    except Exception as e:
        flash(f"Error creating backup: {str(e)}", 'danger')
        return redirect(url_for('admin.backup_dashboard'))

@admin_bp.route('/backup/restore/<int:backup_id>', methods=['POST'])
@login_required
@admin_required
def backup_restore(backup_id):
    """
    Restore database from a specific backup file.
    WARNING: Destructive operation - requires confirmation.
    
    Expected: User confirms before reaching this endpoint.
    """
    from app.models import BackupLog
    from app.services.backup_service import BackupService
    
    try:
        backup = BackupLog.query.get_or_404(backup_id)
        
        if backup.operation != 'BACKUP':
            flash('Invalid backup record', 'danger')
            return redirect(url_for('admin.backup_dashboard'))
        
        service = BackupService()
        result = service.restore_database(backup.file_path, created_by_id=current_user.id)
        
        if result['success']:
            flash(f"✓ Database restored from {backup.filename}", 'success')
        else:
            flash(f"✗ Restore failed: {result['error']}", 'danger')
        
        return redirect(url_for('admin.backup_dashboard'))
    
    except Exception as e:
        flash(f"Error restoring backup: {str(e)}", 'danger')
        return redirect(url_for('admin.backup_dashboard'))

@admin_bp.route('/backup/upload', methods=['POST'])
@login_required
@admin_required
def backup_upload():
    """
    Upload backup file from external source for migration/restore.
    
    Accepts: .sql, .bak files
    Max size: Based on environment (default 1GB)
    """
    from app.models import BackupLog
    import os
    from werkzeug.utils import secure_filename
    
    try:
        if 'backup_file' not in request.files:
            return {'success': False, 'error': 'No file provided'}, 400
        
        file = request.files['backup_file']
        if not file.filename or file.filename == '':
            return {'success': False, 'error': 'No file selected'}, 400
        
        # Validate file extension
        allowed_extensions = {'sql', 'bak'}
        if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return {'success': False, 'error': 'Only .sql and .bak files allowed'}, 400
        
        # Create backups directory
        backup_dir = os.environ.get('BACKUP_LOCATION', './backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Save file with timestamp prefix
        timestamp = get_gmt7_time().strftime('%Y%m%d_%H%M%S')
        filename = f"upload_external_{timestamp}_{secure_filename(file.filename)}"
        file_path = os.path.join(backup_dir, filename)
        file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Log upload
        from app.models import BackupLog
        log_entry = BackupLog(
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            backup_type='binary' if filename.endswith('.bak') else 'sql',
            status='VERIFIED',
            operation='BACKUP',  # Mark as backup for history
            created_by_id=current_user.id
        )
        db.session.add(log_entry)
        db.session.commit()
        
        flash(f"✓ File uploaded successfully: {filename} ({file_size / (1024*1024):.2f} MB)", 'success')
        return redirect(url_for('admin.backup_dashboard'))
    
    except Exception as e:
        flash(f"Upload error: {str(e)}", 'danger')
        return redirect(url_for('admin.backup_dashboard'))

@admin_bp.route('/backup/delete/<int:backup_id>', methods=['POST'])
@login_required
@admin_required
def backup_delete(backup_id):
    """
    Delete a backup file and its log record.
    """
    from app.models import BackupLog
    import os
    
    try:
        backup = BackupLog.query.get_or_404(backup_id)
        file_path = backup.file_path
        
        # Delete file from disk
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete log record
        db.session.delete(backup)
        db.session.commit()
        
        flash(f"✓ Backup deleted: {backup.filename}", 'success')
        return redirect(url_for('admin.backup_dashboard'))
    
    except Exception as e:
        flash(f"Delete error: {str(e)}", 'danger')
        return redirect(url_for('admin.backup_dashboard'))

@admin_bp.route('/backup/api/list', methods=['GET'])
@login_required
@admin_required
def backup_api_list():
    """
    API endpoint returning backup history as JSON.
    Used for AJAX refresh without page reload.
    """
    from app.models import BackupLog
    from datetime import datetime
    
    try:
        backups = BackupLog.query.filter(
            BackupLog.operation == 'BACKUP',
            BackupLog.status.in_(['SUCCESS', 'VERIFIED'])
        ).order_by(BackupLog.created_at.desc()).limit(50).all()
        
        data = []
        for backup in backups:
            file_size_mb = backup.file_size / (1024 * 1024)
            data.append({
                'id': backup.id,
                'filename': backup.filename,
                'file_size': f"{file_size_mb:.2f} MB",
                'backup_type': backup.backup_type,
                'status': backup.status,
                'created_at': backup.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'created_by': backup.created_by.username if backup.created_by else 'System'
            })
        
        return {'success': True, 'data': data}, 200
    
    except Exception as e:
        return {'success': False, 'error': str(e)}, 500

@admin_bp.route('/backup/schedule', methods=['GET', 'POST'])
@login_required
@admin_required
def backup_schedule():
    """
    Configure automated backup schedule.
    
    POST params (from schedule form):
    - enabled: 'on' (checkbox) or absent
    - days_of_week: list of day indices (0-6)
    - execution_time: HH:MM format
    - backup_format: 'sql' or 'binary'
    - retention_days: integer
    """
    from app.models import BackupSchedule
    import json
    
    if request.method == 'POST':
        try:
            schedule = BackupSchedule.query.first()
            if not schedule:
                schedule = BackupSchedule()
            
            # Parse form data
            schedule.enabled = 'enabled' in request.form
            schedule.execution_time = request.form.get('execution_time', '02:00')
            schedule.backup_format = request.form.get('backup_format', 'sql')
            schedule.retention_days = int(request.form.get('retention_days', 30))
            
            # Days selected (from checkboxes with name="days")
            days_selected = request.form.getlist('days')
            schedule.days_of_week = json.dumps([int(d) for d in days_selected if d.isdigit()])
            
            schedule.updated_at = get_gmt7_time()
            db.session.add(schedule)
            db.session.commit()
            
            # Reschedule the backup job in APScheduler
            from app.extensions import scheduler
            try:
                # Remove existing job
                for job in scheduler.get_jobs():
                    if job.name == 'scheduled_backup':
                        scheduler.remove_job(job.id)
                
                if schedule.enabled:
                    # Re-register backup job
                    days = json.loads(schedule.days_of_week)
                    if days:
                        hour, minute = map(int, schedule.execution_time.split(':'))
                        day_names = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
                        triggered_days = [day_names[d] for d in days if 0 <= d < 7]
                        
                        if triggered_days:
                            trigger = CronTrigger(
                                day_of_week=','.join(triggered_days),
                                hour=hour,
                                minute=minute,
                                timezone='Asia/Jakarta'
                            )
                            scheduler.add_job(
                                _scheduled_backup_task,
                                trigger=trigger,
                                id='scheduled_backup',
                                name='scheduled_backup',
                                replace_existing=True
                            )
            except Exception as e:
                print(f"Scheduler reschedule error: {e}")
            
            status_text = "Jadwal backup aktif" if schedule.enabled else "Jadwal backup dinonaktifkan"
            flash(f"✓ {status_text}: {schedule.execution_time}, Format: {schedule.backup_format}", 'success')
            return redirect(url_for('admin.backup_dashboard'))
        
        except Exception as e:
            flash(f"Schedule update error: {str(e)}", 'danger')
            return redirect(url_for('admin.backup_dashboard'))
    
    return redirect(url_for('admin.backup_dashboard'))

# ============================================================================
# BACKGROUND TASK: Scheduled Backup Execution
# ============================================================================

def _scheduled_backup_task():
    """
    Background task executed by APScheduler at configured times.
    Runs backup_database() and logs result.
    
    This function is called by the scheduler, NOT by user action.
    Runs with application context to access database.
    """
    from app.services.backup_service import BackupService
    from app import create_app
    from config import Config
    
    try:
        # Create app context for database access
        app = create_app(Config)
        with app.app_context():
            from app.models import BackupSchedule
            
            # Get schedule to check format
            schedule = BackupSchedule.query.first()
            backup_format = schedule.backup_format if schedule else 'sql'
            
            # Execute backup
            service = BackupService()
            result = service.backup_database(
                format=backup_format,
                created_by_id=None  # System-initiated backup (no user ID)
            )
            
            if result['success']:
                print(f"[SCHEDULED BACKUP] ✓ Success: {result['filename']} ({result['message']})")
            else:
                print(f"[SCHEDULED BACKUP] ✗ Failed: {result['error']}")
            
            # Run cleanup if schedule exists
            if schedule:
                cleanup_result = service.cleanup_old_backups(retention_days=schedule.retention_days)
                if cleanup_result['deleted_count'] > 0:
                    print(f"[SCHEDULED BACKUP CLEANUP] Deleted {cleanup_result['deleted_count']} old backups")
    
    except Exception as e:
        print(f"[SCHEDULED BACKUP] ERROR: {str(e)}")

