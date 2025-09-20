from flask import Flask, render_template, request, redirect, session, send_file
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import os
from io import BytesIO

load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key'

AZURE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = "uploads"

if not AZURE_CONNECTION_STRING:
    raise ValueError("AZURE_STORAGE_CONNECTION_STRING is not set.")

blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)

USER = {"username": "admin", "password": "password"}

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == USER['username'] and request.form['password'] == USER['password']:
            session['user'] = USER['username']
            return redirect('/dashboard')
        return "Invalid credentials", 403
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect('/')
    files = [blob.name for blob in container_client.list_blobs()]
    return render_template('dashboard.html', files=files)

@app.route('/upload', methods=['POST'])
def upload():
    if 'user' not in session:
        return redirect('/')
    file = request.files['file']
    blob_client = container_client.get_blob_client(file.filename)
    blob_client.upload_blob(file, overwrite=True)
    return redirect('/dashboard')

@app.route('/download/<filename>')
def download(filename):
    if 'user' not in session:
        return redirect('/')
    blob_client = container_client.get_blob_client(filename)
    download_stream = blob_client.download_blob()
    return send_file(BytesIO(download_stream.readall()), as_attachment=True, download_name=filename)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')
