from datetime import datetime,timezone,timedelta
from model import db  # Import db dari model/__init__.py


class Prediction(db.Model):
    __tablename__ = 'predictions'

    id = db.Column(db.Integer, primary_key=True)
    image_document_id = db.Column(db.Integer, db.ForeignKey('image_document.id'), nullable=False)
    result = db.Column(db.Enum('asli', 'palsu', name='prediction_result'), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    analyzed_at = db.Column(db.DateTime, default=datetime.now(timezone.utc)+ timedelta(hours=7))

    # Relasi ke Document (opsional)
    image_document = db.relationship('imageDocument', backref=db.backref('prediction', uselist=False))