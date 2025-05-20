from flask import Blueprint, render_template, request, flash, redirect, url_for
# from controller.HomeController import home_index 
from flask_login import login_required


home_bp = Blueprint('home', __name__)

@home_bp.get('/')
@login_required
def home_index():
    return render_template('home.html')
