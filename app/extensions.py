from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Inisialisasi plugin (belum di-bind ke app)
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
talisman = Talisman()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=["500 per day", "100 per hour"])
