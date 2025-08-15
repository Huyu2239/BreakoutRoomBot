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
        
        if not hasattr(self.bot, 'session_lock'):
            return await interaction.followup.send("システムエラー: セッションロックが初期化されていません。")
            
        async with self.bot.session_lock:
            # 権限チェック: 管理者または特定の役割を持つユーザーのみ実行可能
            if not (interaction.user.guild_permissions.manage_channels or 
                   interaction.user.guild_permissions.administrator):
                return await interaction.followup.send("この操作には「チャンネルの管理」権限が必要です。")
                
            if not hasattr(self.bot, 'main_room') or self.bot.main_room is None:
                return await interaction.followup.send("開始されたブレイクアウトルームがありません。")
            if not hasattr(self.bot, 'breakout_rooms') or not self.bot.breakout_rooms:
                return await interaction.followup.send("削除するブレイクアウトルームがありません。")

            # ブレイクアウトルームの全メンバーをメインルームに移動
            moved_members = 0
            failed_moves = []
            for room in self.bot.breakout_rooms:
                for member in room.members:
                    try:
                        await member.move_to(self.bot.main_room)
                        moved_members += 1
                    except discord.HTTPException as e:
                        logger.error(f"Failed to move member {member.name}: {e}")
                        failed_moves.append(member.name)
                    except Exception as e:
                        logger.error(f"Unexpected error moving member {member.name}: {e}")
                        failed_moves.append(member.name)
            
            # ブレイクアウトルームを削除
            deleted_rooms = 0
            failed_deletes = []
            for room in self.bot.breakout_rooms:
                try:
                    await room.delete()
                    deleted_rooms += 1
                except discord.HTTPException as e:
                    logger.error(f"Failed to delete room {room.name}: {e}")
                    failed_deletes.append(room.name)
                except Exception as e:
                    logger.error(f"Unexpected error deleting room {room.name}: {e}")
                    failed_deletes.append(room.name)
            
            # 状態をリセット（削除に成功したかどうかに関わらず）
            self.bot.main_room = None
            self.bot.breakout_rooms = []
            
            # 結果を報告
            message = "ブレイクアウトルームを終了しました。"
            if failed_moves:
                message += f"\n⚠️ メンバー移動に失敗: {', '.join(failed_moves)}"
            if failed_deletes:
                message += f"\n⚠️ チャンネル削除に失敗: {', '.join(failed_deletes)}"
            
            await interaction.followup.send(message)


async def setup(bot):
    await bot.add_cog(FinishCog(bot))