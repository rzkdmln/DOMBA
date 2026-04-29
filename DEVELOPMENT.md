# Panduan Kelola Server & Local - Proyek DOMBA

Dokumen ini berisi rangkuman konfigurasi terminal, alur update kode (Git), dan solusi jaringan untuk akses SIAK Terpusat.

## 🚀 1. Perintah Cepat (Aktivasi Environment)

Kita sudah menyamakan perintah antara VPS dan Lokal (Windsurf/VSCode) agar memori otot tidak bingung.

### Di VPS (Linux)

Ketik perintah ini untuk masuk ke folder proyek dan mengaktifkan venv:

```bash
activate-domba
```

**Settingan ada di ~/.bashrc**

Tambahkan baris berikut ke `~/.bashrc`:

```bash
# DOMBA Project Alias
alias activate-domba='cd /var/www/DOMBA && source venv/bin/activate'
```

Setelah menambahkan, jalankan:

```bash
source ~/.bashrc
```

### Di Windows (Windsurf/VSCode)

Ketik perintah ini di PowerShell:

```powershell
activate-domba
```

**Settingan ada di $PROFILE**

Tambahkan baris berikut ke PowerShell profile:

```powershell
# DOMBA Project Alias
function activate-domba {
    Set-Location "E:\APLIKASI\DOMBA"
    & ".\venv\Scripts\Activate.ps1"
}
```

Untuk edit profile, jalankan:

```powershell
notepad $PROFILE
```

Jika muncul error execution policy, jalankan:

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 🔄 2. Alur Update Kode (Git Workflow)

Lakukan urutan ini agar file rahasia (.env) tidak bocor dan tidak terjadi bentrok di server.

### Langkah 1: Di Laptop (Windsurf)

1. Selesaikan coding
2. Buka GitHub Desktop
3. **PENTING**: Pastikan file .env TIDAK DICENTANG
4. Isi Summary (contoh: "Update tampilan tabel")
5. Klik Commit
6. Klik Push

### Langkah 2: Di VPS (Server)

1. Masuk ke environment:
   ```bash
   activate-domba
   ```

2. Tarik update terbaru:
   ```bash
   git pull origin main
   ```

3. Restart aplikasi agar perubahan muncul:
   ```bash
   systemctl restart domba
   ```

### Troubleshooting Git

**Error saat pull di VPS?**
```bash
git reset --hard HEAD
git pull origin main
```

**File .env muncul di Git?**
```bash
git rm --cached .env
git commit -m "Remove .env from tracking"
```

---

## 🛡️ 3. Manajemen File .env (PENTING!)

File .env sudah di-ignore oleh Git. Artinya, isinya berbeda antara laptop dan VPS.

### Isi .env VPS (Production)

```ini
FLASK_DEBUG=0
FLASK_ENV=production
APPLICATION_ROOT=/domba
DATABASE_URL=postgresql://domba_user:password@localhost/domba_db
SECRET_KEY=your-production-secret-key
```

### Isi .env Laptop (Development)

```ini
FLASK_DEBUG=1
FLASK_ENV=development
APPLICATION_ROOT=/
DATABASE_URL=postgresql://domba_user:password@localhost/domba_db
SECRET_KEY=your-development-secret-key
```

### Catatan Penting

- Jangan pernah commit file .env ke Git
- Pastikan .env ada di .gitignore
- Password database di VPS dan laptop bisa berbeda
- SECRET_KEY harus berbeda antara production dan development

---

## 🌐 4. Solusi Akses Dual Network (VPN + Lokal)

Agar bisa akses SIAK Terpusat (10.32.5.26) sambil tetap terhubung ke VPN, kita menggunakan Split Tunneling.

### A. Settingan File .ovpn

Tambahkan baris ini sebelum tag `<ca>` di file konfigurasi OpenVPN kamu:

```text
route 10.32.5.0 255.255.255.0 net_gateway
route 192.168.99.0 255.255.255.0 net_gateway
```

**Penjelasan:**
- `route 10.32.5.0`: IP range SIAK Terpusat
- `net_gateway`: Menggunakan gateway internet lokal, bukan VPN
- `route 192.168.99.0`: IP range jaringan lokal lain (jika ada)

### B. Settingan Metric (Prioritas Jaringan)

Agar aplikasi SIAK membaca IP lokal (192.168.x.x) dan bukan IP VPN:

#### Windows

1. Buka **Control Panel** → **Network and Sharing Center** → **Change adapter settings**
2. Klik kanan pada adapter yang ingin diubah → **Properties**
3. Klik **Configure** → tab **Advanced**
4. Cari **Interface Metric**
5. Set nilai:
   - **Wi-Fi/LAN Asli**: Set ke **10** (Prioritas Utama)
   - **TAP-Windows (OpenVPN)**: Set ke **100** (Prioritas Kedua)

#### Linux

Edit file konfigurasi network interface:

```bash
# Untuk interface utama (eth0/wlan0)
sudo ip link set eth0 metric 10

# Untuk OpenVPN (tun0)
sudo ip link set tun0 metric 100
```

### Verifikasi

Cek routing table untuk memastikan:

**Windows:**
```cmd
route print
```

**Linux:**
```bash
ip route show
```

Pastikan traffic ke 10.32.5.0/24 dan 192.168.99.0/24 lewat gateway lokal.

---

## 🛠️ 5. Troubleshooting Cepat

### Aplikasi tidak berubah setelah pull?

**Solusi:**
```bash
# Di VPS
activate-domba
systemctl restart domba
```

### Error saat pull di VPS?

**Solusi:**
```bash
# Reset local changes
git reset --hard HEAD
# Pull ulang
git pull origin main
# Restart aplikasi
systemctl restart domba
```

### Venv di Windows tidak mau jalan?

**Solusi:**
```powershell
# Jalankan di PowerShell (Admin)
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### PostgreSQL connection error?

**Cek:**
```bash
# Linux
sudo systemctl status postgresql
sudo systemctl start postgresql

# Windows
# Buka Services.msc dan cari PostgreSQL service
```

### Port 8000 sudah digunakan?

**Linux:**
```bash
sudo lsof -i :8000
sudo kill -9 <PID>
```

**Windows:**
```cmd
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Environment variables tidak terbaca?

**Cek:**
```bash
# Linux
echo $FLASK_DEBUG
printenv | grep FLASK

# Windows PowerShell
echo $env:FLASK_DEBUG
Get-ChildItem Env: | Where-Object {$_.Name -like "FLASK*"}
```

---

## 📋 6. Referensi Dokumentasi Lengkap

Untuk dokumentasi lebih detail:

- **[README.md](README.md)** - Overview project dan instalasi dasar
- **[PRODUCTION.md](PRODUCTION.md)** - Panduan deployment ke VPS lengkap
- **[BACKUP_SYSTEM.md](BACKUP_SYSTEM.md)** - Sistem backup & restore database

---

## 💡 Tips Produktivitas

### Shortcut Commands

Buat alias tambahan di `~/.bashrc` atau `$PROFILE`:

**Linux:**
```bash
# DOMBA shortcuts
alias domba-restart='systemctl restart domba'
alias domba-logs='journalctl -u domba -f'
alias domba-status='systemctl status domba'
```

**Windows PowerShell:**
```powershell
# DOMBA shortcuts
function domba-restart { python app.py }
function domba-logs { Get-Content app.log -Wait }
```

### Git Workflow Best Practices

1. Selalu pull sebelum mulai coding
2. Commit sering dengan pesan yang jelas
3. Jangan commit file .env
4. Push setelah selesai fitur utama
5. Test di local sebelum push

### Environment Management

- Gunakan virtual environment untuk setiap project
- Install dependencies dari requirements.txt
- Lock versi dependencies untuk consistency
- Update requirements.txt setelah install package baru

---

**Last Updated:** April 29, 2026  
**Version:** 1.0  
**Status:** Active ✅
