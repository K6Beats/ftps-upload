from flask import Flask, request, jsonify
import base64
import os
import subprocess
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ FTPS uploader is live using lftp workaround."

@app.route('/upload', methods=['POST'])
def upload():
    start_time = datetime.utcnow()
    try:
        data = request.get_json()
        host = data.get('host')
        username = data.get('username')
        password = data.get('password')
        remote_filename = data.get('remote_filename', 'upload.bin')
        file_content_b64 = data.get('file_content')

        if not all([host, username, password, file_content_b64]):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

        print(f"\n=== ⏱ START: {start_time} UTC ===")
        print(f"📥 Upload request received")
        print(f"🔗 Host: {host}")
        print(f"📄 Filename: {remote_filename}")

        temp_path = f"/tmp/{remote_filename}"
        with open(temp_path, 'wb') as f:
            f.write(base64.b64decode(file_content_b64))
        print(f"📦 File written to: {temp_path}")

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
        print("🚀 Running lftp command...")

        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=280  # slightly less than gunicorn timeout
        )

        print(f"🔧 lftp STDOUT:\n{result.stdout}")
        print(f"⚠️  lftp STDERR:\n{result.stderr}")

        if result.returncode != 0:
            print("❌ lftp failed with non-zero exit code")
            return jsonify({'status': 'error', 'message': result.stderr}), 500

        os.remove(temp_path)
        print(f"✅ Upload complete and temp file cleaned up")
        print(f"=== ✅ FINISHED: {datetime.utcnow()} UTC ===")

        return jsonify({'status': 'success'}), 200

    except subprocess.TimeoutExpired:
        print("🔥 subprocess timed out (likely due to large file or server stall)")
        return jsonify({'status': 'error', 'message': 'Upload timed out'}), 504

    except Exception as e:
        print("❌ General error during upload:", str(e))
        return jsonify({'status': 'error', 'message': str(e)}), 500
