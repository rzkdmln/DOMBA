# DOMBA Database Backup & Disaster Recovery System
## Technical Documentation & Implementation Guide

**Version:** 1.0  
**Last Updated:** April 14, 2026  
**Status:** Production Ready  

---

## Table of Contents

1. [Overview & Architecture](#overview--architecture)
2. [System Components](#system-components)
3. [Installation & Setup](#installation--setup)
4. [Configuration Guide](#configuration-guide)
5. [User Manual](#user-manual)
6. [API Endpoints Reference](#api-endpoints-reference)
7. [Disaster Recovery Procedures](#disaster-recovery-procedures)
8. [Troubleshooting](#troubleshooting)
9. [Security Considerations](#security-considerations)
10. [Performance & Optimization](#performance--optimization)

---

## Overview & Architecture

### Purpose
The DOMBA Backup & Restore System provides automated database backup, manual restore, and scheduled maintenance capabilities. It's designed for disaster recovery and business continuity.

### Key Features
- ✅ **Automated Backups**: Scheduled daily/weekly/monthly backups via APScheduler
- ✅ **Multiple Formats**: SQL (text) and Binary (custom PostgreSQL format)
- ✅ **Web UI Dashboard**: Complete backup management interface at `/admin/backup`
- ✅ **File Upload**: Upload external backups for migration/restore
- ✅ **Auto-Initialization**: Database auto-created on first startup
- ✅ **Retention Policy**: Automatic cleanup of old backups
- ✅ **Audit Trail**: Complete logging of all backup operations
- ✅ **SweetAlert2 Notifications**: User-friendly UI feedback

### Technology Stack
- **Backend**: Python Flask with Flask-SQLAlchemy
- **Scheduler**: APScheduler (background task scheduling)
- **Database Tools**: PostgreSQL native `pg_dump` & `pg_restore`
- **ORM**: SQLAlchemy for audit logging
- **Frontend**: Tailwind CSS + SweetAlert2 + Vanilla JavaScript

---

## System Components

### 1. Data Models

#### BackupSchedule Model
```python
class BackupSchedule(db.Model):
    id                  # Primary key
    enabled             # bool: Schedule active/inactive
    days_of_week        # JSON: [0-6] for days (0=Mon, 6=Sun)
    execution_time      # str: "HH:MM" format (e.g., "02:00")
    backup_format       # str: 'sql' or 'binary'
    retention_days      # int: Days to keep backups (default 30)
    created_at          # datetime: Created timestamp
    updated_at          # datetime: Last updated
    created_by_id       # FK: User who created schedule
```

#### BackupLog Model
```python
class BackupLog(db.Model):
    id                  # Primary key
    filename            # str: Backup file name (e.g., "backup_domba_20260414_120000.sql")
    file_path           # str: Absolute path to backup file
    file_size           # int: File size in bytes
    backup_type         # str: 'sql' or 'binary'
    status              # str: 'SUCCESS', 'FAILED', 'VERIFIED', 'CORRUPTED'
    operation           # str: 'BACKUP', 'RESTORE', 'MANUAL', 'SCHEDULED'
    error_message       # str: Error details if failed
    created_at          # datetime: Operation timestamp
    created_by_id       # FK: User who triggered operation or NULL for scheduled
```

### 2. Service Layer

#### BackupService Class (`app/services/backup_service.py`)
Handles all database backup/restore operations using PostgreSQL native tools.

**Key Methods:**
- `backup_database(format='sql')` - Create backup
- `restore_database(file_path)` - Restore from backup
- `verify_backup(file_path)` - Verify backup integrity
- `cleanup_old_backups(retention_days=30)` - Enforce retention policy
- `list_backups(limit=50)` - Get backup history
- `get_connection_string()` - Resolve database credentials

#### InitService Class (`app/services/init_service.py`)
Handles database initialization on application startup.

**Key Methods:**
- `run_initialization()` - Execute full init sequence
- `_database_exists()` - Check if database exists
- `_create_database()` - Create database if missing
- `_seed_default_admin()` - Create default admin user

### 3. Admin Routes (7 Endpoints)

All routes in `app/routes/admin_routes.py` with `@admin_required` decorator:

| Route | Method | Purpose |
|-------|--------|---------|
| `/admin/backup` | GET | Display backup dashboard |
| `/admin/backup/create` | POST | Trigger manual backup |
| `/admin/backup/restore/<id>` | POST | Restore from backup |
| `/admin/backup/upload` | POST | Upload external backup file |
| `/admin/backup/delete/<id>` | POST | Delete backup file |
| `/admin/backup/api/list` | GET | JSON list of backups (AJAX) |
| `/admin/backup/schedule` | GET/POST | Configure backup schedule |

### 4. Scheduler Integration

**APScheduler Configuration:**
- Executor: ThreadPoolExecutor (2 workers)
- Timezone: Asia/Jakarta
- Job Name: `scheduled_backup`
- Trigger: CronTrigger (day of week + time)

**Background Task Function:**
`_scheduled_backup_task()` runs at configured times and executes:
1. Call `BackupService.backup_database()`
2. Log successful/failed backup
3. Run retention cleanup if enabled

### 5. Frontend Components

#### Template (`app/templates/admin/backup.html`)
- Quick action buttons (Manual backup, Upload)
- Backup history table (sortable, searchable)
- Schedule configuration panel (collapsible)
- Drag-n-drop upload area
- Disaster recovery guidance

#### JavaScript (`app/static/js/internal/admin_backup.js`)
- `triggerBackup(format)` - Manual backup trigger
- `restoreBackup(backupId, filename)` - Restore with confirmation
- `deleteBackup(backupId, filename)` - Delete backup
- `initDragDropUpload()` - Drag-n-drop file upload
- `saveSchedule()` - Save schedule configuration
- `loadBackupHistory()` - AJAX history refresh
- SweetAlert2 notification helpers

---

## Installation & Setup

### Prerequisites
- Python 3.8+
- PostgreSQL server (locally or remote)
- PostgreSQL client tools (`pg_dump`, `pg_restore`)
- 500MB+ available disk space for backups

### Step 1: Install Dependencies

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install new dependencies
pip install -r requirements.txt
```

**New package:** APScheduler==3.10.4

### Step 2: Configure Environment Variables

```bash
# Copy template to .env
cp .env.example .env

# Edit .env with your settings
# Key variables for backup:
# - DATABASE_URL: PostgreSQL connection string
# - BACKUP_LOCATION: Where to save backups (default: ./backups)
# - BACKUP_RETENTION_DAYS: Days to keep backups (default: 30)
```

### Step 3: Database Migration

```bash
# Create migration for new models
flask db migrate -m "Add BackupSchedule and BackupLog models"

# Apply migration
flask db upgrade
```

### Step 4: Test Auto-Initialization

```bash
# First run will auto-create database and tables
python app.py

# Check output for initialization messages:
# [INIT] Starting database initialization...
# [INIT] ✓ Database created: domba_db
# [INIT] ✓ Tables created/verified
# [INIT] ✓ Admin user created: admin
# [SCHEDULER] ✓ Background scheduler started
```

### Step 5: Verify Installation

1. Open browser → http://localhost:8000
2. Login as admin (username: admin, password: admin)
3. Navigate to Admin Dashboard → Manajemen Backup
4. Click "Backup Sekarang" (SQL) to test
5. Verify backup file in `./backups/` directory

---

## Configuration Guide

### Environment Variables

```ini
# Database Connection
DATABASE_URL=postgresql://user:pass@localhost:5432/domba_db

# Backup Storage
BACKUP_LOCATION=./backups              # Relative or absolute path
BACKUP_RETENTION_DAYS=30               # Days to keep backups

# Flask Settings
FLASK_DEBUG=false                       # Always false in production
PORT=8000
SECRET_KEY=your-strong-secret-key-here
```

### PostgreSQL Connection Formats

```python
# Standard URL
DATABASE_URL=postgresql://domba_user:password@localhost:5432/domba_db

# With host parameter
DATABASE_URL=postgresql://domba_user:password@192.168.1.100:5432/domba_db

# For SSL connections
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require

# Local socket (Unix only)
DATABASE_URL=postgresql:///domba_db?host=/var/run/postgresql
```

### Backup Schedule Configuration

Via Admin UI (`/admin/backup`):

1. **Enable Schedule**: Toggle checkbox
2. **Select Days**: Choose which days (Mon-Sun)
3. **Set Time**: Select execution time (HH:MM)
4. **Backup Format**: SQL or Binary
5. **Retention**: Days to keep backups
6. **Save**: Click "Simpan Jadwal"

**Example Configurations:**

**Daily at 2:00 AM (SQL format):**
- Days: Mon-Sun (all)
- Time: 02:00
- Format: SQL
- Retention: 30 days

**Weekly on Sunday at 3:00 AM (Binary format):**
- Days: Sunday
- Time: 03:00
- Format: Binary
- Retention: 60 days

---

## User Manual

### Creating a Backup

**Manual Backup (Recommended for testing):**
1. Login as admin
2. Go to Admin Dashboard → Manajemen Backup
3. Click "Backup Sekarang"
4. Choose format: SQL or Binary
5. Confirm in modal
6. Monitor progress (don't close browser)
7. Backup appears in history table

**Scheduled Backup (Recommended for production):**
1. Configure schedule in "Konfigurasi Jadwal Backup Otomatis"
2. Enable toggle + select days/time
3. Save configuration
4. Backups run automatically at scheduled times

### Restoring from Backup

⚠️ **WARNING: This operation overwrites current database!**

**Step-by-Step:**
1. Go to Manajemen Backup dashboard
2. Find backup in history table
3. Click "Restore" button
4. Read warning carefully
5. Click "✓ Lanjutkan Restore"
6. Wait for completion (don't close browser)
7. Page auto-refreshes when done

**Verification:**
- Check if data is restored correctly
- Verify recent transactions/records
- Check application logs for errors

### Uploading External Backup

**For Database Migration:**

1. Go to Manajemen Backup dashboard
2. Find "Upload File Backup" section
3. Drag-drop .sql or .bak file OR click to browse
4. File details appear below
5. Click "Upload File"
6. Confirm upload
7. File appears in history (ready for restore)

### Managing Backup Schedule

**View Current Schedule:**
- Click "Konfigurasi Jadwal Backup Otomatis" section
- Current settings displayed

**Modify Schedule:**
1. Update any setting (days, time, format, retention)
2. Click "Simpan Jadwal"
3. Confirm in modal
4. Changes take effect immediately

**Disable Scheduled Backups:**
1. Uncheck "Aktifkan Jadwal Backup Otomatis"
2. Click "Simpan Jadwal"
3. Scheduled backups stop (manual backups still available)

---

## API Endpoints Reference

### GET /admin/backup
Display backup management dashboard.
- **Auth**: Admin only
- **Response**: HTML page with backup history, schedule config, upload area

### POST /admin/backup/create
Create manual backup.
- **Auth**: Admin only
- **Params**:
  - `format`: 'sql' or 'binary'
- **Response**: Redirect to backup dashboard with success/error message

### POST /admin/backup/restore/<backup_id>
Restore database from backup.
- **Auth**: Admin only
- **URL Params**: `backup_id` (integer)
- **Response**: Redirect with result message
- **Warning**: Destructive operation - confirms user before proceeding

### POST /admin/backup/upload
Upload external backup file.
- **Auth**: Admin only
- **File**: multipart/form-data - `backup_file` field
- **Accepted Types**: .sql, .bak
- **Response**: Redirect with success/error message

### POST /admin/backup/delete/<backup_id>
Delete backup file and log record.
- **Auth**: Admin only
- **URL Params**: `backup_id` (integer)
- **Response**: Redirect with confirmation message

### GET /admin/backup/api/list
Get backup history as JSON (for AJAX).
- **Auth**: Admin only
- **Response Format**:
  ```json
  {
    "success": true,
    "data": [
      {
        "id": 1,
        "filename": "backup_domba_20260414_120000.sql",
        "file_size": "156.45 MB",
        "backup_type": "sql",
        "status": "VERIFIED",
        "created_at": "2026-04-14 12:00:00",
        "created_by": "admin"
      }
    ]
  }
  ```

### GET/POST /admin/backup/schedule
View/update backup schedule.
- **Auth**: Admin only
- **GET**: Redirect to backup dashboard
- **POST**: Update schedule configuration
- **POST Params**:
  - `enabled`: checkbox (present = enabled)
  - `days[]`: list of day indices (0-6)
  - `execution_time`: "HH:MM"
  - `backup_format`: 'sql' or 'binary'
  - `retention_days`: integer

---

## Disaster Recovery Procedures

### Scenario 1: Database Corruption

**Symptoms:**
- Database queries return errors
- Application shows database connection errors
- Data appears corrupted or missing

**Recovery Steps:**
1. **Don't panic** - Database is backed up
2. Go to `/admin/backup` (may require DB reconnection)
3. Select most recent good backup from history
4. Click "Restore" and confirm
5. Wait for restoration to complete
6. Test application - verify data integrity
7. If still issues, try older backup
8. Notify system administrator

### Scenario 2: Accidental Data Deletion

**Steps:**
1. Immediately **STOP** all user operations
2. Go to backup dashboard
3. Select backup near time of deletion
4. Restore database
5. Verify deleted data is recovered
6. Check backup logs for details

### Scenario 3: Scheduled Backup Failed

**Check:**
1. Login to admin dashboard
2. Look for backup with "FAILED" status
3. Click to see error message
4. Common causes:
   - Disk full - free up space in BACKUP_LOCATION
   - Database too large - increase timeout
   - PostgreSQL tools not installed - check path
   - Invalid credentials - verify DATABASE_URL

**Resolution:**
- Fix root cause
- Retry manual backup
- Check application logs: `/var/log/domba.log`

### Scenario 4: Disaster Recovery - Rebuild Server

**Complete Recovery Procedure:**

```bash
# 1. Install PostgreSQL on new server
sudo apt update
sudo apt install postgresql postgresql-contrib

# 2. Create database and user
sudo -u postgres psql
CREATE DATABASE domba_db;
CREATE USER domba_user WITH PASSWORD 'strong_password';
GRANT ALL PRIVILEGES ON DATABASE domba_db TO domba_user;
\q

# 3. Install DOMBA application
cd /var/www
git clone https://github.com/rzkdmln/DOMBA.git
cd DOMBA
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with production settings
# Ensure DATABASE_URL matches new PostgreSQL connection

# 5. Run auto-initialization
python app.py
# Wait for messages:
# [INIT] Starting database initialization...
# [INIT] ✓ Database created/verified
# App will exit after init

# 6. Restore from backup file
# Copy backup file to server
scp backup_domba_20260414_120000.sql user@newserver:/tmp/

# Or upload via UI once app is running

# 7. Start application
python app.py
# Login to /admin/backup
# Upload the backup file
# Click "Restore" to recover data

# 8. Verify restoration
# Check data integrity
# Run transactions to confirm
# Test all critical features
```

---

## Troubleshooting

### Issue: Backup creation fails with "pg_dump: command not found"

**Cause:** PostgreSQL client tools not installed

**Solution:**
```bash
# Linux (Ubuntu/Debian)
sudo apt install postgresql-client

# Linux (CentOS/RHEL)
sudo yum install postgresql

# macOS
brew install postgresql

# Windows: Include PostgreSQL in PATH or install postgres client tools
```

### Issue: "Connection refused" when creating backup

**Cause:** PostgreSQL database unreachable

**Check:**
```bash
# Test connection
psql -U domba_user -h localhost -d domba_db

# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Verify DATABASE_URL in .env
```

### Issue: Backup file is deleted but still appears in history

**Cause:** Log record wasn't deleted

**Solution:**
```python
# From Flask shell
from app.models import BackupLog
from app.extensions import db

# Delete orphaned log records
orphaned = BackupLog.query.filter(
    BackupLog.file_path.notlike('%.sql'),
    BackupLog.file_path.notlike('%.bak')
).delete()

db.session.commit()
```

### Issue: Scheduled backup doesn't run

**Cause:** Scheduler not started or job misconfigured

**Check:**
1. Verify APScheduler is imported in `app/extensions.py`
2. Check app startup output for: `[SCHEDULER] ✓ Background scheduler started`
3. Verify schedule is enabled in UI
4. Check backup schedule has at least one day selected

**Debug:**
```python
# From Flask shell
from app.extensions import scheduler

# List jobs
for job in scheduler.get_jobs():
    print(f"Job: {job.name}, Next run: {job.next_run_time}")
```

### Issue: Restore fails with permission error

**Cause:** File permissions or directory issues

**Solution:**
```bash
# Check backup directory permissions
ls -la ./backups

# Fix permissions if needed
chmod 755 ./backups
chown www-data:www-data ./backups
```

### Issue: Database auto-initialization doesn't trigger

**Cause:** Database already exists but tables missing

**Solution:**
```bash
# Manual initialization
flask init-backup-db

# Or delete database and restart
psql -U postgres
DROP DATABASE domba_db;
\q

# Restart app - it will auto-recreate
python app.py
```

---

## Security Considerations

### 1. Credential Management

**Best Practice:**
- Never commit .env to git
- Use environment variables in production
- Rotate database passwords regularly
- Use .env with restricted file permissions

**Implementation:**
```bash
# Restrict .env to owner only
chmod 600 .env

# In .gitignore
.env
*.bak
```

### 2. Access Control

**Current:**
- All backup endpoints require `@admin_required` decorator
- Only admin_dinas role can access `/admin/backup`

**Audit Trail:**
- Every operation logged with user ID
- BackupLog tracks who performed operation

### 3. Backup File Protection

**Recommendations:**
- Store backups on separate disk with encryption at rest
- Use backup encryption for sensitive data (future feature)
- Restrict file permissions: `chmod 600 backup_files`
- Regularly transfer backups to secure offsite location

### 4. SQL Injection Prevention

**Implemented:**
- All SQL executed via subprocess (not ORM injection risk)
- File paths validated and sanitized
- User input validated before execution

### 5. Database Credentials

**Handling:**
- Credentials read from DATABASE_URL or individual env vars
- PGPASSWORD passed via environment to subprocess (not command line)
- Never logs credentials in backup files

---

## Performance & Optimization

### Backup Performance

**Factors Affecting Speed:**
- Database size (linear)
- Disk I/O performance
- Network latency (if remote PostgreSQL)
- System load/other processes

**Optimization Tips:**

1. **For Large Databases (>500MB):**
   ```ini
   # Use binary format (more efficient)
   BACKUP_FORMAT=binary
   
   # Schedule during low-traffic hours
   EXECUTION_TIME=03:00  # 3:00 AM
   ```

2. **Increase Timeout if Needed:**
   ```python
   # In backup_service.py, increase timeout:
   timeout=7200  # 2 hours instead of 1 hour
   ```

3. **Parallel Backup (Future Enhancement):**
   - Consider `pg_dump -j` for parallel jobs
   - Requires PostgreSQL 10+

### Storage Optimization

**Retention Strategy:**
- Daily backups × 7 days = 7 daily backups
- Weekly backups × 4 weeks = 4 weekly backups  
- Monthly backups × 12 months = 12 monthly backups
- **Configuration**: Set retention_days accordingly

**Compression (Future):**
```python
# Could add gzip compression
import gzip
with open(backup_path, 'rb') as f_in:
    with gzip.open(backup_path + '.gz', 'wb') as f_out:
        f_out.write(f_in.read())
```

### Cleanup Performance

**Retention cleanup runs:**
- During scheduled backup execution
- Can take time for many old files

**Monitor:**
```bash
# Check backup directory
du -sh ./backups
ls -lah ./backups | wc -l  # Count files
```

---

## Maintenance Checklist

### Weekly
- [ ] Verify latest backup status in UI
- [ ] Check backup file sizes normal
- [ ] No "FAILED" backups in log

### Monthly
- [ ] Test restore operation on test database
- [ ] Verify backup file integ integrity
- [ ] Review backup schedule if needed
- [ ] Check disk space usage

### Quarterly
- [ ] Full disaster recovery drill
- [ ] Review retention policy
- [ ] Update documentation if changed
- [ ] Audit backup access logs

### Annually
- [ ] Review backup strategy vs. business needs
- [ ] Test multi-year retention
- [ ] Update disaster recovery plan
- [ ] Performance benchmarking

---

## Future Enhancements

1. **Email Notifications**: Alert on backup success/failure
2. **Incremental Backups**: Reduce storage by backing up changes only
3. **Cloud Storage Integration**: Auto-upload to S3/Google Cloud
4. **Backup Encryption**: Encrypt sensitive backup files  
5. **Point-in-Time Recovery**: Restore to specific timestamp
6. **Parallel Backups**: Use multiple workers for large databases
7. **Backup Tagging**: Label and organize backups by type
8. **Metrics Dashboard**: Backup success rate, avg time, storage usage

---

## Support & Contact

For issues or questions:
- Check [Troubleshooting](#troubleshooting) section
- Review application logs: `app logs tail -f`
- Contact: admin@disdukcapil-garut.go.id

---

## Appendix: Database Models

### Full Schema

```sql
-- BackupSchedule Table
CREATE TABLE backup_schedule (
    id SERIAL PRIMARY KEY,
    enabled BOOLEAN DEFAULT false,
    days_of_week VARCHAR(50) DEFAULT '[0]',
    execution_time VARCHAR(8) DEFAULT '02:00',
    backup_format VARCHAR(20) DEFAULT 'sql',
    retention_days INTEGER DEFAULT 30,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by_id INTEGER REFERENCES "user"(id)
);

-- BackupLog Table
CREATE TABLE backup_log (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_size BIGINT DEFAULT 0,
    file_path VARCHAR(512) NOT NULL,
    backup_type VARCHAR(20) DEFAULT 'sql',
    status VARCHAR(20) DEFAULT 'SUCCESS',
    operation VARCHAR(20) DEFAULT 'BACKUP',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by_id INTEGER REFERENCES "user"(id)
);

-- Indices for performance
CREATE INDEX idx_backup_log_created_at ON backup_log(created_at DESC);
CREATE INDEX idx_backup_log_status ON backup_log(status);
CREATE INDEX idx_backup_schedule_enabled ON backup_schedule(enabled);
```

---

**End of Documentation**
