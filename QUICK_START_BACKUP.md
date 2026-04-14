# DOMBA Backup System - Quick Start Guide

## 🚀 Installation (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt  # APScheduler==3.10.4 added
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your DATABASE_URL and backup settings
```

### 3. Run Database Migration
```bash
flask db migrate -m "Add backup models"
flask db upgrade
```

### 4. Start Application
```bash
python app.py
```
✅ App will auto-create database, tables, and default admin user

---

## 📊 Accessing Backup Dashboard

1. **Login**: http://localhost:8000/auth/login
   - Username: `admin`
   - Password: `admin` (change immediately!)

2. **Go to Backup Management**:
   - Click Admin Dashboard
   - Select "Manajemen Backup & Restore Database"
   - Or direct: http://localhost:8000/admin/backup

---

## 💾 Creating Backups

### Manual Backup (Testing)
```
1. Click "Backup Sekarang" button
2. Choose format:
   - SQL (.sql): Text format, portable
   - Binary (.bak): Compressed format, efficient
3. Confirm
4. Backup appears in history table
```

### Scheduled Backup (Production)
```
1. Scroll to "Konfigurasi Jadwal Backup Otomatis"
2. Check "Aktifkan Jadwal Backup Otomatis"
3. Select days (Mon-Sun)
4. Set time (e.g., 02:00 for 2 AM)
5. Choose format (SQL or Binary)
6. Set retention (days)
7. Click "Simpan Jadwal"
```

Backups run automatically at scheduled time.

---

## 🔄 Restoring from Backup

⚠️ **WARNING**: This overwrites current database!

```
1. Find backup in history table
2. Click "Restore" button
3. Read warning carefully
4. Click "✓ Lanjutkan Restore"
5. Wait for completion
6. Verify data is restored
```

---

## 📤 Uploading External Backups

For database migration from another server:

```
1. Section: "Upload File Backup"
2. Drag-drop .sql or .bak file (or click to browse)
3. Click "Upload File"
4. File appears in history
5. Use "Restore" button to restore when ready
```

---

## 📋 Backup History Commands

### CLI Commands
```bash
# Create backup immediately
flask backup-now

# Test database connection
flask test-db-connection

# Initialize backup tables
flask init-backup-db
```

### API Endpoint
```bash
# Get backup list as JSON
curl http://localhost:8000/admin/backup/api/list \
  -H "Authorization: Bearer <token>"
```

---

##  File Locations

| Item | Location |
|------|----------|
| Backups | `./backups/` (or configured BACKUP_LOCATION) |
| Models | `app/models.py` (BackupSchedule, BackupLog) |
| Services | `app/services/backup_service.py`, `init_service.py` |
| Routes | `app/routes/admin_routes.py` (7 endpoints) |
| Template | `app/templates/admin/backup.html` |
| Frontend JS | `app/static/js/internal/admin_backup.js` |
| Docs | `BACKUP_SYSTEM.md` (full documentation) |

---

## ⚙️ Configuration

### Environment Variables (.env)
```ini
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/domba_db

# Backup Storage
BACKUP_LOCATION=./backups
BACKUP_RETENTION_DAYS=30
```

### Backup Schedule Format
- **Days**: JSON array [0-6] where 0=Monday, 6=Sunday
  - Example: [0,3,6] = Monday, Thursday, Sunday
- **Time**: HH:MM format (24-hour)
  - Example: "02:30" = 2:30 AM
- **Formats**: 'sql' or 'binary'
- **Retention**: Days (30 = delete backups older than 30 days)

---

## 🔍 Verification Checklist

After installation, verify:

- [ ] App starts without errors
- [ ] Admin login works (admin / admin)
- [ ] Can access `/admin/backup`
- [ ] Can create manual backup (SQL format)
- [ ] Backup file exists in `./backups/`
- [ ] Backup appears in history table
- [ ] File size > 0 MB
- [ ] Can view backup details
- [ ] Schedule UI loads without errors

---

## 🚨 Common Issues

| Issue | Solution |
|-------|----------|
| `pg_dump: command not found` | Install PostgreSQL client tools |
| `Connection refused` | Check DATABASE_URL, PostgreSQL running |
| `Permission denied` | Check backup directory permissions |
| `Backup file empty` | Database may be empty, check size |
| `Restore fails` | Ensure backup file is valid, check logs |

---

## 📚 Full Documentation

For detailed information:
- See `BACKUP_SYSTEM.md` for complete documentation
- System architecture, security, disaster recovery procedures
- Performance optimization, troubleshooting guide

---

## 🎯 Recommended Setup for Production

1. **Daily Backups**
   - Days: Mon-Sun (all days)
   - Time: 02:00 (2 AM)
   - Format: Binary (efficient)
   - Retention: 30 days

2. **Weekly Full Backup**
   - Days: Sunday
   - Time: 03:00 (3 AM)
   - Format: SQL (portable)
   - Keep manually (don't auto-delete)

3. **Monthly Archive**
   - Manually backup first Sunday of month
   - Store in archive location
   - Keep 12 months

4. **Off-Site Backup**
   - Copy backups to external storage weekly
   - Cloud storage (S3, Google Cloud)
   - Different physical location

---

## 🆘 Support

### Check Application Logs
```bash
# View recent logs
tail -20 app.log

# Follow logs in real-time
tail -f app.log
```

### Database Check
```bash
# Connect to PostgreSQL
psql -U domba_user -d domba_db

# Check backup tables
SELECT COUNT(*) FROM backup_log;
SELECT COUNT(*) FROM backup_schedule;

# View latest backup
SELECT * FROM backup_log ORDER BY created_at DESC LIMIT 5;
```

### Test Restore (Dry Run)
```python
# From Python shell
from app.services.backup_service import BackupService

service = BackupService()

# Test connection
backup = service.backup_database(format='sql')
print(f"Backup status: {backup['success']}")
```

---

## 📞 Contact

For issues or questions regarding the backup system:
- Review `BACKUP_SYSTEM.md` troubleshooting section
- Check application error logs
- Contact system administrator

---

**Last Updated**: April 14, 2026  
**Version**: 1.0  
**Status**: Production Ready ✅
