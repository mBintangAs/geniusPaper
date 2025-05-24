from model.user import User
from model import db
from model.prediction import Prediction
import bcrypt
from flask_login import login_user as flask_login_user
import os
from werkzeug.utils import secure_filename
from model.document import Document
from model.imageDocument import imageDocument as ImageDocument
from pdf2image import convert_from_path
import uuid, time


UPLOAD_FOLDER = 'static/uploads'  # Pastikan folder ini ada
ALLOWED_MIMETYPES = {'application/pdf', 'image/jpeg', 'image/png','image/jpg'}

def allowed_file(file):
    return file and file.mimetype in ALLOWED_MIMETYPES

def upload_image(filename, file, user_id):
    if not filename or not file:
        return False, "Filename dan file harus diisi."

    if not allowed_file(file):
        return False, "Hanya file PDF, JPG, JPEG, dan PNG yang diperbolehkan."

     # Ambil nama asli file dari file.filename, lalu tambahkan timestamp dan ekstensi
    original_filename = secure_filename(file.filename)
    name, ext = os.path.splitext(original_filename)
    timestamp = int(time.time() * 1000)
    safe_filename = f"{name}_{timestamp}{ext}"
    save_path = os.path.join(UPLOAD_FOLDER, safe_filename)

    try:
        # Simpan file ke fol
        # der
        file.save(save_path)

        # Simpan metadata ke database
        document = Document(
            user_id=user_id,
            filename=secure_filename(filename),
            file_path=save_path,
        )
        db.session.add(document)
        db.session.flush()  # <-- Ini akan mengisi document.id tanpa commit

        if ext.lower() == '.pdf':
            images = convert_from_path(save_path, dpi=300)
            for i, image in enumerate(images):
                img_filename = f"{uuid.uuid4().hex}_page{i+1}.jpg"
                img_path = os.path.join(UPLOAD_FOLDER, img_filename)
                image.save(img_path)
                
                image_doc = ImageDocument(
                    document_id=document.id,
                    filename=img_filename,
                    file_path=img_path
                )
                db.session.add(image_doc)
                db.session.flush()  # Agar image_doc.id terisi jika perlu
                predict_image(image_doc.id)
        else:
            image_doc = ImageDocument(
                document_id=document.id,
                filename=safe_filename,
                file_path=save_path
            )
            db.session.add(image_doc)
            db.session.flush()
            predict_image(image_doc.id)

        db.session.commit()
        return True, "File berhasil diupload dan disimpan."
    except Exception as e:
        if os.path.exists(save_path):
            os.remove(save_path)
        db.session.rollback()
        return False, f"Terjadi kesalahan: {str(e)}"
    
def predict_image(image_document_id):
    # Ambil image_document berdasarkan ID
    image_document = ImageDocument.query.get(image_document_id)
    if not image_document:
        return False, "Image document tidak ditemukan."

    # Lakukan prediksi (logika prediksi Anda di sini)
    # Misalnya, kita hanya mengembalikan hasil dummy
    result = "asli"  # atau "palsu"
    confidence = 0.95  # Contoh nilai confidence

    try:
        prediction = Prediction(
            image_document_id=image_document.id,
            result=result,
            confidence=confidence
        )
        db.session.add(prediction)
        db.session.commit()
        return True, "Prediksi berhasil."
    except Exception as e:
        db.session.rollback()
        
        return False, f"Terjadi kesalahan: {str(e)}"
    
def fetch_all_documents(user_id):
    try:
        documents = Document.query.filter_by(user_id=user_id).order_by(Document.created_at.desc()).all()
        return documents
    except Exception as e:
        print(f"Error fetching documents: {str(e)}")
        return []