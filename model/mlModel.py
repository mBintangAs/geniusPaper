from datetime import datetime
from model import db  # Import db dari model/__init__.py


class MLModel(db.Model):
    __tablename__ = 'ml_models'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Nama model
    version = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    deployed_at = db.Column(db.DateTime, default=datetime.utcnow)