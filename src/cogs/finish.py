import logging
import discord
from discord.ext import commands
from discord import app_commands

logger = logging.getLogger(__name__)


class FinishCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="終了", description="ブレイクアウトルームを終了")
    async def finish(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        session = self.bot.room_sessions.get(interaction.guild.id)
        if session is None:
            return await interaction.followup.send("セッションが開始されていません。")

        # 先にメンバー移動
        for room in session.voice_channels:
            for member in room.members:
                try:
                    await member.move_to(session.main_voice_channel)
                except Exception:
                    pass

        # 次にチャンネル削除
        for room in session.voice_channels:
            try:
                await room.delete()
            except Exception:
                pass

        self.bot.room_sessions.pop(interaction.guild.id)
        await interaction.followup.send("ブレイクアウトルームを終了しました。")


async def setup(bot):
    await bot.add_cog(FinishCog(bot))
