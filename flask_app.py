# app.py
from flask import Flask, request, jsonify
from ftplib import FTP_TLS

app = Flask(__name__)

@app.route('/')
def home():
    return "FTPS uploader is live"

@app.route('/upload', methods=['POST'])
def upload():
    try:
        data = request.json
        host = data['host']
        username = data['username']
        password = data['password']
        file_content = data['file_content']
        remote_filename = data['remote_filename']

        with open(remote_filename, 'wb') as f:
            f.write(file_content.encode('utf-8'))  # adjust as needed

        ftps = FTP_TLS(host)
        ftps.login(user=username, passwd=password)
        ftps.prot_p()

        with open(remote_filename, 'rb') as f:
            ftps.storbinary(f'STOR {remote_filename}', f)

        ftps.quit()
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
