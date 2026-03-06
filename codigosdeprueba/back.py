import sys
import time
from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.go2.sport.sport_client import SportClient

VELOCIDAD = 0.5
VELOCIDAD_GIRO = 0.5
DURACION_MOVIMIENTO = 5

COMANDOS = [
    ("parate",     "Ponerse de pie"),
    ("sientate",   "Sentarse"),
    ("adelante",   "Caminar adelante"),
    ("atras",      "Caminar atras"),
    ("derecha",    "Girar derecha"),
    ("izquierda",  "Girar izquierda"),
    ("alto",       "Detenerse"),
    ("saluda",     "Saludar"),
    ("backflip",   "Backflip"),
    ("frontflip",  "Frontflip"),
    ("leftflip",   "Flip izquierda"),
    ("handstand",  "Handstand"),
    ("recuperar",  "Recovery Stand"),
]

def ejecutar(sc, num):
    try:
        idx = int(num) - 1
    except ValueError:
        print("  Escribe un numero")
        return

    if idx < 0 or idx >= len(COMANDOS):
        print(f"  Numero invalido (1-{len(COMANDOS)})")
        return

    cmd = COMANDOS[idx][0]
    print(f"  >> Ejecutando: {COMANDOS[idx][1]}")

    if cmd == "parate":
        sc.StandUp()
    elif cmd == "sientate":
        sc.StandDown()
    elif cmd == "adelante":
        sc.Move(VELOCIDAD, 0, 0)
        time.sleep(DURACION_MOVIMIENTO)
        sc.StopMove()
    elif cmd == "atras":
        sc.Move(-VELOCIDAD, 0, 0)
        time.sleep(DURACION_MOVIMIENTO)
        sc.StopMove()
    elif cmd == "derecha":
        sc.Move(0, 0, -VELOCIDAD_GIRO)
        time.sleep(DURACION_MOVIMIENTO)
        sc.StopMove()
    elif cmd == "izquierda":
        sc.Move(0, 0, VELOCIDAD_GIRO)
        time.sleep(DURACION_MOVIMIENTO)
        sc.StopMove()
    elif cmd == "alto":
        sc.StopMove()
    elif cmd == "saluda":
        sc.Hello()
    elif cmd == "backflip":
        sc.BackFlip()
    elif cmd == "frontflip":
        sc.FrontFlip()
    elif cmd == "leftflip":
        sc.LeftFlip()
    elif cmd == "handstand":
        sc.HandStand(True)
        time.sleep(5)
        sc.HandStand(False)
    elif cmd == "recuperar":
        sc.RecoveryStand()
    print(f"  >> Listo")

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 escuincle_texto.py <interfaz_red>")
        sys.exit(1)

    ChannelFactoryInitialize(0, sys.argv[1])
    sc = SportClient()
    sc.SetTimeout(10.0)
    sc.Init()

    sc.StandUp()
    time.sleep(2)

    print("\n  ESCUINCLE - Control por Texto")
    print("  --------------------------------")
    for i, (_, desc) in enumerate(COMANDOS, 1):
        print(f"  {i:2d}. {desc}")
    print("  --------------------------------")
    print("  0 = salir\n")

    while True:
        try:
            cmd = input("escuincle> ")
            if cmd.strip() == "0":
                print("  Apagando...")
                sc.StopMove()
                sc.StandDown()
                time.sleep(2)
                break
            ejecutar(sc, cmd)
        except KeyboardInterrupt:
            print("\n  Apagando...")
            sc.StopMove()
            sc.StandDown()
            time.sleep(2)
            break

if __name__ == "__main__":
    main()