import base64
import os
import subprocess
import textwrap
import threading
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

def log(msg: str):
    print(f"[{datetime.utcnow().isoformat(timespec='seconds')}Z] {msg}", flush=True)

def run_lftp_upload(host, username, password, filename, temp_path):
    try:
        log(f"🔧 [thread] Preparing lftp command for: {filename}")
        lftp_cmd = textwrap.dedent(
            f"""
            set ftp:ssl-force true
            set ftp:ssl-protect-data true
            set ftp:passive-mode true
            open -u "{username}","{password}" ftps://{host}
            put {temp_path} -o {filename}
            bye
            """
        ).strip()

        log(f"📜 [thread] lftp command:\n{lftp_cmd}")

        result = subprocess.run(
            ["lftp", "-c", lftp_cmd],
            capture_output=True,
            text=True,
            timeout=600
        )

        log(f"📄 [thread] STDOUT:\n{result.stdout or '<empty>'}")
        log(f"⚠️  [thread] STDERR:\n{result.stderr or '<empty>'}")
        log(f"🔚 [thread] Return code: {result.returncode}")

        os.remove(temp_path)

        if result.returncode != 0:
            log(f"❌ [thread] Upload FAILED: {filename}")
        else:
            log(f"✅ [thread] Upload SUCCESS: {filename}")

    except subprocess.TimeoutExpired:
        log(f"⏰ [thread] lftp timed out for {filename}")
    except Exception as e:
        log(f"💥 [thread] Unexpected error: {e}")


@app.route("/")
def home():
    return "✅ FTPS uploader with background task is live."


@app.route("/upload", methods=["POST"])
def upload():
    try:
        data = request.get_json(silent=True) or {}
        host = data.get("host")
        username = data.get("username")
        password = data.get("password")
        filename = data.get("remote_filename", "upload.bin")
        file_content_b64 = data.get("file_content")

        if not all([host, username, password, file_content_b64]):
            return jsonify({"status": "error", "message": "Missing required fields"}), 400

        log("=== ⏱ START: " + str(datetime.utcnow()))
        log("📥 Upload request received")
        log(f"🔗 Host: {host}")
        log(f"📄 Filename: {filename}")

        # Save file
        tmp_path = f"/tmp/{filename}"
        with open(tmp_path, "wb") as f:
            f.write(base64.b64decode(file_content_b64))
        log(f"📦 File written to: {tmp_path}")

        # Start upload in a new thread
        thread = threading.Thread(
            target=run_lftp_upload,
            args=(host, username, password, filename, tmp_path),
            daemon=True
        )
        thread.start()

        return jsonify({"status": "accepted", "message": f"Upload started for {filename}"}), 202

    except Exception as e:
        log(f"❌ Unexpected error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
