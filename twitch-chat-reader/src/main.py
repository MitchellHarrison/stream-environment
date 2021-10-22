import asyncio
from listener import Listener

async def main():
    listener = Listener()
    await listener.run()


if __name__ == "__main__":
    asyncio.run(main())

