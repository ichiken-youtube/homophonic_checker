@echo off
setlocal enabledelayedexpansion
cd /d %~dp0

REM ドラッグ＆ドロップされたファイルの数をカウント
set /a count=0
for %%x in (%*) do (
    set /a count+=1
    set "file=%%x"
)

REM ドラッグ＆ドロップされたファイルが1つであるか確認
if %count% equ 1 (
    REM Pythonスクリプトを呼び出し、ファイルパスを渡す
    echo %file%
    python homophonic_phrases.py %file%
) else (
    echo エラー: ドラッグ＆ドロップで1つのファイルを指定してください。
)

pause