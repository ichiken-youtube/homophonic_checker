from pykakasi import kakasi
from janome.tokenizer import Tokenizer
import re
from pprint import pprint
import sys
import os


def read_text_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        # '-->'が含まれる行と空白行を除外してテキストを結合
        cleaned_text = ''
        for line in lines:
            #if not line.strip() or '-->' in line:
            #    continue
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

    jukugo_List = []  # 熟語を格納するリスト

    # テキストを形態素解析し、名詞や動詞などの熟語を抽出
    for token in tokenizer.tokenize(text):
        # 名詞や動詞などの熟語を抽出
        if token.part_of_speech.split(',')[0] in ["名詞", "動詞", "形容詞", "副詞"]:
            jukugo_List.append(token.surface)
            print(str(token.surface) + str(token.part_of_speech.split(',')))

    return jukugo_List

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
            result_dict[kanji['orig']] = kanji['hira']

    return result_dict

def find_duplicate_readings(dictionary):
    reading_to_kanji = {}  # 読みをキー、漢字を値とする辞書
    duplicates = {}  # 重複した読みを持つエントリを格納する辞書

    for kanji, reading in dictionary.items():
        if reading in reading_to_kanji:
            # 重複した読みが見つかった場合
            if reading not in duplicates:
                duplicates[reading] = [reading_to_kanji[reading]]
            duplicates[reading].append(kanji)
        else:
            reading_to_kanji[reading] = kanji

    return duplicates

def dispYomi(srt_text, dpReadings):

    for yomi in dpReadings.keys():
        print('\n□'+str(yomi))
        for kanji in dpReadings[yomi]:
            print('┗'+str(kanji))
            for line_num,line in enumerate(srt_text.splitlines()):
                #print(line)
                if kanji in line:
                    print('  '+str(line_num+1)+' '+str(line))


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
    print('--------------------日本語形態素解析--------------------')
    jukugo_d = extract_jukugo(text)
    #print(jukugo_d)
    jukugo = remove_duplicates(remove_numeric_elements(jukugo_d))
    #print(jukugo)
    print('--------------------読み解析中--------------------')
    yomiDict = convert_kanji_to_reading(jukugo)
    #print(yomiDict)
    dpReadings = find_duplicate_readings(yomiDict)
    print('--------------------同音異義語が発見されました。--------------------')
    dispYomi(srt_text,dpReadings)