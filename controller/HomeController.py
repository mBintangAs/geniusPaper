from model.user import User
from model import db
import bcrypt
from flask_login import login_user as flask_login_user

def home_index():
    return "Welcome to the Home Page"