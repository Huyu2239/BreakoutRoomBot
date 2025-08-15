import glob
import logging
import asyncio
from typing import Dict, Optional, Any
import discord
from discord.ext import commands

from config import DISCORD_BOT_TOKEN


class BreakoutRoomBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="b!",
            intents=discord.Intents.all(),
        )
        self.help_command = None
        # 複数サーバーの状態管理
        self.guild_sessions: Dict[int, Dict[str, Any]] = {}

    def get_guild_session(self, guild_id: int) -> Dict[str, Any]:
        """ギルドのセッション情報を取得（存在しない場合は作成）"""
        if guild_id not in self.guild_sessions:
            self.guild_sessions[guild_id] = {
                'main_room': None,
                'breakout_rooms': [],
                'session_lock': asyncio.Lock(),
                'category_id': None
            }
        return self.guild_sessions[guild_id]

    async def setup_hook(self):
        logger = logging.getLogger("discord")
        
        try:
            await self.load_extension("jishaku")
            logger.info("Loaded jishaku extension")
        except Exception as e:
            logger.warning(f"Failed to load jishaku extension: {e}")
        
        for path in glob.glob("cogs/*.py", recursive=True):
            cog_name = path[:-3].replace("/", ".")
            try:
                await self.load_extension(cog_name)
                logger.info(f"Loaded extension: {cog_name}")
            except Exception as e:
                logger.error(f"Failed to load extension {cog_name}: {e}")
        
        try:
            await self.tree.sync()  # グローバル同期
            logger.info("Synced application commands globally")
        except Exception as e:
            logger.error(f"Failed to sync application commands: {e}")

    async def on_ready(self):
        logger = logging.getLogger("discord")
        logger.info(">> Bot is ready!")
        logger.info(f"Serving {len(self.guilds)} guilds")

if __name__ == "__main__":
    bot = BreakoutRoomBot()
    bot.run(token=DISCORD_BOT_TOKEN)
