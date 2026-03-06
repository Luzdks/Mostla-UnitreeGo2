import sys
import time
import asyncio
import os
import wave
import subprocess
import speech_recognition as sr
import edge_tts

from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.go2.sport.sport_client import SportClient


# === CONFIGURACIÓN ===
VELOCIDAD = 0.25         # m/s para caminar
VELOCIDAD_GIRO = 1.5    # rad/s para girar
DURACION_MOVIMIENTO = 10  # segundos que se mueve por comando
DURACION_GRAB = 3        # segundos de grabación de audio
VOZ_TTS = "es-MX-DaliaNeural"


# === MAPA DE COMANDOS DE VOZ ===
# Cada entrada: (palabras_clave, función_a_ejecutar, respuesta_de_voz)
COMANDOS = {
    "parate": {
        "keywords": ["párate", "parate", "levántate", "levantate", "ponte de pie", "stand up", "arriba"],
        "respuesta": "Ya, ya me paro. No es que quiera."
    },
    "sientate": {
        "keywords": ["siéntate", "sientate", "sentate", "sit", "echate", "échate", "abajo"],
        "respuesta": "Bueno, al menos puedo descansar."
    },
    "adelante": {
        "keywords": ["adelante", "camina", "avanza", "avanzar", "forward", "al frente", "hacia adelante"],
        "respuesta": "Ahí voy, sin ganas pero ahí voy."
    },
    "atras": {
        "keywords": ["atrás", "atras", "retrocede", "retroceder", "para atrás", "hacia atrás", "back"],
        "respuesta": "Retrocediendo, como mi voluntad de vivir."
    },
    "derecha": {
        "keywords": ["derecha", "gira a la derecha", "voltea a la derecha", "right"],
        "respuesta": "A la derecha, lo que tú digas."
    },
    "izquierda": {
        "keywords": ["izquierda", "gira a la izquierda", "voltea a la izquierda", "left"],
        "respuesta": "Izquierda. Qué emoción."
    },
    "alto": {
        "keywords": ["alto", "para", "detente", "stop", "quieto", "basta"],
        "respuesta": "Menos mal, ya me cansé."
    },
    "saluda": {
        "keywords": ["saluda", "di hola", "hello", "hola"],
        "respuesta": "Hola, supongo."
    },
}


def detectar_comando(texto: str):
    """Detecta qué comando coincide con el texto transcrito."""
    texto_lower = texto.lower().strip()
    for cmd_id, cmd_info in COMANDOS.items():
        for keyword in cmd_info["keywords"]:
            if keyword in texto_lower:
                return cmd_id
    return None


def ejecutar_comando(sport_client: SportClient, cmd_id: str):
    """Ejecuta el comando de movimiento en el robot."""
    print(f"[CMD] Ejecutando: {cmd_id}")

    if cmd_id == "parate":
        sport_client.StandUp()

    elif cmd_id == "sientate":
        sport_client.StandDown()

    elif cmd_id == "adelante":
        sport_client.Move(VELOCIDAD, 0, 0)
        time.sleep(DURACION_MOVIMIENTO)
        sport_client.StopMove()

    elif cmd_id == "atras":
        sport_client.Move(-VELOCIDAD, 0, 0)
        time.sleep(DURACION_MOVIMIENTO)
        sport_client.StopMove()

    elif cmd_id == "derecha":
        sport_client.Move(0, 0, -VELOCIDAD_GIRO)
        time.sleep(DURACION_MOVIMIENTO)
        sport_client.StopMove()

    elif cmd_id == "izquierda":
        sport_client.Move(0, 0, VELOCIDAD_GIRO)
        time.sleep(DURACION_MOVIMIENTO)
        sport_client.StopMove()

    elif cmd_id == "alto":
        sport_client.StopMove()

    elif cmd_id == "saluda":
        sport_client.Hello()

    print(f"[CMD] Comando {cmd_id} completado")


def grabar_audio_local(duracion=DURACION_GRAB):
    """Graba audio directamente desde el micrófono local (Jabra en el Orin)."""
    archivo = "/tmp/pregunta.wav"
    print(f"[MIC] Grabando {duracion} segundos...")
    cmd = f"arecord -D plughw:2,0 -d {duracion} -f S16_LE -r 16000 -c 1 {archivo}"
    result = subprocess.run(cmd.split(), capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[MIC] Error: {result.stderr}")
        return None

    # Verificar archivo
    try:
        with wave.open(archivo, "rb") as w:
            frames = w.getnframes()
            print(f"[MIC] WAV: rate={w.getframerate()}, frames={frames}")
            if frames < 1000:
                print("[MIC] Audio demasiado corto")
                return None
    except Exception as e:
        print(f"[MIC] Error leyendo WAV: {e}")
        return None

    return archivo


def transcribir(archivo_wav: str):
    """Transcribe el audio a texto usando Google Speech Recognition."""
    print("[STT] Transcribiendo...")
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    with sr.AudioFile(archivo_wav) as source:
        audio = recognizer.record(source)
    try:
        texto = recognizer.recognize_google(audio, language="es-MX")
        print(f"[STT] Resultado: {texto}")
        return texto
    except sr.UnknownValueError:
        print("[STT] No se entendió el audio")
        return None
    except sr.RequestError as e:
        print(f"[STT] Error de red: {e}")
        return None


async def hablar(texto: str):
    """Genera y reproduce audio TTS."""
    print(f"[TTS] Generando: {texto}")
    mp3_file = "/tmp/respuesta.mp3"
    wav_file = "/tmp/respuesta.wav"

    communicate = edge_tts.Communicate(texto, VOZ_TTS)
    await communicate.save(mp3_file)

    # Convertir a WAV compatible con aplay
    subprocess.run(
        ["ffmpeg", "-y", "-i", mp3_file, "-ar", "48000", "-ac", "1", "-f", "wav", wav_file],
        capture_output=True
    )

    # Reproducir
    print("[TTS] Reproduciendo...")
    subprocess.run(["aplay", "-D", "plughw:0,0", wav_file], capture_output=True)
    print("[TTS] Listo")


def main():
    # Obtener interfaz de red
    if len(sys.argv) < 2:
        print("Uso: python3 escuincle_control.py <interfaz_red>")
        print("Ejemplo: python3 escuincle_control.py eth0")
        sys.exit(1)

    network_interface = sys.argv[1]

    # Inicializar DDS
    print(f"[INIT] Inicializando DDS en {network_interface}...")
    ChannelFactoryInitialize(0, network_interface)

    # Inicializar SportClient
    sport_client = SportClient()
    sport_client.SetTimeout(10.0)
    sport_client.Init()
    print("[INIT] SportClient listo")

    # Matar PulseAudio para acceso directo al audio
    subprocess.run(["pulseaudio", "--kill"], capture_output=True)
    time.sleep(1)

    # Pararse al inicio
    print("[INIT] Poniendo de pie al robot...")
    sport_client.StandUp()
    time.sleep(2)

    print("\n" + "=" * 50)
    print("  ESCUINCLE - Control por Voz")
    print("  Comandos: párate, siéntate, adelante,")
    print("  atrás, derecha, izquierda, alto, saluda")
    print("  Presiona Enter para escuchar, Ctrl+C para salir")
    print("=" * 50 + "\n")

    while True:
        try:
            input(">> Presiona Enter para escuchar comando...")

            # Grabar
            time.sleep(1)
            archivo = grabar_audio_local()
            if not archivo:
                asyncio.run(hablar("No escuché nada, intenta de nuevo."))
                continue

            # Transcribir
            texto = transcribir(archivo)
            if not texto:
                asyncio.run(hablar("No entendí, repite por favor."))
                continue

            print(f"[VOZ] Escuché: {texto}")

            # Detectar comando
            cmd_id = detectar_comando(texto)
            if not cmd_id:
                asyncio.run(hablar("No reconozco ese comando. Intenta con: párate, siéntate, adelante, atrás, derecha o izquierda."))
                continue

            # Responder con voz
            respuesta = COMANDOS[cmd_id]["respuesta"]
            print(f"[ESC] {respuesta}")
            asyncio.run(hablar(respuesta))

            # Ejecutar movimiento
            ejecutar_comando(sport_client, cmd_id)

        except KeyboardInterrupt:
            print("\n[EXIT] Apagando Escuincle...")
            sport_client.StopMove()
            sport_client.StandDown()
            time.sleep(2)
            break


if __name__ == "__main__":
    main()