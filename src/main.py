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
        
        # 既存のブレイクアウトルームをクリーンアップ
        await self._cleanup_existing_breakout_rooms()
    
    async def _cleanup_existing_breakout_rooms(self):
        """Bot起動時に残っているブレイクアウトルームをクリーンアップ"""
        logger = logging.getLogger("discord")
        total_cleaned = 0
        
        for guild in self.guilds:
            try:
                session = self.get_guild_session(guild.id)
                async with session['session_lock']:
                    # 設定されたカテゴリIDを探す（環境変数やDB設定がある場合）
                    # ここでは数字のみのチャンネル名を持つボイスチャンネルを対象とする
                    cleanup_count = 0
                    for category in guild.categories:
                        for channel in category.voice_channels:
                            if channel.name.isdigit() or (len(channel.name) == 3 and channel.name.zfill(3) == channel.name):
                                try:
                                    await channel.delete(reason="Bot restart cleanup")
                                    cleanup_count += 1
                                    logger.info(f"Cleaned up breakout room: {channel.name} in {guild.name}")
                                except Exception as e:
                                    logger.error(f"Failed to cleanup channel {channel.name} in {guild.name}: {e}")
                    
                    if cleanup_count > 0:
                        logger.info(f"Cleaned up {cleanup_count} breakout rooms in {guild.name}")
                        total_cleaned += cleanup_count
                        
            except Exception as e:
                logger.error(f"Error during cleanup in guild {guild.name}: {e}")
        
        if total_cleaned > 0:
            logger.info(f"Total cleaned up: {total_cleaned} breakout rooms across all guilds")

if __name__ == "__main__":
    bot = BreakoutRoomBot()
    bot.run(token=DISCORD_BOT_TOKEN)
