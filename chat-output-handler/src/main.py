import asyncio
from outputhandler import OutputHandler

async def main():
    handler = OutputHandler()
    await handler.run()


if __name__ == "__main__":
    asyncio.run(main())

