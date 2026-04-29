from flask import Flask
from config import Config
from app.extensions import db, migrate, login_manager, talisman, csrf, limiter, scheduler, scheduler_started
import click
from flask.cli import with_appcontext
import os
from werkzeug.middleware.proxy_fix import ProxyFix
from whitenoise import WhiteNoise
import sys

def create_app(config_class=Config):
    app = Flask(__name__, static_url_path=config_class.STATIC_URL_PATH)
    app.config.from_object(config_class)

# Praktik Enterprise: ProxyFix harus berada di lapisan terluar
    if not app.debug:
        import os
        static_root = os.path.join(os.path.dirname(__file__), 'static')
        
        # 1. Bungkus dengan WhiteNoise dulu
        app.wsgi_app = WhiteNoise(app.wsgi_app, root=static_root, prefix='static/', index_file=False)
        
        # 2. TERAKHIR bungkus dengan ProxyFix agar bisa membaca header 'https' dari Nginx
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=1, 
            x_proto=1, 
            x_host=1, 
            x_port=1,
            x_prefix=1
        )

    # 1. Init Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    
# Init Talisman with CSP (Updated for Cloudflare Insights)
    csp = {
        'default-src': [
            '\'self\'',
            '*.tile.openstreetmap.org',
            'https://*.basemaps.cartocdn.com'
        ],
        'img-src': ['\'self\'', 'data:', 'https:', '*.tile.openstreetmap.org', 'https://*.basemaps.cartocdn.com'],
        'connect-src': [
            '\'self\'', 
            'https://*.tile.openstreetmap.org', 
            'https://*.basemaps.cartocdn.com',
            'https://cloudflareinsights.com',      # Diperlukan untuk mengirim data analitik
            'https://static.cloudflareinsights.com'
        ],
        'script-src': [
            '\'self\'', 
            '\'unsafe-inline\'', 
            '\'unsafe-eval\'',
            'https://static.cloudflareinsights.com' # Mengizinkan pemuatan skrip beacon.min.js
        ],
        'style-src': [
            '\'self\'', 
            '\'unsafe-inline\''
        ],
        'font-src': ['\'self\'', 'data:'],
    }
    talisman.init_app(
        app, 
        content_security_policy=csp, 
        force_https=False,
        permissions_policy={
            'geolocation': 'self'
        }
    )
    
    # Konfigurasi Login Manager (Nanti dipakai di Tahap 2 & 3)
    login_manager.login_view = 'auth.login'  # type: ignore
    login_manager.login_message = 'Silakan login untuk mengakses halaman ini.'
    login_manager.login_message_category = 'warning'

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # Session expiration check before each request
    @app.before_request
    def check_session_expiration():
        from flask_login import current_user
        from flask import session, redirect, url_for, request
        from app.utils import get_gmt7_time

        # Skip check for login page and static files
        if request.path.startswith('/static') or request.path == '/auth/login':
            return

        # Check if user is authenticated
        if current_user.is_authenticated:
            login_date = session.get('login_date')
            today = get_gmt7_time().date()

            # If login date is different from today, logout user
            if login_date and login_date != today:
                from flask_login import logout_user
                logout_user()
                session.clear()
                return redirect(url_for('auth.login'))

    # 2. Register Blueprints (Routes)
    # Kita import di dalam fungsi untuk menghindari Circular Import
    from app.routes.public_routes import public_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.ops_routes import ops_bp

    app.register_blueprint(public_bp) # URL: /
    app.register_blueprint(auth_bp, url_prefix='/auth') # URL: /auth/login
    app.register_blueprint(admin_bp, url_prefix='/admin') # URL: /admin/dashboard
    app.register_blueprint(ops_bp, url_prefix='/operator') # URL: /operator/dashboard

    # 2.5 Register Jinja2 custom filters for templates
    import json
    app.jinja_env.filters['fromjson'] = lambda x: json.loads(x) if isinstance(x, str) else x

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        from flask import render_template
        return render_template('errors/500.html'), 500

    @app.errorhandler(429)
    def ratelimit_handler(e):
        from flask import render_template
        return render_template('errors/429.html'), 429

    # Favicon route to handle browser requests
    @app.route('/favicon.ico')
    def favicon():
        from flask import Response
        svg_favicon = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">🏛️</text></svg>'''
        return Response(svg_favicon, mimetype='image/svg+xml')

    # Register CLI command
    @app.cli.command("init-db")
    @with_appcontext
    def init_db_command():
        """Membersihkan data lama dan membuat tabel baru."""
        click.echo("Menghapus tabel lama...")
        # Gunakan Flask-SQLAlchemy drop_all() yang lebih portable
        db.drop_all()
        
        from app.models import Kecamatan, User, Stok, Transaksi, DetailCetak
        db.create_all()
        click.echo("Selesai! Tabel berhasil dibuat.")

        # Create default kecamatan/locations
        from app.models import Kecamatan, Stok
        if not Kecamatan.query.filter_by(kode_wilayah='32.05.00').first():
            dinas = Kecamatan(nama_kecamatan='Dinas', kode_wilayah='32.05.00')
            db.session.add(dinas)
            db.session.flush() # Get ID
            db.session.add(Stok(kecamatan_id=dinas.id, jumlah_ktp=0)) # Saldo awal dinas
            
            # Sample Kecamatan
            kec1 = Kecamatan(nama_kecamatan='Kecamatan Garut Kota', kode_wilayah='32.05.01')
            kec2 = Kecamatan(nama_kecamatan='Kecamatan Tarogong Kidul', kode_wilayah='32.05.02')
            db.session.add_all([kec1, kec2])
            db.session.commit()
            
            # Add Stok for each
            db.session.add(Stok(kecamatan_id=kec1.id, jumlah_ktp=0))
            db.session.add(Stok(kecamatan_id=kec2.id, jumlah_ktp=0))
            db.session.commit()
            click.echo("Data wilayah awal berhasil dibuat.")

        # Create default admin user
        from app.models import User
        from werkzeug.security import generate_password_hash

        if not User.query.filter_by(username='administrator').first():
            admin_user = User()
            admin_user.username = 'administrator'
            admin_user.nama_lengkap = 'Administrator Sistem'
            admin_user.password_hash = generate_password_hash('administrator', method='pbkdf2:sha256:600000')
            admin_user.role = 'admin_dinas'
            db.session.add(admin_user)
            db.session.commit()

    # CLI command: Manual trigger for backup
    @app.cli.command("backup-now")
    @with_appcontext
    def backup_now_command():
        """Trigger manual database backup immediately."""
        from app.services.backup_service import BackupService
        
        click.echo("Starting manual backup...")
        service = BackupService()
        result = service.backup_database(format='sql')
        
        if result['success']:
            click.echo(f"✓ Backup successful: {result['filename']}")
            click.echo(f"  File size: {result['message']}")
        else:
            click.echo(f"✗ Backup failed: {result['error']}")

    # CLI command: Test database connectivity
    @app.cli.command("test-db-connection")
    @with_appcontext
    def test_db_connection():
        """Test database connection and credentials."""
        try:
            from sqlalchemy import text
            result = db.session.execute(text("SELECT 1"))
            click.echo("✓ Database connection successful")
        except Exception as e:
            click.echo(f"✗ Database connection failed: {e}")

    # CLI command: Initialize database
    @app.cli.command("init-backup-db")
    @with_appcontext
    def init_backup_db():
        """Initialize backup-related tables (BackupSchedule, BackupLog)."""
        try:
            db.create_all()
            click.echo("✓ Backup tables initialized")
        except Exception as e:
            click.echo(f"✗ Failed to initialize backup tables: {e}")

    # 3. Initialize Scheduler for automated backups
    def _init_scheduler():
        """Initialize and start the APScheduler for backup tasks."""
        global scheduler_started
        
        if scheduler_started:
            return
        
        try:
            # Configure scheduler
            from apscheduler.executors.pool import ThreadPoolExecutor
            executors = {
                'default': ThreadPoolExecutor(max_workers=2)
            }
            
            job_defaults = {
                'coalesce': True,
                'max_instances': 1
            }
            
            scheduler.configure(
                executors=executors,
                job_defaults=job_defaults,
                timezone='Asia/Jakarta'
            )
            
            # Register backup job from schedule if enabled
            def _register_backup_jobs():
                from app.models import BackupSchedule
                from .routes.admin_routes import _scheduled_backup_task
                
                # Remove existing jobs
                for job in scheduler.get_jobs():
                    if job.name == 'scheduled_backup':
                        scheduler.remove_job(job.id)
                
                # Check if any schedule is enabled
                with app.app_context():
                    schedule = BackupSchedule.query.first()
                    if schedule and schedule.enabled:
                        import json
                        from datetime import datetime
                        
                        # Parse execution time (HH:MM format)
                        try:
                            hour, minute = schedule.execution_time.split(':')
                            hour, minute = int(hour), int(minute)
                        except:
                            hour, minute = 2, 0  # Default to 2:00 AM
                        
                        # Parse days of week (JSON array)
                        try:
                            days = json.loads(schedule.days_of_week)
                        except:
                            days = [0]  # Default to Senin
                        
                        # Add cron trigger for each day
                        day_names = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
                        triggered_days = [day_names[d] for d in days if 0 <= d < 7]
                        
                        if triggered_days:
                            from apscheduler.triggers.cron import CronTrigger
                            trigger = CronTrigger(
                                day_of_week=','.join(triggered_days),
                                hour=hour,
                                minute=minute,
                                timezone='Asia/Jakarta'
                            )
                            
                            scheduler.add_job(
                                _scheduled_backup_task,
                                trigger=trigger,
                                id='scheduled_backup',
                                name='scheduled_backup',
                                replace_existing=True
                            )
                            
                            print(f"[SCHEDULER] ✓ Backup job scheduled for {','.join(triggered_days)} at {hour:02d}:{minute:02d}")
            
            # Start scheduler
            if not scheduler.running:
                scheduler.start()
                scheduler_started = True
                
                # Register jobs after scheduler starts
                _register_backup_jobs()
                
                print("[SCHEDULER] ✓ Background scheduler started for automated backups")
        
        except Exception as e:
            print(f"[SCHEDULER] Warning: Failed to initialize scheduler: {e}")

    def _is_flask_db_command() -> bool:
        # Saat menjalankan perintah migrasi (mis. `flask db upgrade`), Flask akan tetap memanggil
        # create_app(). Auto-initialization (seed/create/cek DB) bisa mengubah skema terlebih dulu
        # sehingga migrasi gagal (mis. DuplicateColumn). Karena itu, kita skip di mode CLI migrasi.
        return len(sys.argv) >= 2 and sys.argv[1] == 'db'

    # 4. Auto-initialization on startup (Disaster Recovery Protection)
    if not _is_flask_db_command():
        with app.app_context():
            try:
                from app.services.init_service import InitService
                print("\n" + "="*70)
                print("DOMBA Application Startup")
                print("="*70)
                
                init_service = InitService(app, db)
                init_result = init_service.run_initialization()
                
                for msg in init_result['messages']:
                    print(f"  {msg}")
                
                if init_result['warnings']:
                    for warn in init_result['warnings']:
                        print(f"  {warn}")
                
                print("="*70 + "\n")
                
                # Initialize scheduler for automated backups
                _init_scheduler()
            
            except Exception as e:
                print(f"Warning during auto-initialization: {e}")

    return app