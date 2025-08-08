from datetime import datetime, timezone, timedelta
from model import db  # Import db dari model/__init__.py

class imageDocument(db.Model):
    __tablename__ = 'image_document'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc )+ timedelta(hours=7))


    # Relasi ke User (opsional, untuk akses user dari document)
    document = db.relationship('Document', backref=db.backref('image_document', lazy=True))