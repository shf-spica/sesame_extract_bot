from janome.tokenizer import Tokenizer
from janome.analyzer import Analyzer
from janome.tokenfilter import TokenFilter

class CustomToken:
    """JanomeのTokenの代わりとして機能する自作クラス"""
    def __init__(self, surface, part_of_speech, infl_type, infl_form, base_form, reading, phonetic):
        self.surface = surface
        self.part_of_speech = part_of_speech
        self.infl_type = infl_type
        self.infl_form = infl_form
        self.base_form = base_form
        self.reading = reading
        self.phonetic = phonetic

    def __str__(self):
        return f"{self.surface}\t{self.part_of_speech},{self.infl_type},{self.infl_form},{self.base_form},{self.reading},{self.phonetic}"


class VerbChunkFilter(TokenFilter):
    """
    動詞 + 接続助詞(て/で) + 非自立動詞 を結合するカスタムフィルタ
    """
    def apply(self, tokens):
        buffer = []
        for token in tokens:
            pos = token.part_of_speech.split(',')
            
            # 状態0: バッファが空のとき
            if len(buffer) == 0:
                if pos[0] == '動詞' and pos[1] != '非自立':
                    buffer.append(token)
                else:
                    yield token
                    
            # 状態1: バッファに動詞が1つあるとき
            elif len(buffer) == 1:
                if pos[0] == '助詞' and pos[1] == '接続助詞' and token.surface in ('て', 'で'):
                    buffer.append(token)
                else:
                    yield buffer.pop(0)
                    if pos[0] == '動詞' and pos[1] != '非自立':
                        buffer.append(token)
                    else:
                        yield token
                        
            # 状態2: バッファに「動詞 + て/で」があるとき
            elif len(buffer) == 2:
                if pos[0] == '動詞' and pos[1] == '非自立':
                    # 3つ揃ったので結合して新しいトークンを作成
                    surface = buffer[0].surface + buffer[1].surface + token.surface
                    base_form = buffer[0].base_form + buffer[1].surface + token.base_form
                    
                    # 読み(reading)が取得できない('*'になる)単語への安全対策
                    r0 = buffer[0].reading if buffer[0].reading != '*' else buffer[0].surface
                    r1 = buffer[1].reading if buffer[1].reading != '*' else buffer[1].surface
                    r2 = token.reading if token.reading != '*' else token.surface
                    reading = r0 + r1 + r2
                    
                    # 自作のCustomTokenを使って結合結果を出力
                    new_token = CustomToken(
                        surface=surface,
                        part_of_speech=buffer[0].part_of_speech,
                        infl_type=buffer[0].infl_type,
                        infl_form=buffer[0].infl_form,
                        base_form=base_form,
                        reading=reading,
                        phonetic=reading
                    )
                    yield new_token
                    buffer = [] # バッファをリセット
                else:
                    yield buffer.pop(0)
                    yield buffer.pop(0)
                    if pos[0] == '動詞' and pos[1] != '非自立':
                        buffer.append(token)
                    else:
                        yield token

        # 最後まで処理してバッファに残っているものがあれば放出
        for token in buffer:
            yield token


# === テスト実行部分 ===
text = "早アタはどこの音取ってるかガチ聴き"

tokenizer = Tokenizer()
analyzer = Analyzer(tokenizer=tokenizer, token_filters=[VerbChunkFilter()])

print("--- カスタムフィルタ適用後 ---")
for token in analyzer.analyze(text):
    print(f"{token.surface}\t{token.part_of_speech}")

print(analyzer.analyze(text))