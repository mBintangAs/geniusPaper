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
from datetime import datetime, timezone, timedelta

import numpy as np

UPLOAD_FOLDER = 'static/uploads'  # Pastikan folder ini ada
ALLOWED_MIMETYPES = {'application/pdf', 'image/jpeg', 'image/png','image/jpg'}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def log(text, level='INFO'):
    try:
        now = datetime.now(timezone.utc) + timedelta(hours=7)  # UTC+7
        log_path = os.path.abspath(os.path.join(BASE_DIR, '..', 'log.txt'))
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{now.strftime('%Y-%m-%d %H:%M:%S %z')}] {level}: {text}\n")
    except Exception:
        # Jangan lempar error logging untuk mencegah cascade failure
        pass

def allowed_file(file):
    return file and file.mimetype in ALLOWED_MIMETYPES

def upload_image(filename, file, user_id):
    if not filename or not file:
        return False, "Filename dan file harus diisi."

    if not allowed_file(file):
        return False, "Hanya file PDF, JPG, JPEG, dan PNG yang diperbolehkan."
    log(f"Memproses gambar {filename}")
     # Ambil nama asli file dari file.filename, lalu tambahkan timestamp dan ekstensi
    original_filename = secure_filename(file.filename)
    name, ext = os.path.splitext(original_filename)
    timestamp = int(time.time() * 1000)
    safe_filename = f"{name}_{timestamp}{ext}"
    save_path = os.path.join(UPLOAD_FOLDER, safe_filename)

    try:
        # Simpan file ke folder
        log(f"meyimpan file {filename} ke folder {save_path}")
        file.save(save_path)

        # Simpan metadata ke database
        document = Document(
            user_id=user_id,
            filename=secure_filename(filename),
            file_path=save_path.replace("static/", "", 1),
        )
        db.session.add(document)
        db.session.commit()
        log(f"menyimpan {filename} ke database")
        if ext.lower() == '.pdf':
            images = convert_from_path(save_path, dpi=300, poppler_path="/usr/bin")
            log(f"Konversi PDF ke image perhalaman")
            for i, image in enumerate(images):
                log(f"Memproses halaman {i+1}")
                img_filename = f"{uuid.uuid4().hex}_page{i+1}.jpg"
                img_path = os.path.join(UPLOAD_FOLDER, img_filename)
                image.save(img_path)
                log(f"Saved image: {img_path}")
                image_doc = ImageDocument(
                    document_id=document.id,
                    filename=img_filename,
                    file_path=img_path.replace("static/", "", 1)
                )
                db.session.add(image_doc)
                db.session.commit()
                predict_image2(image_doc.id)
        else:
            image_doc = ImageDocument(
                document_id=document.id,
                filename=safe_filename,
                file_path=save_path.replace("static/", "", 1)
            )
            db.session.add(image_doc)
            db.session.commit()
            log(f"Saved image document: {image_doc.file_path}")
            predict_image2(image_doc.id)

        return True, "File berhasil diupload dan disimpan."
    except Exception as e:
        # if os.path.exists(save_path):
            # os.remove(save_path)
        db.session.rollback()
        return False, f"Terjadi kesalahan: {str(e)}"
    
def predict_image(image_document_id):
    try : 
    # Ambil image_document berdasarkan ID
        image_document = ImageDocument.query.get(image_document_id)
        if not image_document:
            return False, "Image document tidak ditemukan."
        
        scaler_path = os.path.join(BASE_DIR, '..', 'scaler_glcm-30092025.pkl')
        model_path = os.path.join(BASE_DIR, '..', 'model_ann_autentikasi-30092025.keras')

        scaler = joblib.load(os.path.abspath(scaler_path))
        model = load_model(os.path.abspath(model_path))
        # Ekstrak fitur
        fitur_uji = ekstrak_glcm_fitur(image_document.file_path)
        fitur_uji_scaled = scaler.transform([fitur_uji])

        # Prediksi
        prediksi = model.predict(fitur_uji_scaled)[0][0]
        log(f"Prediksi: {prediksi}")


        #  kenapa di bawah 0.5 asli, karena label 0 itu asli dan 1 itu palsu
        # jika prediksi mendekati angka 0 maka dia asli,
        # dan sebaliknya jika dia menjauhi 0 atau mendekati 1 maka dia palsu
        if prediksi < 0.5:
            log(f"✅ Prediksi: ASLI ({(1-prediksi)*100:.2f}% yakin)")
            result = "asli"  # atau "palsu"
            confidence = (1-prediksi)  # Contoh nilai confidence
        else:
            log(f"❌ Prediksi: PALSU ({prediksi*100:.2f}% yakin)")
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
        log(f"Error during prediction: {str(e)}")
        return False, f"Terjadi kesalahan: {str(e)}"
    
def fetch_all_documents(user_id):
    try:
        documents = Document.query.filter_by(user_id=user_id).order_by(Document.created_at.desc()).all()
        return documents
    except Exception as e:
        log(f"Error fetching documents: {str(e)}")
        return []
def get_document_by_id(document_id,user_id):
    try:
        document = Document.query.filter_by(user_id=user_id, id=document_id).first()
        return document
    except Exception as e:
        log(f"Error fetching document by ID: {str(e)}")
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

from skimage.feature import graycomatrix, graycoprops, local_binary_pattern
from skimage.io import imread
import numpy as np

def ekstrak_glcm_fitur2(image):
   
    angles = [0, np.pi/4, np.pi/2, 3*np.pi/4]
    glcm = graycomatrix(image, distances=[1], angles=angles, levels=256, symmetric=True, normed=True)
    features = [
        graycoprops(glcm, 'contrast').mean(),
        graycoprops(glcm, 'dissimilarity').mean(),
        graycoprops(glcm, 'homogeneity').mean(),
        graycoprops(glcm, 'energy').mean(),
        graycoprops(glcm, 'correlation').mean()
    ]
    return features

def ekstrak_lbp_fitur(image, P=24, R=3, eps=1e-7):
    lbp = local_binary_pattern(image, P, R, method="uniform")
    (hist, _) = np.histogram(lbp.ravel(),
                             bins=np.arange(0, P + 3),
                             range=(0, P + 2))
    hist = hist.astype("float")
    hist /= (hist.sum() + eps)
    return hist



def predict_image2(image_document_id):
    try:
        # Ambil image_document berdasarkan ID
        image_document = ImageDocument.query.get(image_document_id)
        if not image_document:
            return False, "Image document tidak ditemukan."
        
        # --- PERUBAHAN 1: Path & Pemuatan Model ---
        # Scaler tidak lagi digunakan
        # Ganti dengan path ke model XGBoost .pkl Anda
        log("Load Pickle")
        model_path = os.path.join(BASE_DIR, '..', 'model_deteksi_surat_glcm_lbp.pkl')

        # Muat model XGBoost dengan joblib
        model = joblib.load(os.path.abspath(model_path))
        
        # --- PERUBAHAN 2: EKSTRAKSI FITUR GABUNGAN (GLCM + LBP) ---
        # Baca gambar sekali saja
        log(f"Ekstraksi fitur untuk gambar: {image_document.file_path}")
        img = imread(os.path.join('static', image_document.file_path), as_gray=True)
        img = (img * 255).astype('uint8')

        # Ekstrak kedua jenis fitur
        log("Ekstrak GLCM FITUR")
        fitur_glcm = ekstrak_glcm_fitur2(img)
        log("Ekstrak LBP FITUR")
        fitur_lbp = ekstrak_lbp_fitur(img)
        
        # Gabungkan keduanya menjadi satu vektor fitur
        fitur_gabungan = np.hstack([fitur_glcm, fitur_lbp])
        fitur_untuk_prediksi = fitur_gabungan.reshape(1, -1)

        # --- PERUBAHAN 3: Prediksi dengan .predict_proba() ---
        # Dapatkan probabilitas untuk setiap kelas [prob_asli, prob_palsu]
        log("Melakukan prediksi")
        prediksi_proba = model.predict_proba(fitur_untuk_prediksi)[0]
        log(f"Probabilitas prediksi: {prediksi_proba}")
        probabilitas_asli = prediksi_proba[0] # Ambil probabilitas untuk kelas 'Asli' (label 0)
        probabilitas_palsu = prediksi_proba[1] # Ambil probabilitas untuk kelas 'Palsu' (label 1)
        log(f"Probabilitas 'Asli': {probabilitas_asli:.4f}")
        log(f"Probabilitas 'Palsu': {probabilitas_palsu:.4f}")

        # --- PERUBAHAN 4: Logika disesuaikan untuk output predict_proba ---
        # Jika probabilitas 'Palsu' < 0.5, maka prediksinya adalah 'Asli'
        if probabilitas_palsu < 0.5:
            result = "asli"
            confidence = 1 - probabilitas_palsu # Keyakinan adalah probabilitas kelas 'Asli'
            log(f"✅ Prediksi: ASLI ({confidence*100:.2f}% yakin)")
        else:
            result = "palsu"
            confidence = probabilitas_palsu # Keyakinan adalah probabilitas kelas 'Palsu'
            log(f"❌ Prediksi: PALSU ({confidence*100:.2f}% yakin)")

        prediction = Prediction(
            image_document_id=image_document.id,
            result=result,
            confidence=float(confidence) # Pastikan tipe datanya float
        )
        db.session.add(prediction)
        db.session.commit()
        log("Menyimpan prediksi ke database")
        return True, "Prediksi berhasil."
    except Exception as e:
        db.session.rollback()
        log(f"Error during prediction: {str(e)}")
        return False, f"Terjadi kesalahan: {str(e)}"