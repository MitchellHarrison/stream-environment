import asyncio
from bot import Bot

async def main():
    bot = Bot()
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())

