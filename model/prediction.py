from datetime import datetime
from model import db  # Import db dari model/__init__.py

class Prediction(db.Model):
    __tablename__ = 'predictions'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    result = db.Column(db.Enum('asli', 'palsu', name='prediction_result'), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    model_version = db.Column(db.String(50), nullable=False)
    analyzed_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relasi ke Document (opsional)
    document = db.relationship('Document', backref=db.backref('predictions', lazy=True))