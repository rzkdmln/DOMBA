# Panduan Instalasi Produksi (Production Setup)

Panduan ini menjelaskan langkah-langkah untuk mendeploy aplikasi **DOMBA** ke server produksi.

## 1. Persiapan Server

### Jalur A: Ubuntu / Debian
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv nginx postgresql postgresql-contrib libpq-dev -y
```

### Jalur B: CentOS / RHEL / Rocky Linux / AlmaLinux
```bash
sudo dnf update -y
sudo dnf install python3 python3-pip python3-devel nginx postgresql-server postgresql-contrib libpq-devel gcc -y
sudo postgresql-setup --initdb
sudo systemctl enable --now postgresql
```

## 2. Konfigurasi Database
Buat database dan user di PostgreSQL:
```bash
sudo -u postgres psql
CREATE DATABASE domba_db;
CREATE USER domba_user WITH PASSWORD 'password_anda';
GRANT ALL PRIVILEGES ON DATABASE domba_db TO domba_user;
\q
```

## 3. Clone & Environment Setup
```bash
cd /var/www
# Copy folder project ke sini
sudo chown -R $USER:$USER /var/www/DOMBA
cd /var/www/DOMBA

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

## 4. Konfigurasi Aplikasi
Edit file `config.py` atau gunakan environment variables:
- `SQLALCHEMY_DATABASE_URI`: `postgresql://domba_user:password_anda@localhost/domba_db`
- `SECRET_KEY`: Gunakan key yang kuat (generate via `python -c 'import secrets; print(secrets.token_hex(24))'`)
- `FLASK_DEBUG`: Set ke `0` atau `False`

## 5. Inisialisasi Database
```bash
flask db upgrade
flask init-db
```

## 6. Setup Gunicorn (Systemd)
Buat file service agar aplikasi berjalan otomatis:
`sudo nano /etc/systemd/system/domba.service`

Isi file:
```ini
[Unit]
Description=Gunicorn instance to serve DOMBA
After=network.target

[Service]
# Ubuntu/Debian: User=www-data, Group=www-data
# CentOS/RHEL/Rocky: User=nginx, Group=nginx
User=www-data
Group=www-data
WorkingDirectory=/var/www/DOMBA
Environment="PATH=/var/www/DOMBA/venv/bin"
ExecStart=/var/www/DOMBA/venv/bin/gunicorn --workers 3 --bind unix:domba.sock -m 007 app:app

[Install]
WantedBy=multi-user.target
```

Jalankan service:
```bash
sudo systemctl start domba
sudo systemctl enable domba
```

## 7. Setup Nginx
Buat konfigurasi situs Nginx:
`sudo nano /etc/nginx/sites-available/domba`

Isi file:
```nginx
server {
    listen 80;
    server_name nama_domain_atau_ip_anda;

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/DOMBA/domba.sock;
    }

    location /static/ {
        alias /var/www/DOMBA/app/static/;
    }
}
```

Aktifkan konfigurasi:
```bash
sudo ln -s /etc/nginx/sites-available/domba /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

## 8. Keamanan Tambahan (Opsional)
- **HTTPS**: Sangat disarankan menggunakan Certbot (SSL) agar fitur keamanan Talisman berjalan maksimal.
  ```bash
  sudo apt install certbot python3-certbot-nginx
  sudo certbot --nginx -d domain_anda.com
  ```
- **Firewall (Ubuntu/UFW)**:
  ```bash
  sudo ufw allow 'Nginx Full'
  sudo ufw allow ssh
  sudo ufw enable
  ```
- **Firewall (CentOS/Firewalld)**:
  ```bash
  sudo firewall-cmd --permanent --add-service=http
  sudo firewall-cmd --permanent --add-service=https
  sudo firewall-cmd --reload
  ```
