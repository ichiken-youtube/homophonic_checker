from pykakasi import kakasi
from janome.tokenizer import Tokenizer
from pprint import pprint
import Levenshtein
from collections import defaultdict
import sys
import os
import re


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
    for line in text.splitlines():
        if not line.strip() or '-->' in line:
            continue
        result += line

    return result


def extract_jukugo(text):
    # JanomeのTokenizerを初期化
    tokenizer = Tokenizer()

    jukugoList = []  # 熟語を格納するリスト
    #jukugoDict = {}

    # テキストを形態素解析し、名詞や動詞などの熟語を抽出
    for token in tokenizer.tokenize(text):
        # 名詞や動詞などの熟語を抽出
        print(token)
        if token.part_of_speech.split(',')[0] in ["名詞", "動詞", "形容詞", "副詞"]:
            #jukugoDict.append(token.surface)
            if token.reading == '*'and '数' != token.part_of_speech.split(',')[1]:
                continue
            #jukugoDict[token.surface] = token.reading
            jukugoList.append(token)
            #print(str(token.surface) + str(token.part_of_speech.split(',')))
            

    return jukugoList#jukugoDict

def remove_duplicates(input_list):
    unique_list = []
    seen_elements = set()

    for element in input_list:
        if element not in seen_elements:
            seen_elements.add(element)
            unique_list.append(element)

    return unique_list

def remove_numeric_elements(input_list):
    return [element for element in input_list if not element.isdigit()]

def convert_kanji_to_reading(word_list):
    # Kakasiオブジェクトを作成
    kks = kakasi()

    result_dict = {}  # 辞書を初期化

    # リスト内の漢字文字列を読みに変換し、辞書に追加
    for kanjis in word_list:
        #print(kanjis)
        conv = kks.convert(kanjis)
        for kanji in conv:
            #print(kanji)
            if(not is_hiragana(kanji['orig'])):
                result_dict[kanji['orig']] = kanji['hira']

    return result_dict

def find_duplicate_readings(tokens):
    duplicates = {}  # 重複した読みを持つエントリを格納する辞書

    for token in tokens:
        kanji = token.surface
        reading = token.reading + ',' + token.part_of_speech.split(',')[0] + ',' + token.part_of_speech.split(',')[1]
        if reading in duplicates:
            # 重複した読みが見つかった場合
            if kanji not in duplicates[reading]:
                duplicates[reading].append(kanji)
        else:
            duplicates[reading] = [kanji]

    return duplicates

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
                if (ed <= 0.3 and token1.part_of_speech.split(',')[0] == token2.part_of_speech.split(',')[0] 
                    and token1.part_of_speech.split(',')[1] == token2.part_of_speech.split(',')[1]):
#                    and token2.surface not in similar_words[key]
                    for sw in similar_words[key]:
                        if sw.surface == token2.surface:
                            break
                    else:
                        #print(token2.surface)
                        similar_words[key].append(token2)
                    continue

        if len(similar_words[key])==1:
            del similar_words[key]


    return dict(similar_words)


def dispYomi(srt_text,token_list, dpReadings):

    for yomi in dpReadings.keys():

        print('\n■'+str(yomi))
        for kanji in dpReadings[yomi]:
            print('┗'+kanji.surface)
            last_num = 0
            for token in token_list:
                #print(line)
                #print(token.surface,token.part_of_speech.split(','))
                if '数' == token.part_of_speech.split(',')[1]:
                    last_num = token.surface
                    #print(last_num)
                if (kanji.surface == token.surface 
                    and kanji.part_of_speech.split(',')[0] == token.part_of_speech.split(',')[0] 
                    and kanji.part_of_speech.split(',')[1] == token.part_of_speech.split(',')[1]):
                    print(last_num,end=', ')
                    index,line=find_matching_line(srt_text,last_num,kanji.surface)
                    print(index,end=', ')
                    print(line)


def find_matching_line(text, textBlockNum, query):
    lines = text.split('\n')  # 文字列を行ごとに分割

    x_found = False  # x に一致する行が見つかったかどうかを追跡するフラグ

    for i,line in enumerate(lines):
        if x_found:
            if query in line:
                return i+1,line  # x に一致する行の後で、A を含む行を見つけた場合、その行を返す
        if str(textBlockNum) == line:
            x_found = True  # x に一致する行が見つかったらフラグをセット
    
    return -1,''  # 一致箇所が見つからない場合は -1 を返す

def is_hiragana(input_str):
    # 正規表現を使用して、文字列がすべてひらがなで構成されているかチェック
    return bool(re.match(r'^[ぁ-んー]*$', input_str))

# Listing homophonic phrases in the subtitles
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
     #print(srt_text)
    print('-----------------------日本語形態素解析-----------------------')
    jukugoTList = extract_jukugo(text)
    print('--------------------------読み解析中--------------------------')
    dpReadings = find_similar_words(jukugoTList)
    print('\n\n---同音異義語、あるいはタイプミスと思われる語句が発見されました---')
    #pprint(dpReadings)
    dispYomi(srt_text,jukugoTList,dpReadings)

    print('\n--------------------------------------------------------------')
    print('{字幕ブロック番号}, {行数}, {行の内容}\nのフォーマットで表示しています。')

