import time
import sys
from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.go2.sport.sport_client import SportClient

if len(sys.argv) < 2:
    print("Uso: python3 test.py eth0")
    sys.exit(1)

ChannelFactoryInitialize(0, sys.argv[1])

client = SportClient()
client.SetTimeout(10.0)
client.Init()

print("Parándose...")
client.StandUp()
time.sleep(2)

print("Saludando!")
client.Hello()
time.sleep(3)

print("Sentándose...")
client.StandDown()
time.sleep(2)

print("Listo!")