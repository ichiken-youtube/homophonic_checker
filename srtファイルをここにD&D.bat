@echo off
setlocal enabledelayedexpansion
cd /d %~dp0

REM �h���b�O���h���b�v���ꂽ�t�@�C���̐����J�E���g
set /a count=0
for %%x in (%*) do (
    set /a count+=1
    set "file=%%x"
)

REM �h���b�O���h���b�v���ꂽ�t�@�C����1�ł��邩�m�F
if %count% equ 1 (
    REM Python�X�N���v�g���Ăяo���A�t�@�C���p�X��n��
    echo %file%
    python homophonic_phrases.py %file%
) else (
    echo �G���[: �h���b�O���h���b�v��1�̃t�@�C�����w�肵�Ă��������B
)

pause