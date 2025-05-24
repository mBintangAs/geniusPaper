from flask import Flask, render_template
from model import db  # Import db dari model/__init__.py
from route.login import login_bp
from route.home import home_bp
from flask_login import LoginManager

# ...existing code...


app = Flask(__name__, template_folder="views")
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://django:root@localhost/gpaper'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.secret_key = 'INI_SECRET_KEY'

db.init_app(app)  # Inisialisasi db dengan app
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login.login_index'  # Nama endpoint login


# Import semua model setelah db diinisialisasi
from model.user import User
from model.document import Document
from model.prediction import Prediction
from model.mlModel import MLModel
from model.imageDocument import imageDocument


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.register_blueprint(login_bp)
app.register_blueprint(home_bp)

if __name__ == "__main__":
    # with app.app_context():
    #     db.drop_all()
    #     db.create_all()
    app.run(debug=True)
