import asyncio
import edge_tts
import speech_recognition as sr
from anthropic import Anthropic
import os
import wave
import time

anthropic = Anthropic(api_key="ANTHROPIC_API_KEY")
historial = []

SYSTEM = """Eres un perro robot cuadrúpedo amigable del Tec de Monterrey.
Tu nombre es Escuincle. Respondes breve en español.
Máximo 2 oraciones por respuesta. Eres amable. Nunca uses emojis"""

DEVICE = "plughw:2,0"

def grabar_audio(duracion=5):
    print(f"[LOG] Grabando {duracion} segundos...")
    cmd = f"arecord -D {DEVICE} -d {duracion} -f S16_LE -r 48000 -c 1 /tmp/pregunta.wav"
    os.system(cmd)
    try:
        with wave.open("/tmp/pregunta.wav", "rb") as w:
            print(f"[LOG] WAV: channels={w.getnchannels()}, rate={w.getframerate()}, frames={w.getnframes()}")
    except Exception as e:
        print(f"[LOG] Error leyendo WAV: {e}")

def transcribir():
    print("[LOG] Transcribiendo...")
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    with sr.AudioFile("/tmp/pregunta.wav") as source:
        audio = recognizer.record(source)
    try:
        texto = recognizer.recognize_google(audio, language="es-MX")
        print(f"[LOG] Transcripcion: {texto}")
        return texto
    except sr.UnknownValueError:
        print("[LOG] No se entendio el audio")
        return None
    except sr.RequestError as e:
        print(f"[LOG] Error de red: {e}")
        return None

def responder(texto):
    print(f"[LOG] Enviando a Claude: {texto}")
    historial.append({"role": "user", "content": texto})
    response = anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        system=SYSTEM,
        messages=historial
    )
    respuesta = response.content[0].text
    historial.append({"role": "assistant", "content": respuesta})
    print(f"[LOG] Claude: {respuesta}")
    return respuesta

async def generar_voz(texto):
    print("[LOG] Generando voz...")
    communicate = edge_tts.Communicate(texto, "es-MX-DaliaNeural")
    await communicate.save("/tmp/respuesta.mp3")
    os.system("ffmpeg -y -i /tmp/respuesta.mp3 -ar 48000 -ac 1 -f wav /tmp/respuesta.wav -loglevel quiet")

def reproducir_audio():
    print("[LOG] Reproduciendo...")
    os.system(f"amixer -c 0 set PCM 11 unmute 2>/dev/null")
    os.system(f"aplay -D {DEVICE} /tmp/respuesta.wav")

def main():
    os.system("pulseaudio --kill 2>/dev/null")
    time.sleep(2)
    print("Escuincle listo! Presiona Enter para hablar, Ctrl+C para salir.")
    while True:
        try:
            input("\nPresiona Enter para escuchar...")
            grabar_audio()
            texto = transcribir()
            if not texto:
                print("No entendi, intenta de nuevo.")
                continue
            print(f"Escuche: {texto}")
            respuesta = responder(texto)
            print(f"Escuincle: {respuesta}")
            asyncio.run(generar_voz(respuesta))
            reproducir_audio()
        except KeyboardInterrupt:
            print("\nApagando Escuincle...")
            break

if __name__ == "__main__":
    main()