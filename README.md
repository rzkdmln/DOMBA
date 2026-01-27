# Sistem Informasi Transparansi Ketersediaan Blangko KTP-el

![Dashboard Preview](docs/img/dashboard-preview.png)

## Deskripsi Sistem

Sistem informasi transparansi ketersediaan blangko KTP-el untuk seluruh wilayah Kecamatan di Kabupaten Garut. Sistem ini menyediakan dashboard publik yang menampilkan data stok blangko KTP-el secara real-time, interaktif, dan responsif untuk memantau ketersediaan di 42 kecamatan di Kabupaten Garut.

## Fitur Utama

- **Dashboard Publik**: Tampilan data stok blangko KTP-el dengan tabel yang dapat diurutkan dan dicari.
- **Peta Interaktif**: Visualisasi lokasi kecamatan menggunakan Leaflet.js (Local Assets).
- **Keamanan Berlapis**: Implementasi CSRF Protection, Content Security Policy (CSP), dan Rate Limiting.
- **Anti-Bot Captcha**: Sistem tantangan matematika sederhana pada halaman login.
- **Halaman Error Kustom**: UI ramah pengguna untuk error 404, 429 (Rate Limit), dan 500.
- **Responsif & Modern**: Desain optimal untuk mobile/tablet menggunakan Tailwind CSS dan Plus Jakarta Sans.
- **Local Assets**: Berjalan sepenuhnya tanpa koneksi internet (semua library CSS/JS sudah lokal).

## Teknologi yang Digunakan

- **Backend**: Flask (Python), SQLAlchemy, PostgreSQL.
- **Keamanan**: Flask-Talisman (CSP/Headers), Flask-WTF (CSRF), Flask-Limiter.
- **Frontend**: Tailwind CSS 3.4, FontAwesome 6 (Local), Plus Jakarta Sans.
- **Peta**: Leaflet.js (Local).
- **Tabel**: DataTables (Local).
- **Autentikasi**: Flask-Login dengan Math Captcha.
- **Notifikasi**: SweetAlert2 (Local).

## Instalasi dan Setup

### Persyaratan Sistem

- Python 3.8+
- PostgreSQL database
- Virtual environment (disarankan)

### Langkah Instalasi

1. **Clone atau download project ini**

2. **Buat virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Aktivasi virtual environment:**
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Setup database:**
   - Pastikan PostgreSQL berjalan
   - Update konfigurasi database di `config.py`
   - Jalankan migrasi database:
     ```bash
     flask db upgrade
     ```

6. **Inisialisasi data awal:**
   ```bash
   flask init-db
   ```
   Ini akan membuat user admin dengan username: `admin`, password: `admin`

## Menjalankan Aplikasi

```bash
python app.py
```

Aplikasi akan berjalan di `http://127.0.0.1:8000` dan dapat diakses dari jaringan lokal.

## Panduan Produksi (Deployment)

Untuk mendeploy aplikasi ini ke server produksi (VPS), silakan merujuk pada panduan detail di [PRODUCTION.md](PRODUCTION.md). Secara garis besar, tahapan yang diperlukan adalah:

1. **Setup Server**: Persiapan Python, PostgreSQL, dan Nginx pada Ubuntu/Debian atau CentOS.
2. **Database**: Inisialisasi database dan user PostgreSQL.
3. **App Setup**: Konfigurasi virtual environment, install dependencies, dan environment variables.
4. **Service**: Menggunakan Gunicorn dan Systemd untuk agar aplikasi berjalan di background.
5. **Web Server**: Konfigurasi Nginx sebagai Reverse Proxy dan SSL (Certbot) untuk keamanan HTTPS.

### Akses Sistem

- **Dashboard Publik**: `http://127.0.0.1:8000/`
- **Login**: `http://127.0.0.1:8000/auth/login`
- **Dashboard Admin**: `http://127.0.0.1:8000/admin/dashboard` (setelah login sebagai admin)

## Struktur Project

```
├── app.py                 # Entry point aplikasi Flask
├── config.py              # Konfigurasi aplikasi
├── requirements.txt       # Dependencies Python
├── setup_project.py       # Script setup project
├── app/
│   ├── __init__.py        # Factory aplikasi Flask
│   ├── extensions.py      # Ekstensi Flask (SQLAlchemy, Login, dll)
│   ├── models.py          # Model database
│   ├── utils.py           # Utility functions
│   ├── routes/            # Blueprint routes
│   │   ├── __init__.py
│   │   ├── admin_routes.py
│   │   ├── auth_routes.py
│   │   ├── ops_routes.py
│   │   └── public_routes.py
│   ├── static/            # Static files (CSS, JS, images)
│   │   ├── css/
│   │   ├── js/
│   │   └── img/
│   └── templates/         # Jinja2 templates
│       ├── base_internal.html
│       ├── base_public.html
│       ├── admin/
│       ├── auth/
│       ├── errors/
│       ├── operator/
│       └── public/
└── migrations/            # Database migrations
```

## Penggunaan

### Untuk Pengguna Umum
- Akses dashboard publik untuk melihat ketersediaan blangko KTP-el
- Gunakan fitur pencarian dan pengurutan tabel
- Lihat lokasi kecamatan di peta interaktif

### Untuk Admin/Operator
- Login dengan kredensial yang diberikan
- Kelola data stok dan transaksi
- Monitor aktivitas sistem

## Troubleshooting

### Masalah Umum

1. **Database connection error**
   - Pastikan PostgreSQL berjalan
   - Periksa konfigurasi di `config.py`

2. **Template syntax error**
   - Jalankan validasi template: `python -c "import jinja2; env = jinja2.Environment(); env.parse(open('app/templates/auth/login.html').read()); print('Template syntax is valid')"`

3. **Port sudah digunakan**
   - Ubah port di `app.py` atau hentikan proses yang menggunakan port 8000

4. **Dependencies tidak terinstall**
   - Jalankan `pip install -r requirements.txt` di virtual environment yang aktif

### Logs dan Debugging

- Aplikasi berjalan dalam mode debug
- Periksa console browser untuk error JavaScript
- Periksa terminal untuk error Python/Flask

## Kontribusi

Untuk pengembangan lebih lanjut atau perbaikan, silakan buat issue atau pull request di repository ini.

## Lisensi

Sistem ini dikembangkan untuk Pemerintah Kabupaten Garut.
