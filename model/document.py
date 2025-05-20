from datetime import datetime
from model import db  # Import db dari model/__init__.py

class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.Text, nullable=False)
    original_format = db.Column(db.String(50), nullable=False)
    converted_format = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relasi ke User (opsional, untuk akses user dari document)
    user = db.relationship('User', backref=db.backref('documents', lazy=True))