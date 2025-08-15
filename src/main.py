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
            await self.tree.sync(guild=discord.Object(id=SERVER_ID))
            logger.info("Synced application commands")
        except Exception as e:
            logger.error(f"Failed to sync application commands: {e}")

    async def on_ready(self):
        logger = logging.getLogger("discord")
        logger.info(">> Bot is ready!")
        
        # 既存のブレイクアウトルームをクリーンアップ
        await self._cleanup_existing_breakout_rooms()
    
    async def _cleanup_existing_breakout_rooms(self):
        """Bot起動時に残っているブレイクアウトルームをクリーンアップ"""
        logger = logging.getLogger("discord")
        try:
            guild = self.get_guild(SERVER_ID)
            if not guild:
                logger.warning(f"Guild with ID {SERVER_ID} not found")
                return
            
            category = guild.get_channel(CATEGORY_ID)
            if not category:
                logger.warning(f"Category with ID {CATEGORY_ID} not found")
                return
            
            # 数字のみの名前のチャンネルを削除（ブレイクアウトルーム）
            cleanup_count = 0
            for channel in category.voice_channels:
                if channel.name.isdigit() or (len(channel.name) == 3 and channel.name.zfill(3) == channel.name):
                    try:
                        await channel.delete(reason="Bot restart cleanup")
                        cleanup_count += 1
                        logger.info(f"Cleaned up breakout room: {channel.name}")
                    except Exception as e:
                        logger.error(f"Failed to cleanup channel {channel.name}: {e}")
            
            if cleanup_count > 0:
                logger.info(f"Cleaned up {cleanup_count} existing breakout rooms")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

if __name__ == "__main__":
    bot = BreakoutRoomBot()
    bot.run(token=DISCORD_BOT_TOKEN)
