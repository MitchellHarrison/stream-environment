import asyncio
from chathandler import ChatHandler


async def main():
    handler = ChatHandler()
    await handler.run()


if __name__ == "__main__":
    asyncio.run(main())
