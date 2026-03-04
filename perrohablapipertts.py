# Opción A: Piper TTS (muy rápido, corre en Jetson sin problema)
# pip install piper-tts

import subprocess
import sounddevice as sd
import soundfile as sf

def hablar(texto: str, idioma: str = "es"):
    """Convierte texto a voz y reproduce por el altavoz"""
    
    # Generar audio con Piper
    subprocess.run([
        "piper",
        "--model", "es_ES-davefx-medium.onnx",
        "--output_file", "/tmp/respuesta.wav"
    ], input=texto.encode(), check=True)
    
    # Reproducir
    data, samplerate = sf.read("/tmp/respuesta.wav")
    sd.play(data, samplerate)
    sd.wait()
