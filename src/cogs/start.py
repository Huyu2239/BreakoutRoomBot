import logging
import random
import discord
from discord.ext import commands
from discord import app_commands

logger = logging.getLogger(__name__)


class StartCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="開始", description="ブレイクアウトルームを開始")
    @app_commands.describe(num="チャンネル数")
    async def start(self, interaction: discord.Interaction, num: int):
        await interaction.response.defer(thinking=True)
        
        # ギルドセッションを取得
        session = self.bot.get_guild_session(interaction.guild.id)
        
        async with session['session_lock']:
            # 既にセッションが開始されているかチェック
            if session['main_room']:
                return await interaction.followup.send("すでに開始されています。")
            
            # ユーザーの権限チェック
            if not (interaction.user.guild_permissions.manage_channels or 
                   interaction.user.guild_permissions.administrator):
                return await interaction.followup.send("この操作には「チャンネルの管理」権限が必要です。")
            
            # ボイスチャンネル接続チェック
            if not interaction.user.voice:
                return await interaction.followup.send("ボイスチャンネルに接続してください。")
            
            # 入力値検証
            if num < 1:
                return await interaction.followup.send("チャンネル数は1以上で設定してください。")
            
            if num > 50:  # Discord の制限を考慮
                return await interaction.followup.send("チャンネル数は50以下で設定してください。")
            
            voice_channel_members = interaction.user.voice.channel.members
            if num > len(voice_channel_members):
                return await interaction.followup.send("VC参加人数を超えています。")
            
            # カテゴリ設定確認
            if not session['category_id']:
                return await interaction.followup.send(
                    "カテゴリが設定されていません。`/set-category` でカテゴリを設定してください。"
                )
            
            category = interaction.guild.get_channel(session['category_id'])
            if not category:
                session['category_id'] = None  # 無効なIDをクリア
                return await interaction.followup.send(
                    "設定されたカテゴリが見つかりません。`/set-category` で再設定してください。"
                )
            
            # ボットの権限確認
            permissions = category.permissions_for(interaction.guild.me)
            if not (permissions.manage_channels and permissions.move_members):
                return await interaction.followup.send(
                    f"カテゴリ「{category.name}」でボットに必要な権限がありません。\n"
                    "必要な権限: チャンネルの管理、メンバーを移動"
                )
            
            # メインルームを設定
            session['main_room'] = interaction.user.voice.channel
            
            try:
                # チャンネル作成
                channels = [
                    await category.create_voice_channel(name=f"{str(i+1).zfill(3)}") 
                    for i in range(num)
                ]
            except discord.HTTPException as e:
                session['main_room'] = None
                logger.error(f"Failed to create voice channels in {interaction.guild.name}: {e}")
                return await interaction.followup.send("チャンネルの作成に失敗しました。権限を確認してください。")
            
            # メンバー移動
            members = voice_channel_members.copy()
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
                            logger.error(f"Failed to move member {members[member_index].name} in {interaction.guild.name}: {e}")
                            failed_moves.append(members[member_index].name)
                        except Exception as e:
                            logger.error(f"Unexpected error moving member {members[member_index].name} in {interaction.guild.name}: {e}")
                            failed_moves.append(members[member_index].name)
                        member_index += 1
            
            # セッション状態を更新
            session['breakout_rooms'] = channels
            
            # 結果報告
            if failed_moves:
                await interaction.followup.send(
                    f"ブレイクアウトルームを開始しました。\n"
                    f"⚠️ 以下のメンバーの移動に失敗しました: {', '.join(failed_moves)}"
                )
            else:
                await interaction.followup.send("ブレイクアウトルームを開始しました。")
            
            logger.info(f"Breakout session started in {interaction.guild.name} with {len(channels)} rooms")


async def setup(bot):
    await bot.add_cog(StartCog(bot))