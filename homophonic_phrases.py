from janome.tokenizer import Tokenizer
from pprint import pprint
import Levenshtein
from collections import defaultdict
import sys
import os
import re
import shutil

if not os.path.isfile('settings.py'):
    shutil.copy('_settings.py', 'settings.py')
    
import settings

def read_text_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        # '-->'が含まれる行と空白行を除外してテキストを結合
        cleaned_text = ''
        for line in lines:
            '''if not line.strip() or '-->' in line:
                continue'''
            cleaned_text += line

        return cleaned_text
    except FileNotFoundError:
        return "指定されたファイルは存在しません。"
    except Exception as e:
        return f"ファイルの読み込み中にエラーが発生しました: {str(e)}"
    
def remove_timecord(text):
    result = ''
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if '-->' in line:
            continue
        if line.isdigit():
            if i + 1 < len(lines) and '-->' in lines[i + 1]:
                continue
        result = result + '\n' + line

    return result


def extract_jukugo(text):
    # JanomeのTokenizerを初期化
    tokenizer = Tokenizer()

    jukugoList = []  # 熟語を格納するリスト

    # テキストを形態素解析し、名詞や動詞などの熟語を抽出
    for token in tokenizer.tokenize(text):
        # 名詞や動詞などの熟語を抽出
        print(token)
        if token.part_of_speech.split(',')[0] in ["名詞", "動詞", "形容詞", "副詞"]:
            if token.reading == '*'and '数' != token.part_of_speech.split(',')[1]:
                continue
            jukugoList.append(token)            

    return jukugoList#jukugoDict

def get_relative_ed(text1, text2):
    if len(text1) == 0 or len(text2) == 0:
        return 999
    dist = Levenshtein.distance(text1, text2)
    return dist/len(text1)

def create_key(token):
    return f"{token.reading}_{token.part_of_speech.split(',')[0]}_{token.part_of_speech.split(',')[1]}"

def find_similar_words(token_list):
    similar_words = defaultdict(list)

    for i, token1 in enumerate(token_list):
        if token1.reading == '*':
            continue  # 読みが '*' の場合、何もしない
        key = create_key(token1)
        if key not in similar_words.keys():
            similar_words[key].append(token1)

        for j, token2 in enumerate(token_list):#token動詞をそれぞれ突き合わせる
            if i < j:
                ed = get_relative_ed(token1.reading, token2.reading)
                #品詞や編集距離が近い条件に合致
                if (ed <= settings.ERROR_MARGIN and token1.part_of_speech.split(',')[0] == token2.part_of_speech.split(',')[0] 
                    and token1.part_of_speech.split(',')[1] == token2.part_of_speech.split(',')[1]):
                    for sw in similar_words[key]:
                        if sw.surface == token2.surface:
                            break
                    else:
                        similar_words[key].append(token2)
                    continue

        if len(similar_words[key])==1:
            del similar_words[key]


    return dict(similar_words)


def dispYomi(srt_text,token_list, dpReadings):
    lines = srt_text.split('\n')  # 文字列を行ごとに分割

    for yomi in dpReadings.keys():

        print('\n■'+str(yomi))
        for kanji in dpReadings[yomi]:
            print('┗'+kanji.surface)
            index = 0
            for token in token_list:
                if (kanji.surface == token.surface 
                    and kanji.part_of_speech.split(',')[0] == token.part_of_speech.split(',')[0] 
                    and kanji.part_of_speech.split(',')[1] == token.part_of_speech.split(',')[1]):
                    block,index=find_matching_line(srt_text,index,kanji.surface,dpReadings[yomi])
                    print(('        '+str(block))[-8:],end='\t')
                    print(('        '+str(index+1))[-6:] ,end='\t')
                    if index > -1 and index < len(lines):
                        print(lines[index])
                    else:
                        print('')


def find_matching_line(text,target_index, query, similar_words):
    lines = text.split('\n')  # 文字列を行ごとに分割

    before_target_index = True
    last_block=0



    for i,line in enumerate(lines):
        if before_target_index:
            if i >  target_index:
                before_target_index = False
            continue
        else:
            if '-->' in line:
                continue
            if line.isdigit():
                if i + 1 < len(lines) and '-->' in lines[i + 1]:
                    last_block=int(line)
            if query in line:
                for kanji in similar_words:
                    if kanji.surface in query:
                        continue
                    if kanji.surface in line and query != kanji.surface:
                        break
                else:
                    return last_block,i
                
                continue
                

    
    return -1,-1  # 一致箇所が見つからない場合は -1 を返す

def is_hiragana(input_str):
    # 正規表現を使用して、文字列がすべてひらがなで構成されているかチェック
    return bool(re.match(r'^[ぁ-んー]*$', input_str))

if __name__ == "__main__":
    # コマンドライン引数から渡されたファイルのパスを取得
    if len(sys.argv) == 2:
        file_path = sys.argv[1]
        print(f"渡されたファイルのパス: {file_path}")
    else:
        print("エラー: ファイルのパスを正しく渡してください。")
        exit(1)

    if os.path.isfile(file_path):
        pass
    else:
        print(f"{file_path} は存在しません。")
        exit(1)

    srt_text = read_text_file(file_path)
    text = remove_timecord(srt_text)
    print('-----------------------日本語形態素解析-----------------------')
    jukugoTList = extract_jukugo(text)
    print('--------------------------読み解析中--------------------------')
    dpReadings = find_similar_words(jukugoTList)
    print('\n\n---同音異義語、あるいはタイプミスと思われる語句が発見されました---')
    dispYomi(srt_text,jukugoTList,dpReadings)

    print('\n--------------------------------------------------------------')
    print('■{読み}_{品詞}_{品詞細分類}')
    print('┗{字幕ファイル内での用法}')
    print('{字幕ブロック番号}, {行数}, {行の内容}\nのフォーマットで表示しています。')

