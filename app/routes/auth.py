from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.services.auth_service import AuthService
from app.models.user import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        result = AuthService.login(email, password)
        if 'error' in result:
            return render_template('auth/login.html', error=result['error'])
        user = User.get_by_id(result['uid'])
        if not user:
            return render_template('auth/login.html', error='Account not found. Please register.')
        session['user_id'] = user['uid']
        session['email'] = user['email']
        session['role'] = user.get('role', 'guest')
        session['name'] = user.get('name', '')
        session.permanent = True
        return redirect(url_for('index'))
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        name = request.form.get('name', '').strip()
        role = request.form.get('role', 'guest')
        if len(password) < 6:
            return render_template('auth/register.html', error='Password must be at least 6 characters.')
        result = AuthService.register(email, password, {'name': name, 'role': role})
        if isinstance(result, dict) and 'error' in result:
            return render_template('auth/register.html', error=result['error'])
        session['user_id'] = result.uid
        session['email'] = result.email
        session['role'] = role
        session['name'] = name
        session.permanent = True
        return redirect(url_for('index'))
    return render_template('auth/register.html')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        result = AuthService.send_password_reset(email)
        if 'error' in result:
            return render_template('auth/forgot_password.html', error=result['error'])
        return render_template('auth/forgot_password.html', success=True)
    return render_template('auth/forgot_password.html')

@auth_bp.route('/logout')
def logout():
    AuthService.logout()
    return redirect(url_for('index'))
