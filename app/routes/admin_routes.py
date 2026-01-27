from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from app.models import Kecamatan, Stok, Transaksi, User, DetailCetak
from app.extensions import db
from sqlalchemy import func
from app.utils import get_gmt7_time, admin_required
import pandas as pd
from io import BytesIO
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Get sorting parameters
    sort_by = request.args.get('sort_by', 'jumlah_ktp')  # Default: jumlah stok
    sort_order = request.args.get('sort_order', 'desc')  # Default: descending (terbanyak ke tersedikit)
    
    # Validate per_page options
    if per_page not in [10, 20, 0]:  # 0 means show all
        per_page = 10
    
    # Validate sorting options
    valid_sort_columns = ['nama_kecamatan', 'jumlah_ktp']
    if sort_by not in valid_sort_columns:
        sort_by = 'jumlah_ktp'
    if sort_order not in ['asc', 'desc']:
        sort_order = 'desc'
    
    # Get summary statistics
    total_kecamatan = Kecamatan.query.count()
    total_stok_ktp = db.session.query(func.sum(Stok.jumlah_ktp)).scalar() or 0
    total_stok_kia = db.session.query(func.sum(Stok.jumlah_kia)).scalar() or 0
    total_users = User.query.count()

    # Get recent transactions (last 10)
    recent_transactions = Transaksi.query.order_by(Transaksi.created_at.desc()).limit(10).all()

    # Get recent printing logs (last 10)
    recent_cetaks = DetailCetak.query.order_by(DetailCetak.tanggal_cetak.desc()).limit(10).all()

    # Get stock levels for all kecamatan with pagination
    if per_page == 0:  # Show all
        stock_query = db.session.query(
            Kecamatan.nama_kecamatan,
            Stok.jumlah_ktp,
            Stok.jumlah_kia,
            Stok.last_updated
        ).join(Stok)
        
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
            Kecamatan.nama_kecamatan,
            Stok.jumlah_ktp,
            Stok.jumlah_kia,
            Stok.last_updated
        ).join(Stok)
        
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
        
        total_stock_records = stock_query.count()
        stock_data = stock_query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Calculate pagination info
        total_pages = (total_stock_records + per_page - 1) // per_page
        pagination_info = {
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'total_records': total_stock_records,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'prev_page': page - 1 if page > 1 else None,
            'next_page': page + 1 if page < total_pages else None
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

    return render_template('admin/dashboard.html',
                         total_kecamatan=total_kecamatan,
                         total_stok_ktp=total_stok_ktp,
                         total_stok_kia=total_stok_kia,
                         total_users=total_users,
                         recent_transactions=recent_transactions,
                         recent_cetaks=recent_cetaks,
                         stock_data=stock_data,
                         low_stock_alerts=low_stock_alerts,
                         pagination_info=pagination_info)

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
        total_cetaks = len(cetaks)
        pagination_info = None
    else:
        # Paginated query
        total_cetaks = cetaks_query.count()
        cetaks = cetaks_query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Calculate pagination info
        total_pages = (total_cetaks + per_page - 1) // per_page
        pagination_info = {
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'total_records': total_cetaks,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'prev_page': page - 1 if page > 1 else None,
            'next_page': page + 1 if page < total_pages else None
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

@admin_bp.route('/lapor-pakai', methods=['GET', 'POST'])
@login_required
@admin_required
def lapor_pakai():
    import re
    from datetime import timedelta
    
    # Ensure admin has a kecamatan_id (Dinas)
    if not current_user.kecamatan_id:
        dinas = Kecamatan.query.filter_by(kode_wilayah='32.05.00').first()
        if dinas:
            current_user.kecamatan_id = dinas.id
            db.session.commit()

    if request.method == 'POST':
        nik = request.form.get('nik')
        nama = request.form.get('nama_lengkap')
        jenis_cetak = request.form.get('jenis_cetak')
        registrasi_ikd = request.form.get('registrasi_ikd') == 'true'
        status_cetak = request.form.get('status_cetak', 'BERHASIL')
        keterangan_gagal = request.form.get('keterangan_gagal')
        
        if not nik or not nama or not jenis_cetak:
            flash('NIK, Nama Lengkap, dan Jenis Cetak are required!', 'danger')
            return redirect(url_for('admin.lapor_pakai'))
        
        # Validasi NIK: 16 digit angka
        if not re.match(r'^\d{16}$', nik):
            flash('NIK harus terdiri dari 16 digit angka!', 'danger')
            return redirect(url_for('admin.lapor_pakai'))
        
        # Validasi Nama Lengkap: huruf kapital, spasi, dash, kutip
        if not re.match(r'^[A-Z\s\'\-]+$', nama):
            flash('Nama Lengkap hanya boleh huruf kapital, spasi, dash, atau kutip!', 'danger')
            return redirect(url_for('admin.lapor_pakai'))
        
        # 1. Simpan detail cetak
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
        
        # 2. Kurangi stok KTP
        stok = Stok.query.filter_by(kecamatan_id=current_user.kecamatan_id).first()
        if stok and stok.jumlah_ktp > 0:
            stok.jumlah_ktp -= 1
            
            # 3. Catat di Transaksi for audit trail
            jenis_trans = 'CETAK' if status_cetak == 'BERHASIL' else 'RUSAK'
            transaksi = Transaksi(
                kecamatan_id=current_user.kecamatan_id,
                user_id=current_user.id,
                jenis_transaksi=jenis_trans,
                jumlah_ktp=1,
                jumlah_kia=0
            )
            
            db.session.add(new_record)
            db.session.add(transaksi)
            db.session.commit()
            
            flash(f'Berhasil mencatat pencetakan KTP-el untuk {nama}', 'success')
        else:
            flash('Gagal! Stok KTP-el tidak mencukupi.', 'danger')
            
        return redirect(url_for('admin.lapor_pakai'))

    # GET request
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    history_query = DetailCetak.query.filter(DetailCetak.status_ambil == False)\
        .order_by(DetailCetak.tanggal_cetak.desc())
    
    total_cetak = history_query.count()
    history = history_query.offset((page - 1) * per_page).limit(per_page).all()
    
    total_pages = (total_cetak + per_page - 1) // per_page
    pagination_info = {
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages,
        'total_records': total_cetak,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_page': page - 1 if page > 1 else None,
        'next_page': page + 1 if page < total_pages else None
    }
        
    stok = Stok.query.filter_by(kecamatan_id=current_user.kecamatan_id).first()
    
    return render_template('operator/lapor_pakai.html', 
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
        return redirect(url_for('admin.lapor_pakai'))
    
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
    return redirect(url_for('admin.lapor_pakai'))

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
    
    if not nik or not nama or not jenis_cetak:
        flash('Semua field required!', 'danger')
        return redirect(url_for('admin.lapor_pakai'))
    
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
    return redirect(url_for('admin.lapor_pakai'))

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
    return redirect(url_for('admin.lapor_pakai'))

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
        total_users = len(users)
        pagination_info = None
    else:
        # Paginated query
        total_users = users_query.count()
        users = users_query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Calculate pagination info
        total_pages = (total_users + per_page - 1) // per_page
        pagination_info = {
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'total_records': total_users,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'prev_page': page - 1 if page > 1 else None,
            'next_page': page + 1 if page < total_pages else None
        }
    
    kecamatans = Kecamatan.query.filter(Kecamatan.kode_wilayah != '32.05.00').all()
    
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
    
    # Kurangi stok Gudang Dinas
    dinas = Kecamatan.query.filter_by(kode_wilayah='32.05.00').first()
    stok_dinas = Stok.query.filter_by(kecamatan_id=dinas.id).first()
    if stok_dinas:
        stok_dinas.jumlah_ktp -= transaksi.jumlah_ktp
    
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
        
        # 1. Kurangi Stok Gudang Dinas
        stok_dinas.jumlah_ktp -= jumlah
        
        # 2. Tambah Stok Kecamatan Tujuan
        stok_tujuan = Stok.query.filter_by(kecamatan_id=kecamatan_id).first()
        if not stok_tujuan:
            stok_tujuan = Stok(kecamatan_id=kecamatan_id, jumlah_ktp=0)
            db.session.add(stok_tujuan)
        
        stok_tujuan.jumlah_ktp += jumlah
        
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
        
        flash(f'Berhasil mendistribusikan {jumlah} blangko ke {stok_tujuan.kecamatan.nama_kecamatan}', 'success')
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
        
        total_stock_records = stock_query.count()
        stock_data = stock_query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Calculate pagination info
        total_pages = (total_stock_records + per_page - 1) // per_page
        pagination_info = {
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'total_records': total_stock_records,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'prev_page': page - 1 if page > 1 else None,
            'next_page': page + 1 if page < total_pages else None
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

