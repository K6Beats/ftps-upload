from flask import Flask, request, jsonify
import base64
import os
import subprocess

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ FTPS uploader is live using lftp workaround."

@app.route('/upload', methods=['POST'])
def upload():
    try:
        data = request.get_json()
        host = data.get('host')
        username = data.get('username')
        password = data.get('password')
        remote_filename = data.get('remote_filename', 'upload.bin')
        file_content_b64 = data.get('file_content')

        if not all([host, username, password, file_content_b64]):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

        print(f"📥 Upload: {remote_filename} to {host}")

        temp_path = f"/tmp/{remote_filename}"
        with open(temp_path, 'wb') as f:
            f.write(base64.b64decode(file_content_b64))

        # lftp upload command
        cmd = f'''
        lftp -e "
            set ftp:ssl-force true;
            set ftp:ssl-protect-data true;
            set ftp:passive-mode true;
            open -u {username},{password} ftps://{host};
            put {temp_path} -o {remote_filename};
            bye
        "
        '''

        print("🔄 Running lftp...")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            print("❌ lftp error:", result.stderr)
            return jsonify({'status': 'error', 'message': result.stderr}), 500

        print("✅ File uploaded via lftp")
        os.remove(temp_path)
        return jsonify({'status': 'success'}), 200

    except Exception as e:
        print("❌ Upload failed:", str(e))
        return jsonify({'status': 'error', 'message': str(e)}), 500
