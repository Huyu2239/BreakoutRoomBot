import asyncio
import logging
import random
import discord
from discord.ext import commands
from discord import app_commands

from libs.room_session import RoomSession


logger = logging.getLogger(__name__)


class StartCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="開始", description="ブレイクアウトルームを開始")
    @app_commands.rename(num="チャンネル数")
    async def start(self, interaction: discord.Interaction, num: int):
        await interaction.response.defer(thinking=True)
        if num < 1:
            return await interaction.followup.send("チャンネル数は1以上で設定してください。")
        if num > len(interaction.user.voice.channel.members):
            return await interaction.followup.send("部屋数がVC参加人数を超えています。")
        if not interaction.user.voice:
            return await interaction.followup.send("ボイスチャンネルに接続してください。")
        if self.bot.room_sessions.get(interaction.guild.id):
            return await interaction.followup.send("すでに開始されています。")

        self.bot.room_sessions[interaction.guild.id] = RoomSession(interaction.guild.id, interaction.user.voice.channel, [])

        category = interaction.user.voice.channel.category
        members = interaction.user.voice.channel.members
        try:
            channels = [await category.create_voice_channel(name=f"{str(i+1).zfill(3)}") for i in range(num)]
        except Exception as e:
            logger.error(f"Failed to create voice channels: {e}")
            return await interaction.followup.send("チャンネルを作成できませんでした。")
        self.bot.room_sessions[interaction.guild.id].voice_channels = channels

        # 無作為にmemberをchannelsに移動。
        random.shuffle(members)
        base_members_per_channel = len(members) // num
        extra_members = len(members) % num
        member_index = 0
        for i, channel in enumerate(channels):
            members_for_this_channel = base_members_per_channel
            if i < extra_members:
                members_for_this_channel += 1
            for _ in range(members_for_this_channel):
                if member_index < len(members):
                    await members[member_index].move_to(channel)
                    member_index += 1
        await interaction.followup.send("ブレイクアウトルームを開始しました。")


async def setup(bot):
    await bot.add_cog(StartCog(bot))