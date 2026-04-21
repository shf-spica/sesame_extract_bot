import discord
import os
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Intentの設定（これがないと文字が読めない）
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ ログイン完了: {client.user}")

@client.event
async def on_message(message):
    # 【最重要】どんなメッセージが来ても絶対にターミナルに出力する
    print(f"📩 受信テスト -> 送信者: {message.author.name}, 内容: {message.content}")

    # ボット自身の発言には反応しない
    if message.author == client.user:
        return

    # オウム返ししてDiscordに送信する
    await message.channel.send(f"「{message.content}」と受信しました！")

client.run(TOKEN)
