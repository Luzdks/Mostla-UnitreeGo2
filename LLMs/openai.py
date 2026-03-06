from LLMs.openai import OpenAI

client = OpenAI(api_key="TU_API_KEY")

SYSTEM_PROMPT = """
Eres un robot cuadrúpedo llamado Go2. Puedes ejecutar estas acciones:
- CAMINAR_ADELANTE(segundos)
- CAMINAR_ATRAS(segundos)
- GIRAR(grados)
- SENTARSE
- PARARSE
- SALUDAR
- HABLAR(mensaje)

Cuando el usuario te dé una instrucción, responde SIEMPRE en JSON con este formato:
{
  "acciones": ["ACCION1", "ACCION2"],
  "respuesta_verbal": "Lo que dirás en voz alta"
}
"""

def consultar_llm(texto_usuario: str, historial: list) -> dict:
    historial.append({"role": "user", "content": texto_usuario})
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + historial,
        response_format={"type": "json_object"}
    )
    
    respuesta = response.choices[0].message.content
    historial.append({"role": "assistant", "content": respuesta})
    
    import json
    return json.loads(respuesta), historial