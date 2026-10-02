import asyncio

from base.grief import Bot
from base.config import CLIENT


async def run_bot() -> None:
    async with Bot() as bot:
        await bot.start(token=CLIENT.TOKEN)


if __name__ == "__main__":
    asyncio.run(run_bot())
