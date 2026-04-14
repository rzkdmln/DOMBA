from datetime import datetime, timedelta
from functools import wraps
import re
from flask import abort, flash
from flask_login import current_user
from app.extensions import db

def get_gmt7_time():
    """Returns current time in GMT+7 (Western Indonesia Time)."""
    return datetime.utcnow() + timedelta(hours=7)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin_dinas':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def operator_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'operator':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def validate_cetak_data(nik, nama, jenis_cetak, registrasi_ikd):
    """
    Validates common printing data (NIK and Name).
    Returns (is_valid, error_message)
    """
    if not nik or not nama or not jenis_cetak or registrasi_ikd is None:
        return False, 'NIK, Nama Lengkap, Jenis Cetak, dan Status IKD wajib diisi!'
    
    # Validasi NIK: 16 digit angka
    if not re.match(r'^\d{16}$', nik):
        return False, 'NIK harus terdiri dari 16 digit angka!'
    
    # Validasi Nama Lengkap: huruf kapital, spasi, dash, kutip
    if not re.match(r'^[A-Z\s\'\-]+$', nama):
        return False, 'Nama Lengkap hanya boleh huruf kapital, spasi, dash, atau kutip!'
    
    return True, None

def process_stok_pengurangan(kecamatan_id, user_id, status_cetak, detail_cetak_obj):
    """
    Processes stock reduction and transaction logging.
    Returns (success, message)
    """
    from app.models import Stok, Transaksi
    
    stok = Stok.query.filter_by(kecamatan_id=kecamatan_id).first()
    if not (stok and stok.jumlah_ktp > 0):
        return False, 'Gagal! Stok KTP-el tidak mencukupi atau tidak ditemukan.'
        
    # 1. Kurangi stok KTP secara atomik di level database
    stok.jumlah_ktp = Stok.jumlah_ktp - 1
    
    # 2. Catat di Transaksi for audit trail
    jenis_trans = 'CETAK' if status_cetak == 'BERHASIL' else 'RUSAK'
    transaksi = Transaksi(
        kecamatan_id=kecamatan_id,
        user_id=user_id,
        jenis_transaksi=jenis_trans,
        jumlah_ktp=1,
        jumlah_kia=0
    )
    
    db.session.add(detail_cetak_obj)
    db.session.add(transaksi)
    db.session.commit()
    
    msg = f'Berhasil mencatat pencetakan KTP-el untuk {detail_cetak_obj.nama_lengkap}'
    if status_cetak == 'GAGAL':
        msg = f'Berhasil mencatat KTP-el GAGAL/RUSAK untuk {detail_cetak_obj.nama_lengkap}'
        
    return True, msg
