from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.dispatcher import Dispatcher
import asyncio
import warnings
import numpy as np


ip = "127.0.0.1"
port = 12000

def fromSonicPi(*args):
    print(args)

dispatcher = Dispatcher()
dispatcher.map("/sonicpi/*", fromSonicPi)
server = AsyncIOOSCUDPServer((ip, port), dispatcher, asyncio.get_event_loop())

async def loop():
    """Example main loop that only runs for 10 iterations before finishing"""
    i = 0
    global current_image
    while True:
        print(f"iteration: {i}")
        i += 1
        await asyncio.sleep(0.1)

async def init_main():
    server = AsyncIOOSCUDPServer((ip, port), dispatcher, asyncio.get_event_loop())
    transport, protocol = await server.create_serve_endpoint()  # Create datagram endpoint and start serving

    await loop()  # Enter main loop of program
    transport.close()  # Clean up serve endpoint

if __name__ == '__main__':
    asyncio.run(init_main())