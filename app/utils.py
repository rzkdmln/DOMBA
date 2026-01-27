from datetime import datetime, timedelta
from functools import wraps
from flask import abort
from flask_login import current_user

def get_gmt7_time():
    """Returns current time in GMT+7 (Western Indonesia Time)."""
    return datetime.utcnow() + timedelta(hours=7)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin_dinas':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
