from flask import Flask, request, jsonify
from ftplib import FTP_TLS
import base64

app = Flask(__name__)

@app.route('/')
def home():
    return "FTPS uploader is running."

@app.route('/upload', methods=['POST'])
def upload():
    try:
        data = request.get_json()
        host = data['host']
        username = data['username']
        password = data['password']
        remote_filename = data['remote_filename']
        file_content_b64 = data['file_content']  # base64 string

        # Decode base64 to binary
        file_bytes = base64.b64decode(file_content_b64)

        # Save temporarily
        with open(remote_filename, 'wb') as f:
            f.write(file_bytes)

        ftps = FTP_TLS(host)
        ftps.login(user=username, passwd=password)
        ftps.prot_p()  # Secure data connection

        with open(remote_filename, 'rb') as f:
            ftps.storbinary(f'STOR {remote_filename}', f)

        ftps.quit()
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
