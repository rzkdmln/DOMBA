from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app.models import User
from app.extensions import db, limiter
from datetime import datetime
from app.utils import get_gmt7_time
import random
from flask import session

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=['POST'])
def login():
    if request.method == 'POST':
        # Captcha Validation
        user_answer = request.form.get('captcha_answer', '')
        actual_answer = session.get('captcha_answer')
        
        if actual_answer is None or str(user_answer) != str(actual_answer):
            flash('Jawaban matematika salah. Silakan coba lagi.', 'error')
            return redirect(url_for('auth.login'))
            
        # Clear captcha after attempt
        session.pop('captcha_answer', None)

        username = request.form.get('username', '')
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            # Check if password is same as username (needs change)
            if password == username:
                login_user(user)
                flash('Password Anda masih default. Silakan ubah password untuk melanjutkan.', 'warning')
                return redirect(url_for('auth.change_password'))
            
            # Update last login
            user.last_login = get_gmt7_time()
            db.session.commit()
            
            login_user(user)
            flash('Login berhasil! Mengalihkan ke dashboard...', 'success')

            # Redirect based on role
            if user.role == 'admin_dinas':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'operator_kecamatan':
                return redirect(url_for('operator.dashboard'))
            else:
                flash('Role tidak valid.', 'error')
        else:
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




