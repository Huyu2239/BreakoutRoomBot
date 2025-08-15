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
        self.bot.session_lock = asyncio.Lock()

    @app_commands.command(name="開始", description="ブレイクアウトルームを開始")
    @app_commands.describe(num="チャンネル数")
    @app_commands.guilds(discord.Object(id=SERVER_ID))
    async def start(self, interaction: discord.Interaction, num: int):
        await interaction.response.defer(thinking=True)
        
        async with self.bot.session_lock:
            if self.bot.main_room:
                return await interaction.followup.send("すでに開始されています。")
            
            if not interaction.user.voice:
                return await interaction.followup.send("ボイスチャンネルに接続してください。")
            
            # 権限チェック: 管理者または特定の役割を持つユーザーのみ実行可能
            if not (interaction.user.guild_permissions.manage_channels or 
                   interaction.user.guild_permissions.administrator):
                return await interaction.followup.send("この操作には「チャンネルの管理」権限が必要です。")
            
            if num < 1:
                return await interaction.followup.send("チャンネル数は1以上で設定してください。")
            
            if num > 50:  # Discord の制限を考慮した上限設定
                return await interaction.followup.send("チャンネル数は50以下で設定してください。")
            
            voice_channel_members = interaction.user.voice.channel.members
            if num > len(voice_channel_members):
                return await interaction.followup.send("VC参加人数を超えています。")
            
            self.bot.main_room = interaction.user.voice.channel
            
            category = interaction.guild.get_channel(CATEGORY_ID)
            if not category:
                self.bot.main_room = None
                return await interaction.followup.send("指定されたカテゴリが見つかりません。")
            
            try:
                channels = [await category.create_voice_channel(name=f"{str(i+1).zfill(3)}") for i in range(num)]
            except discord.HTTPException as e:
                self.bot.main_room = None
                logger.error(f"Failed to create voice channels: {e}")
                return await interaction.followup.send("チャンネルの作成に失敗しました。権限を確認してください。")
            
            members = voice_channel_members
            
            # 無作為にmemberをchannelsに移動。
            random.shuffle(members)
            base_members_per_channel = len(members) // num
            extra_members = len(members) % num
            member_index = 0
            failed_moves = []
            
            for i, channel in enumerate(channels):
                members_for_this_channel = base_members_per_channel
                if i < extra_members:
                    members_for_this_channel += 1
                for _ in range(members_for_this_channel):
                    if member_index < len(members):
                        try:
                            await members[member_index].move_to(channel)
                        except discord.HTTPException as e:
                            logger.error(f"Failed to move member {members[member_index].name} to {channel.name}: {e}")
                            failed_moves.append(members[member_index].name)
                        except Exception as e:
                            logger.error(f"Unexpected error moving member {members[member_index].name}: {e}")
                            failed_moves.append(members[member_index].name)
                        member_index += 1
            
            self.bot.breakout_rooms = channels
            
            if failed_moves:
                await interaction.followup.send(
                    f"ブレイクアウトルームを開始しました。\n"
                    f"⚠️ 以下のメンバーの移動に失敗しました: {', '.join(failed_moves)}"
                )
            else:
                await interaction.followup.send("ブレイクアウトルームを開始しました。")


async def setup(bot):
    await bot.add_cog(StartCog(bot))