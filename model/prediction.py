from datetime import datetime
from model import db  # Import db dari model/__init__.py

class Prediction(db.Model):
    __tablename__ = 'predictions'

    id = db.Column(db.Integer, primary_key=True)
    image_document_id = db.Column(db.Integer, db.ForeignKey('image_document.id'), nullable=False)
    result = db.Column(db.Enum('asli', 'palsu', name='prediction_result'), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    analyzed_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relasi ke Document (opsional)
    document = db.relationship('imageDocument', backref=db.backref('predictions', lazy=True))