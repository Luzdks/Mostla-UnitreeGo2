import pyaudio
from faster_whisper import WhisperModel

# Cargar modelo (tiny/base para tiempo real, large para precisión)
model = WhisperModel("base", device="cuda", compute_type="float16")

def escuchar_usuario():
    """Graba audio del micrófono y lo transcribe"""
    # Configurar PyAudio
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=1024
    )
    
    print("🎙️ Escuchando...")
    frames = []
    
    # Grabar 5 segundos (o usar VAD para detección automática)
    for _ in range(0, int(16000 / 1024 * 5)):
        data = stream.read(1024)
        frames.append(data)
    
    stream.stop_stream()
    stream.close()
    
    # Transcribir
    segments, _ = model.transcribe(b"".join(frames), language="es")
    texto = " ".join([s.text for s in segments])
    print(f"👤 Usuario dijo: {texto}")
    return texto