from app.extensions import db
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from app.utils import get_gmt7_time
from flask_login import UserMixin

class Kecamatan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama_kecamatan = db.Column(db.String(100), nullable=False)
    kode_wilayah = db.Column(db.String(20), unique=True, nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    # One-to-One relationship with Stok
    stok = db.relationship('Stok', backref='kecamatan', uselist=False)

    def __repr__(self):
        return f'<Kecamatan {self.nama_kecamatan}>'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    nama_lengkap = db.Column(db.String(100), nullable=True)  # Nama lengkap user
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin_dinas' or 'operator_kecamatan'
    created_at = db.Column(db.DateTime, default=get_gmt7_time)  # Tanggal pembuatan user

    # Foreign Key to Kecamatan if role is 'operator_kecamatan', nullable for 'admin_dinas'
    kecamatan_id = db.Column(db.Integer, db.ForeignKey('kecamatan.id'), nullable=True)

    # Last login timestamp
    last_login = db.Column(db.DateTime, nullable=True)

    # Relationship back to Kecamatan
    kecamatan = db.relationship('Kecamatan', backref='operator')

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

class Stok(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kecamatan_id = db.Column(db.Integer, db.ForeignKey('kecamatan.id'), unique=True, nullable=False)
    jumlah_ktp = db.Column(db.Integer, default=0)
    jumlah_kia = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=get_gmt7_time, onupdate=get_gmt7_time)

    def __repr__(self):
        return f'<Stok Kecamatan {self.kecamatan_id}: KTP={self.jumlah_ktp}, KIA={self.jumlah_kia}>'

class Transaksi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kecamatan_id = db.Column(db.Integer, db.ForeignKey('kecamatan.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    jenis_transaksi = db.Column(db.String(20), nullable=False)  # 'IN_FROM_PUSAT', 'DISTRIBUSI_TO_KEC', 'CETAK', 'RUSAK'
    jumlah_ktp = db.Column(db.Integer, default=0)
    jumlah_kia = db.Column(db.Integer, default=0)
    keterangan = db.Column(db.String(255), nullable=True)  # Keterangan tambahan untuk transaksi
    created_at = db.Column(db.DateTime, default=get_gmt7_time)

    # Relationships
    kecamatan = db.relationship('Kecamatan', backref='transaksi')
    user = db.relationship('User', backref='transaksi')

    def __repr__(self):
        return f'<Transaksi {self.jenis_transaksi} by User {self.user_id} for Kecamatan {self.kecamatan_id}>'

class DetailCetak(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nik = db.Column(db.String(16), nullable=False)
    nama_lengkap = db.Column(db.String(100), nullable=False)
    tanggal_cetak = db.Column(db.DateTime, default=get_gmt7_time)
    
    # Pengambilan
    status_ambil = db.Column(db.Boolean, default=False) # False = Belum Diambil, True = Sudah
    tanggal_ambil = db.Column(db.DateTime, nullable=True)
    hubungan = db.Column(db.String(50), nullable=True) # Hubungan pengambil: Yang Bersangkutan, Suami, dll.
    penerima = db.Column(db.String(100), nullable=True) # Nama lengkap pengambil

    # Identitas Operator/Kecamatan
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    kecamatan_id = db.Column(db.Integer, db.ForeignKey('kecamatan.id'), nullable=False)
    
    # Status Cetak
    status_cetak = db.Column(db.String(20), default='BERHASIL') # 'BERHASIL', 'GAGAL'
    keterangan_gagal = db.Column(db.String(255), nullable=True)
    
    # Jenis Cetak dan Registrasi
    jenis_cetak = db.Column(db.String(50), nullable=True) # 'Cetak Baru', 'Hilang', 'Rusak', 'Perubahan Data'
    registrasi_ikd = db.Column(db.Boolean, default=False) # True jika registrasi IKD

    # Relationships
    user = db.relationship('User', backref='cetak_records')
    kecamatan = db.relationship('Kecamatan', backref='cetak_records')

    def __repr__(self):
        return f'<DetailCetak {self.nik} - {self.nama_lengkap}>'

# ============================================================================
# DISASTER RECOVERY & BACKUP MANAGEMENT MODELS
# ============================================================================
# These models support automated database backup, restore, and scheduling.
# BackupSchedule: Stores recurring backup schedules (when & how often)
# BackupLog: Audit trail of all backup operations (for compliance & recovery)

class BackupSchedule(db.Model):
    """
    Penjadwalan backup otomatis yang dapat diatur melalui UI admin.
    
    Attributes:
        id (int): Primary key
        enabled (bool): Apakah jadwal backup aktif?
        days_of_week (str): JSON array [0-6] untuk hari (0=Senin, 6=Minggu)
        execution_time (str): Waktu eksekusi HH:MM format (misal: "10:30")
        backup_format (str): Format backup 'sql' atau 'binary'
        created_at (datetime): Tanggal pembuatan jadwal
        updated_at (datetime): Terakhir dimodifikasi
        created_by_id (int): User ID yang membuat jadwal
    """
    id = db.Column(db.Integer, primary_key=True)
    enabled = db.Column(db.Boolean, default=False)
    days_of_week = db.Column(db.String(50), default='[1]')  # JSON: [1,3,5] = Senin,Rabu,Jumat
    execution_time = db.Column(db.String(8), default='02:00')  # HH:MM format
    backup_format = db.Column(db.String(20), default='sql')  # 'sql' atau 'binary'
    retention_days = db.Column(db.Integer, default=30)  # Hapus backup lebih dari N hari
    created_at = db.Column(db.DateTime, default=get_gmt7_time)
    updated_at = db.Column(db.DateTime, default=get_gmt7_time, onupdate=get_gmt7_time)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # Relationships
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    def __repr__(self):
        return f'<BackupSchedule enabled={self.enabled} time={self.execution_time}>'

class BackupLog(db.Model):
    """
    Audit trail untuk semua operasi backup & restore.
    Digunakan untuk tracking, verifikasi integritas, dan compliance.
    
    Attributes:
        id (int): Primary key
        filename (str): Nama file backup (misal: backup_2026_04_14_103045.sql)
        file_size (int): Ukuran file dalam bytes
        file_path (str): Path absolut ke file backup
        backup_type (str): 'sql' atau 'binary' (custom PostgreSQL format)
        status (str): 'SUCCESS', 'FAILED', 'VERIFIED', 'CORRUPTED'
        operation (str): 'BACKUP', 'RESTORE', 'MANUAL', 'SCHEDULED'
        error_message (str): Pesan error jika status FAILED/CORRUPTED
        created_at (datetime): Kapan operasi dilakukan
        created_by_id (int): User ID yang melakukan operasi
    """
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.BigInteger, default=0)  # Bytes
    file_path = db.Column(db.String(512), nullable=False)
    backup_type = db.Column(db.String(20), default='sql')  # 'sql' atau 'binary'
    status = db.Column(db.String(20), default='SUCCESS')  # SUCCESS, FAILED, VERIFIED, CORRUPTED
    operation = db.Column(db.String(20), default='BACKUP')  # BACKUP, RESTORE, MANUAL, SCHEDULED
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=get_gmt7_time)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # Relationships
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    def __repr__(self):
        return f'<BackupLog {self.filename} - {self.status}>'

    def get_file_size_mb(self):
        """Helper: Format file size as MB string"""
        mb = self.file_size / (1024 * 1024)
        return f"{mb:.2f} MB"