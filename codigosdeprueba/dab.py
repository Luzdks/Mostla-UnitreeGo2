import time
import sys
from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.go2.sport.sport_client import SportClient

if __name__ == "__main__":
    ChannelFactoryInitialize(0)

    sport_client = SportClient()
    sport_client.SetTimeout(10.0)
    sport_client.Init()

    print("Preparando el dab...")
    time.sleep(1)

    # Pararse
    sport_client.StandUp()
    print("De pie!")
    time.sleep(2)

    # Pararse en dos patas (dab position)
    sport_client.HandStand(True)
    print("DAB! 🤙")
    time.sleep(3)

    # Volver a posicion normal
    sport_client.HandStand(False)
    time.sleep(2)

    sport_client.StandDown()
    print("Listo!")