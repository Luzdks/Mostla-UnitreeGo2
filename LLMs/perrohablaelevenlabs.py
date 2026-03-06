# Opción B: ElevenLabs (voz más natural, requiere internet)
from elevenlabs.client import ElevenLabs
from elevenlabs import play

eleven_client = ElevenLabs(api_key="TU_API_KEY")

def hablar_elevenlabs(texto: str):
    audio = eleven_client.text_to_speech.convert(
        voice_id="pNInz6obpgDQGcFmaJgB",
        text=texto,
        model_id="eleven_multilingual_v2"
    )
    play(audio)