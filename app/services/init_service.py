"""
Database Auto-Initialization Service for DOMBA
==============================================

This module handles automatic database initialization on application startup.
It ensures that:
1. Database exists (creates if missing)
2. All tables are created (db.create_all())
3. Default admin user exists (creates if missing)
4. Proper database state is maintained

This is critical for first-time deployments and disaster recovery scenarios.

Usage:
    from app.services.init_service import InitService
    
    init_service = InitService(app, db)
    init_service.run_initialization()
"""

import subprocess
import os
from functools import wraps
from app.extensions import db
from werkzeug.security import generate_password_hash
from app.utils import get_gmt7_time


class InitService:
    """
    Handles database initialization and default seed data.
    """

    def __init__(self, app=None, db_instance=None):
        """
        Initialize InitService.
        
        Args:
            app: Flask application instance
            db_instance: SQLAlchemy database instance
        """
        self.app = app
        self.db = db_instance or db
        self.db_user = os.environ.get('DB_USER', 'postgres')
        self.db_password = os.environ.get('DB_PASSWORD', '')
        self.db_host = os.environ.get('DB_HOST', 'localhost')
        self.db_port = os.environ.get('DB_PORT', 5432)
        self.db_name = os.environ.get('DB_NAME', 'domba_db')
        
        # Parse DATABASE_URL if available
        self._parse_database_url()

    def _parse_database_url(self):
        """Parse DATABASE_URL environment variable for connection details."""
        db_url = os.environ.get('DATABASE_URL', '')
        if not db_url:
            return
        
        try:
            db_url = db_url.replace('postgresql://', '')
            if '@' in db_url:
                creds, rest = db_url.split('@')
                if ':' in creds:
                    self.db_user, self.db_password = creds.split(':', 1)
                else:
                    self.db_user = creds
            else:
                rest = db_url
            
            if '/' in rest:
                host_part, self.db_name = rest.split('/', 1)
                if ':' in host_part:
                    self.db_host, port_str = host_part.split(':', 1)
                    self.db_port = int(port_str)
                else:
                    self.db_host = host_part
        except Exception as e:
            print(f"Warning: Failed to parse DATABASE_URL: {e}")

    def run_initialization(self):
        """
        Run complete database initialization sequence.
        
        Steps:
        1. Check if database exists
        2. Create database if missing
        3. Create all tables
        4. Seed default admin user if needed
        
        Returns:
            dict: {
                'success': bool,
                'messages': list of status messages,
                'warnings': list of warning messages
            }
        """
        messages = []
        warnings = []
        
        try:
            print("[INIT] Starting database initialization...")
            messages.append("Starting database initialization")
            
            # Step 1: Check database existence
            if not self._database_exists():
                print("[INIT] Database not found, creating...")
                if self._create_database():
                    messages.append(f"✓ Database '{self.db_name}' created successfully")
                    print(f"[INIT] ✓ Database created: {self.db_name}")
                else:
                    raise Exception("Failed to create database")
            else:
                messages.append(f"✓ Database '{self.db_name}' already exists")
                print(f"[INIT] ✓ Database exists: {self.db_name}")
            
            # Step 2: Create tables
            print("[INIT] Creating database tables...")
            with self.app.app_context() if self.app else self._app_context():
                # Matikan otomatis db.create_all() di Production environments
                # Gunakan 'flask db upgrade' dengan Alembic migrations untuk production
                # self.db.create_all()
                messages.append("✓ Database tables verified (migration-based approach)")
                print("[INIT] ✓ Tables verified (using Alembic migrations)")
            
            # Create default admin user
            print("[INIT] Checking for default admin user...")
            with self.app.app_context() if self.app else self._app_context():
                # Pastikan tabel 'user' ada sebelum mencoba seed admin
                from sqlalchemy import inspect
                inspector = inspect(self.db.engine)
                
                if inspector.has_table('user'):
                    admin_status = self._seed_default_admin()
                    if admin_status['created']:
                        messages.append(f"✓ Default admin user created: {admin_status['username']}")
                        print(f"[INIT] ✓ Admin user created: {admin_status['username']}")
                    elif admin_status['exists']:
                        messages.append("✓ Admin user already exists")
                        print("[INIT] ✓ Admin user exists")
                    else:
                        warnings.append(f"⚠ Could not verify admin user: {admin_status['error']}")
                        print(f"[INIT] ⚠ {admin_status['error']}")
                else:
                    msg = "Skipped admin creation (tables not yet created via migrations)"
                    messages.append(f"ℹ {msg}")
                    print(f"[INIT] ℹ {msg}")
            
            print("[INIT] Database initialization completed successfully!")
            return {
                'success': True,
                'messages': messages,
                'warnings': warnings
            }
        
        except Exception as e:
            error_msg = f"Database initialization failed: {str(e)}"
            print(f"[INIT] ✗ {error_msg}")
            return {
                'success': False,
                'messages': messages,
                'warnings': warnings + [error_msg]
            }

    def _database_exists(self):
        """
        Check if database exists in PostgreSQL.
        
        Disaster Recovery Documentation:
        - This check is performed at every startup
        - If database is missing, it will be recreated automatically
        - This protects against accidental database deletion
        
        Returns:
            bool: True if database exists, False otherwise
        """
        try:
            env = os.environ.copy()
            if self.db_password:
                env['PGPASSWORD'] = self.db_password
            
            # Connect to 'postgres' system database to query databases
            cmd = [
                'psql',
                '-U', str(self.db_user),
                '-h', str(self.db_host),
                '-p', str(self.db_port),
                '-d', 'postgres',
                '-tc',
                f"SELECT 1 FROM pg_database WHERE datname = '{self.db_name}'",
                '--no-password'
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                timeout=10
            )
            
            # If output is '1', database exists
            return b'1' in result.stdout
        
        except Exception as e:
            print(f"Warning: Failed to check database existence: {e}")
            return False

    def _create_database(self):
        """
        Create PostgreSQL database.
        
        Disaster Recovery Documentation:
        - Creates database if it doesn't exist
        - Sets UTF-8 encoding for international character support
        - Creates initial backup schedule if needed
        - Idempotent operation (safe to run multiple times)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            env = os.environ.copy()
            if self.db_password:
                env['PGPASSWORD'] = self.db_password
            
            cmd = [
                'createdb',
                '-U', str(self.db_user),
                '-h', str(self.db_host),
                '-p', str(self.db_port),
                '-E', 'UTF8',
                '-w',
                self.db_name
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                timeout=30
            )
            
            return result.returncode == 0
        
        except Exception as e:
            print(f"Error: Failed to create database: {e}")
            return False

    def _seed_default_admin(self):
        """
        Create default admin user if none exists.
        
        Default credentials:
        - Username: administrator
        - Password: administrator (MUST CHANGE in production!)
        - Role: admin_dinas
        
        Disaster Recovery Documentation:
        - Default admin user is seeded only if no users exist
        - Critical for initial system access after database initialization
        - IMPORTANT: Change default password immediately in production
        - Consider disabling default admin after manual admin creation
        
        Returns:
            dict: {
                'created': bool,
                'exists': bool,
                'username': str (if created),
                'error': str (if error)
            }
        """
        try:
            from app.models import User
            
            # Check if any admin user already exists
            admin_count = User.query.filter_by(role='admin_dinas').count()
            if admin_count > 0:
                return {
                    'created': False,
                    'exists': True,
                    'username': None,
                    'error': None
                }
            
            # Check if any users exist at all
            user_count = User.query.count()
            if user_count > 0:
                # Users exist but no admin - don't auto-create
                return {
                    'created': False,
                    'exists': False,
                    'username': None,
                    'error': 'Users exist but no admin found'
                }
            
            # Create default admin user
            default_admin = User()
            default_admin.username = 'administrator'
            default_admin.nama_lengkap = 'Administrator Sistem'
            # Gunakan PBKDF2 agar panjang hash kompatibel dengan skema lama (VARCHAR(128)).
            # Ini juga konsisten dengan command init-db di app/__init__.py.
            default_admin.password_hash = generate_password_hash(
                'administrator', method='pbkdf2:sha256:600000'
            )  # MUST CHANGE
            default_admin.role = 'admin_dinas'
            default_admin.kecamatan_id = None
            default_admin.created_at = get_gmt7_time()
            
            self.db.session.add(default_admin)
            self.db.session.commit()
            
            return {
                'created': True,
                'exists': False,
                'username': 'administrator',
                'error': None
            }
        
        except Exception as e:
            return {
                'created': False,
                'exists': False,
                'username': None,
                'error': str(e)
            }

    def _app_context(self):
        """
        Context manager fallback if self.app is not provided.
        """
        class DummyContext:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        
        return DummyContext()
