from model.user import User
from model import db
import bcrypt
from flask_login import login_user as flask_login_user


def login_user(username, password):
    if not username or not password:
        return False, 'Username dan password harus diisi.'

    user = User.query.filter_by(username=username).first()
   
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')) :
        return False, 'Username atau Password salah.'

    flask_login_user(user)  # Login user, session diatur oleh flask_login
    return True, 'Login berhasil.'

def register_user(username, password, confirm_password):
    # Validasi field
    if not username or not password or not confirm_password:
        return False, 'Semua field harus diisi.'

    # Cek username unik
    if User.query.filter_by(username=username).first():
        return False, 'Username sudah terdaftar.'

    # Cek password sama
    if password != confirm_password:
        return False, 'Password dan konfirmasi tidak sama.'

    try:
        # Simpan user baru
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user = User(username=username, password=hashed_password.decode('utf-8'))
        db.session.add(user)
        db.session.commit()
        return True, 'Registrasi berhasil. Silakan login.'
    except Exception as e:
        with open("log.txt", "a") as log_file:
            log_file.write(f"Error: {str(e)}\n")
        db.session.rollback()
        return False, f'Terjadi kesalahan: {str(e)}'