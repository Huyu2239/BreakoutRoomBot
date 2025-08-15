import logging
import discord
from discord.ext import commands
from discord import app_commands

logger = logging.getLogger(__name__)


class SetupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="set-category", description="ブレイクアウトルーム用のカテゴリを設定")
    @app_commands.describe(category="ブレイクアウトルームを作成するカテゴリ")
    async def set_category(self, interaction: discord.Interaction, category: discord.CategoryChannel):
        """ブレイクアウトルーム作成用のカテゴリを設定"""
        await interaction.response.defer(thinking=True)
        
        # 権限チェック
        if not (interaction.user.guild_permissions.manage_channels or 
               interaction.user.guild_permissions.administrator):
            return await interaction.followup.send("この操作には「チャンネルの管理」権限が必要です。")
        
        # ボットがカテゴリに対する権限を持っているかチェック
        permissions = category.permissions_for(interaction.guild.me)
        if not (permissions.manage_channels and permissions.move_members):
            return await interaction.followup.send(
                f"カテゴリ「{category.name}」でボットに以下の権限が必要です：\n"
                "• チャンネルの管理\n"
                "• メンバーを移動"
            )
        
        # ギルドセッションを取得してカテゴリIDを設定
        session = self.bot.get_guild_session(interaction.guild.id)
        session['category_id'] = category.id
        
        await interaction.followup.send(
            f"✅ ブレイクアウトルーム用カテゴリを「{category.name}」に設定しました。"
        )
        logger.info(f"Category set to {category.name} ({category.id}) in guild {interaction.guild.name}")

    @app_commands.command(name="show-settings", description="現在の設定を表示")
    async def show_settings(self, interaction: discord.Interaction):
        """現在のボット設定を表示"""
        session = self.bot.get_guild_session(interaction.guild.id)
        
        embed = discord.Embed(title="🔧 ブレイクアウトルームボット設定", color=0x00ff00)
        
        # カテゴリ設定
        if session['category_id']:
            category = interaction.guild.get_channel(session['category_id'])
            if category:
                embed.add_field(
                    name="📁 設定カテゴリ", 
                    value=f"{category.name} (ID: {category.id})", 
                    inline=False
                )
            else:
                embed.add_field(
                    name="📁 設定カテゴリ", 
                    value=f"⚠️ カテゴリが見つかりません (ID: {session['category_id']})", 
                    inline=False
                )
        else:
            embed.add_field(
                name="📁 設定カテゴリ", 
                value="❌ 未設定 (`/set-category` で設定してください)", 
                inline=False
            )
        
        # セッション状態
        if session['main_room']:
            embed.add_field(
                name="🎙️ 現在のセッション", 
                value=f"メインルーム: {session['main_room'].name}\nブレイクアウトルーム: {len(session['breakout_rooms'])}個", 
                inline=False
            )
        else:
            embed.add_field(
                name="🎙️ 現在のセッション", 
                value="なし", 
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="cleanup", description="残ったブレイクアウトルームを手動でクリーンアップ")
    async def cleanup(self, interaction: discord.Interaction):
        """残ったブレイクアウトルーム（001-999形式）を手動で削除"""
        await interaction.response.defer(thinking=True)
        
        # 権限チェック
        if not (interaction.user.guild_permissions.manage_channels or 
               interaction.user.guild_permissions.administrator):
            return await interaction.followup.send("この操作には「チャンネルの管理」権限が必要です。")
        
        session = self.bot.get_guild_session(interaction.guild.id)
        
        async with session['session_lock']:
            # アクティブなセッションがある場合は警告
            if session['main_room'] or session['breakout_rooms']:
                return await interaction.followup.send(
                    "⚠️ アクティブなブレイクアウトセッションがあります。\n"
                    "先に `/終了` でセッションを終了してからクリーンアップしてください。"
                )
            
            # 設定されたカテゴリがある場合はそこから、なければ全カテゴリから検索
            categories_to_check = []
            if session['category_id']:
                category = interaction.guild.get_channel(session['category_id'])
                if category:
                    categories_to_check = [category]
                else:
                    return await interaction.followup.send(
                        "設定されたカテゴリが見つかりません。`/set-category` で再設定してください。"
                    )
            else:
                categories_to_check = interaction.guild.categories
            
            cleanup_count = 0
            failed_deletes = []
            
            for category in categories_to_check:
                for channel in category.voice_channels:
                    # 001, 002, 003... の3桁ゼロパディング形式のみ削除
                    if (len(channel.name) == 3 and 
                        channel.name.isdigit() and 
                        channel.name.startswith('0')):
                        try:
                            await channel.delete(reason=f"Manual cleanup by {interaction.user}")
                            cleanup_count += 1
                            logger.info(f"Cleaned up breakout room: {channel.name} in {interaction.guild.name}")
                        except Exception as e:
                            logger.error(f"Failed to cleanup channel {channel.name} in {interaction.guild.name}: {e}")
                            failed_deletes.append(channel.name)
            
            # 結果報告
            message = f"🗑️ クリーンアップ完了: {cleanup_count}個のチャンネルを削除しました。"
            
            if failed_deletes:
                message += f"\n⚠️ 削除に失敗したチャンネル: {', '.join(failed_deletes)}"
            
            if cleanup_count == 0 and not failed_deletes:
                message = "✅ クリーンアップ対象のチャンネルは見つかりませんでした。"
            
            await interaction.followup.send(message)
            logger.info(f"Manual cleanup completed in {interaction.guild.name}: {cleanup_count} channels deleted")


async def setup(bot):
    await bot.add_cog(SetupCog(bot))