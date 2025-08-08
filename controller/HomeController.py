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
import joblib
from tensorflow.keras.models import load_model
from skimage.io import imread
from skimage.feature import graycomatrix, graycoprops
import numpy as np

UPLOAD_FOLDER = 'static/uploads'  # Pastikan folder ini ada
ALLOWED_MIMETYPES = {'application/pdf', 'image/jpeg', 'image/png','image/jpg'}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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
            file_path=save_path.replace("static/", "", 1),
        )
        db.session.add(document)
        db.session.commit()
        if ext.lower() == '.pdf':
            images = convert_from_path(save_path, dpi=300)
            for i, image in enumerate(images):
                img_filename = f"{uuid.uuid4().hex}_page{i+1}.jpg"
                img_path = os.path.join(UPLOAD_FOLDER, img_filename)
                image.save(img_path)
                
                image_doc = ImageDocument(
                    document_id=document.id,
                    filename=img_filename,
                    file_path=img_path.replace("static/", "", 1)
                )
                db.session.add(image_doc)
                db.session.commit()
                predict_image(image_doc.id)
        else:
            image_doc = ImageDocument(
                document_id=document.id,
                filename=safe_filename,
                file_path=save_path.replace("static/", "", 1)
            )
            db.session.add(image_doc)
            db.session.commit()
            predict_image(image_doc.id)

        return True, "File berhasil diupload dan disimpan."
    except Exception as e:
        if os.path.exists(save_path):
            os.remove(save_path)
        db.session.rollback()
        return False, f"Terjadi kesalahan: {str(e)}"
    
def predict_image(image_document_id):
    try : 
    # Ambil image_document berdasarkan ID
        image_document = ImageDocument.query.get(image_document_id)
        if not image_document:
            return False, "Image document tidak ditemukan."
        
        scaler_path = os.path.join(BASE_DIR, '..', 'scaler_glcm.pkl')
        model_path = os.path.join(BASE_DIR, '..', 'model_ann_autentikasi.keras')

        scaler = joblib.load(os.path.abspath(scaler_path))
        model = load_model(os.path.abspath(model_path))
        # Ekstrak fitur
        fitur_uji = ekstrak_glcm_fitur(image_document.file_path)
        fitur_uji_scaled = scaler.transform([fitur_uji])

        # Prediksi
        prediksi = model.predict(fitur_uji_scaled)[0][0]
        print(f"Prediksi: {prediksi}")


        #  kenapa di bawah 0.5 asli, karena label 0 itu asli dan 1 itu palsu
        # jika prediksi mendekati angka 0 maka dia asli,
        # dan sebaliknya jika dia menjauhi 0 atau mendekati 1 maka dia palsu
        if prediksi < 0.5:
            print(f"✅ Prediksi: ASLI ({(1-prediksi)*100:.2f}% yakin)")
            result = "asli"  # atau "palsu"
            confidence = (1-prediksi)  # Contoh nilai confidence
        else:
            print(f"❌ Prediksi: PALSU ({prediksi*100:.2f}% yakin)")
            result = "palsu"  # atau "palsu"
            confidence = prediksi  # Contoh nilai confidence

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
        print(f"Error during prediction: {str(e)}")
        return False, f"Terjadi kesalahan: {str(e)}"
    
def fetch_all_documents(user_id):
    try:
        documents = Document.query.filter_by(user_id=user_id).order_by(Document.created_at.desc()).all()
        return documents
    except Exception as e:
        print(f"Error fetching documents: {str(e)}")
        return []
def get_document_by_id(document_id,user_id):
    try:
        document = Document.query.filter_by(user_id=user_id, id=document_id).first()
        return document
    except Exception as e:
        print(f"Error fetching document by ID: {str(e)}")
        return None



def ekstrak_glcm_fitur(image_path):
    if not image_path.startswith('static/'):
        image_path = os.path.join('static', image_path)
    img = imread(image_path, as_gray=True)
    img = (img * 255).astype('uint8')
    glcm = graycomatrix(img, distances=[1], angles=[0], levels=256, symmetric=True, normed=True)
    features = [
        graycoprops(glcm, 'contrast')[0, 0],
        graycoprops(glcm, 'dissimilarity')[0, 0],
        graycoprops(glcm, 'homogeneity')[0, 0],
        graycoprops(glcm, 'energy')[0, 0],
        graycoprops(glcm, 'correlation')[0, 0]
    ]
    return np.array(features)
