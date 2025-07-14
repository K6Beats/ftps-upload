from flask import Flask, request, jsonify
from ftplib import FTP_TLS
import base64
import os
import socket

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ FTPS uploader is live and ready."

@app.route('/upload', methods=['POST'])
def upload():
    try:
        data = request.get_json()

        # Extract required fields
        host = data.get('host')
        username = data.get('username')
        password = data.get('password')
        remote_filename = data.get('remote_filename', 'upload.bin')
        file_content_b64 = data.get('file_content')

        if not all([host, username, password, file_content_b64]):
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields: host, username, password, file_content'
            }), 400

        print(f"📥 Upload request: {remote_filename}")
        print(f"🔗 Connecting to FTPS host: {host}")

        # Decode base64
        file_bytes = base64.b64decode(file_content_b64)

        # Save to /tmp (safe for Render)
        temp_file_path = f"/tmp/{remote_filename}"
        with open(temp_file_path, 'wb') as f:
            f.write(file_bytes)

        # FTPS setup
        ftps = FTP_TLS()
        ftps.connect(host, 21, timeout=15)
        ftps.login(user=username, passwd=password)
        ftps.prot_p()
        ftps.set_pasv(True)

        print("✅ Logged in to FTPS")
        print("📁 Current server directory:", ftps.pwd())

        # Upload
        with open(temp_file_path, 'rb') as f:
            ftps.storbinary(f'STOR {remote_filename}', f)

        print(f"✅ Upload complete: /{remote_filename}")
        ftps.quit()
        os.remove(temp_file_path)

        return jsonify({'status': 'success'}), 200

    except Exception as e:
        print("❌ Upload failed:", str(e))
        return jsonify({'status': 'error', 'message': str(e)}), 500
