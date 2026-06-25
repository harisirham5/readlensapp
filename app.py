from dotenv import load_dotenv
load_dotenv()
from flask import Flask, render_template, Response, jsonify, request, send_from_directory
import cv2
import threading
import os
import urllib.request
import warnings
import uuid
import json
import re
import time
from datetime import datetime
from base64 import b64decode, binascii
from nvidia_helper import NvidiaHelper
import base64
from gtts import gTTS
import concurrent.futures

global_esp32_ip = "172.20.10.2"

# Suppress warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)

# --- Secret key: MUST be overridden in production ---
# Read from FLASK_SECRET_KEY env var. If missing, generate an ephemeral random
# key at startup so the app still boots — but warn loudly because sessions will
# not survive a restart and cookies from one run are invalid on the next.
_env_secret = os.environ.get("FLASK_SECRET_KEY")
if _env_secret and _env_secret.strip():
    app.secret_key = _env_secret.strip()
else:
    import secrets
    app.secret_key = secrets.token_hex(32)
    print(
        "WARNING: FLASK_SECRET_KEY is not set — using a randomly-generated key. "
        "Sessions/cookies will not survive a server restart. Set FLASK_SECRET_KEY "
        "in your environment or .env for stable behaviour."
    )

# --- Vault I/O lock ---
# All reads/writes to per-user files under BASE_SERIALIZE_VAULT serialize on this
# lock so concurrent requests (ESP32 button press + heartbeat refresh) cannot
# interleave file writes and corrupt JSON.
_vault_lock = threading.Lock()

# Characters allowed in a safe username. Anything else is rejected.
# Path-traversal payloads (../, /, \, NUL) are rejected with this rule.
_USERNAME_RE = re.compile(r"^[A-Za-z0-9_\-]{1,32}$")

# The central "vault" on your laptop
BASE_STORAGE = "readlens_vault"

def is_valid_username(username):
    """True only for usernames that match the safe-character allowlist."""
    return bool(_USERNAME_RE.match(username)) if username else False


def get_user_paths(username):
    """Ensures user folders exist and returns their paths.

    Validates `username` against the safe-character allowlist before touching
    the filesystem so callers cannot smuggle path separators or traversal
    sequences into the vault path.
    """
    if not is_valid_username(username):
        raise ValueError(f"Invalid username: {username!r}")
    user_root = os.path.join(BASE_STORAGE, username)
    image_dir = os.path.join(user_root, "images")
    chats_dir = os.path.join(user_root, "chats")
    sessions_file = os.path.join(user_root, "sessions.json")

    os.makedirs(image_dir, exist_ok=True)
    os.makedirs(chats_dir, exist_ok=True)

    if not os.path.exists(sessions_file):
        with open(sessions_file, 'w') as f:
            json.dump([], f)

    return user_root, chats_dir, sessions_file, image_dir


def _read_json(path, default):
    """Read a JSON file, returning `default` if missing or unreadable."""
    if not os.path.exists(path):
        return default
    with open(path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except (json.JSONDecodeError, ValueError):
            return default


def _write_json(path, data):
    """Atomically write JSON: write to a temp file then rename."""
    tmp = f"{path}.tmp"
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def enforce_chat_limit(username):
    """Keeps only the 10 most recent conversations and deletes the rest to save space."""
    _, chats_dir, sessions_file, _ = get_user_paths(username)

    with _vault_lock:
        sessions = _read_json(sessions_file, [])
        sessions.sort(key=lambda x: x.get('timestamp', 0), reverse=True)

        if len(sessions) > 10:
            to_keep = sessions[:10]
            to_delete = sessions[10:]

            for session in to_delete:
                chat_file = os.path.join(chats_dir, f"{session['id']}.json")
                if os.path.exists(chat_file):
                    try:
                        os.remove(chat_file)
                    except OSError:
                        pass

            _write_json(sessions_file, to_keep)

print("Initializing NVIDIA AI models. This may take a moment...")

# --- Initialize NVIDIA API Helper ---
try:
    nvidia_ai = NvidiaHelper()
    if nvidia_ai.ready:
        print("✅ NVIDIA API ready!")
    else:
        print("⚠️  NVIDIA API running in DEGRADED mode (no key). /chatbot and /process_image will return 503 until NVIDIA_API_KEY is set.")
except Exception as e:
    print(f"❌ NVIDIA API Initialization failed: {e}")
    nvidia_ai = None

# --- Camera Logic (Local Webcam backup) ---
camera = cv2.VideoCapture(0)
current_frame = None
frame_lock = threading.Lock()

def gen_frames():
    global current_frame
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            with frame_lock:
                current_frame = frame.copy()
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_sessions', methods=['GET'])
def get_sessions():
    username = request.args.get('username')
    if not username or not is_valid_username(username):
        return jsonify([])

    _, _, sessions_file, _ = get_user_paths(username)
    with _vault_lock:
        data = _read_json(sessions_file, [])
    return jsonify(data)

active_username = "Unknown"
active_chat_id = None
hardware_status = "IDLE"
latest_hardware_chat_id = None

@app.route('/get_chat', methods=['GET'])
def get_chat():
    global active_username, active_chat_id
    username = request.args.get('username')
    chat_id = request.args.get('chat_id')
    if not username or not is_valid_username(username):
        return jsonify([])
    if not chat_id or not _is_safe_chat_id(chat_id):
        return jsonify([])
    if username: active_username = username
    if chat_id: active_chat_id = chat_id

    _, chats_dir, _, _ = get_user_paths(username)
    chat_file = os.path.join(chats_dir, f"{chat_id}.json")

    with _vault_lock:
        data = _read_json(chat_file, [])
    return jsonify(data)


def _is_safe_chat_id(chat_id):
    """True only for chat IDs matching our generated pattern: chat_<digits>_<6 hex>."""
    return bool(re.fullmatch(r"[A-Za-z0-9_\-]{1,64}", chat_id)) if chat_id else False

@app.route('/get_image', methods=['GET'])
def get_image():
    username = request.args.get('username')
    filename = request.args.get('filename')
    if not username or not filename:
        return "Missing parameters", 400
    # Reject traversal payloads in BOTH parameters. The filename must be a
    # bare basename (no slashes, no '..' segments, no hidden-dot files).
    if not is_valid_username(username):
        return "Invalid username", 400
    if not _is_safe_image_filename(filename):
        return "Invalid filename", 400
    _, _, _, image_dir = get_user_paths(username)
    # send_from_directory enforces that the result stays inside image_dir, and
    # our pre-validation above guarantees the basename is traversal-free.
    return send_from_directory(image_dir, filename)


def _is_safe_image_filename(filename):
    """True only for bareimagen filenames like img_1234_abc.jpg — no '/' or '..'."""
    return bool(re.fullmatch(r"[A-Za-z0-9_\-]+\.[A-Za-z0-9]{1,8}", filename)) if filename else False

def send_audio_to_glasses(text_to_speak):
    """
    Converts text to an MP3 file and saves it in the static folder 
    for the ESP32-S3 to fetch.
    """
    try:
        print(f"🔊 Generating audio for: '{text_to_speak[:30]}...'")
        tts = gTTS(text=text_to_speak, lang='en')
        static_dir = os.path.join(app.root_path, 'static')
        os.makedirs(static_dir, exist_ok=True)
        voice_path = os.path.join(static_dir, 'voice.mp3')
        tts.save(voice_path)
        print(f"📡 Audio saved to static/voice.mp3")
    except Exception as e:
        print(f"❌ Failed to stream audio to smart glasses: {e}")

@app.route('/chatbot', methods=['POST'])
def chatbot():
    if not nvidia_ai or not nvidia_ai.ready:
        return jsonify({'error': 'NVIDIA API not configured'}), 503

    data = request.json or {}
    user_input = (data.get('message') or '').strip()
    username = data.get('username') or 'Unknown'
    chat_id = data.get('chat_id')

    if not user_input:
        return jsonify({'error': 'No message'}), 400
    if not is_valid_username(username):
        return jsonify({'error': 'Invalid username'}), 400
    if chat_id and not _is_safe_chat_id(chat_id):
        return jsonify({'error': 'Invalid chat_id'}), 400

    _, chats_dir, sessions_file, image_dir = get_user_paths(username)

    is_new_chat = False
    if not chat_id:
        chat_id = f"chat_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        is_new_chat = True

    chat_file = os.path.join(chats_dir, f"{chat_id}.json")

    with _vault_lock:
        history = _read_json(chat_file, [])

        try:
            # Check if this chat contains a captured image for vision follow-up
            image_base64 = None
            for item in reversed(history):
                if item.get('image_file') and _is_safe_image_filename(item['image_file']):
                    img_path = os.path.join(image_dir, item['image_file'])
                    if os.path.exists(img_path):
                        with open(img_path, 'rb') as img_f:
                            image_base64 = base64.b64encode(img_f.read()).decode('utf-8')
                    break  # Only use the most recent image

            if image_base64:
                # Vision-aware follow-up: send both the question and the image
                vision_prompt = (
                    "The user previously captured this image with their smart glasses. "
                    "Now they are asking a follow-up question: "
                    f'"{user_input}". Answer naturally and concisely.'
                )
                bot_response = nvidia_ai.generate_vision_text(vision_prompt, image_base64)
            else:
                bot_response = nvidia_ai.generate_text(user_input)
        except Exception as e:
            print(f"NVIDIA Error: {e}")
            bot_response = "I'm having trouble connecting to the NVIDIA brain right now."

        history.append({
            'timestamp': datetime.now().isoformat(),
            'user': user_input,
            'bot': bot_response
        })

        _write_json(chat_file, history)

        sessions = _read_json(sessions_file, [])

        if is_new_chat:
            title = user_input[:25] + "..." if len(user_input) > 25 else user_input
            sessions.insert(0, {'id': chat_id, 'title': title, 'timestamp': time.time()})
        else:
            for s in sessions:
                if s['id'] == chat_id:
                    s['timestamp'] = time.time()
                    break

        _write_json(sessions_file, sessions)

    enforce_chat_limit(username)
    send_audio_to_glasses(bot_response)
    return jsonify({
        'text': bot_response,
        'chat_id': chat_id
    })

@app.route('/process_image', methods=['POST'])
def process_image():
    global active_username, active_chat_id, hardware_status, latest_hardware_chat_id
    if not nvidia_ai or not nvidia_ai.ready:
        return jsonify({"text": "NVIDIA API not configured", "error": "Service unavailable"}), 503

    # Content-Type may include charset/mimetype parameters
    # (e.g. "image/jpeg; charset=binary" from ESP32 Arduino HTTPClient).
    # Match the prefix, not strict equality.
    content_type = request.content_type or ''
    is_from_esp32 = content_type.startswith('image/jpeg')

    if is_from_esp32:
        if not request.data:
            return jsonify({"text": "Empty image payload", "error": "empty"}), 400
        image_data = request.data
        mode = request.headers.get('X-Glasses-Mode', 'DESCRIBE')
        action = 'ocr' if mode == 'TEXT' else 'describe'
        username = active_username
        hardware_status = f"PROCESSING_{action.upper()}"
        # Force a brand new chat for every hardware button press
        chat_id = None
        clean_base64 = base64.b64encode(image_data).decode('utf-8')
    else:
        data = request.json or {}
        action = data.get('action')
        image_source = data.get('image_source')
        username = data.get('username', 'Unknown')
        chat_id = data.get('chat_id')

        if not username or not image_source:
            return jsonify({"text": "Error: Missing data"}), 400

    if not is_valid_username(username):
        return jsonify({"text": "Invalid username", "error": "bad_username"}), 400
    if chat_id and not _is_safe_chat_id(chat_id):
        return jsonify({f"text": "Invalid chat_id", "error": "bad_chat_id"}), 400

    _, chats_dir, sessions_file, image_dir = get_user_paths(username)

    is_new_chat = False
    if not chat_id:
        chat_id = f"chat_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        is_new_chat = True
        if is_from_esp32:
            latest_hardware_chat_id = chat_id
            active_chat_id = chat_id

    chat_file = os.path.join(chats_dir, f"{chat_id}.json")

    try:
        if not is_from_esp32:
            if image_source.startswith('data:image'):
                clean_base64 = image_source.split(',', 1)[1]
            else:
                clean_base64 = image_source

            # Fail fast on malformed base64 before spending time on I/O.
            try:
                image_data = b64decode(clean_base64, validate=True)
            except (binascii.Error, ValueError) as b64e:
                return jsonify({
                    "text": "Invalid image data",
                    "error": f"base64: {b64e}"
                }), 400
            if not image_data:
                return jsonify({"text": "Empty image data", "error": "empty"}), 400

        image_filename = f"img_{int(time.time())}_{uuid.uuid4().hex[:6]}.jpg"
        image_filepath = os.path.join(image_dir, image_filename)
        with open(image_filepath, 'wb') as f:
            f.write(image_data)

        print(f"Sending image to NVIDIA Vision (Action: {action})...")
        if action == 'ocr':
            prompt = "You are assisting a blind user wearing smart glasses. Read the most important information visible in the image. Prioritize names, warnings, dates, prices, and instructions. Summarize first. Keep the response under 10 words."
        else:
            prompt = "You are assisting a blind user wearing smart glasses. Describe the most important object or objects from the user's point of view. Prioritize objects being held, touched, or directly in front of the user. Use simple, natural language. Keep the response under 5 words. If uncertain, use words like likely or possibly."

        result = nvidia_ai.generate_vision_text(prompt, clean_base64)
        print("NVIDIA Success")

        with _vault_lock:
            history = _read_json(chat_file, [])

            history.append({
                'timestamp': datetime.now().isoformat(),
                'user': f"[Image Analysis - {action.upper()}]",
                'bot': result,
                'image_file': image_filename,
                'type': f"image_{action}"
            })

            _write_json(chat_file, history)

            sessions = _read_json(sessions_file, [])

            if is_new_chat:
                title = f"Image Scan: {action.upper()}"
                sessions.insert(0, {'id': chat_id, 'title': title, 'timestamp': time.time()})
            else:
                for s in sessions:
                    if s['id'] == chat_id:
                        s['timestamp'] = time.time()
                        break

            _write_json(sessions_file, sessions)

        enforce_chat_limit(username)

        send_audio_to_glasses(result)

        if is_from_esp32:
            hardware_status = "IDLE"

        return jsonify({
            "text": result,
            "chat_id": chat_id,
            "action": action
        })

    except Exception as e:
        if is_from_esp32:
            hardware_status = "IDLE"

        print(f"Error processing image with NVIDIA: {e}")
        return jsonify({"text": "Error analyzing image over the network.", "error": str(e)}), 400
    finally:
        # Belt-and-suspenders: never leave PROCESSING_* stuck if we crash.
        if is_from_esp32 and hardware_status.startswith("PROCESSING_"):
            hardware_status = "IDLE"

@app.route('/connect_device', methods=['POST'])
def connect_device():
    global global_esp32_ip
    
    # Try the last known IP first
    try:
        response = urllib.request.urlopen(f"http://{global_esp32_ip}/", timeout=1.5)
        if response.getcode() == 200 and "SUCCESS" in response.read().decode('utf-8'):
            return jsonify({
                "status": "connected",
                "message": "readlens hardware successfully synchronized!",
                "device_ip": global_esp32_ip
            }), 200
    except Exception:
        pass

    # If it fails, scan common iPhone hotspot IPs
    def check_ip(ip):
        try:
            url = f"http://{ip}/"
            req = urllib.request.urlopen(url, timeout=1.0)
            if req.getcode() == 200 and "SUCCESS" in req.read().decode('utf-8'):
                return ip
        except Exception:
            pass
        return None

    ips_to_check = [f"172.20.10.{i}" for i in range(1, 15)]
    found_ip = None

    # shutdown_wasm=True (default) frees the worker threads once the pool
    # leaves this `with` block. We also explicitly cancel any pending futures
    # when we find a result early so we don't burn cycles pinging the rest
    # of the subnet after we already have an answer.
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(check_ip, ip): ip for ip in ips_to_check}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                found_ip = res
                # Cancel any not-yet-started futures; ignore "can't cancel"
                # errors on already-running ones — they'll just harmlessly
                # return and be discarded.
                for f in futures:
                    f.cancel()
                break

    if found_ip:
        global_esp32_ip = found_ip
        return jsonify({
            "status": "connected",
            "message": "readlens hardware successfully synchronized!",
            "device_ip": found_ip
        }), 200
    
    return jsonify({
        "status": "error",
        "message": "Could not locate your readlens. Check if it is fully powered."
    }), 500

@app.route('/ping_device', methods=['GET'])
def ping_device():
    global global_esp32_ip, active_chat_id, active_username, hardware_status, latest_hardware_chat_id
    username = request.args.get('username')
    if username:
        if is_valid_username(username):
            active_username = username

    try:
        req = urllib.request.Request(f"http://{global_esp32_ip}/", headers={'Connection': 'close'})
        with urllib.request.urlopen(req, timeout=2) as response:
            _ = response.read()
            if response.getcode() == 200:
                return jsonify({
                    "status": "alive",
                    "latest_hardware_chat_id": latest_hardware_chat_id,
                    "hardware_status": hardware_status
                }), 200
    except Exception as e:
        pass

    # 502 Bad Gateway — the device upstream is down. Frontend code can branch
    # on `res.ok` instead of only payload inspection.
    return jsonify({"status": "dead", "reason": "timeout"}), 502

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)