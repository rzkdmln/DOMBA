"""
Backup & Restore Service for DOMBA Database
============================================

This module handles all database backup and restore operations using PostgreSQL's
pg_dump and pg_restore utilities. It supports both plain SQL and binary (custom) formats.

Key Features:
- Automatic backup creation in SQL or binary format
- Restore from backup with error handling
- File integrity verification
- Automated retention policy (delete old backups)
- Credential resolution from .env or form input
- Comprehensive error logging and audit trail

Usage:
    from app.services.backup_service import BackupService
    
    service = BackupService()
    
    # Create backup
    result = service.backup_database(format='sql')
    
    # Restore from backup
    result = service.restore_database('/backups/backup_2026_04_14_123456.sql')
"""

import subprocess
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
import re
from app.extensions import db
from app.models import BackupLog
from app.utils import get_gmt7_time


class BackupService:
    """
    Database backup and restore service using PostgreSQL native tools.
    """

    def __init__(self, db_user=None, db_password=None, db_host=None, db_port=None, db_name=None):
        """
        Initialize BackupService with database credentials.
        
        If credentials are not provided, they will be resolved from:
        1. Function parameters (highest priority)
        2. DATABASE_URL environment variable (parsed)
        3. Individual env variables: DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
        
        Args:
            db_user (str, optional): PostgreSQL username
            db_password (str, optional): PostgreSQL password
            db_host (str, optional): PostgreSQL host
            db_port (int, optional): PostgreSQL port
            db_name (str, optional): Database name
        """
        self.db_user = db_user or os.environ.get('DB_USER', 'postgres')
        self.db_password = db_password or os.environ.get('DB_PASSWORD', '')
        self.db_host = db_host or os.environ.get('DB_HOST', 'localhost')
        self.db_port = db_port or os.environ.get('DB_PORT', 5432)
        self.db_name = db_name or os.environ.get('DB_NAME', 'domba_db')
        
        # Try to parse DATABASE_URL if credentials seem incomplete
        if not all([self.db_user, self.db_password]):
            self._parse_database_url()
        
        # Backup directory path (configurable via env, defaults to ./backups)
        self.backup_dir = Path(os.environ.get('BACKUP_LOCATION', './backups'))
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def _parse_database_url(self):
        """
        Parse DATABASE_URL environment variable.
        Expected format: postgresql://user:password@host:port/dbname
        """
        db_url = os.environ.get('DATABASE_URL', '')
        if not db_url:
            return
        
        try:
            # Remove 'postgresql://' prefix
            db_url = db_url.replace('postgresql://', '')
            
            # Extract user:password
            if '@' in db_url:
                creds, rest = db_url.split('@')
                if ':' in creds:
                    self.db_user, self.db_password = creds.split(':', 1)
                else:
                    self.db_user = creds
            else:
                rest = db_url
            
            # Extract host:port/dbname
            if '/' in rest:
                host_part, self.db_name = rest.split('/', 1)
                if ':' in host_part:
                    self.db_host, port_str = host_part.split(':', 1)
                    self.db_port = int(port_str)
                else:
                    self.db_host = host_part
        except Exception as e:
            print(f"Warning: Failed to parse DATABASE_URL: {e}")

    def get_connection_string(self):
        """
        Build PGPASSWORD and connection parameters for pg_dump/pg_restore.
        
        Returns:
            tuple: (env_dict, connection_args_list)
                env_dict: Contains PGPASSWORD for subprocess
                connection_args_list: List of connection parameters for command
        """
        env = os.environ.copy()
        if self.db_password:
            env['PGPASSWORD'] = self.db_password
        
        connection_args = [
            '-U', str(self.db_user),
            '-h', str(self.db_host),
            '-p', str(self.db_port),
            '-d', str(self.db_name),
        ]
        
        return env, connection_args

    def backup_database(self, format='sql', created_by_id=None):
        """
        Create a backup of the database.
        
        Args:
            format (str): 'sql' for plain text SQL, 'binary' for custom PostgreSQL format
            created_by_id (int, optional): User ID who triggered this backup
        
        Returns:
            dict: {
                'success': bool,
                'filename': str (backup filename if success),
                'file_size': int (bytes),
                'file_path': str (absolute path to backup file),
                'message': str (status message),
                'error': str (error message if failed)
            }
        
        Disaster Recovery Documentation:
        - SQL format is human-readable and portable across PostgreSQL versions
        - Binary format is faster and more efficient for large databases
        - Always verify backup file size > 0 before considering it successful
        - Store backups in separate physical location for true DR protection
        """
        try:
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_ext = '.sql' if format == 'sql' else '.bak'
            filename = f'backup_domba_{timestamp}{file_ext}'
            file_path = self.backup_dir / filename
            
            # Build pg_dump command
            env, conn_args = self.get_connection_string()
            
            if format == 'sql':
                # Plain text SQL dump
                cmd = ['pg_dump', '-v'] + conn_args + ['--no-password']
            else:
                # Binary custom format (more efficient)
                cmd = ['pg_dump', '-Fc', '-v'] + conn_args + ['--no-password']
            
            # Execute pg_dump and write to file
            with open(file_path, 'wb') as f:
                result = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    env=env,
                    timeout=3600  # 1 hour timeout
                )
            
            # Check for errors
            if result.returncode != 0:
                error_msg = result.stderr.decode('utf-8', errors='ignore')
                self._log_backup_operation(
                    filename=filename,
                    file_path=str(file_path),
                    file_size=0,
                    backup_type=format,
                    status='FAILED',
                    operation='BACKUP',
                    error_message=f'pg_dump error: {error_msg}',
                    created_by_id=created_by_id
                )
                return {
                    'success': False,
                    'filename': filename,
                    'file_size': 0,
                    'file_path': str(file_path),
                    'message': 'Backup gagal - pg_dump error',
                    'error': error_msg
                }
            
            # Verify backup integrity (file size check)
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                os.remove(file_path)
                self._log_backup_operation(
                    filename=filename,
                    file_path=str(file_path),
                    file_size=0,
                    backup_type=format,
                    status='FAILED',
                    operation='BACKUP',
                    error_message='Backup file kosong (0 bytes)',
                    created_by_id=created_by_id
                )
                return {
                    'success': False,
                    'filename': filename,
                    'file_size': 0,
                    'file_path': str(file_path),
                    'message': 'Backup gagal - file kosong',
                    'error': 'Generated backup file is empty'
                }
            
            # Log successful backup
            self._log_backup_operation(
                filename=filename,
                file_path=str(file_path),
                file_size=file_size,
                backup_type=format,
                status='VERIFIED',
                operation='BACKUP',
                created_by_id=created_by_id
            )
            
            return {
                'success': True,
                'filename': filename,
                'file_size': file_size,
                'file_path': str(file_path),
                'message': f'Backup berhasil - {self._format_size(file_size)}',
                'error': None
            }
        
        except subprocess.TimeoutExpired:
            error_msg = 'Backup timeout (database terlalu besar) - lebih dari 1 jam'
            self._log_backup_operation(
                filename=filename,
                file_path=str(file_path),
                file_size=0,
                backup_type=format,
                status='FAILED',
                operation='BACKUP',
                error_message=error_msg,
                created_by_id=created_by_id
            )
            return {
                'success': False,
                'filename': filename,
                'file_size': 0,
                'file_path': str(file_path),
                'message': 'Backup timeout',
                'error': error_msg
            }
        
        except Exception as e:
            error_msg = str(e)
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
            
            self._log_backup_operation(
                filename=filename,
                file_path=str(file_path),
                file_size=0,
                backup_type=format,
                status='FAILED',
                operation='BACKUP',
                error_message=error_msg,
                created_by_id=created_by_id
            )
            
            return {
                'success': False,
                'filename': filename,
                'file_size': 0,
                'file_path': str(file_path),
                'message': 'Backup gagal - exception occurred',
                'error': error_msg
            }

    def restore_database(self, file_path, created_by_id=None):
        """
        Restore database from a backup file.
        
        Warning: This operation will overwrite the current database!
        Always confirm with user before executing.
        
        Args:
            file_path (str): Path to backup file (.sql or .bak)
            created_by_id (int, optional): User ID who triggered this restore
        
        Returns:
            dict: {
                'success': bool,
                'message': str,
                'error': str (if failed)
            }
        
        Disaster Recovery Documentation:
        - Restore operations are destructive and irreversible
        - Always backup current database before restore
        - Verify backup file integrity before attempting restore
        - Consider restoration during maintenance window
        - Monitor application after restore for inconsistencies
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                self._log_backup_operation(
                    filename=file_path.name,
                    file_path=str(file_path),
                    file_size=0,
                    backup_type='unknown',
                    status='FAILED',
                    operation='RESTORE',
                    error_message=f'Backup file tidak ditemukan: {file_path}',
                    created_by_id=created_by_id
                )
                return {
                    'success': False,
                    'message': 'File backup tidak ditemukan',
                    'error': f'Path: {file_path}'
                }
            
            # Determine format from file extension
            if file_path.suffix.lower() == '.bak':
                is_binary = True
                format_flag = '-Fc'
            else:
                is_binary = False
                format_flag = None
            
            # Build pg_restore command
            env, conn_args = self.get_connection_string()
            
            if is_binary:
                cmd = ['pg_restore'] + conn_args + [format_flag, str(file_path), '--no-password']
            else:
                # For SQL format, use psql instead of pg_restore
                cmd = ['psql'] + conn_args + ['-f', str(file_path), '--no-password']
            
            # Execute restore
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.decode('utf-8', errors='ignore')
                self._log_backup_operation(
                    filename=file_path.name,
                    file_path=str(file_path),
                    file_size=file_path.stat().st_size,
                    backup_type='binary' if is_binary else 'sql',
                    status='FAILED',
                    operation='RESTORE',
                    error_message=f'pg_restore error: {error_msg}',
                    created_by_id=created_by_id
                )
                return {
                    'success': False,
                    'message': 'Restore gagal - lihat error log',
                    'error': error_msg
                }
            
            # Log successful restore
            self._log_backup_operation(
                filename=file_path.name,
                file_path=str(file_path),
                file_size=file_path.stat().st_size,
                backup_type='binary' if is_binary else 'sql',
                status='SUCCESS',
                operation='RESTORE',
                created_by_id=created_by_id
            )
            
            return {
                'success': True,
                'message': f'Restore berhasil dari {file_path.name}',
                'error': None
            }
        
        except subprocess.TimeoutExpired:
            error_msg = 'Restore timeout - restoration took more than 1 hour'
            self._log_backup_operation(
                filename=file_path.name,
                file_path=str(file_path),
                file_size=0,
                backup_type='unknown',
                status='FAILED',
                operation='RESTORE',
                error_message=error_msg,
                created_by_id=created_by_id
            )
            return {
                'success': False,
                'message': 'Restore timeout',
                'error': error_msg
            }
        
        except Exception as e:
            error_msg = str(e)
            self._log_backup_operation(
                filename=file_path.name,
                file_path=str(file_path),
                file_size=0,
                backup_type='unknown',
                status='FAILED',
                operation='RESTORE',
                error_message=error_msg,
                created_by_id=created_by_id
            )
            return {
                'success': False,
                'message': 'Restore gagal - exception occurred',
                'error': error_msg
            }

    def verify_backup(self, file_path):
        """
        Verify the integrity of a backup file.
        
        For SQL files: Checks file size > 0 and contains SQL syntax
        For binary files: Checks file header and validity
        
        Args:
            file_path (str): Path to backup file
        
        Returns:
            dict: {
                'valid': bool,
                'message': str,
                'file_size': int
            }
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return {
                    'valid': False,
                    'message': 'File tidak ditemukan',
                    'file_size': 0
                }
            
            file_size = file_path.stat().st_size
            
            if file_size == 0:
                return {
                    'valid': False,
                    'message': 'File backup kosong (0 bytes)',
                    'file_size': 0
                }
            
            # Check file header for magic bytes (basic validation)
            with open(file_path, 'rb') as f:
                header = f.read(20)
            
            # Binary format has specific magic bytes
            if file_path.suffix.lower() == '.bak':
                if not header.startswith(b'PGDMP'):
                    return {
                        'valid': False,
                        'message': 'File bukan PostgreSQL custom format backup yang valid',
                        'file_size': file_size
                    }
            else:
                # SQL files should start with valid SQL comments or commands
                if not (header.startswith(b'--') or header.startswith(b'/*') or header.startswith(b'CREATE') or header.startswith(b'INSERT') or header.startswith(b'SELECT')):
                    return {
                        'valid': False,
                        'message': 'File tidak terlihat seperti backup SQL yang valid',
                        'file_size': file_size
                    }
            
            return {
                'valid': True,
                'message': f'Backup valid - ukuran {self._format_size(file_size)}',
                'file_size': file_size
            }
        
        except Exception as e:
            return {
                'valid': False,
                'message': f'Verification error: {str(e)}',
                'file_size': 0
            }

    def cleanup_old_backups(self, retention_days=30):
        """
        Delete backup files older than retention_days.
        
        This implements the retention policy for automated cleanup.
        Only deletes files that have corresponding BackupLog records.
        
        Args:
            retention_days (int): Delete backups older than this many days
        
        Returns:
            dict: {
                'success': bool,
                'deleted_count': int,
                'freed_space': int (bytes),
                'message': str
            }
        
        Disaster Recovery Documentation:
        - Retention policy balances storage cost vs. recovery granularity
        - Default 30 days typically satisfies business continuity requirements
        - Adjust based on storage capacity and organizational policies
        - Keep at least 1 backup at all times (never delete last backup)
        """
        try:
            cutoff_date = get_gmt7_time() - timedelta(days=retention_days)
            
            # Find old backup records
            old_backups = BackupLog.query.filter(
                BackupLog.created_at < cutoff_date,
                BackupLog.operation == 'BACKUP'
            ).all()
            
            deleted_count = 0
            freed_space = 0
            failed_deletions = []
            
            for backup in old_backups:
                try:
                    file_path = Path(backup.file_path)
                    if file_path.exists():
                        freed_space += file_path.stat().st_size
                        file_path.unlink()  # Delete file
                        deleted_count += 1
                    
                    # Delete log record
                    db.session.delete(backup)
                    db.session.commit()
                
                except Exception as e:
                    failed_deletions.append(f"{backup.filename}: {str(e)}")
            
            message = f'Deleted {deleted_count} old backup(s), freed {self._format_size(freed_space)}'
            if failed_deletions:
                message += f'. Failed: {len(failed_deletions)}'
            
            return {
                'success': len(failed_deletions) == 0,
                'deleted_count': deleted_count,
                'freed_space': freed_space,
                'message': message,
                'failed_deletions': failed_deletions
            }
        
        except Exception as e:
            return {
                'success': False,
                'deleted_count': 0,
                'freed_space': 0,
                'message': f'Cleanup error: {str(e)}',
                'failed_deletions': [str(e)]
            }

    def list_backups(self, limit=50):
        """
        Get list of available backups sorted by date (newest first).
        
        Args:
            limit (int): Maximum number of backups to return
        
        Returns:
            list: List of BackupLog objects
        """
        return BackupLog.query.filter(
            BackupLog.operation == 'BACKUP',
            BackupLog.status.in_(['SUCCESS', 'VERIFIED'])
        ).order_by(BackupLog.created_at.desc()).limit(limit).all()

    def _log_backup_operation(self, filename, file_path, file_size, backup_type, status, operation, error_message=None, created_by_id=None):
        """
        Log backup operation to database audit trail.
        
        Args:
            filename (str): Backup filename
            file_path (str): Full path to backup file
            file_size (int): File size in bytes
            backup_type (str): 'sql' or 'binary'
            status (str): 'SUCCESS', 'FAILED', 'VERIFIED', 'CORRUPTED'
            operation (str): 'BACKUP', 'RESTORE', 'MANUAL', 'SCHEDULED'
            error_message (str, optional): Error details if failed
            created_by_id (int, optional): User ID who triggered operation
        """
        try:
            log_entry = BackupLog(
                filename=filename,
                file_path=file_path,
                file_size=file_size,
                backup_type=backup_type,
                status=status,
                operation=operation,
                error_message=error_message,
                created_by_id=created_by_id
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            print(f"Warning: Failed to log backup operation: {e}")

    @staticmethod
    def _format_size(bytes_size):
        """Convert bytes to human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} TB"
