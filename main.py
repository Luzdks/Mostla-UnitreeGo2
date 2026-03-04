def main():
    historial = []
    
    print("🤖 Go2 listo. Habla para darle instrucciones.")
    hablar("Hola, soy Go2. ¿En qué puedo ayudarte?")
    
    while True:
        try:
            # 1. Escuchar al usuario
            texto_usuario = escuchar_usuario()
            if not texto_usuario.strip():
                continue
            
            # 2. Consultar el LLM
            resultado, historial = consultar_llm(texto_usuario, historial)
            
            acciones = resultado.get("acciones", [])
            respuesta_verbal = resultado.get("respuesta_verbal", "")
            
            print(f"🤖 Acciones: {acciones}")
            print(f"🗣️ Respuesta: {respuesta_verbal}")
            
            # 3. Hablar primero (en paralelo con acciones si se desea)
            if respuesta_verbal:
                hablar(respuesta_verbal)
            
            # 4. Ejecutar acciones físicas
            ejecutar_lista_acciones(acciones)
            
        except KeyboardInterrupt:
            print("Apagando Go2...")
            sport_client.StandDown()
            break
        except Exception as e:
            print(f"Error: {e}")
            hablar("Lo siento, hubo un error. Intenta de nuevo.")

if __name__ == "__main__":
    main()
```

---

## 🗺️ Roadmap Sugerido
```
Semana 1-2   →  Conectar Jetson al Go2, probar SDK básico
Semana 3     →  Integrar Whisper + micrófono, verificar STT en español
Semana 4     →  Conectar LLM (empezar con GPT-4 API, migrar a local después)
Semana 5     →  Integrar TTS y probar conversación básica
Semana 6-8   →  Afinar el system prompt, agregar más acciones, pruebas reales