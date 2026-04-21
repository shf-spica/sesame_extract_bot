import discord
import re
import asyncio
import os
from dotenv import load_dotenv
import MeCab

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

t = MeCab.Tagger('-r /etc/mecabrc -d /usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd')

class Fixed_Token:
    def __init__(self, surface="", reading="", part_of_speech=""):
        self.surface = surface
        self.reading = reading
        self.part_of_speech = part_of_speech

    def __str__(self):
        return f"{self.surface}\t{self.part_of_speech},{self.reading}"

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
    
    #tokenを接尾辞をまとめて整形
    text_to_analyze = message.content
    tokens = []
    node = t.parseToNode(text_to_analyze)

    while node:
        if node.surface:    #空白でなければ
            features = node.feature.split(',')
            pos = ",".join(features[0:4])
            reading = features[7] if len(features) > 7 else node.surface
            tokens.append(Fixed_Token(node.surface, reading, pos))
        node = node.next

    prev_char = None
    prev_chars = []
    prev_token = None
    prev_i = 0
    is_sesame_exist = False
    i = 0
    sesame_index_1 = []
    sesame_index_2 = []
    ignore = ['感嘆詞', 'フィラー']

    # 1回目のループ
    for token in tokens:
        print(token)

        reading = token.reading if token.reading != '*' else token.surface
        chars = re.findall(r'.[ぁぃぅぇぉゃゅょゎァィゥェォャュョヮ]?', reading)
        
        pos = token.part_of_speech.split(',')
        if pos[0] == '記号' or ( all(c == prev_char for c in chars) and all( c == prev_char for c in prev_chars)): # 記号または繰り返しならカウントを進めてスキップ
            i += 1
            continue

        if len(chars) > 0:
            if prev_char == chars[0] and token.surface != prev_token:
                is_sesame_exist = True
                sesame_index_1.append(prev_i)
                sesame_index_2.append(i)
            
            prev_char = chars[-1]
            prev_chars = chars
            prev_i = i

            if len(sesame_index_2) > 0 and sesame_index_2[-1] and (pos[0] == '接続助詞' or pos[1] == '非自立'):
                sesame_index_1.append(sesame_index_2[-1])
                sesame_index_2.pop()    #末尾を削除
                sesame_index_2.append(i)
                print(i)

        prev_token = token.surface
        i += 1

    result = ""
    i = 0

    # 2回目のループ
    for token in tokens:

        if i in sesame_index_1:
            result += f"{token.surface}"
        elif i in sesame_index_2:
            result += f"{token.surface}⁉️"            
        i += 1

    if is_sesame_exist:
        print(sesame_index_1)
        print(sesame_index_2)
        print(f"{result}")
        WAIT_SECONDS = 10800  # 待機時間（秒）

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

discord_token = os.getenv("TOKEN")
client.run(discord_token)