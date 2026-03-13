import sys
sys.path.insert(0, '/home/unitree/unitree_sdk2_python')
from unitree_sdk2py.core.channel import ChannelFactory
from unitree_sdk2py.go2.video.video_client import VideoClient
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import time

latest_jpeg = b''
lock = threading.Lock()

def fetch():
    global latest_jpeg
    ChannelFactory().Init(0, 'eth0')
    client = VideoClient()
    client.SetTimeout(3.0)
    client.Init()

    # --- FPS counter ---
    frame_count = 0
    t_start = time.time()

    while True:
        ret, data = client.GetImageSample()
        if ret == 0:
            with lock:
                latest_jpeg = bytes(data)

            # --- Contar frame y mostrar cada segundo ---
            frame_count += 1
            elapsed = time.time() - t_start
            if elapsed >= 1.0:
                print(f"FPS: {frame_count / elapsed:.1f}", flush=True)
                frame_count = 0
                t_start = time.time()

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
        self.end_headers()
        while True:
            with lock:
                jpg = latest_jpeg
            self.wfile.write(b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpg + b'\r\n')

threading.Thread(target=fetch, daemon=True).start()
print("Stream en: http://10.22.246.248:8888")
HTTPServer(('0.0.0.0', 8888), Handler).serve_forever()