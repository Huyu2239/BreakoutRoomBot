import os


DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')


if not all([DISCORD_BOT_TOKEN]):
    raise ValueError("必要な環境変数が設定されていません。.envファイルを確認してください。")
