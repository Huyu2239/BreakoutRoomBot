import os


def get_required_env_var(name: str, convert_func=None):
    """必須環境変数を安全に取得する"""
    value = os.getenv(name)
    if value is None:
        raise ValueError(f"必須環境変数 '{name}' が設定されていません。.envファイルを確認してください。")
    
    if convert_func:
        try:
            return convert_func(value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"環境変数 '{name}' の値 '{value}' を{convert_func.__name__}に変換できません: {e}")
    
    return value


DISCORD_BOT_TOKEN = get_required_env_var('DISCORD_BOT_TOKEN')
SERVER_ID = get_required_env_var('SERVER_ID', int)
CATEGORY_ID = get_required_env_var('CATEGORY_ID', int)
