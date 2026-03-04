import time
from unitree_sdk2py.go2.sport.sport_client import SportClient

sport_client = SportClient()
sport_client.Init()

def ejecutar_accion(accion: str):
    """Mapea texto de acción → comando SDK de Unitree"""
    
    if accion.startswith("CAMINAR_ADELANTE"):
        segundos = float(accion.split("(")[1].replace(")", ""))
        sport_client.Move(0.5, 0, 0)   # vx, vy, vyaw
        time.sleep(segundos)
        sport_client.StopMove()
        
    elif accion.startswith("CAMINAR_ATRAS"):
        segundos = float(accion.split("(")[1].replace(")", ""))
        sport_client.Move(-0.5, 0, 0)
        time.sleep(segundos)
        sport_client.StopMove()
        
    elif accion.startswith("GIRAR"):
        grados = float(accion.split("(")[1].replace(")", ""))
        sport_client.Move(0, 0, grados * 0.017)  # convertir a rad/s
        time.sleep(2)
        sport_client.StopMove()
        
    elif accion == "SENTARSE":
        sport_client.StandDown()
        
    elif accion == "PARARSE":
        sport_client.StandUp()
        
    elif accion == "SALUDAR":
        # Secuencia de movimiento personalizada
        sport_client.Hello()  # Si disponible en SDK
        
def ejecutar_lista_acciones(acciones: list):
    for accion in acciones:
        if not accion.startswith("HABLAR"):
            ejecutar_accion(accion)