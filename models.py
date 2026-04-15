from extensions import db
from flask_login import UserMixin
from datetime import datetime

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
    nama_lengkap = db.Column(db.String(100)) # Tambahkan ini jika dibutuhkan
    password_hash = db.Column(db.String(512), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin_dinas' or 'operator_kecamatan'
    last_login = db.Column(db.DateTime) # Tambahkan ini supaya migrasi tidak bentrok
    
    # Foreign Key to Kecamatan
    kecamatan_id = db.Column(db.Integer, db.ForeignKey('kecamatan.id'), nullable=True)
    kecamatan = db.relationship('Kecamatan', backref='operator')

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

class Stok(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kecamatan_id = db.Column(db.Integer, db.ForeignKey('kecamatan.id'), unique=True, nullable=False)
    jumlah_ktp = db.Column(db.Integer, default=0)
    jumlah_kia = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Stok Kecamatan {self.kecamatan_id}: KTP={self.jumlah_ktp}, KIA={self.jumlah_kia}>'

class Transaksi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kecamatan_id = db.Column(db.Integer, db.ForeignKey('kecamatan.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    jenis_transaksi = db.Column(db.String(20), nullable=False)  # 'IN_FROM_PUSAT', 'DISTRIBUSI_TO_KEC', 'CETAK', 'RUSAK'
    jumlah_ktp = db.Column(db.Integer, default=0)
    jumlah_kia = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    kecamatan = db.relationship('Kecamatan', backref='transaksi')
    user = db.relationship('User', backref='transaksi')

    def __repr__(self):
        return f'<Transaksi {self.jenis_transaksi} by User {self.user_id} for Kecamatan {self.kecamatan_id}>'