from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app.models import User
from app.extensions import db, limiter
from datetime import datetime, date
from app.utils import get_gmt7_time
import random
from flask import session
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=['POST'])
def login():
    logger.debug(f"Login attempt - Method: {request.method}, Authenticated: {current_user.is_authenticated}")

    # Check if user is already authenticated
    if current_user.is_authenticated:
        # Check if session is from current day
        login_date = session.get('login_date')
        today = get_gmt7_time().date()
        logger.debug(f"User already authenticated - login_date: {login_date}, today: {today}")

        if login_date == today:
            # Session is valid, redirect to appropriate dashboard
            logger.debug(f"Session valid, redirecting to dashboard for role: {current_user.role}")
            if current_user.role == 'admin_dinas':
                return redirect(url_for('admin.dashboard'))
            elif current_user.role == 'operator_kecamatan':
                return redirect(url_for('operator.dashboard'))
        else:
            # Session expired, logout and continue to login
            logger.debug("Session expired, logging out user")
            logout_user()
            flash('Sesi Anda telah berakhir. Silakan login kembali.', 'info')

    if request.method == 'POST':
        logger.debug("Processing POST login request")

        # Captcha Validation
        user_answer = request.form.get('captcha_answer', '')
        actual_answer = session.get('captcha_answer')
        logger.debug(f"Captcha validation - user_answer: {user_answer}, actual_answer: {actual_answer}")

        if actual_answer is None or str(user_answer) != str(actual_answer):
            logger.warning("Captcha validation failed")
            flash('Jawaban matematika salah. Silakan coba lagi.', 'error')
            return redirect(url_for('auth.login'))

        # Clear captcha after attempt
        session.pop('captcha_answer', None)

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        logger.debug(f"Login attempt for username: {username}")

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            logger.info(f"Password correct for user: {username}, role: {user.role}")

            # Check if password is same as username (needs change)
            if password == username:
                # Store login date in session
                session['login_date'] = get_gmt7_time().date()
                logger.debug(f"Login date stored in session: {session.get('login_date')}")
                login_user(user)
                logger.debug(f"User logged in (default password), is_authenticated: {current_user.is_authenticated}")
                flash('Password Anda masih default. Silakan ubah password untuk melanjutkan.', 'warning')
                return redirect(url_for('auth.change_password'))

            # Update last login
            user.last_login = get_gmt7_time()
            db.session.commit()

            # Store login date in session for daily expiration check
            session['login_date'] = get_gmt7_time().date()
            logger.debug(f"Login date stored in session: {session.get('login_date')}")

            login_user(user)
            logger.debug(f"User logged in, is_authenticated: {current_user.is_authenticated}")
            flash('Login berhasil! Mengalihkan ke dashboard...', 'success')

            # Redirect based on role
            if user.role == 'admin_dinas':
                logger.debug("Redirecting to admin dashboard")
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'operator_kecamatan':
                logger.debug("Redirecting to operator dashboard")
                return redirect(url_for('operator.dashboard'))
            else:
                logger.error(f"Invalid role: {user.role}")
                flash('Role tidak valid.', 'error')
        else:
            logger.warning(f"Invalid credentials for username: {username}")
            flash('Username atau password salah.', 'error')

    # Generate new captcha for GET request or failed POST
    num1 = random.randint(1, 9)
    num2 = random.randint(1, 9)
    ops = random.choice(['+', '-'])
    if ops == '+':
        result = num1 + num2
    else:
        # Ensure result is positive for simplicity
        if num1 < num2: num1, num2 = num2, num1
        result = num1 - num2

    session['captcha_question'] = f"{num1} {ops} {num2}"
    session['captcha_answer'] = result
    logger.debug(f"Generated captcha: {session['captcha_question']} = {result}")

    return render_template('auth/login.html')

@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not check_password_hash(current_user.password_hash, current_password):
            flash('Password saat ini salah.', 'error')
            return redirect(url_for('auth.change_password'))
        
        if new_password != confirm_password:
            flash('Password baru dan konfirmasi tidak cocok.', 'error')
            return redirect(url_for('auth.change_password'))
        
        if len(new_password) < 6:
            flash('Password baru minimal 6 karakter.', 'error')
            return redirect(url_for('auth.change_password'))
        
        if new_password == current_password:
            flash('Password baru tidak boleh sama dengan password saat ini.', 'error')
            return redirect(url_for('auth.change_password'))
        
        # Update password
        from werkzeug.security import generate_password_hash
        current_user.password_hash = generate_password_hash(new_password, method='pbkdf2:sha256:600000')
        db.session.commit()
        
        flash('Password berhasil diubah.', 'success')
        
        # Redirect based on role
        if current_user.role == 'admin_dinas':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'operator_kecamatan':
            return redirect(url_for('operator.dashboard'))
    
    return render_template('auth/change_password.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah logout dari sistem.', 'info')
    return redirect(url_for('auth.login'))




