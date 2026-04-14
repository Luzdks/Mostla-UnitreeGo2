import sys, time, threading, cv2, numpy as np, base64, urllib.request, json
sys.path.insert(0, '/home/unitree/unitree_sdk2_python')
from unitree_sdk2py.core.channel import ChannelFactory
from unitree_sdk2py.go2.video.video_client import VideoClient
from http.server import BaseHTTPRequestHandler, HTTPServer
from ultralytics import YOLO

# ─────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────
# REEMPLAZA ESTA IP por la de tu PC/Laptop en la red local
OLLAMA_SERVER_IP  = '10.22.159.235' 
OLLAMA_MODEL      = 'moondream'    # Modelo de visión ligero
FRAME_INTERVAL    = 1 / 15
SEMANTIC_INTERVAL = 2.5            # Segundos entre consultas locales

# ─────────────────────────────────────────
# ESTADO GLOBAL
# ─────────────────────────────────────────
latest_jpeg    = b''
lock           = threading.Lock()
active_source  = 'go2' 
detection_on   = False
semantic_on    = False
semantic_label = '' 
semantic_lock  = threading.Lock()

# ─────────────────────────────────────────
# YOLO (Detección local en CPU del Go2)
# ─────────────────────────────────────────
print("[yolo] Cargando modelo...")
model_yolo = YOLO('yolov8n.pt')

def apply_detection(frame):
    small = cv2.resize(frame, (640, 384))
    results = model_yolo(small, verbose=False)[0]
    h_orig, w_orig = frame.shape[:2]
    scale_x, scale_y = w_orig / 640, h_orig / 384
    annotated = frame.copy()
    
    for box in results.boxes:
        if float(box.conf[0]) < 0.40: continue
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        x1, y1 = int(x1 * scale_x), int(y1 * scale_y)
        x2, y2 = int(x2 * scale_x), int(y2 * scale_y)
        
        label = model_yolo.names[int(box.cls[0])]
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(annotated, f"{label}", (x1, y1 - 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    return annotated

# ─────────────────────────────────────────
# SEMÁNTICA LOCAL (OLLAMA)
# ─────────────────────────────────────────
def ask_local_vision(jpg_bytes):
    """
    Envía el frame a Ollama en tu PC. 
    No requiere APIs externas ni instalaciones pesadas en el Go2.
    """
    b64 = base64.b64encode(jpg_bytes).decode('utf-8')
    url = f"http://{OLLAMA_SERVER_IP}:11434/api/generate"
    
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": "Describe en UNA frase corta (máx 12 palabras) qué ves y si hay obstáculos.",
        "stream": False,
        "images": [b64]
    }
    
    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps(payload).encode(),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            return data.get('response', '').strip()
    except Exception as e:
        print(f"[ollama-error] {e}")
        return ''

def semantic_loop():
    global semantic_label
    while True:
        if not semantic_on:
            time.sleep(0.5); continue
        
        with lock:
            jpg = latest_jpeg
        if not jpg:
            time.sleep(0.5); continue
            
        # Reducir para velocidad de transmisión
        buf = np.frombuffer(jpg, np.uint8)
        frame = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        if frame is not None:
            small = cv2.resize(frame, (480, 270)) # Resolución baja = más rápido
            _, small_jpg = cv2.imencode('.jpg', small, [cv2.IMWRITE_JPEG_QUALITY, 70])
            
            result = ask_local_vision(small_jpg.tobytes())
            with semantic_lock:
                semantic_label = result
        time.sleep(SEMANTIC_INTERVAL)

# ─────────────────────────────────────────
# PROCESAMIENTO Y STREAMING (IGUAL AL ORIGINAL)
# ─────────────────────────────────────────
def overlay_semantic(frame):
    with semantic_lock:
        text = semantic_label
    if not text: return frame
    h, w = frame.shape[:2]
    cv2.rectangle(frame, (0, h - 40), (w, h), (0, 0, 0), -1)
    cv2.putText(frame, text, (10, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    return frame

def process_frame(frame):
    if detection_on: frame = apply_detection(frame)
    if semantic_on:  frame = overlay_semantic(frame)
    return frame

def fetch_go2():
    global latest_jpeg
    try:
        ChannelFactory().Init(0, 'eth0')
        client = VideoClient()
        client.Init()
        while True:
            if active_source != 'go2': time.sleep(0.1); continue
            ret, data = client.GetImageSample()
            if ret == 0 and data:
                frame = cv2.imdecode(np.frombuffer(bytes(data), np.uint8), cv2.IMREAD_COLOR)
                if frame is not None:
                    frame = process_frame(frame)
                    _, jpg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    with lock: latest_jpeg = jpg.tobytes()
    except Exception as e: print(f"[go2] {e}")

def fetch_usb(device='/dev/video0'):
    global latest_jpeg
    cap = None
    while True:
        if active_source != 'usb':
            if cap: cap.release(); cap = None
            time.sleep(0.1); continue
        if cap is None:
            cap = cv2.VideoCapture(device)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        ret, frame = cap.read()
        if ret:
            frame = process_frame(frame)
            _, jpg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            with lock: latest_jpeg = jpg.tobytes()
        time.sleep(0.03)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def do_GET(self):
        global active_source, detection_on, semantic_on
        if '/switch' in self.path:
            active_source = 'usb' if 'src=usb' in self.path else 'go2'
            self._text(f"Fuente: {active_source}")
        elif '/detection' in self.path:
            detection_on = 'state=on' in self.path
            self._text(f"YOLO: {detection_on}")
        elif '/semantic' in self.path:
            semantic_on = 'state=on' in self.path
            self._text(f"Semántica: {semantic_on}")
        elif self.path == '/status':
            self._text(f"Src: {active_source} | YOLO: {detection_on} | Sem: {semantic_on}\nUlt: {semantic_label}")
        else:
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()
            try:
                while True:
                    with lock: jpg = latest_jpeg
                    if jpg:
                        self.wfile.write(b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpg + b'\r\n')
                    time.sleep(0.05)
            except: pass

    def _text(self, msg):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(msg.encode())

# ─────────────────────────────────────────
# LANZAMIENTO
# ─────────────────────────────────────────
threading.Thread(target=fetch_go2, daemon=True).start()
threading.Thread(target=fetch_usb, daemon=True).start()
threading.Thread(target=semantic_loop, daemon=True).start()

print(f"Servidor en puerto 8888. Usando Ollama en {OLLAMA_SERVER_IP}")
HTTPServer(('0.0.0.0', 8888), Handler).serve_forever()