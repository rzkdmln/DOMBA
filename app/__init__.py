from flask import Flask
from config import Config
from app.extensions import db, migrate, login_manager, talisman, csrf, limiter
import click
from flask.cli import with_appcontext

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 1. Init Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    
    # Init Talisman with CSP
    csp = {
        'default-src': [
            '\'self\'',
            '*.tile.openstreetmap.org',
            'https://*.basemaps.cartocdn.com'
        ],
        'img-src': ['\'self\'', 'data:', 'https:', '*.tile.openstreetmap.org', 'https://*.basemaps.cartocdn.com'],
        'connect-src': ['\'self\'', 'https://*.tile.openstreetmap.org', 'https://*.basemaps.cartocdn.com'],
        'script-src': [
            '\'self\'', 
            '\'unsafe-inline\'', 
            '\'unsafe-eval\''
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
        force_https=False if app.debug else True,
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

        if not User.query.filter_by(username='admin').first():
            admin_user = User()
            admin_user.username = 'admin'
            admin_user.nama_lengkap = 'Administrator Sistem'
            admin_user.password_hash = generate_password_hash('admin', method='pbkdf2:sha256:600000')
            admin_user.role = 'admin_dinas'
            db.session.add(admin_user)
            db.session.commit()
            click.echo("User admin default telah dibuat (username: admin, password: admin)")
        else:
            click.echo("User admin sudah ada.")

        # Create a sample operator for testing
        if not User.query.filter_by(username='operator').first():
            kec = Kecamatan.query.filter_by(kode_wilayah='32.05.01').first()
            if kec:
                op_user = User()
                op_user.username = 'operator'
                op_user.nama_lengkap = 'Operator Sample'
                op_user.password_hash = generate_password_hash('operator', method='pbkdf2:sha256:600000')
                op_user.role = 'operator_kecamatan'
                op_user.kecamatan_id = kec.id
                db.session.add(op_user)
                db.session.commit()
                click.echo("User operator default telah dibuat (username: operator, password: operator)")

    return app