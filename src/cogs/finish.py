import logging
import discord
from discord.ext import commands
from discord import app_commands

from config import SERVER_ID

logger = logging.getLogger(__name__)


class FinishCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="終了", description="ブレイクアウトルームを終了")
    @app_commands.guilds(discord.Object(id=SERVER_ID))
    async def finish(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        if not hasattr(self.bot, 'main_room') or self.bot.main_room is None:
            return await interaction.followup.send("開始されたブレイクアウトルームがありません。")
        if not hasattr(self.bot, 'breakout_rooms') or not self.bot.breakout_rooms:
            return await interaction.followup.send("削除するブレイクアウトルームがありません。")

        # ブレイクアウトルームの全メンバーをメインルームに移動
        moved_members = 0
        for room in self.bot.breakout_rooms:
            for member in room.members:
                try:
                    await member.move_to(self.bot.main_room)
                    moved_members += 1
                except Exception as e:
                    logger.error(f"Failed to move member {member.name}: {e}")
        # ブレイクアウトルームを削除
        deleted_rooms = 0
        for room in self.bot.breakout_rooms:
            try:
                await room.delete()
                deleted_rooms += 1
            except Exception as e:
                logger.error(f"Failed to delete room {room.name}: {e}")
        # ボットの状態をリセット
        self.bot.main_room = None
        self.bot.breakout_rooms = []
        await interaction.followup.send("ブレイクアウトルームを終了しました。")


async def setup(bot):
    await bot.add_cog(FinishCog(bot))