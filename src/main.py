import glob
import logging
import discord
from discord.ext import commands

from config import DISCORD_BOT_TOKEN, SERVER_ID


class BreakoutRoomBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="b!",
            intents=discord.Intents.all(),
        )
        self.help_command = None

    async def setup_hook(self):
        await self.load_extension("jishaku")
        for path in glob.glob("cogs/*.py", recursive=True):
            await self.load_extension(path[:-3].replace("/", "."))
        await self.tree.sync(guild=discord.Object(id=SERVER_ID))

    async def on_ready(self):
        logger = logging.getLogger("discord")
        logger.info(">> Bot is ready!")

if __name__ == "__main__":
    bot = BreakoutRoomBot()
    bot.run(token=DISCORD_BOT_TOKEN)
