import discord
from janome.tokenizer import Tokenizer
import re
import asyncio
import os
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
t = Tokenizer()

@client.event
async def on_ready():
    print(f'ログイン成功: {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if not message.content.strip():
        return

    if "⁉️" in message.content:
        return

    text_to_analyze = message.content
    tokens = list(t.tokenize(text_to_analyze))
    
    prev_char = None
    is_sesame_exist = False
    i = 0
    sesame_index_1 = []
    sesame_index_2 = []

    # 1回目のループ
    for token in tokens:
        reading = token.reading if token.reading != '*' else token.surface
        chars = re.findall(r'.[ぁぃぅぇぉゃゅょゎァィゥェォャュョヮ]?', reading)
        
        if len(chars) > 0:
            if prev_char == chars[0]:
                is_sesame_exist = True
                # 【重要】この2行のインデント（字下げ）が if の中に入っている必要があります
                sesame_index_1.append(i - 1)
                sesame_index_2.append(i)
            
            prev_char = chars[-1]
            
        i += 1

    result = ""
    i = 0

    # 2回目のループ
    for token in tokens:

        if i in sesame_index_1:
            result += f"**{token.surface}"
        elif i in sesame_index_2:
            result += f"{token.surface}**"
        else:
            result += token.surface
            
        i += 1

    if is_sesame_exist:
        WAIT_SECONDS = 10  # 待機時間（秒）

        # 条件1：リアクション用
        def check_reaction(reaction, user):
            return user != client.user and reaction.message.id == message.id and str(reaction.emoji) == '⁉️'

        # 条件2：返信用
        def check_message(m):
            is_reply = m.reference is not None and m.reference.message_id == message.id
            is_exact_match = (m.content == "⁉️")
            return is_reply and is_exact_match

        # 2つのタスクを作成する
        reaction_task = asyncio.create_task(client.wait_for('reaction_add', check=check_reaction))
        message_task = asyncio.create_task(client.wait_for('message', check=check_message))

        # どちらか早い方が完了するまで待つ
        done, pending = await asyncio.wait(
            [reaction_task, message_task],
            timeout=WAIT_SECONDS,
            return_when=asyncio.FIRST_COMPLETED
        )

        # 待機が終わらなかった方（裏で待ち続けているタスク）を安全にキャンセルして消す
        for p in pending:
            p.cancel()

        # 結果の判定
        if not done:
            await message.reply(f"{result}⁉️")
            
load_dotenv()
discord_token = os.getenv("TOKEN")
client.run(discord_token)