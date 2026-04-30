import os
from dotenv import load_dotenv

# Load file .env
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'kunci-cadangan-kalau-env-gagal-ganti-segera'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Database Optimization (Penting untuk mencegah 502 Bad Gateway)
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,       # Cek apakah koneksi masih hidup sebelum melakukan query
        "pool_recycle": 300,         # Daur ulang koneksi setiap 5 menit (300 detik)
        "pool_timeout": 30,          # Batas waktu tunggu mendapatkan koneksi dari pool
        "pool_size": 10,             # Jumlah koneksi standby
        "max_overflow": 20,          # Toleransi tambahan koneksi saat beban tinggi
    }
    
    # Application root for subdirectory deployments (e.g., /domba)
    # Set APPLICATION_ROOT in .env for production, otherwise defaults to '/'
    APPLICATION_ROOT = os.environ.get('APPLICATION_ROOT', '/')
    
    # Static URL path - prefix /domba to static URL when deployed in subdirectory
    app_root = APPLICATION_ROOT.rstrip('/')
    STATIC_URL_PATH = f'{app_root}/static' if app_root != '' else '/static'
    
    # Security Configurations
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Disabled temporarily for debugging session issues
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
