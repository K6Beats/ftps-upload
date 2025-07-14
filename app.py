from flask import Flask, request, jsonify
from ftplib import FTP_TLS
import base64
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ FTPS uploader is live."

@app.route('/upload', methods=['POST'])
def upload():
    try:
        data = request.get_json()

        # Extract fields
        host = data.get('host')
        username = data.get('username')
        password = data.get('password')
        remote_filename = data.get('remote_filename', 'upload.bin')
        file_content_b64 = data.get('file_content')

        # Logging
        print(f"Incoming upload for: {remote_filename}")
        print(f"Connecting to FTPS host: {host}")

        # Decode base64 to bytes
        file_bytes = base64.b64decode(file_content_b64)

        # Save temporarily
        temp_file_path = f"/tmp/{remote_filename}"
        with open(temp_file_path, 'wb') as f:
            f.write(file_bytes)

        # Connect to FTPS
        ftps = FTP_TLS(host)
        ftps.login(user=username, passwd=password)
        ftps.prot_p()
        ftps.set_pasv(True)
        print("✅ Connected and logged in via FTPS")

        # Upload file
        with open(temp_file_path, 'rb') as f:
            ftps.storbinary(f'STOR {remote_filename}', f)
        print(f"✅ Uploaded: {remote_filename}")

        ftps.quit()
        os.remove(temp_file_path)  # clean up

        return jsonify({'status': 'success'}), 200

    except Exception as e:
        print("❌ Upload failed:", str(e))
        return jsonify({'status': 'error', 'message': str(e)}), 500
