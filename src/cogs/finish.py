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
        
        # ギルドセッションを取得
        session = self.bot.get_guild_session(interaction.guild.id)
        
        async with session['session_lock']:
            # 権限チェック
            if not (interaction.user.guild_permissions.manage_channels or 
                   interaction.user.guild_permissions.administrator):
                return await interaction.followup.send("この操作には「チャンネルの管理」権限が必要です。")
                
            # セッション存在確認
            if not session['main_room']:
                return await interaction.followup.send("開始されたブレイクアウトルームがありません。")
            
            if not session['breakout_rooms']:
                return await interaction.followup.send("削除するブレイクアウトルームがありません。")

            # ブレイクアウトルームの全メンバーをメインルームに移動
            moved_members = 0
            failed_moves = []
            
            for room in session['breakout_rooms']:
                for member in room.members:
                    try:
                        await member.move_to(session['main_room'])
                        moved_members += 1
                    except discord.HTTPException as e:
                        logger.error(f"Failed to move member {member.name} in {interaction.guild.name}: {e}")
                        failed_moves.append(member.name)
                    except Exception as e:
                        logger.error(f"Unexpected error moving member {member.name} in {interaction.guild.name}: {e}")
                        failed_moves.append(member.name)
            
            # ブレイクアウトルームを削除
            deleted_rooms = 0
            failed_deletes = []
            
            for room in session['breakout_rooms']:
                try:
                    await room.delete(reason="Breakout session ended")
                    deleted_rooms += 1
                except discord.HTTPException as e:
                    logger.error(f"Failed to delete room {room.name} in {interaction.guild.name}: {e}")
                    failed_deletes.append(room.name)
                except Exception as e:
                    logger.error(f"Unexpected error deleting room {room.name} in {interaction.guild.name}: {e}")
                    failed_deletes.append(room.name)
            
            # セッション状態をリセット
            session['main_room'] = None
            session['breakout_rooms'] = []
            
            # 結果報告
            message = f"ブレイクアウトルームを終了しました。\n"
            message += f"📊 移動したメンバー: {moved_members}人\n"
            message += f"🗑️ 削除したルーム: {deleted_rooms}個"
            
            if failed_moves:
                message += f"\n⚠️ メンバー移動に失敗: {', '.join(failed_moves)}"
            
            if failed_deletes:
                message += f"\n⚠️ チャンネル削除に失敗: {', '.join(failed_deletes)}"
            
            await interaction.followup.send(message)
            logger.info(f"Breakout session ended in {interaction.guild.name}: {moved_members} members moved, {deleted_rooms} rooms deleted")


async def setup(bot):
    await bot.add_cog(FinishCog(bot))