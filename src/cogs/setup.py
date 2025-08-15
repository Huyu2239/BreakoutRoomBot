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


async def setup(bot):
    await bot.add_cog(SetupCog(bot))