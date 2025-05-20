from flask import Blueprint, render_template, request, flash, redirect, url_for
from controller.AuthController import register_user ,login_user

login_bp = Blueprint('login', __name__)

@login_bp.get('/login')
def login_index():
    return render_template('login.html')

@login_bp.get('/register')
def register_index():
    return render_template('register.html')

@login_bp.post('/register')
def register_post():
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirmation_password')
    success, message = register_user(username, password, confirm_password)
    flash(message, 'success' if success else 'error')
    if success:
        return redirect(url_for('login.login_index'))
    return redirect(url_for('login.register_index'))

@login_bp.post('/login')
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    success, message = login_user(username, password)
    flash(message, 'success' if success else 'error')
    if success:
        return redirect(url_for('home.home_index'))
    return redirect(request.referrer)
