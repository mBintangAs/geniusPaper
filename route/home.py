from flask import Blueprint, render_template, request, flash, redirect, url_for
# from controller.HomeController import home_index 
from flask_login import login_required
from controller.HomeController import upload_image,fetch_all_documents,get_document_by_id
from flask_login import current_user
from flask import jsonify


home_bp = Blueprint('home', __name__)

@home_bp.get('/')
@login_required
def home_index():
    doc_id = request.args.get('doc_id')
    if doc_id:
        print(f"Fetching document with ID: {doc_id}")
        # Fetch the document by ID
        document = get_document_by_id(doc_id, current_user.id)
    data = fetch_all_documents(current_user.id)
    return render_template('home.html', documents=data, user=current_user,document=document if doc_id else None)

@home_bp.post('/')
@login_required
def home_post():
    filename = request.form.get('filename')
    file = request.files.get('file')
    # print(file)
    user_id = current_user.id
    success, message = upload_image(filename, file, user_id)
    print(success, message)
    flash(message, 'success' if success else 'error')
    return redirect('/')
