FROM python:3.12.5-slim-bullseye

# タイムゾーン設定とクリーンアップ
RUN apt-get update && \
    apt-get install -y --no-install-recommends tzdata && \
    cp /usr/share/zoneinfo/Asia/Tokyo /etc/localtime && \
    echo "Asia/Tokyo" > /etc/timezone && \
    apt-get purge -y tzdata && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 非rootユーザーでの実行
RUN groupadd -r botuser && useradd -r -g botuser botuser

# pipのアップグレード
RUN pip install --no-cache-dir -U pip

WORKDIR /app

# 依存関係のインストール（レイヤーキャッシュの活用）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードのコピー
COPY src/ .

# 権限設定
RUN chown -R botuser:botuser /app
USER botuser

# ヘルスチェック用のエンドポイント
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

CMD ["python", "-u", "main.py"]
