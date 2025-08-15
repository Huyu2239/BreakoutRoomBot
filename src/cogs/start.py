import asyncio
import logging
import random
import discord
from discord.ext import commands
from discord import app_commands

from config import SERVER_ID, CATEGORY_ID

logger = logging.getLogger(__name__)


class StartCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.main_room = None
        self.bot.breakout_rooms = []

    @app_commands.command(name="開始", description="ブレイクアウトルームを開始")
    @app_commands.describe(num="チャンネル数")
    @app_commands.guilds(discord.Object(id=SERVER_ID))
    async def start(self, interaction: discord.Interaction, num: int):
        await interaction.response.defer(thinking=True)
        if self.bot.main_room:
            return await interaction.followup.send("すでに開始されています。")
        if not interaction.user.voice:
            return await interaction.followup.send("ボイスチャンネルに接続してください。")
        if num < 1:
            return await interaction.followup.send("チャンネル数は1以上で設定してください。")
        if num > len(interaction.user.voice.channel.members):
            return await interaction.followup.send("VS参加人数を超えています。")
        self.bot.main_room = interaction.user.voice.channel
        category = interaction.guild.get_channel(CATEGORY_ID)
        channels = [await category.create_voice_channel(name=f"{str(i+1).zfill(3)}") for i in range(num)]
        members = interaction.user.voice.channel.members
        

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
        self.bot.breakout_rooms = channels
        await interaction.followup.send("ブレイクアウトルームを開始しました。")


async def setup(bot):
    await bot.add_cog(StartCog(bot))