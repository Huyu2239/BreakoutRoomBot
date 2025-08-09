import os


DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
SERVER_ID = int(os.getenv('SERVER_ID'))
CATEGORY_ID = int(os.getenv('CATEGORY_ID'))


if not all([DISCORD_BOT_TOKEN, SERVER_ID, CATEGORY_ID]):
    raise ValueError("必要な環境変数が設定されていません。.envファイルを確認してください。")
